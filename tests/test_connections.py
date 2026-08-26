"""
Tests for Universal Database Connection Layer (Phase 1).
Validates SQLite connections, URL normalization, password masking, error diagnostics, and query execution.
"""
import os
import pytest
import pandas as pd
import sqlalchemy
from app.database import (
    DatabaseConnectionManager,
    DatabaseType,
    InvalidURLError,
    UnsupportedDatabaseError,
    mask_url,
    detect_database_type,
    normalize_connection_url,
    get_default_olist_engine,
    EnginePool,
)


def test_detect_database_type():
    """Verify database dialect detection from connection strings."""
    assert detect_database_type("sqlite:///data/test.db") == DatabaseType.SQLITE
    assert detect_database_type("sqlite:///:memory:") == DatabaseType.SQLITE
    assert detect_database_type("postgresql://user:pass@localhost/db") == DatabaseType.POSTGRESQL
    assert detect_database_type("postgres://user:pass@localhost/db") == DatabaseType.POSTGRESQL
    assert detect_database_type("mysql://user:pass@localhost/db") == DatabaseType.MYSQL
    assert detect_database_type("mysql+pymysql://user:pass@localhost/db") == DatabaseType.MYSQL
    assert detect_database_type("oracle://user:pass@localhost/db") == DatabaseType.UNKNOWN
    assert detect_database_type("") == DatabaseType.UNKNOWN


def test_mask_url():
    """Verify passwords are never exposed in connection URL strings."""
    masked = mask_url("postgresql://admin:super_secret_pw@db.company.com:5432/analytics")
    assert "super_secret_pw" not in masked
    assert "***" in masked
    assert "admin" in masked
    assert "analytics" in masked

    masked_mysql = mask_url("mysql+pymysql://root:p@ssword!@127.0.0.1:3306/sales")
    assert "p@ssword!" not in masked_mysql
    assert "***" in masked_mysql


def test_normalize_connection_url():
    """Verify driver normalization for PostgreSQL and MySQL."""
    pg_norm = normalize_connection_url("postgresql://user:pass@localhost:5432/db")
    assert "postgresql+psycopg2://" in pg_norm

    my_norm = normalize_connection_url("mysql://user:pass@localhost:3306/db")
    assert "mysql+pymysql://" in my_norm

    sqlite_norm = normalize_connection_url("sqlite:///:memory:")
    assert sqlite_norm == "sqlite:///:memory:"

    with pytest.raises(InvalidURLError):
        normalize_connection_url("")


def test_sqlite_memory_connection():
    """Test connecting to SQLite in-memory and executing basic query."""
    mgr = DatabaseConnectionManager("sqlite:///:memory:", name="TestMemory")
    assert mgr.db_type == DatabaseType.SQLITE
    assert mgr.is_connected is True

    success, msg = mgr.test_connection()
    assert success is True
    assert "SQLITE" in msg

    # Create a small table and query it
    with mgr.engine.connect() as conn:
        conn.execute(sqlalchemy.text("CREATE TABLE test_table (id INT, name TEXT)"))
        conn.execute(sqlalchemy.text("INSERT INTO test_table VALUES (1, 'DataPilot'), (2, 'AI')"))
        conn.commit()

    df = mgr.execute_query("SELECT * FROM test_table ORDER BY id")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df['name']) == ['DataPilot', 'AI']

    mgr.dispose()


def test_default_olist_engine():
    """Verify fallback Olist SQLite database connects cleanly."""
    engine, url = get_default_olist_engine()
    assert engine is not None
    assert "sqlite:///" in url

    mgr = DatabaseConnectionManager(url, name="OlistDemo")
    assert mgr.is_connected is True

    df = mgr.execute_query("SELECT COUNT(*) AS total_orders FROM orders")
    assert len(df) == 1
    assert df.iloc[0]['total_orders'] > 90000


def test_unsupported_database_error():
    """Verify unsupported database dialects raise UnsupportedDatabaseError."""
    with pytest.raises(UnsupportedDatabaseError):
        DatabaseConnectionManager("mongodb://localhost:27017/test")


def test_invalid_url_error():
    """Verify empty or malformed URLs raise InvalidURLError."""
    with pytest.raises(InvalidURLError):
        DatabaseConnectionManager("   ")


def test_unreachable_host_error():
    """Verify connection testing against unreachable hosts produces sanitized error."""
    # Use a non-routable dummy host with immediate timeout
    mgr = DatabaseConnectionManager("postgresql://invalid_user:invalid_pass@127.0.0.1:59999/dummy_db")
    success, msg = mgr.test_connection()
    assert success is False
    assert any(w in msg.lower() for w in ["host unavailable", "connection refused", "could not connect", "operational error"])
    # Passwords must not be revealed in the error message
    assert "invalid_pass" not in msg

    mgr.dispose()
