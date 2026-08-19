"""
Module 3 - Inspect Olist CSVs and load them into SQLite.
"""
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import sqlalchemy

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
DB_PATH = os.path.join(DATA_DIR, 'olist.db')

# Step 1: List and inspect all CSV files
csv_files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith('.csv')])
print(f"Found {len(csv_files)} CSV files:\n")

dataframes = {}
for csv_file in csv_files:
    filepath = os.path.join(DATA_DIR, csv_file)
    df = pd.read_csv(filepath)
    # Derive a clean table name
    table_name = csv_file.replace('.csv', '').replace('olist_', '').replace('_dataset', '')
    dataframes[table_name] = df
    
    print(f"=== {csv_file} => table: '{table_name}' ===")
    print(f"  Rows: {len(df):,}")
    print(f"  Columns ({len(df.columns)}): {list(df.columns)}")
    print(f"  Dtypes:")
    for col, dtype in df.dtypes.items():
        print(f"    {col}: {dtype}")
    print()

# Step 2: Load into SQLite
print("=" * 60)
print(f"Loading into SQLite: {DB_PATH}")
print("=" * 60)

# Remove existing DB if present
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print("Removed existing olist.db")

engine = sqlalchemy.create_engine(f"sqlite:///{DB_PATH}")

for table_name, df in dataframes.items():
    df.to_sql(table_name, engine, index=False, if_exists='replace')
    print(f"  Loaded '{table_name}': {len(df):,} rows")

# Step 3: Verify by reading back from SQLite
print("\n" + "=" * 60)
print("Verification - reading back from SQLite:")
print("=" * 60)

with engine.connect() as conn:
    # List all tables
    result = conn.execute(sqlalchemy.text(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ))
    tables = [row[0] for row in result]
    print(f"\nTables in olist.db: {tables}\n")
    
    for table in tables:
        count = conn.execute(sqlalchemy.text(f"SELECT COUNT(*) FROM [{table}]")).scalar()
        print(f"  {table}: {count:,} rows")
    
    # Show sample rows from orders table
    print("\n--- Sample rows from 'orders' table ---")
    sample = pd.read_sql("SELECT * FROM orders LIMIT 3", conn)
    print(sample.to_string(index=False))
    
    print("\n--- Sample rows from 'order_items' table ---")
    sample = pd.read_sql("SELECT * FROM order_items LIMIT 3", conn)
    print(sample.to_string(index=False))

print(f"\n✅ olist.db created successfully at: {os.path.abspath(DB_PATH)}")
print(f"   File size: {os.path.getsize(DB_PATH) / (1024*1024):.1f} MB")
