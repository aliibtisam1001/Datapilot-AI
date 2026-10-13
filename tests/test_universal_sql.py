"""
Tests for Universal AI SQL Generation & Schema Selection (Phase 3).
Validates SQL generation against arbitrary domain schemas (E-Commerce, Sales CRM, HR Payroll).
"""
import os
import pytest
import sqlalchemy
from sqlalchemy import create_engine
import pandas as pd
from dotenv import load_dotenv

from app.database import get_database_schema
from app.agent.schema_selector import SchemaSelector
from app.agent.sql_generator import UniversalSQLGenerator, generate_sql_query
from app.guardrails import validate_sql

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
RUN_LIVE_GROQ_TESTS = os.getenv("RUN_LIVE_GROQ_TESTS") == "1"


@pytest.fixture
def ecommerce_engine():
    """Create in-memory SQLite database for custom e-commerce schema."""
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(sqlalchemy.text("""
            CREATE TABLE store_customers (
                cust_id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                country TEXT NOT NULL
            );
        """))
        conn.execute(sqlalchemy.text("""
            CREATE TABLE customer_orders (
                order_id INTEGER PRIMARY KEY,
                cust_id INTEGER,
                order_amount REAL NOT NULL,
                order_date TEXT NOT NULL,
                FOREIGN KEY (cust_id) REFERENCES store_customers(cust_id)
            );
        """))
        conn.execute(sqlalchemy.text("""
            INSERT INTO store_customers VALUES (1, 'Alice Smith', 'USA'), (2, 'Bob Jones', 'Canada'), (3, 'Charlie Brown', 'USA');
        """))
        conn.execute(sqlalchemy.text("""
            INSERT INTO customer_orders VALUES (101, 1, 250.0, '2024-01-15'), (102, 1, 150.0, '2024-02-10'), (103, 2, 500.0, '2024-01-20');
        """))
        conn.commit()
    return engine


@pytest.fixture
def sales_engine():
    """Create in-memory SQLite database for Sales CRM schema."""
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(sqlalchemy.text("""
            CREATE TABLE sales_reps (
                rep_id INTEGER PRIMARY KEY,
                rep_name TEXT NOT NULL,
                region TEXT NOT NULL
            );
        """))
        conn.execute(sqlalchemy.text("""
            CREATE TABLE closed_deals (
                deal_id INTEGER PRIMARY KEY,
                rep_id INTEGER,
                deal_value REAL NOT NULL,
                stage TEXT NOT NULL,
                closed_at TEXT NOT NULL,
                FOREIGN KEY (rep_id) REFERENCES sales_reps(rep_id)
            );
        """))
        conn.execute(sqlalchemy.text("""
            INSERT INTO sales_reps VALUES (1, 'David Miller', 'North'), (2, 'Emma Watson', 'South');
        """))
        conn.execute(sqlalchemy.text("""
            INSERT INTO closed_deals VALUES (1, 1, 12000.0, 'Won', '2024-03-01'), (2, 2, 45000.0, 'Won', '2024-03-05');
        """))
        conn.commit()
    return engine


@pytest.fixture
def hr_engine():
    """Create in-memory SQLite database for HR payroll schema."""
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(sqlalchemy.text("""
            CREATE TABLE company_departments (
                dept_id INTEGER PRIMARY KEY,
                dept_name TEXT NOT NULL
            );
        """))
        conn.execute(sqlalchemy.text("""
            CREATE TABLE staff_directory (
                staff_id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                salary REAL NOT NULL,
                dept_id INTEGER,
                FOREIGN KEY (dept_id) REFERENCES company_departments(dept_id)
            );
        """))
        conn.execute(sqlalchemy.text("""
            INSERT INTO company_departments VALUES (10, 'Engineering'), (20, 'Marketing');
        """))
        conn.execute(sqlalchemy.text("""
            INSERT INTO staff_directory VALUES (1, 'Sarah Connor', 120000.0, 10), (2, 'John Doe', 85000.0, 20), (3, 'Kyle Reese', 110000.0, 10);
        """))
        conn.commit()
    return engine


def test_schema_selector_pruning():
    """Verify that SchemaSelector prunes a multi-table schema to relevant tables."""
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        for i in range(12):
            conn.execute(sqlalchemy.text(f"CREATE TABLE table_{i} (id INT PRIMARY KEY, val_{i} TEXT);"))
        conn.commit()

    full_schema = get_database_schema(engine)
    assert len(full_schema.tables) == 12

    pruned = SchemaSelector.select_relevant_schema(full_schema, "Show me information about table_3 and table_7", max_tables=5)
    assert len(pruned.tables) <= 5
    assert "table_3" in pruned.tables
    assert "table_7" in pruned.tables


@pytest.mark.skipif(not (GROQ_API_KEY and RUN_LIVE_GROQ_TESTS), reason="Set RUN_LIVE_GROQ_TESTS=1 for live LLM tests")
def test_universal_sql_ecommerce(ecommerce_engine):
    """Test SQL generation on custom e-commerce schema."""
    schema = get_database_schema(ecommerce_engine)
    res = generate_sql_query(
        question="What is the total order amount for each customer name?",
        db_schema=schema,
        api_key=GROQ_API_KEY,
    )
    assert res.sql is not None
    assert "SELECT" in res.sql.upper()
    assert "store_customers" in res.sql or "customer_orders" in res.sql

    with ecommerce_engine.connect() as conn:
        df = pd.read_sql(sqlalchemy.text(res.sql), conn)
    assert not df.empty
    assert len(df) >= 1


@pytest.mark.skipif(not (GROQ_API_KEY and RUN_LIVE_GROQ_TESTS), reason="Set RUN_LIVE_GROQ_TESTS=1 for live LLM tests")
def test_universal_sql_sales_crm(sales_engine):
    """Test SQL generation on Sales CRM schema."""
    schema = get_database_schema(sales_engine)
    res = generate_sql_query(
        question="Which sales rep generated the highest deal value?",
        db_schema=schema,
        api_key=GROQ_API_KEY,
    )
    assert "SELECT" in res.sql.upper()
    with sales_engine.connect() as conn:
        df = pd.read_sql(sqlalchemy.text(res.sql), conn)
    assert not df.empty


@pytest.mark.skipif(not (GROQ_API_KEY and RUN_LIVE_GROQ_TESTS), reason="Set RUN_LIVE_GROQ_TESTS=1 for live LLM tests")
def test_universal_sql_hr(hr_engine):
    """Test SQL generation on HR Payroll schema."""
    schema = get_database_schema(hr_engine)
    res = generate_sql_query(
        question="What is the average salary in the Engineering department?",
        db_schema=schema,
        api_key=GROQ_API_KEY,
    )
    assert "SELECT" in res.sql.upper()
    with hr_engine.connect() as conn:
        df = pd.read_sql(sqlalchemy.text(res.sql), conn)
    assert not df.empty
