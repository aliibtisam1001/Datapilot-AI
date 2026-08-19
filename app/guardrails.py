"""
Module 7 - SQL Guardrail Layer.
Validates SQL queries before execution:
  - Only SELECT statements allowed
  - Rejects INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, EXEC, PRAGMA (write operations)
  - Rejects multi-statement injection (semicolons followed by another statement)
  - Enforces a configurable row LIMIT cap
"""
import re
import sqlparse


# Dangerous keywords that should never appear as top-level statements
BLOCKED_KEYWORDS = {
    'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE',
    'EXEC', 'EXECUTE', 'PRAGMA', 'ATTACH', 'DETACH', 'REPLACE',
    'GRANT', 'REVOKE', 'TRUNCATE', 'MERGE',
}

DEFAULT_MAX_ROWS = 500


class SQLValidationError(Exception):
    """Raised when a SQL query fails guardrail validation."""
    pass


def validate_sql(sql: str, max_rows: int = DEFAULT_MAX_ROWS) -> str:
    """
    Validate and sanitize a SQL query.

    Args:
        sql: The raw SQL string to validate.
        max_rows: Maximum number of rows to allow (appends/replaces LIMIT).

    Returns:
        The validated (and possibly LIMIT-capped) SQL string.

    Raises:
        SQLValidationError: If the query is not a safe SELECT.
    """
    if not sql or not sql.strip():
        raise SQLValidationError("Empty query.")

    cleaned = sql.strip()

    # Parse the SQL to detect multiple statements
    parsed_statements = sqlparse.parse(cleaned)

    # Filter out empty/whitespace-only statements (trailing semicolons)
    real_statements = [
        s for s in parsed_statements
        if s.get_type() is not None or str(s).strip()
    ]
    # Also filter out statements that are just whitespace/semicolons
    real_statements = [
        s for s in real_statements
        if str(s).strip().rstrip(';').strip()
    ]

    if len(real_statements) == 0:
        raise SQLValidationError("Empty query.")

    if len(real_statements) > 1:
        raise SQLValidationError(
            "Multi-statement queries are not allowed. Only single SELECT statements are permitted."
        )

    stmt = real_statements[0]
    stmt_str = str(stmt).strip()

    # Check statement type via sqlparse
    stmt_type = stmt.get_type()

    # Check if the first meaningful keyword is SELECT (or WITH for CTEs)
    # Normalize: remove comments, get first keyword
    first_keyword = _get_first_keyword(stmt_str)

    if first_keyword not in ('SELECT', 'WITH'):
        raise SQLValidationError(
            f"Only SELECT statements are allowed. Got: {first_keyword or 'unknown'}"
        )

    # Scan for blocked keywords appearing as standalone tokens
    # (not inside strings or as column/table names)
    upper_sql = stmt_str.upper()
    for keyword in BLOCKED_KEYWORDS:
        # Use word boundary regex to avoid false positives
        # e.g., "product_description" should not trigger on "CREATE"
        pattern = r'\b' + keyword + r'\b'
        if re.search(pattern, upper_sql):
            # Double-check it's not inside a string literal
            if _keyword_outside_strings(stmt_str, keyword):
                raise SQLValidationError(
                    f"Forbidden keyword detected: {keyword}. "
                    f"Only SELECT queries are allowed."
                )

    # Enforce row limit
    result_sql = _enforce_limit(stmt_str, max_rows)

    return result_sql


def _get_first_keyword(sql: str) -> str:
    """Extract the first meaningful SQL keyword from a statement."""
    parsed = sqlparse.parse(sql)
    if not parsed:
        return ''
    for token in parsed[0].tokens:
        if token.ttype in (sqlparse.tokens.Whitespace, sqlparse.tokens.Newline,
                           sqlparse.tokens.Comment.Single, sqlparse.tokens.Comment.Multiline):
            continue
        val = str(token).strip().upper()
        if val:
            return val.split()[0] if val else ''
    return ''


def _keyword_outside_strings(sql: str, keyword: str) -> bool:
    """Check if a keyword appears outside of string literals."""
    # Remove all string literals (both single and double quoted)
    no_strings = re.sub(r"'[^']*'", '', sql)
    no_strings = re.sub(r'"[^"]*"', '', no_strings)
    pattern = r'\b' + keyword + r'\b'
    return bool(re.search(pattern, no_strings, re.IGNORECASE))


def _enforce_limit(sql: str, max_rows: int) -> str:
    """Ensure the query has a LIMIT clause not exceeding max_rows."""
    upper = sql.upper().strip().rstrip(';')

    # Check if LIMIT already exists
    limit_match = re.search(r'\bLIMIT\s+(\d+)', upper)
    if limit_match:
        existing_limit = int(limit_match.group(1))
        if existing_limit > max_rows:
            # Replace the existing limit with max_rows
            sql_no_semi = sql.strip().rstrip(';')
            result = re.sub(
                r'\bLIMIT\s+\d+',
                f'LIMIT {max_rows}',
                sql_no_semi,
                flags=re.IGNORECASE
            )
            return result
        return sql.strip().rstrip(';')
    else:
        # Append LIMIT
        sql_no_semi = sql.strip().rstrip(';')
        return f"{sql_no_semi} LIMIT {max_rows}"
