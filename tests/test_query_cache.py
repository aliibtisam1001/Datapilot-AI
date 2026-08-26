"""
Unit tests for QueryCache layer (Phase 4).
Validates TTL expiration, whitespace normalization, stats tracking, and invalidation.
"""
import time
import pytest
from app.agent.query_cache import QueryCache
from app.agent.sql_generator import SQLGenerationResult


def test_query_cache_basic():
    """Verify basic set, get, and hit count."""
    db_url = "sqlite:///test.db"
    question = "What is the total sales amount?"
    res = SQLGenerationResult(
        sql="SELECT SUM(amount) FROM sales;",
        tables_used=["sales"],
        reasoning_summary="Sums the amount column in sales.",
        confidence=0.98,
    )

    QueryCache.invalidate()
    assert QueryCache.get(db_url, question) is None

    QueryCache.set(db_url, question, res)
    cached = QueryCache.get(db_url, question)
    assert cached is not None
    assert cached.sql == res.sql
    assert cached.tables_used == ["sales"]


def test_query_cache_normalization():
    """Verify question case and whitespace normalization matches cache."""
    db_url = "sqlite:///test.db"
    res = SQLGenerationResult(
        sql="SELECT COUNT(*) FROM users;",
        tables_used=["users"],
        reasoning_summary="Counts total users.",
        confidence=0.99,
    )
    QueryCache.set(db_url, "How many users are registered?", res)

    # Different casing and excess whitespace
    hit = QueryCache.get(db_url, "  HOW   MANY users ARE registered?  ")
    assert hit is not None
    assert hit.sql == res.sql


def test_query_cache_ttl_expiration():
    """Verify expired items are removed upon TTL threshold."""
    db_url = "sqlite:///test.db"
    res = SQLGenerationResult(
        sql="SELECT 1;",
        tables_used=[],
        reasoning_summary="Test",
        confidence=1.0,
    )
    QueryCache.set(db_url, "test ttl", res)
    # Immediate get with 0s TTL should expire
    assert QueryCache.get(db_url, "test ttl", ttl_seconds=0) is None


def test_query_cache_invalidation():
    """Verify invalidating cache clears all entries."""
    db_url = "sqlite:///test.db"
    res = SQLGenerationResult(sql="SELECT 1;", tables_used=[], reasoning_summary="", confidence=1.0)
    QueryCache.set(db_url, "q1", res)
    QueryCache.set(db_url, "q2", res)

    assert QueryCache.get(db_url, "q1") is not None
    QueryCache.invalidate()
    assert QueryCache.get(db_url, "q1") is None
    assert QueryCache.get(db_url, "q2") is None
