from langchain_google_genai import ChatGoogleGenerativeAI
from prompts import table_summary_prompt, table_schema
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.prompts import PromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
import config as settings
import os

# Initializations
os.environ[settings.LLM_PROVIDER_TO_USE+"_API_KEY"] = settings.API_KEY
db = SQLDatabase.from_uri(settings.DB_CONNECTION_STRING, include_tables = settings.DB_TABLES)
llm = ChatGoogleGenerativeAI(model=settings.LLM_MODEL, temperature=0.7)

def main(question):
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    agent_executor = create_sql_agent(llm=llm,
                                      toolkit=toolkit,
                                      agent_type="zero-shot-react-description",
                                      verbose=True,
                                      handle_parsing_errors=True)
    table_summary_template = PromptTemplate.from_template(table_summary_prompt)
    table_summary = table_summary_template.invoke(
        {
            "table_schema": table_schema,
            "table_to_summarize": question
        }
    )
    result = agent_executor.invoke({"input": table_summary})
    
    # Return result
    return result["output"]

if __name__ == "__main__":
    main(prompt)
