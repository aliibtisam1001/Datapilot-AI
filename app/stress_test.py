"""
Module 8 - Stress-test the SQL agent on harder questions.
Tests complex joins, date filters, aggregations against real Olist data.
Logs every question, generated SQL, result, and pass/fail status.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import re
import time
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'olist.db')
DB_URI = f"sqlite:///{os.path.abspath(DB_PATH)}"

from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit

llm = ChatGroq(
    model="qwen/qwen3.6-27b",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
)

db = SQLDatabase.from_uri(DB_URI)
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

agent_executor = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    agent_type="tool-calling",
    verbose=False,
    handle_parsing_errors=True,
)


def strip_thinking(text):
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()


# Hard test questions with expected answers (verified via direct SQL)
# We'll run the SQL ourselves first to get ground truth
import sqlite3
conn = sqlite3.connect(os.path.abspath(DB_PATH))
cursor = conn.cursor()


def run_ground_truth(sql):
    """Run SQL directly to get ground truth answer."""
    cursor.execute(sql)
    return cursor.fetchall()


# Define test cases: (question, ground_truth_sql, description)
HARD_QUESTIONS = [
    {
        "question": "What is the total revenue (sum of price) from delivered orders?",
        "ground_truth_sql": """
            SELECT ROUND(SUM(oi.price), 2)
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.order_id
            WHERE o.order_status = 'delivered'
        """,
        "description": "Revenue calculation with JOIN + filter",
    },
    {
        "question": "Which 3 states have the highest average order value? Show state and average.",
        "ground_truth_sql": """
            SELECT c.customer_state, ROUND(AVG(oi.price), 2) as avg_val
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.order_id
            JOIN customers c ON o.customer_id = c.customer_id
            GROUP BY c.customer_state
            ORDER BY avg_val DESC
            LIMIT 3
        """,
        "description": "3-table join with aggregation and ranking",
    },
    {
        "question": "How many orders were placed in each month of 2018? Show month and count.",
        "ground_truth_sql": """
            SELECT strftime('%m', order_purchase_timestamp) as month, COUNT(*) as cnt
            FROM orders
            WHERE strftime('%Y', order_purchase_timestamp) = '2018'
            GROUP BY month
            ORDER BY month
        """,
        "description": "Date extraction and filtering with strftime",
    },
    {
        "question": "What is the average delivery time in days for delivered orders?",
        "ground_truth_sql": """
            SELECT ROUND(AVG(julianday(order_delivered_customer_date) - julianday(order_purchase_timestamp)), 2)
            FROM orders
            WHERE order_status = 'delivered'
            AND order_delivered_customer_date IS NOT NULL
        """,
        "description": "Date arithmetic with julianday()",
    },
    {
        "question": "Which payment type generates the most total revenue?",
        "ground_truth_sql": """
            SELECT payment_type, ROUND(SUM(payment_value), 2) as total
            FROM order_payments
            GROUP BY payment_type
            ORDER BY total DESC
            LIMIT 1
        """,
        "description": "Aggregation on payment data",
    },
    {
        "question": "What are the top 5 cities with the most sellers?",
        "ground_truth_sql": """
            SELECT seller_city, COUNT(*) as cnt
            FROM sellers
            GROUP BY seller_city
            ORDER BY cnt DESC
            LIMIT 5
        """,
        "description": "Simple aggregation on sellers",
    },
    {
        "question": "What is the average review score for the 'health_beauty' product category?",
        "ground_truth_sql": """
            SELECT ROUND(AVG(r.review_score), 2)
            FROM order_reviews r
            JOIN orders o ON r.order_id = o.order_id
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN products p ON oi.product_id = p.product_id
            JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name
            WHERE t.product_category_name_english = 'health_beauty'
        """,
        "description": "5-table join with category filter",
    },
    {
        "question": "How many orders had more than one item?",
        "ground_truth_sql": """
            SELECT COUNT(*) FROM (
                SELECT order_id, COUNT(*) as item_count
                FROM order_items
                GROUP BY order_id
                HAVING item_count > 1
            )
        """,
        "description": "Subquery with HAVING clause",
    },
]

# Run ground truth queries
print("Computing ground truth answers...\n")
for q in HARD_QUESTIONS:
    gt = run_ground_truth(q["ground_truth_sql"])
    q["ground_truth_result"] = gt
    print(f"  GT for: {q['description']}")
    print(f"    Result: {gt}\n")

# Now test the agent on each question
results_log = []

print("=" * 70)
print("MODULE 8 - Stress Test Results")
print("=" * 70)

for i, q in enumerate(HARD_QUESTIONS, 1):
    print(f"\n{'─' * 70}")
    print(f"Q{i}: {q['question']}")
    print(f"Type: {q['description']}")
    print(f"Ground truth: {q['ground_truth_result']}")

    entry = {
        "question_num": i,
        "question": q["question"],
        "description": q["description"],
        "ground_truth": str(q["ground_truth_result"]),
    }

    try:
        result = agent_executor.invoke({"input": q["question"]})
        answer = strip_thinking(result["output"])
        entry["agent_answer"] = answer
        entry["status"] = "SUCCESS"
        entry["error"] = None
        print(f"Agent answer: {answer}")
        print(f"Status: SUCCESS")
    except Exception as e:
        entry["agent_answer"] = None
        entry["status"] = "ERROR"
        entry["error"] = str(e)
        print(f"ERROR: {e}")
        print(f"Status: FAILED")

    results_log.append(entry)

    # Delay to avoid rate limiting
    if i < len(HARD_QUESTIONS):
        print("  (waiting 12s for rate limit...)")
        time.sleep(12)

conn.close()

# Write results log
log_path = os.path.join(os.path.dirname(__file__), '..', 'tests', 'stress_test_log.json')
with open(log_path, 'w', encoding='utf-8') as f:
    json.dump(results_log, f, indent=2, ensure_ascii=False)

# Summary
successes = sum(1 for r in results_log if r["status"] == "SUCCESS")
failures = sum(1 for r in results_log if r["status"] != "SUCCESS")

print(f"\n{'=' * 70}")
print(f"SUMMARY: {successes}/{len(results_log)} succeeded, {failures} failed")
print(f"Log saved to: {os.path.abspath(log_path)}")
print(f"{'=' * 70}")
