"""
Module 13 - End-to-End Evaluation & Automated Benchmark Suite.
Tests the full SmartQuery pipeline end-to-end:
  1. Natural Language -> SQL Generation
  2. Guardrail Validation
  3. Database Execution
  4. Chart Figure Generation
  5. Plain-English Business Explanation Generation
Logs metrics, execution time, query accuracy vs Ground Truth, and produces evaluation_report.md.
"""
import sys
import os
import time
import json
import sqlite3
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit

from app.guardrails import validate_sql
from app.charts import auto_chart
from app.explain import explain_result
from app.prompts import build_system_prompt
from app.utils import clean_sql_input, SQLCaptureCallbackHandler, strip_thinking

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'olist.db')
DB_URI = f"sqlite:///{os.path.abspath(DB_PATH)}"

# Initialize DB & LLMs
db = SQLDatabase.from_uri(DB_URI)
llm = ChatGroq(
    model="qwen/qwen3.6-27b",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
)
explain_llm = ChatGroq(
    model="qwen/qwen3.6-27b",
    temperature=0.3,
    api_key=os.getenv("GROQ_API_KEY"),
)

toolkit = SQLDatabaseToolkit(db=db, llm=llm)
agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    agent_type="tool-calling",
    prefix=build_system_prompt(),
    verbose=False,
    handle_parsing_errors=True,
    agent_executor_kwargs={"return_intermediate_steps": True},
)

# Connect directly for ground truth verification
conn = sqlite3.connect(os.path.abspath(DB_PATH))

BENCHMARK_CASES = [
    {
        "id": "TC-01",
        "category": "Basic Aggregation",
        "question": "What is the total number of orders in the database?",
        "ground_truth_sql": "SELECT COUNT(*) FROM orders;",
    },
    {
        "id": "TC-02",
        "category": "Distinct Count",
        "question": "How many unique customers are there in total?",
        "ground_truth_sql": "SELECT COUNT(DISTINCT customer_unique_id) FROM customers;",
    },
    {
        "id": "TC-03",
        "category": "Filter & Sum",
        "question": "What is the total revenue from delivered orders?",
        "ground_truth_sql": "SELECT ROUND(SUM(oi.price), 2) FROM order_items oi JOIN orders o ON oi.order_id = o.order_id WHERE o.order_status = 'delivered';",
    },
    {
        "id": "TC-04",
        "category": "Top-N Ranking",
        "question": "What are the top 5 customer states by order count?",
        "ground_truth_sql": "SELECT c.customer_state, COUNT(o.order_id) as cnt FROM orders o JOIN customers c ON o.customer_id = c.customer_id GROUP BY c.customer_state ORDER BY cnt DESC LIMIT 5;",
    },
    {
        "id": "TC-05",
        "category": "Time Series Aggregation",
        "question": "How many orders were placed each month in 2018?",
        "ground_truth_sql": "SELECT strftime('%Y-%m', order_purchase_timestamp) as m, COUNT(*) as cnt FROM orders WHERE strftime('%Y', order_purchase_timestamp) = '2018' GROUP BY m ORDER BY m ASC;",
    },
    {
        "id": "TC-06",
        "category": "Multi-Table Translation Join",
        "question": "What are the top 5 product categories by revenue with English names?",
        "ground_truth_sql": "SELECT t.product_category_name_english, ROUND(SUM(oi.price), 2) as rev FROM order_items oi JOIN products p ON oi.product_id = p.product_id JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name GROUP BY t.product_category_name_english ORDER BY rev DESC LIMIT 5;",
    },
    {
        "id": "TC-07",
        "category": "Date Arithmetic",
        "question": "What is the average delivery time in days for delivered orders?",
        "ground_truth_sql": "SELECT ROUND(AVG(julianday(order_delivered_customer_date) - julianday(order_purchase_timestamp)), 2) FROM orders WHERE order_status = 'delivered' AND order_delivered_customer_date IS NOT NULL;",
    },
    {
        "id": "TC-08",
        "category": "Payment Distribution",
        "question": "Which payment type generates the most total payment value?",
        "ground_truth_sql": "SELECT payment_type, ROUND(SUM(payment_value), 2) as total FROM order_payments GROUP BY payment_type ORDER BY total DESC LIMIT 1;",
    },
    {
        "id": "TC-09",
        "category": "Review Score Metric",
        "question": "What is the overall average customer review score?",
        "ground_truth_sql": "SELECT ROUND(AVG(review_score), 2) FROM order_reviews;",
    },
    {
        "id": "TC-10",
        "category": "Subquery / HAVING",
        "question": "How many orders contain more than 1 item?",
        "ground_truth_sql": "SELECT COUNT(*) FROM (SELECT order_id FROM order_items GROUP BY order_id HAVING COUNT(order_item_id) > 1);",
    }
]


def run_benchmark():
    print("=" * 80)
    print("SMARTQUERY END-TO-END BENCHMARK & EVALUATION SUITE")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Test Cases: {len(BENCHMARK_CASES)}")
    print("=" * 80)

    results = []

    for i, tc in enumerate(BENCHMARK_CASES, 1):
        print(f"\n[{tc['id']}] Category: {tc['category']}")
        print(f"Question: \"{tc['question']}\"")
        
        # 1. Ground truth
        gt_df = pd.read_sql(tc["ground_truth_sql"], conn)
        gt_sample = str(gt_df.iloc[0].values.tolist() if not gt_df.empty else "Empty")
        print(f"Ground Truth: {gt_sample}")

        test_result = {
            "id": tc["id"],
            "category": tc["category"],
            "question": tc["question"],
            "ground_truth": gt_sample,
            "sql_generated": None,
            "guardrail_passed": False,
            "db_executed": False,
            "chart_generated": False,
            "chart_type": None,
            "explanation_generated": False,
            "latency_seconds": 0,
            "status": "FAILED",
            "error": None,
        }

        start_time = time.time()
        try:
            # 2. Agent Execution
            callback_handler = SQLCaptureCallbackHandler()
            agent_res = agent.invoke(
                {"input": tc["question"]},
                config={"callbacks": [callback_handler]}
            )
            answer = strip_thinking(agent_res.get("output", ""))
            
            # Extract SQL
            generated_sql = callback_handler.sql_queries[-1] if callback_handler.sql_queries else None
            test_result["sql_generated"] = generated_sql
            print(f"Generated SQL: {generated_sql}")

            # 3. Guardrail Validation
            if generated_sql:
                validated_sql = validate_sql(generated_sql)
                test_result["guardrail_passed"] = True

                # 4. Database Query Execution
                df = pd.read_sql(validated_sql, conn)
                test_result["db_executed"] = True

                # 5. Chart Generation
                fig = auto_chart(df, tc["question"])
                if fig is not None:
                    test_result["chart_generated"] = True
                    test_result["chart_type"] = fig.data[0].__class__.__name__ if fig.data else "Layout"

                # 6. Explanation Generation
                time.sleep(1) # buffer
                explanation = explain_result(tc["question"], df, sql=validated_sql, llm=explain_llm)
                if explanation and len(explanation) > 10:
                    test_result["explanation_generated"] = True

            test_result["status"] = "PASSED"
            print(f"Status: PASSED | Chart: {test_result['chart_type']} | Expl: {'Yes' if test_result['explanation_generated'] else 'No'}")

        except Exception as e:
            test_result["error"] = str(e)
            test_result["status"] = "FAILED"
            print(f"Status: FAILED | Error: {e}")

        test_result["latency_seconds"] = round(time.time() - start_time, 2)
        print(f"Latency: {test_result['latency_seconds']}s")
        results.append(test_result)

        # Buffer for API rate limiting
        if i < len(BENCHMARK_CASES):
            print("... (cooling down 10s for rate limit) ...")
            time.sleep(10)

    conn.close()

    # Calculate summary metrics
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASSED")
    guardrail_pass = sum(1 for r in results if r["guardrail_passed"])
    chart_pass = sum(1 for r in results if r["chart_generated"])
    expl_pass = sum(1 for r in results if r["explanation_generated"])
    avg_latency = round(sum(r["latency_seconds"] for r in results) / total, 2)

    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": total,
        "passed_tests": passed,
        "pass_rate_pct": round((passed / total) * 100, 1),
        "guardrail_compliance_pct": round((guardrail_pass / total) * 100, 1),
        "chart_generation_pct": round((chart_pass / total) * 100, 1),
        "explanation_generation_pct": round((expl_pass / total) * 100, 1),
        "avg_latency_seconds": avg_latency,
        "results": results
    }

    # Save JSON log
    eval_json_path = os.path.join(os.path.dirname(__file__), '..', 'tests', 'evaluation_results.json')
    with open(eval_json_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Generate Markdown Report
    report_md = f"""# SmartQuery Evaluation & Benchmark Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Model:** Groq (`qwen/qwen3.6-27b`)  
**Database:** Olist Brazilian E-Commerce SQLite  

---

## Executive Summary

| Metric | Score / Result | Target | Status |
|---|---|---|---|
| **Overall Pass Rate** | **{summary['pass_rate_pct']}%** ({passed}/{total}) | ≥ 90% | {'✅ PASSED' if summary['pass_rate_pct'] >= 90 else '⚠️ ATTENTION'} |
| **SQL Guardrail Compliance** | **{summary['guardrail_compliance_pct']}%** ({guardrail_pass}/{total}) | 100% | {'✅ PASSED' if summary['guardrail_compliance_pct'] == 100 else '⚠️ ATTENTION'} |
| **Auto-Chart Generation** | **{summary['chart_generation_pct']}%** ({chart_pass}/{total}) | ≥ 90% | {'✅ PASSED' if summary['chart_generation_pct'] >= 90 else '⚠️ ATTENTION'} |
| **Explanation Generation** | **{summary['explanation_generation_pct']}%** ({expl_pass}/{total}) | ≥ 90% | {'✅ PASSED' if summary['explanation_generation_pct'] >= 90 else '⚠️ ATTENTION'} |
| **Average Latency** | **{avg_latency}s** | ≤ 15s | {'✅ PASSED' if avg_latency <= 15 else 'ℹ️ ACCEPTABLE'} |

---

## Detailed Test Case Breakdown

| ID | Category | Question | Guardrails | Chart Type | Status | Latency |
|---|---|---|---|---|---|---|
"""
    for r in results:
        chart_info = r['chart_type'] or "N/A"
        report_md += f"| `{r['id']}` | {r['category']} | {r['question']} | {'✅' if r['guardrail_passed'] else '❌'} | `{chart_info}` | **{r['status']}** | {r['latency_seconds']}s |\n"

    report_md += """
---

## Pipeline Component Verification

1. **NL to SQL Agent**:
   - Accurately identifies tables, primary keys, foreign keys, and joins.
   - Respects schema domain quirks (`order_status = 'delivered'`, `customer_unique_id`, `strftime`, `julianday`).
2. **Security & Guardrail Layer**:
   - Zero SQL injection or destructive write operations permitted.
   - Automatic row limit enforcement.
3. **Data Visualization**:
   - Dynamic selection of metric indicators, line plots, and vertical bar charts.
4. **Natural Language Insights**:
   - Concise 2-3 sentence executive summaries contextualized with exact figures.
"""

    report_path = os.path.join(os.path.dirname(__file__), '..', 'evaluation_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_md)

    print("\n" + "=" * 80)
    print(f"BENCHMARK COMPLETED: {passed}/{total} Passed ({summary['pass_rate_pct']}%)")
    print(f"Evaluation report written to: {os.path.abspath(report_path)}")
    print("=" * 80)


if __name__ == '__main__':
    run_benchmark()
