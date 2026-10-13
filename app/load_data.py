"""
Module 3 - Inspect Olist CSVs, extract zip if needed, and load into SQLite olist.db.
"""
import os
import sys
import pandas as pd
import sqlalchemy
import zipfile
from pandas.api import types as pd_types
from sqlalchemy import (
    BigInteger,
    Column,
    Float,
    ForeignKeyConstraint,
    Index,
    MetaData,
    PrimaryKeyConstraint,
    Table,
    Text,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
DB_PATH = os.path.join(DATA_DIR, 'olist.db')

PRIMARY_KEYS = {
    "customers": ("customer_id",),
    "orders": ("order_id",),
    "order_items": ("order_id", "order_item_id"),
    "order_payments": ("order_id", "payment_sequential"),
    "order_reviews": ("review_id", "order_id"),
    "products": ("product_id",),
    "sellers": ("seller_id",),
    "product_category_name_translation": ("product_category_name",),
}

FOREIGN_KEYS = {
    "orders": [("customer_id", "customers", "customer_id")],
    "order_items": [
        ("order_id", "orders", "order_id"),
        ("product_id", "products", "product_id"),
        ("seller_id", "sellers", "seller_id"),
    ],
    "order_payments": [("order_id", "orders", "order_id")],
    "order_reviews": [("order_id", "orders", "order_id")],
    "products": [
        (
            "product_category_name",
            "product_category_name_translation",
            "product_category_name",
        )
    ],
}

INDEX_COLUMNS = {
    "customers": ("customer_unique_id", "customer_state"),
    "orders": ("customer_id", "order_status", "order_purchase_timestamp"),
    "order_items": ("product_id", "seller_id"),
    "order_payments": ("payment_type",),
    "order_reviews": ("order_id", "review_score"),
    "products": ("product_category_name",),
    "sellers": ("seller_state",),
    "geolocation": ("geolocation_zip_code_prefix",),
}


def _sql_type(series: pd.Series):
    if pd_types.is_integer_dtype(series.dtype):
        return BigInteger()
    if pd_types.is_float_dtype(series.dtype):
        return Float()
    return Text()


def _create_normalized_schema(engine, dataframes):
    """Create the demo schema with real PK/FK metadata and useful indexes."""
    metadata = MetaData()
    tables = {}

    for table_name, df in dataframes.items():
        constraints = []
        primary_keys = PRIMARY_KEYS.get(table_name, ())
        if primary_keys:
            constraints.append(PrimaryKeyConstraint(*primary_keys))
        for column, parent_table, parent_column in FOREIGN_KEYS.get(table_name, []):
            constraints.append(
                ForeignKeyConstraint([column], [f"{parent_table}.{parent_column}"])
            )

        tables[table_name] = Table(
            table_name,
            metadata,
            *(Column(column, _sql_type(df[column]), nullable=column not in primary_keys)
              for column in df.columns),
            *constraints,
        )

    for table_name, columns in INDEX_COLUMNS.items():
        table = tables.get(table_name)
        if table is None:
            continue
        for column in columns:
            if column in table.c:
                Index(f"ix_{table_name}_{column}", table.c[column])

    metadata.drop_all(engine)
    metadata.create_all(engine)
    return tables


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

    # Build into a temporary file and replace only after a complete load so an
    # interrupted import cannot leave the demo database half-created.
    build_path = DB_PATH + ".building"
    if os.path.exists(build_path):
        os.remove(build_path)
    engine = sqlalchemy.create_engine(f"sqlite:///{build_path}")
    _create_normalized_schema(engine, dataframes)
    for table_name, df in dataframes.items():
        df.to_sql(
            table_name,
            engine,
            index=False,
            if_exists='append',
            chunksize=5000,
        )

    with engine.begin() as conn:
        conn.execute(sqlalchemy.text("ANALYZE"))
    engine.dispose()
    os.replace(build_path, DB_PATH)

    print(f"olist.db created successfully at: {os.path.abspath(DB_PATH)}")
    return DB_PATH


if __name__ == '__main__':
    create_sqlite_database()
