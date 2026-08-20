# SmartQuery Evaluation & Benchmark Report

**Generated:** 2026-08-21 04:35:00  
**Model:** Groq (`qwen/qwen3.6-27b`)  
**Database:** Olist Brazilian E-Commerce SQLite (`data/olist.db`)  
**Framework:** LangChain `create_sql_agent` (Tool Calling)  

---

## Executive Summary

| Metric | Score / Result | Target | Status |
|---|---|---|---|
| **Overall Pass Rate** | **100.0%** (10/10) | ≥ 90% | ✅ PASSED |
| **SQL Guardrail Compliance** | **100.0%** (10/10) | 100% | ✅ PASSED |
| **Auto-Chart Generation** | **100.0%** (10/10) | ≥ 90% | ✅ PASSED |
| **Explanation Generation** | **100.0%** (10/10) | ≥ 90% | ✅ PASSED |
| **Average Latency** | **3.86s** | ≤ 15s | ✅ PASSED |

---

## Detailed Test Case Breakdown

| ID | Category | Question | Generated SQL | Guardrails | Chart Type | Status | Latency |
|---|---|---|---|---|---|---|---|
| `TC-01` | Basic Aggregation | *What is the total number of orders in the database?* | `SELECT COUNT(*) AS total_orders FROM orders;` | ✅ | `Indicator` | **PASSED** | 3.32s |
| `TC-02` | Distinct Count | *How many unique customers are there in total?* | `SELECT COUNT(DISTINCT customer_unique_id) AS unique_customers FROM customers;` | ✅ | `Indicator` | **PASSED** | 4.88s |
| `TC-03` | Filter & Sum | *What is the total revenue from delivered orders?* | `SELECT ROUND(SUM(oi.price), 2) AS total_revenue FROM order_items oi JOIN orders o ON oi.order_id = o.order_id WHERE o.order_status = 'delivered';` | ✅ | `Indicator` | **PASSED** | 3.73s |
| `TC-04` | Top-N Ranking | *What are the top 5 customer states by order count?* | `SELECT c.customer_state, COUNT(o.order_id) AS total_orders FROM orders o JOIN customers c ON o.customer_id = c.customer_id GROUP BY c.customer_state ORDER BY total_orders DESC LIMIT 5;` | ✅ | `Bar` | **PASSED** | 4.14s |
| `TC-05` | Time Series Aggregation | *How many orders were placed each month in 2018?* | `SELECT strftime('%Y-%m', order_purchase_timestamp) AS order_month, COUNT(order_id) AS total_orders FROM orders WHERE strftime('%Y', order_purchase_timestamp) = '2018' GROUP BY order_month ORDER BY order_month ASC;` | ✅ | `Scatter (Line)` | **PASSED** | 3.86s |
| `TC-06` | Multi-Table Translation Join | *What are the top 5 product categories by revenue with English names?* | `SELECT t.product_category_name_english AS category, ROUND(SUM(oi.price), 2) AS total_revenue FROM order_items oi JOIN products p ON oi.product_id = p.product_id JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name JOIN orders o ON oi.order_id = o.order_id WHERE o.order_status = 'delivered' GROUP BY t.product_category_name_english ORDER BY total_revenue DESC LIMIT 5;` | ✅ | `Bar` | **PASSED** | 3.61s |
| `TC-07` | Date Arithmetic | *What is the average delivery time in days for delivered orders?* | `SELECT ROUND(AVG(julianday(order_delivered_customer_date) - julianday(order_purchase_timestamp)), 2) AS avg_delivery_days FROM orders WHERE order_status = 'delivered' AND order_delivered_customer_date IS NOT NULL;` | ✅ | `Indicator` | **PASSED** | 3.24s |
| `TC-08` | Payment Distribution | *Which payment type generates the most total payment value?* | `SELECT payment_type, SUM(payment_value) AS total_payment_value FROM order_payments GROUP BY payment_type ORDER BY total_payment_value DESC LIMIT 1;` | ✅ | `Indicator` | **PASSED** | 4.25s |
| `TC-09` | Review Score Metric | *What is the overall average customer review score?* | `SELECT ROUND(AVG(review_score), 2) AS average_review_score FROM order_reviews;` | ✅ | `Indicator` | **PASSED** | 3.32s |
| `TC-10` | Subquery / HAVING | *How many orders contain more than 1 item?* | `SELECT COUNT(*) AS orders_with_more_than_one_item FROM (SELECT order_id FROM order_items GROUP BY order_id HAVING COUNT(order_item_id) > 1);` | ✅ | `Indicator` | **PASSED** | 3.79s |

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
