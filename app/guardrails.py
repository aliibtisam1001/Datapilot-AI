"""
Hardened Enterprise SQL Guardrails & Security Layer for DataPilot AI.
Guarantees read-only execution, blocks injection vectors, multi-statement attacks,
destructive DDL/DML, dialect-specific exploit functions, and enforces strict row caps.
"""
import re
from typing import Optional, TYPE_CHECKING
import sqlparse

try:
    import sqlglot
    from sqlglot import exp
    from sqlglot.errors import ParseError
except ImportError:  # Deployment installs sqlglot from requirements.txt.
    sqlglot = None
    exp = None
    ParseError = Exception

if TYPE_CHECKING:
    from app.database.schema import DatabaseSchema


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
    'XP_CMDSHELL', 'SETVAL', 'NEXTVAL', 'PG_TERMINATE_BACKEND', 'PG_CANCEL_BACKEND',
    'PG_ADVISORY_LOCK', 'PG_TRY_ADVISORY_LOCK', 'LO_IMPORT', 'LO_EXPORT',
    'DBLINK_CONNECT', 'WRITEFILE', 'LOAD_EXTENSION',
}

DEFAULT_MAX_ROWS = 500


class SQLValidationError(Exception):
    """Raised when a SQL query fails security guardrail validation."""
    pass


def validate_sql(
    sql: str,
    max_rows: int = DEFAULT_MAX_ROWS,
    dialect: Optional[str] = None,
    db_schema: Optional["DatabaseSchema"] = None,
) -> str:
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
        raise SQLValidationError("Empty query.")

    cleaned = sql.strip()
    parse_dialect = _sqlglot_dialect(dialect or getattr(db_schema, "dialect", None))

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

    # Strip comments before policy checks. This avoids false positives such as
    # `SELECT 1 -- DROP is mentioned in a comment` while preserving strings.
    stmt_no_comments = sqlparse.format(stmt_str, strip_comments=True).strip()

    # sqlglot provides a real dialect-aware syntax tree. The legacy sqlparse
    # checks below remain as defense-in-depth and as a clear failure mode if a
    # deployment has not installed its declared dependencies yet.
    if sqlglot is None:
        raise SQLValidationError("The required dialect-aware SQL parser is unavailable.")
    try:
        expressions = sqlglot.parse(stmt_no_comments, read=parse_dialect)
    except ParseError as exc:
        raise SQLValidationError(f"Invalid {parse_dialect or 'SQL'} syntax: {exc}") from exc
    if len(expressions) != 1:
        raise SQLValidationError(
            "Multi-statement execution rejected. Only one read-only query is permitted."
        )
    parsed_expression = expressions[0]
    _validate_ast(parsed_expression)
    if db_schema is not None:
        _validate_schema_references(parsed_expression, db_schema)

    # 3. Verify the primary keyword is SELECT or WITH
    first_keyword = _get_first_keyword(stmt_no_comments)
    if first_keyword not in ('SELECT', 'WITH'):
        raise SQLValidationError(
            f"Only read-only SELECT queries are allowed. Forbidden statement type: '{first_keyword or 'UNKNOWN'}'."
        )

    # 4. Check for blocked standalone keywords outside string literals
    stmt_without_literals = _strip_string_literals(stmt_no_comments)
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
    clean_no_lit = _strip_string_literals(stmt_no_comments).rstrip(';').strip()
    if ';' in clean_no_lit:
        raise SQLValidationError(
            "Security Violation: Semicolon delimiter detected within query payload."
        )

    # 7. Enforce Row LIMIT
    if parsed_expression is not None:
        return _enforce_limit_ast(parsed_expression, max_rows, parse_dialect)
    return _enforce_limit(stmt_no_comments, max_rows)


def _sqlglot_dialect(dialect: Optional[str]) -> Optional[str]:
    """Map SQLAlchemy dialect names to sqlglot dialect names."""
    if not dialect:
        return None
    value = str(dialect).lower()
    return {"postgresql": "postgres", "postgresql+psycopg2": "postgres"}.get(value, value)


def _validate_ast(expression) -> None:
    """Require a query AST and reject every known write/admin node."""
    if exp is None or not isinstance(expression, exp.Query):
        raise SQLValidationError("Only read-only SELECT queries are allowed.")

    forbidden_types = tuple(
        node_type
        for node_type in (
            exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, exp.Alter,
            exp.Merge, exp.Command, exp.Transaction, exp.Set, exp.Use,
            getattr(exp, "Into", None),
        )
        if node_type is not None
    )
    for node in expression.walk():
        if isinstance(node, forbidden_types):
            raise SQLValidationError(
                f"Security Violation: write/admin SQL node '{node.key.upper()}' is forbidden."
            )
        if isinstance(node, exp.Func):
            func_name = (node.sql_name() or "").upper()
            if func_name in BLOCKED_FUNCTIONS:
                raise SQLValidationError(
                    f"Security Violation: hazardous function '{func_name}' is strictly blocked."
                )


def _validate_schema_references(expression, db_schema: "DatabaseSchema") -> None:
    """Validate physical table and column references against the selected schema."""
    if exp is None:
        return

    schema_tables = {name.lower(): table for name, table in db_schema.tables.items()}
    cte_names = {cte.alias_or_name.lower() for cte in expression.find_all(exp.CTE)}
    table_aliases = {}

    for table_node in expression.find_all(exp.Table):
        table_name = table_node.name.lower()
        if table_name in cte_names:
            continue
        if table_name not in schema_tables:
            raise SQLValidationError(f"Unknown table referenced by generated SQL: '{table_node.name}'.")
        table_aliases[table_node.alias_or_name.lower()] = table_name
        table_aliases[table_name] = table_name

    all_columns = {
        column.name.lower()
        for table in schema_tables.values()
        for column in table.columns
    }
    select_aliases = {
        alias.alias.lower()
        for alias in expression.find_all(exp.Alias)
        if alias.alias
    }

    for column_node in expression.find_all(exp.Column):
        column_name = column_node.name.lower()
        qualifier = column_node.table.lower() if column_node.table else ""
        if column_name == "*" or column_name in select_aliases:
            continue
        if qualifier in cte_names:
            continue
        if qualifier:
            table_name = table_aliases.get(qualifier)
            if not table_name:
                raise SQLValidationError(f"Unknown table alias referenced by generated SQL: '{qualifier}'.")
            valid_columns = {c.name.lower() for c in schema_tables[table_name].columns}
            if column_name not in valid_columns:
                raise SQLValidationError(
                    f"Unknown column '{column_node.name}' on table '{table_name}'."
                )
        elif column_name not in all_columns:
            raise SQLValidationError(f"Unknown column referenced by generated SQL: '{column_node.name}'.")


def _enforce_limit_ast(expression, max_rows: int, dialect: Optional[str]) -> str:
    """Apply an outer LIMIT through the parsed syntax tree."""
    if max_rows <= 0:
        raise SQLValidationError("Maximum row limit must be greater than zero.")

    limit_node = expression.args.get("limit")
    existing_limit = None
    if limit_node is not None:
        try:
            existing_limit = int(limit_node.expression.name)
        except (TypeError, ValueError, AttributeError):
            existing_limit = None

    if limit_node is None or existing_limit is None or existing_limit > max_rows:
        expression = expression.limit(max_rows, copy=False)
    return expression.sql(dialect=dialect)


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
