from pydantic import BaseModel, Field
from typing_extensions import Annotated, TypedDict
from typing import List

class State(TypedDict):
    relevance_score: str
    user_type: str
    question: str
    rephrased_quest: str
    decomopsed_quests: List
    history: List
    formatted_history: str
    coordinates: List
    evc_charger_id: str
    quest: str
    query: str
    result: str
    final_res: str

class QueryOutput(TypedDict):
    """Output of query."""

    query: Annotated[str, ..., "A valid answer."]

class RephrasedQueryOutput(TypedDict):
    """Rephrased query."""

    query: Annotated[str, ..., "A valid rephrased query."]

class SQLQueryOutput(TypedDict):
    """Generated SQL query."""

    query: Annotated[str, ..., "A valid syntactically correct SQL query."]

class Questions(BaseModel):
    """Decomposed questions."""
    
    questions: List[str] = Field(
        description="A list of sub-questions related to the input query."
    )