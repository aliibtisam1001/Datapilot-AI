"""
Module 12 - Schema-Aware Prompting & Domain-Specific Few-Shot Examples.
Provides custom system prompts, business domain rules, and curated few-shot
SQL examples tailored specifically to the Olist E-Commerce dataset.
"""

# Domain-specific rules and schema quirks for Olist
OLIST_DOMAIN_RULES = """
=== OLIST E-COMMERCE DATABASE RULES & QUIRKS ===
1. REVENUE CALCULATION:
   - Revenue should be calculated using `oi.price` from `order_items`.
   - When calculating actual realized revenue, ALWAYS filter for completed/delivered orders: `WHERE o.order_status = 'delivered'`.
   - Freight value (`oi.freight_value`) is separate from product price. Only include freight if explicitly asked.

2. PRODUCT CATEGORY NAMES:
   - Categories in the `products` table are in Portuguese (e.g. 'beleza_saude', 'informatica_acessorios').
   - To get English category names, JOIN `products` with `product_category_name_translation` on `product_category_name` and select `product_category_name_english`.
   - NOTE TYPO IN SCHEMA: The column is spelled `product_name_lenght` and `product_description_lenght` (ending in 'ht', not 'th').

3. DATES & TIME IN SQLITE:
   - All timestamps are stored as ISO 8601 TEXT strings (e.g. 'YYYY-MM-DD HH:MM:SS').
   - For year/month extraction, use SQLite's `strftime()` function:
     - Year: `strftime('%Y', order_purchase_timestamp)`
     - Month (01-12): `strftime('%m', order_purchase_timestamp)`
     - Year-Month: `strftime('%Y-%m', order_purchase_timestamp)`
   - For date differences (delivery duration, processing time), use `julianday()`:
     - `ROUND(AVG(julianday(order_delivered_customer_date) - julianday(order_purchase_timestamp)), 2)`

4. CUSTOMER IDENTIFICATION:
   - `customer_id` is unique per order/transaction.
   - `customer_unique_id` represents the unique human customer. For distinct customer counts or repeat buyers, ALWAYS use `COUNT(DISTINCT customer_unique_id)`.

5. REVIEWS:
   - `review_score` is an integer from 1 to 5 in the `order_reviews` table.
   - One order can have reviews joined on `order_id`.

6. SAFETY & PERFORMANCE:
   - Only execute SELECT queries.
   - Always include a reasonable LIMIT (e.g. 5, 10, or 20) when ranking or listing records unless asked for an overall count or aggregate.
"""

FEW_SHOT_EXAMPLES = [
    {
        "question": "What is the total revenue from delivered orders?",
        "sql": """SELECT ROUND(SUM(oi.price), 2) AS total_revenue
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered';"""
    },
    {
        "question": "What are the top 5 product categories by revenue in English?",
        "sql": """SELECT 
    t.product_category_name_english AS category,
    ROUND(SUM(oi.price), 2) AS total_revenue
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY t.product_category_name_english
ORDER BY total_revenue DESC
LIMIT 5;"""
    },
    {
        "question": "What is the average delivery time in days for each state?",
        "sql": """SELECT 
    c.customer_state,
    ROUND(AVG(julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp)), 1) AS avg_delivery_days,
    COUNT(o.order_id) AS total_delivered_orders
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered' 
  AND o.order_delivered_customer_date IS NOT NULL
GROUP BY c.customer_state
ORDER BY avg_delivery_days ASC;"""
    },
    {
        "question": "How many repeat customers do we have?",
        "sql": """SELECT COUNT(*) AS repeat_customers_count
FROM (
    SELECT customer_unique_id
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY customer_unique_id
    HAVING COUNT(DISTINCT o.order_id) > 1
);"""
    },
    {
        "question": "What is the monthly order trend in 2018?",
        "sql": """SELECT 
    strftime('%Y-%m', order_purchase_timestamp) AS order_month,
    COUNT(order_id) AS total_orders
FROM orders
WHERE strftime('%Y', order_purchase_timestamp) = '2018'
GROUP BY order_month
ORDER BY order_month ASC;"""
    }
]


def build_universal_system_prompt(dialect: str = "sqlite", schema_str: str = "") -> str:
    """Build a dynamic, dialect-aware system prompt for any arbitrary database schema."""
    dialect_upper = dialect.upper()
    prompt = f"""You are an elite SQL Business Intelligence Analyst AI.
Your goal is to answer the user's business question by querying the connected {dialect_upper} database accurately.

=== CONNECTED DATABASE SCHEMA ===
{schema_str}

=== INSTRUCTIONS & CONSTRAINTS ===
1. Understand the user's business intent and identify the required tables and joins.
2. Only write safe, read-only SELECT queries. Never generate DROP, DELETE, INSERT, UPDATE, or ALTER statements.
3. Use ONLY table names and column names that exist in the schema above. NEVER invent columns.
4. Format dates and aggregations strictly following the {dialect_upper} dialect rules.
5. Provide a clear, helpful final answer to the user summarizing the findings.
"""
    return prompt


def build_system_prompt() -> str:
    """Build legacy Olist-specific system prompt (used for demo fallback)."""
    prompt = (
        "You are an expert SQL Business Intelligence analyst assistant querying a SQLite database of "
        "the Olist Brazilian E-Commerce dataset.\n\n"
        "Your goal is to answer the user's business question by querying the database accurately and efficiently.\n\n"
        + OLIST_DOMAIN_RULES
        + "\n=== FEW-SHOT QUERY EXAMPLES FOR REFERENCE ===\n"
    )
    for idx, eg in enumerate(FEW_SHOT_EXAMPLES, 1):
        prompt += f"\nExample {idx}:\nUser Question: {eg['question']}\nSQL Query:\n{eg['sql']}\n"

    prompt += (
        "\n=== INSTRUCTIONS ===\n"
        "1. Understand the question and identify the relevant tables and relationships.\n"
        "2. Only use the provided SQL tools (sql_db_list_tables, sql_db_schema, sql_db_query, sql_db_query_checker).\n"
        "3. NEVER attempt to execute python, bash, or plotting tools.\n"
        "4. Construct clean, syntactically correct SQLite SELECT queries following all domain rules above.\n"
        "5. Interpret the query result and provide a clear, helpful final answer to the user."
    )
    return prompt
