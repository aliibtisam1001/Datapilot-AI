"""
Module 9 - Explanation Layer.
Takes a query result (DataFrame) and the original question,
sends both to Groq LLM, returns a 2-3 sentence plain-English summary.
"""
import os
import re
import pandas as pd
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()


def strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks from model output."""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()


def build_explanation_llm():
    """Create a ChatGroq instance for explanations."""
    return ChatGroq(
        model="qwen/qwen3.6-27b",
        temperature=0.3,
        api_key=os.getenv("GROQ_API_KEY"),
    )


def explain_result(question: str, df: pd.DataFrame, sql: str = None, llm=None) -> str:
    """
    Generate a plain-English explanation of a query result.

    Args:
        question: The original business question asked by the user.
        df: The pandas DataFrame containing the query result.
        sql: Optional SQL query that produced the result.
        llm: Optional ChatGroq instance (creates one if not provided).

    Returns:
        A 2-3 sentence plain-English summary of the result.
    """
    if llm is None:
        llm = build_explanation_llm()

    # Format the DataFrame for the prompt
    if df.empty:
        data_str = "(No results returned)"
    elif len(df) <= 20:
        data_str = df.to_string(index=False)
    else:
        data_str = df.head(20).to_string(index=False) + f"\n... ({len(df)} total rows)"

    prompt = f"""You are an executive business intelligence analyst assistant. A stakeholder asked a business question, and a SQL query was executed on the database to answer it.

Your job: Write a clear, concise 2-3 sentence summary of the results in plain English. Be specific with numbers. Do NOT mention SQL, databases, tables, or technical details — speak directly as if briefing an executive stakeholder.

User's question: {question}

Query results:
{data_str}
"""
    if sql:
        prompt += f"\nSQL used: {sql}\n"

    prompt += "\nPlain-English summary (2-3 sentences, no technical jargon):"

    response = llm.invoke(prompt)
    return strip_thinking(response.content)


# ============================================================
# Test when run directly
# ============================================================
if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    import sqlite3
    import time

    DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'olist.db')
    conn = sqlite3.connect(DB_PATH)

    llm = build_explanation_llm()

    test_cases = [
        {
            "question": "What are the top 5 product categories by revenue?",
            "sql": """
                SELECT t.product_category_name_english as category, ROUND(SUM(oi.price), 2) as revenue
                FROM order_items oi
                JOIN products p ON oi.product_id = p.product_id
                JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name
                GROUP BY t.product_category_name_english
                ORDER BY revenue DESC
                LIMIT 5
            """,
        },
        {
            "question": "What is the average delivery time by customer state for the top 5 states?",
            "sql": """
                SELECT c.customer_state,
                       ROUND(AVG(julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp)), 1) as avg_days
                FROM orders o
                JOIN customers c ON o.customer_id = c.customer_id
                WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
                GROUP BY c.customer_state
                ORDER BY avg_days ASC
                LIMIT 5
            """,
        },
        {
            "question": "How many orders were canceled and what percentage is that?",
            "sql": """
                SELECT
                    SUM(CASE WHEN order_status = 'canceled' THEN 1 ELSE 0 END) as canceled,
                    COUNT(*) as total,
                    ROUND(100.0 * SUM(CASE WHEN order_status = 'canceled' THEN 1 ELSE 0 END) / COUNT(*), 2) as pct
                FROM orders
            """,
        },
    ]

    print("=" * 60)
    print("MODULE 9 - Explanation Layer Tests")
    print("=" * 60)

    for i, tc in enumerate(test_cases, 1):
        print(f"\n{'─' * 60}")
        print(f"Test {i}: {tc['question']}")
        print(f"{'─' * 60}")

        df = pd.read_sql(tc["sql"], conn)
        print(f"\nData:\n{df.to_string(index=False)}")

        explanation = explain_result(tc["question"], df, sql=tc["sql"], llm=llm)
        print(f"\nExplanation:\n  {explanation}")

        if i < len(test_cases):
            print("  (waiting 12s for rate limit...)")
            time.sleep(12)

    conn.close()
    print(f"\n{'=' * 60}")
    print("Module 9 complete")
    print(f"{'=' * 60}")
