"""Optional legacy LangChain SQL-agent builder.

The production application uses the faster single-turn generator. This module
remains available for manual comparison without performing API calls on import.
"""
import os
import re

from dotenv import load_dotenv
from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq

from app.prompts import build_system_prompt

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "olist.db")
DB_URI = f"sqlite:///{os.path.abspath(DB_PATH)}"


def build_legacy_agent(api_key: str = None, model: str = "qwen/qwen3.6-27b"):
    """Build the slower tool-calling agent only when explicitly requested."""
    llm = ChatGroq(
        model=model,
        temperature=0,
        api_key=api_key or os.getenv("GROQ_API_KEY"),
    )
    database = SQLDatabase.from_uri(DB_URI)
    toolkit = SQLDatabaseToolkit(db=database, llm=llm)
    return create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        agent_type="tool-calling",
        prefix=build_system_prompt(),
        verbose=False,
        handle_parsing_errors=True,
    )


def strip_thinking(text):
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def main():
    agent = build_legacy_agent()
    questions = [
        "How many total orders are in the database?",
        "How many distinct customers are there?",
        "What are the top 5 product categories by number of items sold?",
        "What is the average review score?",
    ]
    for question in questions:
        result = agent.invoke({"input": question})
        print(question)
        print(strip_thinking(result["output"]))


if __name__ == "__main__":
    main()
