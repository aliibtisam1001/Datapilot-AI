"""
Module 5 - Connect LangChain to the Olist SQLite database.
Uses SQLDatabase.from_uri() and prints detected tables/sample rows.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os

# The DB file
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'olist.db')
DB_URI = f"sqlite:///{os.path.abspath(DB_PATH)}"

print(f"Connecting LangChain to: {DB_URI}\n")

from langchain_community.utilities import SQLDatabase

db = SQLDatabase.from_uri(DB_URI)

# 1. Print detected tables
usable_tables = db.get_usable_table_names()
print(f"Usable tables ({len(usable_tables)}):")
for t in sorted(usable_tables):
    print(f"  - {t}")

# 2. Print schema info (DDL) that LangChain sees
print("\n" + "=" * 60)
print("Table schemas (as LangChain sees them):")
print("=" * 60)
table_info = db.get_table_info()
print(table_info)

# 3. Run a quick test query through LangChain's db.run()
print("=" * 60)
print("Test query via db.run():")
print("=" * 60)
result = db.run("SELECT COUNT(*) AS total_orders FROM orders;")
print(f"  SELECT COUNT(*) FROM orders => {result}")

result2 = db.run("SELECT order_status, COUNT(*) as cnt FROM orders GROUP BY order_status ORDER BY cnt DESC LIMIT 5;")
print(f"  Top 5 order statuses => {result2}")

print("\n✅ LangChain SQLDatabase connection verified!")
