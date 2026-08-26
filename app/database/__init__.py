"""
Database Package for DataPilot AI.
Exports DatabaseConnectionManager, EnginePool, DatabaseType, and exception classes.
"""
from app.database.pool import EnginePool
from app.database.connection import (
    DatabaseConnectionManager,
    DatabaseType,
    DatabaseConnectionError,
    InvalidURLError,
    UnsupportedDatabaseError,
    AuthenticationError,
    HostUnavailableError,
    DatabaseNotFoundError,
    mask_url,
    detect_database_type,
    normalize_connection_url,
    get_default_olist_engine,
)

__all__ = [
    "EnginePool",
    "DatabaseConnectionManager",
    "DatabaseType",
    "DatabaseConnectionError",
    "InvalidURLError",
    "UnsupportedDatabaseError",
    "AuthenticationError",
    "HostUnavailableError",
    "DatabaseNotFoundError",
    "mask_url",
    "detect_database_type",
    "normalize_connection_url",
    "get_default_olist_engine",
]
