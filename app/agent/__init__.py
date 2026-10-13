"""
Agent Package for DataPilot AI.
Exports SchemaSelector, UniversalSQLGenerator, generate_sql_query, and QueryCache.
"""
from app.agent.schema_selector import SchemaSelector, select_relevant_schema
from app.agent.sql_generator import UniversalSQLGenerator, SQLGenerationResult, generate_sql_query
from app.agent.query_cache import QueryCache
from app.agent.result_cache import ResultCache, CachedAnalysis
from app.agent.model_router import model_candidates_for

__all__ = [
    "SchemaSelector",
    "select_relevant_schema",
    "UniversalSQLGenerator",
    "SQLGenerationResult",
    "generate_sql_query",
    "QueryCache",
    "ResultCache",
    "CachedAnalysis",
    "model_candidates_for",
]
