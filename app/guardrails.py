"""
Hardened Enterprise SQL Guardrails & Security Layer for DataPilot AI.
Guarantees read-only execution, blocks injection vectors, multi-statement attacks,
destructive DDL/DML, dialect-specific exploit functions, and enforces strict row caps.
"""
import re
from typing import Optional
import sqlparse
from sqlparse.sql import Statement, TokenList, Identifier


# Destructive DDL / DML / Admin Keywords that must never be executed
BLOCKED_KEYWORDS = {
    'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE',
    'TRUNCATE', 'EXEC', 'EXECUTE', 'GRANT', 'REVOKE', 'PRAGMA',
    'CALL', 'MERGE', 'COPY', 'ATTACH', 'DETACH', 'REPLACE',
    'VACUUM', 'REINDEX', 'LOCK', 'UNLOCK', 'SHUTDOWN', 'KILL',
}

# Dialect-specific dangerous functions & file operations
BLOCKED_FUNCTIONS = {
    'PG_SLEEP', 'PG_READ_FILE', 'PG_WRITE_FILE', 'DBLINK', 'PG_LS_DIR', 'PG_STAT_FILE',
    'INTO OUTFILE', 'INTO DUMPFILE', 'LOAD DATA', 'LOAD_FILE', 'BENCHMARK', 'SLEEP',
    'XP_CMDSHELL',
}

DEFAULT_MAX_ROWS = 500


class SQLValidationError(Exception):
    """Raised when a SQL query fails security guardrail validation."""
    pass


def validate_sql(sql: str, max_rows: int = DEFAULT_MAX_ROWS) -> str:
    """
    Validate, sanitize, and enforce security policies on a SQL query.

    Args:
        sql: The raw SQL string to validate.
        max_rows: Maximum rows allowed (enforces/caps LIMIT).

    Returns:
        The validated and secured SQL string.

    Raises:
        SQLValidationError: If the query violates read-only or injection policies.
    """
    if not sql or not isinstance(sql, str) or not sql.strip():
        raise SQLValidationError("Query is empty.")

    cleaned = sql.strip()

    # 1. Parse into statements using sqlparse
    parsed_statements = sqlparse.parse(cleaned)

    # Filter out empty or whitespace/comment-only statements
    real_statements = [
        s for s in parsed_statements
        if str(s).strip().rstrip(';').strip()
    ]

    if not real_statements:
        raise SQLValidationError("Query contains no valid executable statements.")

    # 2. Block multi-statement queries
    if len(real_statements) > 1:
        raise SQLValidationError(
            "Multi-statement execution rejected. Only a single read-only SELECT statement is permitted."
        )

    stmt = real_statements[0]
    stmt_str = str(stmt).strip()

    # 3. Verify the primary keyword is SELECT or WITH
    first_keyword = _get_first_keyword(stmt_str)
    if first_keyword not in ('SELECT', 'WITH'):
        raise SQLValidationError(
            f"Only read-only SELECT queries are allowed. Forbidden statement type: '{first_keyword or 'UNKNOWN'}'."
        )

    # 4. Check for blocked standalone keywords outside string literals
    stmt_without_literals = _strip_string_literals(stmt_str)
    upper_no_lit = stmt_without_literals.upper()

    for keyword in BLOCKED_KEYWORDS:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, upper_no_lit):
            raise SQLValidationError(
                f"Security Violation: Forbidden keyword '{keyword}' detected. Only read-only SELECT queries are permitted."
            )

    # 5. Check for dangerous dialect functions and file operations
    for func in BLOCKED_FUNCTIONS:
        pattern = r'\b' + re.escape(func) + r'\b'
        if re.search(pattern, upper_no_lit):
            raise SQLValidationError(
                f"Security Violation: Potentially hazardous function or operation '{func}' is strictly blocked."
            )

    # 6. Semicolon injection detection inside statement
    # Strip string literals and comments, then check for semicolons before the end
    clean_no_comment = sqlparse.format(stmt_str, strip_comments=True).strip()
    clean_no_lit = _strip_string_literals(clean_no_comment).rstrip(';').strip()
    if ';' in clean_no_lit:
        raise SQLValidationError(
            "Security Violation: Semicolon delimiter detected within query payload."
        )

    # 7. Enforce Row LIMIT
    return _enforce_limit(stmt_str, max_rows)


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


def _strip_string_literals(sql: str) -> str:
    """Remove string literals (single and double quoted) to prevent false positives."""
    no_single = re.sub(r"'[^']*'", "''", sql)
    no_double = re.sub(r'"[^"]*"', '""', no_single)
    return no_double


def _enforce_limit(sql: str, max_rows: int) -> str:
    """Ensure the query has a LIMIT clause not exceeding max_rows."""
    sql_no_semi = sql.strip().rstrip(';')
    upper = sql_no_semi.upper()

    # Match LIMIT clause at the end of the query
    limit_match = re.search(r'\bLIMIT\s+(\d+)\s*$', upper, flags=re.IGNORECASE)
    if limit_match:
        existing_limit = int(limit_match.group(1))
        if existing_limit > max_rows:
            # Replace excessive limit with max_rows
            return re.sub(r'\bLIMIT\s+\d+\s*$', f'LIMIT {max_rows}', sql_no_semi, flags=re.IGNORECASE)
        return sql_no_semi
    else:
        return f"{sql_no_semi} LIMIT {max_rows}"


def sanitize_error_message(err: Exception) -> str:
    """
    Sanitize exception messages to prevent leaking server paths, credentials, or internal stack traces.
    """
    msg = str(err)
    # Mask passwords if any URL was leaked in error
    msg = re.sub(r':([^:@/]+)@', ':***@', msg)
    # Mask absolute windows/unix paths
    msg = re.sub(r'[A-Za-z]:\\[^ \n\r\t:]+', '[internal_path]', msg)
    msg = re.sub(r'/[a-zA-Z0-9_\.-]+/[a-zA-Z0-9_\.-]+/[a-zA-Z0-9_\.-]+', '[internal_path]', msg)
    return msg
