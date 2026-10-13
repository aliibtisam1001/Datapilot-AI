"""
Query Cache Layer for DataPilot AI.
Provides thread-safe in-memory caching of generated SQL queries and reasoning
with Time-To-Live (TTL) expiration to accelerate repeated questions.
"""
import time
import hashlib
import threading
from typing import Dict, Optional, Tuple, Any
from app.agent.sql_generator import SQLGenerationResult


class QueryCache:
    """Thread-safe TTL query cache for natural language SQL generation."""

    _cache: Dict[str, Tuple[SQLGenerationResult, float]] = {}
    _key_databases: Dict[str, str] = {}
    _lock = threading.Lock()
    _stats = {"hits": 0, "misses": 0}
    _max_entries = 256

    @staticmethod
    def _database_fingerprint(db_url: str) -> str:
        return hashlib.sha256(db_url.encode("utf-8")).hexdigest()

    @staticmethod
    def _normalize_key(db_url: str, question: str, schema_signature: str = "") -> str:
        """Create a normalized deterministic cache key."""
        clean_q = " ".join(question.strip().lower().split())
        combined = f"{db_url}:::{schema_signature}:::{clean_q}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    @classmethod
    def get(
        cls,
        db_url: str,
        question: str,
        ttl_seconds: int = 300,
        schema_signature: str = "",
    ) -> Optional[SQLGenerationResult]:
        """
        Retrieve cached SQLGenerationResult if present and not expired.
        """
        if ttl_seconds <= 0:
            return None

        key = cls._normalize_key(db_url, question, schema_signature)
        with cls._lock:
            if key in cls._cache:
                result, timestamp = cls._cache[key]
                if time.time() - timestamp < ttl_seconds:
                    cls._stats["hits"] += 1
                    return result
                else:
                    # Expired
                    del cls._cache[key]
                    cls._key_databases.pop(key, None)
            cls._stats["misses"] += 1
            return None

    @classmethod
    def set(
        cls,
        db_url: str,
        question: str,
        result: SQLGenerationResult,
        schema_signature: str = "",
    ) -> None:
        """Store generated SQL query in cache with current timestamp."""
        key = cls._normalize_key(db_url, question, schema_signature)
        with cls._lock:
            cls._cache[key] = (result, time.time())
            cls._key_databases[key] = cls._database_fingerprint(db_url)
            if len(cls._cache) > cls._max_entries:
                oldest_key = min(cls._cache, key=lambda item: cls._cache[item][1])
                cls._cache.pop(oldest_key, None)
                cls._key_databases.pop(oldest_key, None)

    @classmethod
    def invalidate(cls, db_url: Optional[str] = None) -> None:
        """Invalidate cache for a specific database or all entries."""
        with cls._lock:
            if db_url is None:
                cls._cache.clear()
                cls._key_databases.clear()
            else:
                fingerprint = cls._database_fingerprint(db_url)
                matching = [
                    key for key, value in cls._key_databases.items()
                    if value == fingerprint
                ]
                for key in matching:
                    cls._cache.pop(key, None)
                    cls._key_databases.pop(key, None)

    @classmethod
    def get_stats(cls) -> Dict[str, int]:
        """Return cache hit and miss statistics."""
        with cls._lock:
            return dict(cls._stats)
