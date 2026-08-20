"""
Module 12 - Tests for Schema-Aware Prompting & Few-Shot Examples.
Verifies prompt structure, schema rules inclusion, and SQL validity of all few-shot examples.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import sqlite3
from app.prompts import build_system_prompt, FEW_SHOT_EXAMPLES, OLIST_DOMAIN_RULES
from app.guardrails import validate_sql


def test_system_prompt_contains_rules():
    prompt = build_system_prompt()
    assert "OLIST E-COMMERCE DATABASE RULES" in prompt
    assert "order_status = 'delivered'" in prompt
    assert "product_category_name_translation" in prompt
    assert "strftime" in prompt
    assert "julianday" in prompt
    assert "customer_unique_id" in prompt


def test_few_shot_examples_exist():
    assert len(FEW_SHOT_EXAMPLES) >= 5
    for eg in FEW_SHOT_EXAMPLES:
        assert "question" in eg
        assert "sql" in eg
        assert len(eg["question"]) > 10
        assert len(eg["sql"]) > 10


def test_few_shot_sqls_pass_guardrails():
    """Verify all few-shot SQL examples pass our security guardrails."""
    for eg in FEW_SHOT_EXAMPLES:
        sql = eg["sql"]
        validated = validate_sql(sql)
        assert validated is not None
        assert "SELECT" in validated


def test_few_shot_sqls_execute_on_database():
    """Verify that all few-shot SQL examples actually execute without syntax errors on olist.db."""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'olist.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for eg in FEW_SHOT_EXAMPLES:
        sql = eg["sql"]
        cursor.execute(sql)
        results = cursor.fetchall()
        assert results is not None
        # All examples should return at least one row
        assert len(results) > 0

    conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
