"""
Universal SQL Generator for DataPilot AI.
Generates structured, dialect-accurate, read-only SQL queries from natural language
and dynamic schema definitions for SQLite, PostgreSQL, and MySQL.
"""
import os
import re
import json
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from langchain_groq import ChatGroq

from app.database.schema import DatabaseSchema
from app.guardrails import validate_sql, SQLValidationError
from app.utils import strip_thinking
from app.agent.semantic_context import build_semantic_context


@dataclass
class SQLGenerationResult:
    """Structured response from the SQL generator."""
    sql: str
    tables_used: List[str]
    reasoning_summary: str
    confidence: float
    raw_response: Optional[str] = None


DIALECT_GUIDES = {
    "sqlite": """
- Dialect: SQLite
- Dates: Use `strftime('%Y-%m', date_col)`, `strftime('%Y', date_col)`, `strftime('%m', date_col)`
- Date diff: `ROUND(julianday(end_date) - julianday(start_date), 1)`
- String concat: `col1 || ' ' || col2`
- Case-sensitive names: Use quotes or square brackets `[table]` if column has special characters.
- Add `LIMIT <n>` for top-N ranking or large lists.
""",
    "postgresql": """
- Dialect: PostgreSQL
- Dates: Use `DATE_TRUNC('month', date_col)`, `EXTRACT(YEAR FROM date_col)`, `EXTRACT(MONTH FROM date_col)`
- Date diff: `(end_date::date - start_date::date)` or `EXTRACT(EPOCH FROM (end_date - start_date))/86400`
- String concat: `col1 || ' ' || col2` or `CONCAT(col1, ' ', col2)`
- Add `LIMIT <n>` for top-N ranking or large lists.
- Cast types cleanly if needed (e.g. `col::numeric`).
""",
    "mysql": """
- Dialect: MySQL
- Dates: Use `DATE_FORMAT(date_col, '%Y-%m')`, `YEAR(date_col)`, `MONTH(date_col)`
- Date diff: `DATEDIFF(end_date, start_date)`
- String concat: `CONCAT(col1, ' ', col2)`
- Identifiers: Use backticks `` `table` `` if names contain spaces or keywords.
- Add `LIMIT <n>` for top-N ranking or large lists.
""",
}


class UniversalSQLGenerator:
    """Generates secure, dialect-aware SQL queries from natural language and database schema."""

    @classmethod
    def generate_sql(
        cls,
        question: str,
        db_schema: DatabaseSchema,
        llm: Optional[ChatGroq] = None,
        api_key: Optional[str] = None,
        model_name: str = "openai/gpt-oss-120b",
    ) -> SQLGenerationResult:
        """
        Generate a structured, validated SQL query for the given question and schema.
        """
        if llm is None:
            llm = ChatGroq(
                model=model_name,
                temperature=0.0,
                api_key=api_key or os.getenv("GROQ_API_KEY"),
            )

        dialect = db_schema.dialect.lower()
        dialect_guide = DIALECT_GUIDES.get(dialect, DIALECT_GUIDES["sqlite"])
        schema_text = db_schema.to_compact_schema_string()
        semantic_context = build_semantic_context(db_schema)

        prompt = f"""You are an elite enterprise SQL Data Analyst AI.
Generate a valid, highly optimized, read-only SQL query to answer the user's question.

=== TARGET DATABASE & DIALECT RULES ===
{dialect_guide}

{schema_text}

=== BUSINESS SEMANTICS ===
{semantic_context}

=== CRITICAL SQL GENERATION RULES ===
1. Generate SELECT statements ONLY. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, or schema modifications.
2. Use ONLY table names and column names that exist in the schema above. NEVER invent or hallucinate columns or tables.
3. Form proper INNER or LEFT JOINs using the foreign key relationships shown above.
4. Add an appropriate LIMIT (e.g., 5, 10, or 50) when ranking or listing records unless an overall aggregation/count is requested.
5. Ensure column aliases are clear and human-readable (e.g. `AS total_revenue`, `AS order_count`).
6. Format your entire output as a single, valid JSON object with the following schema:
{{
    "sql": "SELECT ...",
    "tables_used": ["table1", "table2"],
    "reasoning_summary": "1-sentence plain explanation of how the query computes the result.",
    "confidence": 0.95
}}

User Question: {question}

JSON Output:"""

        response = llm.invoke(prompt)
        raw_text = strip_thinking(response.content if hasattr(response, "content") else str(response))

        # Parse JSON from response
        parsed_json = cls._extract_json(raw_text)
        
        raw_sql = parsed_json.get("sql", "").strip()
        tables_used = parsed_json.get("tables_used", [])
        reasoning = parsed_json.get("reasoning_summary", "Query generated based on schema analysis.")
        confidence = max(0.0, min(1.0, float(parsed_json.get("confidence", 0.9))))

        # If JSON extraction failed to find clean SQL, fallback to extracting SQL block
        if not raw_sql:
            raw_sql = cls._extract_sql_fallback(raw_text)

        # Validate with SQL Guardrail layer
        validated_sql = validate_sql(
            raw_sql,
            dialect=dialect,
            db_schema=db_schema,
        )

        return SQLGenerationResult(
            sql=validated_sql,
            tables_used=tables_used,
            reasoning_summary=reasoning,
            confidence=confidence,
            raw_response=raw_text,
        )

    @classmethod
    def repair_sql(
        cls,
        question: str,
        failed_sql: str,
        error_message: str,
        db_schema: DatabaseSchema,
        llm: Optional[ChatGroq] = None,
        api_key: Optional[str] = None,
        model_name: str = "openai/gpt-oss-120b",
    ) -> SQLGenerationResult:
        """Perform one bounded repair pass after a database syntax error."""
        if llm is None:
            llm = ChatGroq(
                model=model_name,
                temperature=0.0,
                api_key=api_key or os.getenv("GROQ_API_KEY"),
            )

        dialect = db_schema.dialect.lower()
        prompt = f"""You are repairing one read-only {dialect.upper()} query.
Return only one JSON object with keys sql, tables_used, reasoning_summary, confidence.
Use only the schema shown below. Do not use write operations.

{db_schema.to_compact_schema_string()}

{build_semantic_context(db_schema)}

Question: {question}
Failed SQL: {failed_sql}
Sanitized database error: {error_message[:800]}

Corrected JSON:"""
        response = llm.invoke(prompt)
        raw_text = strip_thinking(
            response.content if hasattr(response, "content") else str(response)
        )
        parsed = cls._extract_json(raw_text)
        raw_sql = parsed.get("sql", "").strip() or cls._extract_sql_fallback(raw_text)
        validated_sql = validate_sql(
            raw_sql,
            dialect=dialect,
            db_schema=db_schema,
        )
        return SQLGenerationResult(
            sql=validated_sql,
            tables_used=list(parsed.get("tables_used", [])),
            reasoning_summary=parsed.get(
                "reasoning_summary", "Corrected query after database validation."
            ),
            confidence=max(0.0, min(1.0, float(parsed.get("confidence", 0.75)))),
            raw_response=raw_text,
        )

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        """Safely extract JSON dictionary from model response."""
        text = text.strip()
        # Remove markdown code blocks if wrapped
        if "```json" in text:
            match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if match:
                text = match.group(1)
        elif "```" in text:
            match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
            if match:
                text = match.group(1)

        # Find first { and last }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_str = text[start : end + 1]
            try:
                return json.loads(json_str)
            except Exception:
                pass
        return {}

    @staticmethod
    def _extract_sql_fallback(text: str) -> str:
        """Fallback to extract raw SQL statement if JSON parsing failed."""
        if "```sql" in text:
            match = re.search(r'```sql\s*(.*?)\s*```', text, re.DOTALL)
            if match:
                return match.group(1).strip()
        elif "```" in text:
            match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # Look for SELECT ...
        match = re.search(r'\b(SELECT\s+.*)', text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return text.strip()


def generate_sql_query(
    question: str,
    db_schema: DatabaseSchema,
    llm: Optional[ChatGroq] = None,
    api_key: Optional[str] = None,
    model_name: str = "openai/gpt-oss-120b",
) -> SQLGenerationResult:
    """Convenience helper for universal SQL generation."""
    return UniversalSQLGenerator.generate_sql(
        question=question,
        db_schema=db_schema,
        llm=llm,
        api_key=api_key,
        model_name=model_name,
    )
