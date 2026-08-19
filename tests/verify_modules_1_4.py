"""
Comprehensive verification of Modules 1-4.
Run this to confirm everything is set up correctly.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import subprocess

print('=' * 60)
print('MODULE 1 - Environment Check')
print('=' * 60)

import langchain, langchain_groq, streamlit, plotly, pandas, sqlalchemy, pytest, dotenv
print(f'  langchain:   {langchain.__version__}')
print(f'  streamlit:   {streamlit.__version__}')
print(f'  plotly:      {plotly.__version__}')
print(f'  pandas:      {pandas.__version__}')
print(f'  sqlalchemy:  {sqlalchemy.__version__}')
print(f'  pytest:      {pytest.__version__}')
print('  All packages: OK')

for d in ['app', 'data', 'tests', 'notebooks']:
    status = 'OK' if os.path.isdir(d) else 'MISSING'
    print(f'  Folder /{d}: {status}')

r = subprocess.run(['git', 'log', '--oneline'], capture_output=True, text=True)
print(f'  Git commits: {len(r.stdout.strip().splitlines())}')
print()

print('=' * 60)
print('MODULE 2 - Groq API Key Check')
print('=' * 60)

from dotenv import load_dotenv
load_dotenv()
key = os.getenv('GROQ_API_KEY')
print(f'  .env file exists: {os.path.isfile(".env")}')
has_key = 'YES' if key else 'NO'
masked = f'{key[:8]}...{key[-4:]}' if key else 'N/A'
print(f'  GROQ_API_KEY loaded: {has_key} ({masked})')

r = subprocess.run(['git', 'status', '--porcelain', '.env'], capture_output=True, text=True)
ignored = 'YES' if not r.stdout.strip() else 'NO - EXPOSED!'
print(f'  .env ignored by git: {ignored}')
print()

print('=' * 60)
print('MODULE 3 - Database Check')
print('=' * 60)

import sqlite3

db_path = 'data/olist.db'
print(f'  olist.db exists: {os.path.isfile(db_path)}')
size_mb = os.path.getsize(db_path) / (1024 * 1024)
print(f'  olist.db size: {size_mb:.1f} MB')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cursor.fetchall()]
print(f'  Tables ({len(tables)}): {tables}')

expected = {
    'customers': 99441,
    'geolocation': 1000163,
    'order_items': 112650,
    'order_payments': 103886,
    'order_reviews': 99224,
    'orders': 99441,
    'products': 32951,
    'sellers': 3095,
    'product_category_name_translation': 71,
}

all_match = True
for t in tables:
    cursor.execute(f'SELECT COUNT(*) FROM [{t}]')
    actual = cursor.fetchone()[0]
    exp = expected.get(t, -1)
    if actual == exp:
        print(f'    {t}: {actual:>10,} rows  OK')
    else:
        all_match = False
        print(f'    {t}: {actual:>10,} rows  MISMATCH (expected {exp})')

print(f'  All row counts match: {"YES" if all_match else "NO"}')

cursor.execute('SELECT COUNT(DISTINCT customer_unique_id) FROM customers')
unique_customers = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM orders WHERE order_status = 'delivered'")
delivered = cursor.fetchone()[0]
print(f'  Unique customers: {unique_customers:,}')
print(f'  Delivered orders: {delivered:,}')
print()

print('=' * 60)
print('MODULE 4 - Schema Doc Check')
print('=' * 60)

schema_exists = os.path.isfile('schema_notes.md')
print(f'  schema_notes.md exists: {schema_exists}')
if schema_exists:
    with open('schema_notes.md', 'r', encoding='utf-8') as f:
        content = f.read()
    all_documented = True
    for t in tables:
        if t not in content:
            all_documented = False
            print(f'    WARNING: table "{t}" not mentioned!')
    if all_documented:
        print(f'  All tables documented: YES')
    print(f'  Document size: {len(content):,} chars')

conn.close()
print()
print('=' * 60)
result = 'ALL MODULES 1-4: PASSED' if all_match and schema_exists and key else 'SOME CHECKS FAILED'
print(result)
print('=' * 60)
