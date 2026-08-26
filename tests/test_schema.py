"""
Tests for Automatic Schema Discovery & Caching (Phase 2).
Validates table detection, column types, primary/foreign keys, relationships, and schema caching.
"""
import os
import pytest
import sqlalchemy
from sqlalchemy import create_engine

from app.database.schema import (
    ColumnInfo,
    TableSchema,
    DatabaseSchema,
    DatabaseRelationship,
)
from app.database.introspector import (
    SchemaIntrospector,
    get_tables,
    get_table_schema,
    get_database_schema,
    get_relationships,
)
from app.database.cache import SchemaCache, get_cached_schema
from app.database.connection import get_default_olist_engine


@pytest.fixture
def sample_relational_engine():
    """Create an in-memory SQLite database with users, departments, and orders relationships."""
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(sqlalchemy.text("""
            CREATE TABLE departments (
                department_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                budget REAL
            )
        """))
        conn.execute(sqlalchemy.text("""
            CREATE TABLE employees (
                employee_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                dept_id INTEGER,
                salary REAL DEFAULT 50000.0,
                FOREIGN KEY (dept_id) REFERENCES departments (department_id)
            )
        """))
        conn.execute(sqlalchemy.text("""
            CREATE TABLE projects (
                project_id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                lead_employee_id INTEGER,
                FOREIGN KEY (lead_employee_id) REFERENCES employees (employee_id)
            )
        """))
        conn.commit()
    return engine


def test_get_tables(sample_relational_engine):
    """Verify all table names are discovered."""
    tables = get_tables(sample_relational_engine)
    assert sorted(tables) == ["departments", "employees", "projects"]


def test_get_table_schema(sample_relational_engine):
    """Verify column types, nullability, defaults, and primary keys for a table."""
    dept_schema = get_table_schema(sample_relational_engine, "departments")
    assert dept_schema.name == "departments"
    assert dept_schema.primary_keys == ["department_id"]
    assert len(dept_schema.columns) == 3

    col_names = dept_schema.column_names
    assert "department_id" in col_names
    assert "name" in col_names
    assert "budget" in col_names

    dept_id_col = dept_schema.get_column("department_id")
    assert dept_id_col is not None
    assert dept_id_col.primary_key is True


def test_foreign_keys_and_relationships(sample_relational_engine):
    """Verify foreign key discovery and inter-table relationships."""
    emp_schema = get_table_schema(sample_relational_engine, "employees")
    assert len(emp_schema.foreign_keys) == 1
    fk = emp_schema.foreign_keys[0]
    assert fk.referred_table == "departments"
    assert fk.constrained_columns == ["dept_id"]
    assert fk.referred_columns == ["department_id"]

    relationships = get_relationships(sample_relational_engine)
    assert len(relationships) == 2
    rel_strs = [str(r) for r in relationships]
    assert any("employees(dept_id) ──► departments(department_id)" in s for s in rel_strs)
    assert any("projects(lead_employee_id) ──► employees(employee_id)" in s for s in rel_strs)


def test_get_database_schema(sample_relational_engine):
    """Verify full database schema introspection and compact summary representation."""
    db_schema = get_database_schema(sample_relational_engine)
    assert db_schema.dialect == "sqlite"
    assert len(db_schema.tables) == 3
    assert len(db_schema.relationships) == 2

    summary_str = db_schema.to_compact_schema_string()
    assert "=== DATABASE SCHEMA (Dialect: SQLITE) ===" in summary_str
    assert "departments:" in summary_str
    assert "employees:" in summary_str
    assert "projects:" in summary_str
    assert "=== FOREIGN KEY RELATIONSHIPS ===" in summary_str


def test_schema_cache(sample_relational_engine):
    """Verify schema caching, repeated access, and invalidation."""
    test_url = "sqlite:///test_cache_db"
    SchemaCache.invalidate(test_url)
    assert SchemaCache.is_cached(test_url) is False

    # First call: introspects and caches
    schema1 = SchemaCache.get_or_introspect(sample_relational_engine, test_url)
    assert SchemaCache.is_cached(test_url) is True

    # Second call: returns cached instance
    schema2 = SchemaCache.get_or_introspect(sample_relational_engine, test_url)
    assert schema1 is schema2

    # Force refresh
    schema3 = SchemaCache.get_or_introspect(sample_relational_engine, test_url, force_refresh=True)
    assert schema3 is not None
    assert len(schema3.tables) == 3

    # Invalidation
    SchemaCache.invalidate(test_url)
    assert SchemaCache.is_cached(test_url) is False


def test_olist_database_introspection():
    """Verify automatic introspection against the actual Olist SQLite database."""
    engine, url = get_default_olist_engine()
    db_schema = SchemaIntrospector.get_database_schema(engine)

    assert db_schema.dialect == "sqlite"
    assert len(db_schema.tables) == 9
    expected_tables = {
        "orders", "order_items", "customers", "products", "order_payments",
        "order_reviews", "sellers", "geolocation", "product_category_name_translation"
    }
    assert expected_tables.issubset(set(db_schema.table_names))

    orders_table = db_schema.get_table("orders")
    assert orders_table is not None
    assert "order_id" in orders_table.column_names
    assert "customer_id" in orders_table.column_names
    assert "order_status" in orders_table.column_names
