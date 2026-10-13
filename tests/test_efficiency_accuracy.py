"""Regression tests for accuracy, safety, and low-compute execution paths."""
import json
import pandas as pd
import pytest

from app.agent import (
    CachedAnalysis,
    ResultCache,
    UniversalSQLGenerator,
    model_candidates_for,
    select_relevant_schema,
)
from app.database import get_database_schema, get_default_olist_engine
from app.guardrails import SQLValidationError, validate_sql
from app.summarize import summarize_result


@pytest.mark.parametrize("sql", [
    "SELECT * INTO temp_snapshot FROM customers",
    "SELECT setval('order_seq', 1)",
    "SELECT pg_terminate_backend(123)",
])
def test_ast_guardrail_blocks_mutating_select_forms(sql):
    with pytest.raises(SQLValidationError):
        validate_sql(sql, dialect="postgresql")


def test_guardrail_ignores_blocked_words_inside_comments():
    assert validate_sql("SELECT 1 -- DROP is documentation", dialect="sqlite").endswith("LIMIT 500")


def test_olist_schema_selection_preserves_revenue_join_path():
    engine, _ = get_default_olist_engine()
    schema = get_database_schema(engine)
    selected = select_relevant_schema(schema, "Top categories by delivered revenue")
    assert {"order_items", "products", "product_category_name_translation", "orders"}.issubset(
        set(selected.table_names)
    )
    assert selected.relationships


def test_complete_result_cache_copies_data_and_invalidates_one_database():
    ResultCache.invalidate()
    original = pd.DataFrame({"total": [42]})
    result = CachedAnalysis("SELECT 42", original, "42", "42", "small")
    assert ResultCache.set("sqlite:///one", "total", "v1", result)
    assert ResultCache.set("sqlite:///two", "total", "v1", result)

    cached = ResultCache.get("sqlite:///one", "total", "v1")
    cached.dataframe.iloc[0, 0] = 0
    assert ResultCache.get("sqlite:///one", "total", "v1").dataframe.iloc[0, 0] == 42

    ResultCache.invalidate("sqlite:///one")
    assert ResultCache.get("sqlite:///one", "total", "v1") is None
    assert ResultCache.get("sqlite:///two", "total", "v1") is not None


def test_simple_metric_uses_deterministic_summary():
    summary = summarize_result("How many orders?", pd.DataFrame({"total_orders": [99441]}))
    assert summary == "Total Orders is 99,441."


def test_model_router_starts_small_for_simple_questions():
    assert model_candidates_for("How many orders are there?", 1)[0] == "openai/gpt-oss-20b"
    assert model_candidates_for("Compare cohort retention with the previous period", 6)[0] == "openai/gpt-oss-120b"


class _FakeResponse:
    def __init__(self, content):
        self.content = content


class _FakeLLM:
    def __init__(self, content):
        self.content = content

    def invoke(self, _prompt):
        return _FakeResponse(self.content)


def test_generator_validates_tables_columns_and_join_path_before_execution():
    engine, _ = get_default_olist_engine()
    schema = get_database_schema(engine)
    selected = select_relevant_schema(schema, "Top categories by delivered revenue")
    sql = """SELECT t.product_category_name_english AS category, SUM(oi.price) AS revenue
FROM order_items AS oi
JOIN products AS p ON oi.product_id = p.product_id
JOIN product_category_name_translation AS t ON p.product_category_name = t.product_category_name
JOIN orders AS o ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY t.product_category_name_english
ORDER BY revenue DESC LIMIT 5"""
    llm = _FakeLLM(json.dumps({
        "sql": sql,
        "tables_used": ["order_items", "products", "orders"],
        "reasoning_summary": "Delivered revenue by category",
        "confidence": 0.98,
    }))
    result = UniversalSQLGenerator.generate_sql("Top categories by delivered revenue", selected, llm=llm)
    assert "product_category_name_translation" in result.sql


def test_generator_rejects_hallucinated_columns():
    engine, _ = get_default_olist_engine()
    schema = select_relevant_schema(get_database_schema(engine), "Order revenue")
    llm = _FakeLLM(
        '{"sql": "SELECT imaginary_revenue FROM orders", "tables_used": ["orders"], '
        '"reasoning_summary": "bad", "confidence": 0.9}'
    )
    with pytest.raises(SQLValidationError):
        UniversalSQLGenerator.generate_sql("Order revenue", schema, llm=llm)
