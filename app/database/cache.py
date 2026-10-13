"""
Schema Cache Manager for DataPilot AI.
Provides thread-safe in-memory schema caching, cache invalidation, and manual refresh controls.
"""
import threading
import hashlib
from typing import Dict, Optional
from sqlalchemy.engine import Engine

from app.database.schema import DatabaseSchema
from app.database.introspector import SchemaIntrospector


class SchemaCache:
    """Thread-safe schema cache to prevent redundant database introspection."""

    _cache: Dict[str, DatabaseSchema] = {}
    _lock = threading.Lock()

    @staticmethod
    def _key(url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    @classmethod
    def get_or_introspect(cls, engine: Engine, url: str, force_refresh: bool = False) -> DatabaseSchema:
        """
        Get the cached schema for a database connection URL or introspect and cache it.
        """
        key = cls._key(url)
        with cls._lock:
            if not force_refresh and key in cls._cache:
                return cls._cache[key]

        # Introspect without holding the lock for long
        schema = SchemaIntrospector.get_database_schema(engine)

        with cls._lock:
            cls._cache[key] = schema
            return schema

    @classmethod
    def get_cached_schema(cls, url: str) -> Optional[DatabaseSchema]:
        """Get cached schema if present without introspecting."""
        with cls._lock:
            return cls._cache.get(cls._key(url))

    @classmethod
    def invalidate(cls, url: Optional[str] = None) -> None:
        """Invalidate cache for a specific URL or all URLs."""
        with cls._lock:
            if url:
                cls._cache.pop(cls._key(url), None)
            else:
                cls._cache.clear()

    @classmethod
    def is_cached(cls, url: str) -> bool:
        """Check if schema is already cached for the given URL."""
        with cls._lock:
            return cls._key(url) in cls._cache


def get_cached_schema(engine: Engine, url: str, force_refresh: bool = False) -> DatabaseSchema:
    """Convenience function to get cached or fresh schema."""
    return SchemaCache.get_or_introspect(engine, url, force_refresh=force_refresh)
