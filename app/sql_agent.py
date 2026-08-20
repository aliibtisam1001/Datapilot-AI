"""
Module 6 - Build and test the basic SQL agent.
Uses create_sql_agent() with ChatGroq and SQLDatabaseToolkit.
Tests on 3-4 simple questions against the Olist database.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import re
from dotenv import load_dotenv

load_dotenv()

# Setup paths
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'olist.db')
DB_URI = f"sqlite:///{os.path.abspath(DB_PATH)}"

# Setup LLM
from langchain_groq import ChatGroq

llm = ChatGroq(
    model="qwen/qwen3.6-27b",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
)

# Setup Database connection
from langchain_community.utilities import SQLDatabase

db = SQLDatabase.from_uri(DB_URI)

# Setup SQL Agent
from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit

from app.prompts import build_system_prompt

agent_executor = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    agent_type="tool-calling",
    prefix=build_system_prompt(),
    verbose=True,
    handle_parsing_errors=True,
)


def strip_thinking(text):
    """Remove <think>...</think> blocks from model output."""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()


# Test questions
test_questions = [
    "How many total orders are in the database?",
    "How many distinct customers (by customer_unique_id) are there?",
    "What are the top 5 product categories by number of items sold? Show the English category names.",
    "What is the average review score across all reviews?",
]

print("=" * 70)
print("MODULE 6 - SQL Agent Test Results")
print("=" * 70)

for i, question in enumerate(test_questions, 1):
    print(f"\n{'─' * 70}")
    print(f"Question {i}: {question}")
    print(f"{'─' * 70}")
    try:
        result = agent_executor.invoke({"input": question})
        answer = strip_thinking(result["output"])
        print(f"\nAnswer: {answer}")
    except Exception as e:
        print(f"\nERROR: {e}")
    print()

print("=" * 70)
print("Module 6 complete - SQL Agent tested on all questions")
print("=" * 70)
