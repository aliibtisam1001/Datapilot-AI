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
    _lock = threading.Lock()
    _stats = {"hits": 0, "misses": 0}

    @staticmethod
    def _normalize_key(db_url: str, question: str) -> str:
        """Create a normalized deterministic cache key."""
        clean_q = " ".join(question.strip().lower().split())
        combined = f"{db_url}:::{clean_q}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    @classmethod
    def get(cls, db_url: str, question: str, ttl_seconds: int = 300) -> Optional[SQLGenerationResult]:
        """
        Retrieve cached SQLGenerationResult if present and not expired.
        """
        key = cls._normalize_key(db_url, question)
        with cls._lock:
            if key in cls._cache:
                result, timestamp = cls._cache[key]
                if time.time() - timestamp <= ttl_seconds:
                    cls._stats["hits"] += 1
                    return result
                else:
                    # Expired
                    del cls._cache[key]
            cls._stats["misses"] += 1
            return None

    @classmethod
    def set(cls, db_url: str, question: str, result: SQLGenerationResult) -> None:
        """Store generated SQL query in cache with current timestamp."""
        key = cls._normalize_key(db_url, question)
        with cls._lock:
            cls._cache[key] = (result, time.time())

    @classmethod
    def invalidate(cls, db_url: Optional[str] = None) -> None:
        """Invalidate cache for a specific database or all entries."""
        with cls._lock:
            if db_url is None:
                cls._cache.clear()
            else:
                prefix_keys = [k for k in cls._cache.keys()]
                # Since keys are hashed, clearing all or tracking url mapping
                cls._cache.clear()

    @classmethod
    def get_stats(cls) -> Dict[str, int]:
        """Return cache hit and miss statistics."""
        with cls._lock:
            return dict(cls._stats)
