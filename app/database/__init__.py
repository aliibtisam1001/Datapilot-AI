"""
Database Package for DataPilot AI.
Exports DatabaseConnectionManager, MultiDatabaseManager, EnginePool, SchemaIntrospector, SchemaCache, and Schema Data Models.
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
from app.database.manager import MultiDatabaseManager
from app.database.schema import (
    ColumnInfo,
    ForeignKeyInfo,
    IndexInfo,
    TableSchema,
    DatabaseRelationship,
    DatabaseSchema,
)
from app.database.introspector import (
    SchemaIntrospector,
    get_tables,
    get_table_schema,
    get_database_schema,
    get_relationships,
)
from app.database.cache import (
    SchemaCache,
    get_cached_schema,
)

__all__ = [
    # Connection & Multi-DB Management
    "EnginePool",
    "DatabaseConnectionManager",
    "MultiDatabaseManager",
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
    
    # Schema Models
    "ColumnInfo",
    "ForeignKeyInfo",
    "IndexInfo",
    "TableSchema",
    "DatabaseRelationship",
    "DatabaseSchema",
    
    # Introspection
    "SchemaIntrospector",
    "get_tables",
    "get_table_schema",
    "get_database_schema",
    "get_relationships",
    
    # Cache
    "SchemaCache",
    "get_cached_schema",
]
