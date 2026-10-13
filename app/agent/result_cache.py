"""Bounded cache for complete analysis results.

Unlike QueryCache, this avoids both a database roundtrip and a second LLM call
when the same question is repeated against the same schema version.
"""
from dataclasses import dataclass
import hashlib
import threading
import time
from typing import Dict, Optional, Tuple

import pandas as pd


@dataclass
class CachedAnalysis:
    sql: str
    dataframe: pd.DataFrame
    answer: str
    explanation: Optional[str]
    model_name: str


class ResultCache:
    _cache: Dict[str, Tuple[CachedAnalysis, float]] = {}
    _key_databases: Dict[str, str] = {}
    _lock = threading.Lock()
    _max_entries = 64
    _max_dataframe_bytes = 2_000_000

    @staticmethod
    def _database_fingerprint(db_url: str) -> str:
        return hashlib.sha256(db_url.encode("utf-8")).hexdigest()

    @classmethod
    def _key(
        cls,
        db_url: str,
        question: str,
        schema_signature: str,
        namespace: str = "",
    ) -> str:
        normalized_question = " ".join(question.lower().split())
        value = f"{namespace}:::{db_url}:::{schema_signature}:::{normalized_question}"
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    @classmethod
    def get(
        cls,
        db_url: str,
        question: str,
        schema_signature: str,
        ttl_seconds: int = 120,
        namespace: str = "",
    ) -> Optional[CachedAnalysis]:
        if ttl_seconds <= 0:
            return None
        key = cls._key(db_url, question, schema_signature, namespace)
        with cls._lock:
            entry = cls._cache.get(key)
            if not entry:
                return None
            result, created_at = entry
            if time.time() - created_at >= ttl_seconds:
                cls._cache.pop(key, None)
                cls._key_databases.pop(key, None)
                return None
            return CachedAnalysis(
                sql=result.sql,
                dataframe=result.dataframe.copy(deep=True),
                answer=result.answer,
                explanation=result.explanation,
                model_name=result.model_name,
            )

    @classmethod
    def set(
        cls,
        db_url: str,
        question: str,
        schema_signature: str,
        result: CachedAnalysis,
        namespace: str = "",
    ) -> bool:
        size = int(result.dataframe.memory_usage(index=True, deep=True).sum())
        if size > cls._max_dataframe_bytes or len(result.dataframe) > 500:
            return False

        key = cls._key(db_url, question, schema_signature, namespace)
        stored = CachedAnalysis(
            sql=result.sql,
            dataframe=result.dataframe.copy(deep=True),
            answer=result.answer,
            explanation=result.explanation,
            model_name=result.model_name,
        )
        with cls._lock:
            cls._cache[key] = (stored, time.time())
            cls._key_databases[key] = cls._database_fingerprint(db_url)
            if len(cls._cache) > cls._max_entries:
                oldest = min(cls._cache, key=lambda item: cls._cache[item][1])
                cls._cache.pop(oldest, None)
                cls._key_databases.pop(oldest, None)
        return True

    @classmethod
    def invalidate(cls, db_url: Optional[str] = None) -> None:
        with cls._lock:
            if db_url is None:
                cls._cache.clear()
                cls._key_databases.clear()
                return
            fingerprint = cls._database_fingerprint(db_url)
            keys = [
                key for key, value in cls._key_databases.items()
                if value == fingerprint
            ]
            for key in keys:
                cls._cache.pop(key, None)
                cls._key_databases.pop(key, None)
