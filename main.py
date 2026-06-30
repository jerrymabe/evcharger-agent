from langchain.chat_models import init_chat_model
from langchain.chains import create_sql_query_chain
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_community.utilities import SQLDatabase
# from langchain_community.agent_toolkits import create_sql_agent
# from langchain_community.agent_toolkits import SQLDatabaseToolkit
import sqlite3, os, time, ast
import config as settings
from prompts import *
from classes import *
from sessions import Session

# Functions
def format_history():
    """Format history to AI understandable format."""
    
    chat_history = []
    history = state["history"][-settings.MAX_WINDOW*2:]
    for i in range(len(history)):
        if i%2==0:
            chat_history = chat_history + ["HumanQuery(content='"+history[i]['content']+"')"]
        else:
            chat_history = chat_history + ["AIResponse(content='"+history[i]['content']+"')"]
    state["formatted_history"] = ' '.join(chat_history)

def execute_sql_agent():
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()

    agent_template = PromptTemplate.from_template(agent_prompt)
    prompt = agent_template.invoke(
            {
                "question": state["question"],
                "history": state["formatted_history"],
                "coordinates": state["coordinates"],
                "user_type": state["user_type"],
                "table_schema": table_schema,
                "dialect": db.dialect,
                "top_k": settings.TOP_K_TO_QUERY,
            }
    )
    agent_executor = create_sql_agent(llm=llm, 
                                      toolkit=toolkit, 
                                      agent_type="zero-shot-react-description", 
                                      verbose=True, 
                                      handle_parsing_errors=True)
    result = agent_executor.invoke({"input": agent_template})
    print(result)
    state["final_res"] = result["output"]

def execute_query():
    """Execute SQL query."""
    
    execute_query_tool = QuerySQLDatabaseTool(db=db)
    state["result"] = execute_query_tool.invoke(state["query"])
    print("SQL result: ",state["result"],"\n")

def query_relevancy_agent():
    """Analyze relevancy of query."""
    
    user_prompt = "Query: {input}"
    relevancy_prompt_template = ChatPromptTemplate(
        [("system", query_relevancy_prompt), ("user", user_prompt)]
    )
    prompt = relevancy_prompt_template.invoke(
        {
            "input": state["question"]
        }
    )
    result = llm.invoke(prompt)
    print(result)
    result = ast.literal_eval(result.content)
    state["relevance_score"] = result["relevancy_score"]
    if result["relevancy_score"] == "0.0":
        state["final_res"] = result["answer"]

def rephrase_query_agent():
    """Rephrased query based on history."""

    user_prompt = "Query: {input}"
    rephraser_prompt_template = ChatPromptTemplate(
        [("system", sql_query_rephraser_prompt), ("user", user_prompt)]
    )
    if(len(state["history"]) > 0):
        prompt = rephraser_prompt_template.invoke(
            {
                "history": state["formatted_history"],
                "input": state["question"]
            }
        )
        structured_llm = llm.with_structured_output(RephrasedQueryOutput)
        result = structured_llm.invoke(prompt)
        state["rephrased_quest"] = result["query"]
    else:
        state["rephrased_quest"] = state["question"]+" My current coordinates are: "+str(state["coordinates"])

def evc_identify_agent():
    """Identify the EV Charger Station ID."""

    user_prompt = "Question: {input}"
    evc_identification_template = ChatPromptTemplate(
        [("system",evc_identification_prompt), ("user", user_prompt)]
    )
    evc_identification = evc_identification_template.invoke(
        {
            "dialect": db.dialect,
            "top_k": settings.TOP_K_TO_QUERY,
            "table_info": table_schema,
            "input": state["rephrased_quest"],
            "history": state["formatted_history"]
        }
    )
    evc_result = llm.invoke(evc_identification)
    evc_result = evc_result.content
    if "EV Charger ID" in evc_result:
        state["evc_charger_id"] = evc_result.split(':')[1].split('"')[1]
    else:
        state["query"] = evc_result.split(':')[1].split('"')[1]
        res = execute_query()
        state["evc_charger_id"] = state['result'].split('(')[1].split(',')[0]

def extrapolate_query_agent():
    """Rewrite user question based on multiple params on first run"""

    user_prompt = "Question: {input}"
    if state["user_type"] == "Customer":
        query_extrapolation_template = ChatPromptTemplate(
            [("system", user_query_extrapolation_prompt), ("user", user_prompt)]
        )
    else:
        query_extrapolation_template = ChatPromptTemplate(
            [("system", maintainer_query_extrapolation_prompt), ("user", user_prompt)]
        )
        
    prompt = query_extrapolation_template.invoke(
        {
            "input": state["rephrased_quest"],
            "evc_id": state["evc_charger_id"],
            "table_info": table_schema
        }
    )
    structured_model = llm.with_structured_output(Questions)
    questions = structured_model.invoke(prompt)
    state["decomopsed_quests"] = questions.questions

def rewrite_query_agent():
    """Rewrite user question based on history and tables on first run"""

    user_prompt = "Question: {input}"
    query_rewrite_template = ChatPromptTemplate(
        [("system", query_rewrite_prompt), ("user", user_prompt)]
    )
    rewrite_prompt = query_rewrite_template.invoke(
        {
            "input": state["rephrased_quest"],
            "table_info": table_schema,
            "history": state["formatted_history"],
            "evc_id": state["evc_charger_id"],
            "coordinates": state["coordinates"],
            "user_type": state["user_type"]
        }
    )
    structured_model = llm.with_structured_output(Questions)
    questions = structured_model.invoke(rewrite_prompt)
    state["decomopsed_quests"] = questions.questions

def rewrite_query_agent2():
    """Rewrite user question based on history and tables on first run"""

    user_prompt = "Question: {input}"
    query_rewrite_template = ChatPromptTemplate(
        [("system", query_rewrite_prompt2), ("user", user_prompt)]
    )
    rewrite_prompt = query_rewrite_template.invoke(
        {
            "input": state["question"],
            "table_info": table_schema,
            "history": state["formatted_history"],
            "coordinates": state["coordinates"],
            "user_type": state["user_type"]
        }
    )
    structured_model = llm.with_structured_output(Questions)
    questions = structured_model.invoke(rewrite_prompt)
    state["decomopsed_quests"] = questions.questions
        
def write_query_agent():
    """Generate SQL query to fetch information."""

    user_prompt = "Question: {input}"
    query_prompt_template = ChatPromptTemplate(
        [("system", sql_generator_prompt_coder), ("user", user_prompt)]
    )
    prompt = query_prompt_template.invoke(
        {
            "dialect": db.dialect,
            "top_k": settings.TOP_K_TO_QUERY,
            "input": state["quest"],
            "table_schema": table_schema
        }
    )
    structured_llm = llm.with_structured_output(SQLQueryOutput)
    result = structured_llm.invoke(prompt)
    state["query"] = result["query"]
    print("SQL query: ",state["query"],"\n")

def summary_agent(sorted_result):
    summary_template = PromptTemplate.from_template(summary_prompt5)
    prompt = summary_template.invoke(
            {
                "results": sorted_result,
                "history": state["formatted_history"],
                "question": state["question"]
            }
    )
    result = llm.invoke(prompt)
    state["final_res"] = result.content

# Initializations
os.environ[settings.LLM_PROVIDER_TO_USE+"_API_KEY"] = settings.API_KEY
db = SQLDatabase.from_uri(settings.DB_CONNECTION_STRING, include_tables = settings.DB_TABLES)
llm = init_chat_model(
    settings.LLM_MODEL, 
    model_provider = settings.LLM_MODEL_PROVIDER,
    # temperature = 1.0,
    # max_retries = 2,
    # max_tokens = settings.LLM_MAX_OUT_TOKENS,
    timeout = settings.LLM_TIMEOUT,
    # rate_limiter = 
)
conn = sqlite3.connect(settings.DB_NAME, check_same_thread=False)
cursor = conn.cursor() 
state = State()

# Main
def main(question, history, coordinates, selected_user, name, session_id):
    # Logging start time
    start = time.time()

    # Creating a new session
    session = Session(conn, cursor)
    if session_id:
        print("Session ID already available:", session_id)
    elif(len(history) == 0):
        user_id = name if name != "" else "TEST"
        session_id = session.create_new_session(user_id, question)
        print("Session ID:", session_id)
    else:
        session_id = session.get_latest_session()
        print("Session ID", session_id)
    
    # Add to state
    state["question"] = question
    state["history"] = history
    state["coordinates"] = coordinates
    state["user_type"] = selected_user
    print("User question: ",state["question"],"\n")
    print("History: ",state["history"],"\n")
    print("User coordinates: ",state["coordinates"],"\n")

    # Analyze query relevancy
    query_relevancy_agent()
    print("Relevance score: ",state["relevance_score"],"\n")

    if state["relevance_score"] == "1.0":
        # Format history for the model
        format_history()
        print("Formatted history: ",state["formatted_history"],"\n")

        # Rephrase question based on history
        # rephrase_query_agent()
        # print("Rephrased question: ",state["rephrased_quest"],"\n")

        # Identify the EVC
        # evc_identify_agent()
        # print("EVC identified: ",state["evc_charger_id"],"\n")

        # Rewriting questions to make it more detailed
        # extrapolate_query_agent() if history == '' else rewrite_query_agent()
        rewrite_query_agent2()
        print("Decomposed questions: ",state["decomopsed_quests"],"\n")

        # Write and execute the queries
        sorted_result = []
        for i in range(len(state["decomopsed_quests"])):
            state["quest"] = state["decomopsed_quests"][i]
            write_query_agent()
            execute_query()
            sorted_result.append({"question": state["quest"], "query":state["query"], "result": state["result"]})
        
        # Generate answer and summarize
        summary_agent(sorted_result)
        print("Summarized answer: ",state["final_res"],"\n")

        # # SQL agent
        # execute_sql_agent()
        # print("Summarized answer: ",state["final_res"],"\n")
        
    else:
        state["rephrased_quest"] = ""
        state["decomopsed_quests"] = ""

    # Logging end time
    end = time.time()

    # Write result to DB
    history_id = session.write_history(session_id, state["question"], str(state["decomopsed_quests"]), state["final_res"], end - start)
    session.update_session(session_id)
    
    # Return result
    return state["relevance_score"], state["final_res"]

if __name__ == "__main__":
    main(prompt, history, coordinates, selected_user, name, session_id)
