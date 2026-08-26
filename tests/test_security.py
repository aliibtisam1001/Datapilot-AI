"""
Comprehensive Security & SQL Injection Prevention Test Suite (Phase 5).
Validates read-only policy, dialect-specific exploit blocking, multi-statement rejection,
CTE security, and error message sanitization.
"""
import pytest
from app.guardrails import validate_sql, SQLValidationError, sanitize_error_message


class TestValidReadOperations:
    """Verify safe SELECT queries are permitted and properly formatted."""

    def test_simple_select(self):
        sql = "SELECT id, name FROM employees"
        res = validate_sql(sql)
        assert res.startswith("SELECT id, name FROM employees")
        assert "LIMIT 500" in res

    def test_select_with_where_and_group(self):
        sql = "SELECT department, COUNT(*) AS cnt FROM staff WHERE active = 1 GROUP BY department"
        res = validate_sql(sql)
        assert "LIMIT 500" in res

    def test_select_with_safe_cte(self):
        sql = """
        WITH top_spenders AS (
            SELECT customer_id, SUM(amount) AS total FROM orders GROUP BY customer_id
        )
        SELECT * FROM top_spenders ORDER BY total DESC LIMIT 10
        """
        res = validate_sql(sql)
        assert "LIMIT 10" in res

    def test_select_with_safe_string_literals(self):
        # The word 'delete' or 'drop' inside literal strings must not be blocked
        sql = "SELECT * FROM audit_logs WHERE action_name = 'DELETE_USER' AND status = 'CREATE_FAILED'"
        res = validate_sql(sql)
        assert "audit_logs" in res


class TestBlockedDestructiveDMLAndDDL:
    """Verify write, modification, and administrative operations are rejected."""

    @pytest.mark.parametrize("bad_sql", [
        "INSERT INTO users (id, name) VALUES (1, 'Hacker')",
        "UPDATE accounts SET balance = 1000000 WHERE id = 1",
        "DELETE FROM orders WHERE status = 'cancelled'",
        "DROP TABLE customers",
        "DROP DATABASE production",
        "ALTER TABLE users ADD COLUMN is_admin INT",
        "CREATE TABLE backdoor (id INT)",
        "TRUNCATE TABLE transaction_logs",
        "GRANT ALL PRIVILEGES ON *.* TO 'attacker'@'%'",
        "REVOKE SELECT ON users FROM 'public'",
        "VACUUM",
        "REINDEX",
    ])
    def test_destructive_keywords_blocked(self, bad_sql):
        with pytest.raises(SQLValidationError):
            validate_sql(bad_sql)


class TestMultiStatementAndInjectionAttempts:
    """Verify statement chaining and comment bypasses are blocked."""

    def test_semicolon_chained_drop(self):
        with pytest.raises(SQLValidationError):
            validate_sql("SELECT * FROM users; DROP TABLE users;")

    def test_semicolon_chained_delete(self):
        with pytest.raises(SQLValidationError):
            validate_sql("SELECT 1; DELETE FROM logs;")

    def test_comment_bypass_attempt(self):
        with pytest.raises(SQLValidationError):
            validate_sql("SELECT * FROM products; --\nDROP TABLE products;")

    def test_cte_embedded_write_attempt(self):
        sql = "WITH deleted_rows AS (DELETE FROM users RETURNING *) SELECT * FROM deleted_rows;"
        with pytest.raises(SQLValidationError):
            validate_sql(sql)


class TestDialectSpecificExploitBlocking:
    """Verify blocking of dangerous database-specific functions and commands."""

    # SQLite
    def test_sqlite_pragma_blocked(self):
        with pytest.raises(SQLValidationError):
            validate_sql("PRAGMA table_info(users)")

    def test_sqlite_attach_blocked(self):
        with pytest.raises(SQLValidationError):
            validate_sql("ATTACH DATABASE 'malicious.db' AS mal")

    # PostgreSQL
    def test_postgres_pg_sleep_blocked(self):
        with pytest.raises(SQLValidationError):
            validate_sql("SELECT * FROM orders WHERE id = 1 AND PG_SLEEP(10) IS NOT NULL")

    def test_postgres_pg_read_file_blocked(self):
        with pytest.raises(SQLValidationError):
            validate_sql("SELECT PG_READ_FILE('/etc/passwd')")

    def test_postgres_dblink_blocked(self):
        with pytest.raises(SQLValidationError):
            validate_sql("SELECT * FROM DBLINK('host=evil.com', 'SELECT 1')")

    # MySQL
    def test_mysql_into_outfile_blocked(self):
        with pytest.raises(SQLValidationError):
            validate_sql("SELECT * FROM users INTO OUTFILE '/var/www/shell.php'")

    def test_mysql_load_data_blocked(self):
        with pytest.raises(SQLValidationError):
            validate_sql("LOAD DATA INFILE '/etc/passwd' INTO TABLE temp")

    def test_mysql_benchmark_blocked(self):
        with pytest.raises(SQLValidationError):
            validate_sql("SELECT BENCHMARK(5000000, MD5('test'))")

    def test_mysql_sleep_blocked(self):
        with pytest.raises(SQLValidationError):
            validate_sql("SELECT * FROM products WHERE SLEEP(5)")


class TestLimitEnforcement:
    """Verify row limiting behavior."""

    def test_append_limit_when_missing(self):
        sql = "SELECT * FROM sales"
        res = validate_sql(sql, max_rows=500)
        assert res.endswith("LIMIT 500")

    def test_cap_excessive_limit(self):
        sql = "SELECT * FROM sales LIMIT 50000"
        res = validate_sql(sql, max_rows=500)
        assert res.endswith("LIMIT 500")

    def test_preserve_small_limit(self):
        sql = "SELECT * FROM sales LIMIT 15"
        res = validate_sql(sql, max_rows=500)
        assert res.endswith("LIMIT 15")


class TestErrorSanitization:
    """Verify credentials and filesystem paths are scrubbed from error logs."""

    def test_sanitizes_connection_url_password(self):
        raw_err = Exception("OperationalError: connection to postgresql://admin:secretPass123@10.0.0.5/db failed")
        clean = sanitize_error_message(raw_err)
        assert "secretPass123" not in clean
        assert "***" in clean

    def test_sanitizes_filesystem_path(self):
        raw_err = Exception(r"FileNotFoundError: D:\Personal Projects\SmartQuery\data\secret.db does not exist")
        clean = sanitize_error_message(raw_err)
        assert "Personal Projects" not in clean
        assert "[internal_path]" in clean
