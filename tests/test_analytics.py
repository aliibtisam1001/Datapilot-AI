"""
Unit & Integration Tests for Analytics & Metric Discovery (Phase 7).
Validates dynamic KPI discovery and executive briefings.
"""
import os
import pytest
import sqlalchemy
from sqlalchemy import create_engine

from app.database import get_default_olist_engine, get_database_schema
from app.analytics import (
    discover_kpis,
    generate_executive_briefing,
    ExecutiveInsightsEngine,
)


@pytest.fixture
def custom_hr_engine():
    """Create in-memory SQLite database for HR schema."""
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(sqlalchemy.text("""
            CREATE TABLE staff (
                staff_id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                salary REAL NOT NULL,
                department TEXT NOT NULL
            );
        """))
        conn.execute(sqlalchemy.text("""
            INSERT INTO staff VALUES 
            (1, 'Alice', 95000.0, 'Engineering'),
            (2, 'Bob', 80000.0, 'Sales'),
            (3, 'Charlie', 110000.0, 'Engineering');
        """))
        conn.commit()
    return engine


def test_discover_kpis_olist():
    """Verify KPI discovery on the 100k+ Olist database."""
    engine, _ = get_default_olist_engine()
    schema = get_database_schema(engine)
    kpis = discover_kpis(engine, schema)

    assert len(kpis) >= 3
    titles = [k["title"] for k in kpis]
    assert any("order" in t.lower() or "orders" in t.lower() for t in titles)
    assert any("price" in t.lower() or "revenue" in t.lower() or "payment" in t.lower() or "customer" in t.lower() for t in titles)


def test_discover_kpis_hr(custom_hr_engine):
    """Verify KPI discovery on a custom HR database."""
    schema = get_database_schema(custom_hr_engine)
    kpis = discover_kpis(custom_hr_engine, schema)

    assert len(kpis) >= 2
    titles = [k["title"] for k in kpis]
    assert any("staff" in t.lower() for t in titles)
    assert any("salary" in t.lower() for t in titles)


def test_executive_insights_fallback(custom_hr_engine):
    """Verify fallback executive briefing when LLM is offline."""
    schema = get_database_schema(custom_hr_engine)
    kpis = discover_kpis(custom_hr_engine, schema)
    briefing = ExecutiveInsightsEngine._fallback_briefing(kpis, schema)

    assert len(briefing) == 3
    assert all("title" in b and "summary" in b and "tag" in b for b in briefing)
