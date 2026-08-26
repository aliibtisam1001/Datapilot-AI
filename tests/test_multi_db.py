"""
Unit & Integration Tests for Multi-Database Management (Phase 8).
Validates registration, context switching, independent query execution, and database removal.
"""
import pytest
import sqlalchemy
from sqlalchemy import create_engine
import pandas as pd

from app.database import MultiDatabaseManager, DatabaseType


@pytest.fixture
def multi_db():
    """Create a MultiDatabaseManager instance with in-memory test databases."""
    manager = MultiDatabaseManager()

    # Create Sales DB
    sales_engine = create_engine("sqlite:///:memory:")
    with sales_engine.connect() as conn:
        conn.execute(sqlalchemy.text("CREATE TABLE deals (id INT, deal_name TEXT, amount REAL)"))
        conn.execute(sqlalchemy.text("INSERT INTO deals VALUES (1, 'Acme Corp', 50000.0)"))
        conn.commit()

    # Create HR DB
    hr_engine = create_engine("sqlite:///:memory:")
    with hr_engine.connect() as conn:
        conn.execute(sqlalchemy.text("CREATE TABLE staff (id INT, emp_name TEXT, role TEXT)"))
        conn.execute(sqlalchemy.text("INSERT INTO staff VALUES (1, 'Alice', 'Engineer')"))
        conn.commit()

    manager.register_database("Sales DB", "sqlite:///:memory:")
    # Inject active engines for direct testing
    manager.get_database("Sales DB")._engine = sales_engine
    manager.register_database("HR DB", "sqlite:///:memory:")
    manager.get_database("HR DB")._engine = hr_engine

    return manager


def test_list_databases(multi_db):
    """Verify all registered databases appear in listing."""
    dbs = multi_db.list_databases()
    names = [d["name"] for d in dbs]
    assert "Olist E-Commerce (Demo)" in names
    assert "Sales DB" in names
    assert "HR DB" in names


def test_switch_active_database(multi_db):
    """Verify switching active database sets active_name correctly."""
    multi_db.set_active("Sales DB")
    assert multi_db.active_name == "Sales DB"
    active_mgr = multi_db.get_active()
    assert active_mgr.name == "Sales DB"

    df_sales = active_mgr.execute_query("SELECT * FROM deals")
    assert len(df_sales) == 1
    assert df_sales.iloc[0]["deal_name"] == "Acme Corp"

    # Switch to HR
    multi_db.set_active("HR DB")
    assert multi_db.active_name == "HR DB"
    active_hr = multi_db.get_active()
    assert active_hr.name == "HR DB"

    df_hr = active_hr.execute_query("SELECT * FROM staff")
    assert len(df_hr) == 1
    assert df_hr.iloc[0]["emp_name"] == "Alice"


def test_remove_database(multi_db):
    """Verify removing a database unregisters it."""
    assert multi_db.get_database("Sales DB") is not None
    removed = multi_db.remove_database("Sales DB")
    assert removed is True
    assert multi_db.get_database("Sales DB") is None
