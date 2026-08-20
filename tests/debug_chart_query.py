import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
from app.guardrails import validate_sql

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'olist.db')
DB_URI = f"sqlite:///{os.path.abspath(DB_PATH)}"

from langchain_community.utilities import SQLDatabase
db = SQLDatabase.from_uri(DB_URI)

test_sql = "SELECT p.product_category_name, SUM(oi.price) AS total_revenue FROM order_items oi JOIN products p ON oi.product_id = p.product_id GROUP BY p.product_category_name ORDER BY total_revenue DESC LIMIT 5;"

print("Original SQL:", test_sql)
try:
    val_sql = validate_sql(test_sql)
    print("Validated SQL:", val_sql)
except Exception as e:
    print("Validate SQL Error:", e)
    val_sql = test_sql

def run_query_for_chart(db, sql):
    try:
        import sqlalchemy
        engine = sqlalchemy.create_engine(db._engine.url)
        with engine.connect() as conn:
            df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        print("Run query error:", e)
        return pd.DataFrame()

df = run_query_for_chart(db, val_sql)
print("DF shape:", df.shape)
print("DF:\n", df)

from app.charts import auto_chart
fig = auto_chart(df, "What are the top 5 product categories by revenue?")
print("FIG:", fig is not None)
