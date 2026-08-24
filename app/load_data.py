"""
Module 3 - Inspect Olist CSVs, extract zip if needed, and load into SQLite olist.db.
"""
import os
import sys
import pandas as pd
import sqlalchemy
import zipfile

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
DB_PATH = os.path.join(DATA_DIR, 'olist.db')


def create_sqlite_database():
    """Extract CSVs from olist_csvs.zip if needed and load all tables into SQLite olist.db."""
    os.makedirs(DATA_DIR, exist_ok=True)
    zip_path = os.path.join(DATA_DIR, 'olist_csvs.zip')
    
    # Check if CSVs exist, if not try unzipping olist_csvs.zip
    csv_files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith('.csv')])
    if not csv_files and os.path.exists(zip_path):
        print(f"Extracting CSVs from {zip_path}...")
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(DATA_DIR)
        csv_files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith('.csv')])
    
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {DATA_DIR} to build database.")

    dataframes = {}
    for csv_file in csv_files:
        filepath = os.path.join(DATA_DIR, csv_file)
        df = pd.read_csv(filepath)
        table_name = csv_file.replace('.csv', '').replace('olist_', '').replace('_dataset', '')
        dataframes[table_name] = df

    engine = sqlalchemy.create_engine(f"sqlite:///{DB_PATH}")
    for table_name, df in dataframes.items():
        df.to_sql(table_name, engine, index=False, if_exists='replace')

    print(f"✅ olist.db created successfully at: {os.path.abspath(DB_PATH)}")
    return DB_PATH


if __name__ == '__main__':
    create_sqlite_database()
