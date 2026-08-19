"""
Module 7 - Unit tests for the SQL guardrail layer.
Tests both malicious and valid queries to ensure correct behavior.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from app.guardrails import validate_sql, SQLValidationError


# ============================================================
# VALID QUERIES - should pass validation
# ============================================================

class TestValidQueries:
    """Test that legitimate SELECT queries pass through."""

    def test_simple_select(self):
        result = validate_sql("SELECT COUNT(*) FROM orders")
        assert "SELECT COUNT(*) FROM orders" in result

    def test_select_with_where(self):
        result = validate_sql("SELECT * FROM customers WHERE customer_state = 'SP'")
        assert "SELECT" in result
        assert "customers" in result

    def test_select_with_join(self):
        sql = """
        SELECT p.product_id, t.product_category_name_english
        FROM products p
        JOIN product_category_name_translation t
        ON p.product_category_name = t.product_category_name
        """
        result = validate_sql(sql)
        assert "JOIN" in result

    def test_select_with_aggregation(self):
        sql = "SELECT customer_state, COUNT(*) FROM customers GROUP BY customer_state ORDER BY COUNT(*) DESC"
        result = validate_sql(sql)
        assert "GROUP BY" in result

    def test_select_with_subquery(self):
        sql = "SELECT * FROM orders WHERE customer_id IN (SELECT customer_id FROM customers WHERE customer_state = 'RJ')"
        result = validate_sql(sql)
        assert "SELECT" in result

    def test_select_with_cte(self):
        sql = """
        WITH top_states AS (
            SELECT customer_state, COUNT(*) as cnt
            FROM customers
            GROUP BY customer_state
        )
        SELECT * FROM top_states ORDER BY cnt DESC
        """
        result = validate_sql(sql)
        assert "WITH" in result

    def test_trailing_semicolon_ok(self):
        result = validate_sql("SELECT 1;")
        assert "SELECT 1" in result

    def test_select_with_existing_small_limit(self):
        result = validate_sql("SELECT * FROM orders LIMIT 10")
        assert "LIMIT 10" in result


# ============================================================
# LIMIT ENFORCEMENT
# ============================================================

class TestLimitEnforcement:
    """Test that row limits are properly enforced."""

    def test_adds_limit_when_missing(self):
        result = validate_sql("SELECT * FROM orders", max_rows=100)
        assert "LIMIT 100" in result

    def test_caps_excessive_limit(self):
        result = validate_sql("SELECT * FROM orders LIMIT 99999", max_rows=500)
        assert "LIMIT 500" in result

    def test_keeps_small_limit(self):
        result = validate_sql("SELECT * FROM orders LIMIT 10", max_rows=500)
        assert "LIMIT 10" in result

    def test_default_limit(self):
        result = validate_sql("SELECT * FROM orders")
        assert "LIMIT 500" in result  # default max_rows


# ============================================================
# MALICIOUS QUERIES - should be REJECTED
# ============================================================

class TestBlockedStatements:
    """Test that dangerous SQL statements are rejected."""

    def test_insert(self):
        with pytest.raises(SQLValidationError, match="SELECT"):
            validate_sql("INSERT INTO orders VALUES ('x', 'y')")

    def test_update(self):
        with pytest.raises(SQLValidationError, match="SELECT"):
            validate_sql("UPDATE orders SET order_status = 'canceled'")

    def test_delete(self):
        with pytest.raises(SQLValidationError, match="SELECT"):
            validate_sql("DELETE FROM orders")

    def test_drop_table(self):
        with pytest.raises(SQLValidationError, match="SELECT|DROP"):
            validate_sql("DROP TABLE orders")

    def test_alter_table(self):
        with pytest.raises(SQLValidationError, match="SELECT|ALTER"):
            validate_sql("ALTER TABLE orders ADD COLUMN hacked TEXT")

    def test_create_table(self):
        with pytest.raises(SQLValidationError, match="SELECT|CREATE"):
            validate_sql("CREATE TABLE evil (id INTEGER)")

    def test_pragma(self):
        with pytest.raises(SQLValidationError):
            validate_sql("PRAGMA table_info(orders)")


# ============================================================
# INJECTION ATTEMPTS - should be REJECTED
# ============================================================

class TestInjectionAttempts:
    """Test that SQL injection patterns are blocked."""

    def test_select_then_drop(self):
        with pytest.raises(SQLValidationError):
            validate_sql("SELECT 1; DROP TABLE orders")

    def test_select_then_delete(self):
        with pytest.raises(SQLValidationError):
            validate_sql("SELECT * FROM orders; DELETE FROM orders")

    def test_select_then_insert(self):
        with pytest.raises(SQLValidationError):
            validate_sql("SELECT 1; INSERT INTO orders VALUES ('hack')")

    def test_select_then_update(self):
        with pytest.raises(SQLValidationError):
            validate_sql("SELECT 1; UPDATE orders SET order_status = 'hacked'")

    def test_union_based_injection_with_drop(self):
        """DROP keyword should be caught even inside a UNION."""
        with pytest.raises(SQLValidationError):
            validate_sql("SELECT 1 UNION SELECT 1; DROP TABLE orders")


# ============================================================
# EDGE CASES
# ============================================================

class TestEdgeCases:
    """Test edge cases and tricky inputs."""

    def test_empty_string(self):
        with pytest.raises(SQLValidationError, match="Empty"):
            validate_sql("")

    def test_whitespace_only(self):
        with pytest.raises(SQLValidationError, match="Empty"):
            validate_sql("   ")

    def test_none_input(self):
        with pytest.raises(SQLValidationError, match="Empty"):
            validate_sql(None)

    def test_keyword_in_string_literal_ok(self):
        """'DELETE' inside a string value should NOT trigger the block."""
        result = validate_sql("SELECT * FROM orders WHERE order_status = 'DELETE'")
        assert "SELECT" in result

    def test_keyword_in_column_name_ok(self):
        """Column names containing blocked substrings should be fine."""
        result = validate_sql("SELECT product_description_lenght FROM products")
        assert "product_description_lenght" in result

    def test_case_insensitive_block(self):
        with pytest.raises(SQLValidationError):
            validate_sql("drop table orders")

    def test_mixed_case_block(self):
        with pytest.raises(SQLValidationError):
            validate_sql("DrOp TaBlE orders")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
