"""
Engine Pool & Lifecycle Manager.
Provides thread-safe SQLAlchemy engine pooling, pre-ping validation, and clean resource disposal.
"""
import os
import threading
import hashlib
from typing import Dict, Optional
import sqlalchemy
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool, StaticPool, NullPool


class EnginePool:
    """Thread-safe engine pool manager for multi-database connections."""

    _instances: Dict[str, Engine] = {}
    _lock = threading.Lock()

    @staticmethod
    def _key(url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    @classmethod
    def get_or_create_engine(cls, url: str, is_sqlite: bool = False, pool_size: int = 5, max_overflow: int = 10) -> Engine:
        """Get an existing engine for the URL or create a new pooled engine."""
        key = cls._key(url)
        with cls._lock:
            if key in cls._instances:
                return cls._instances[key]

            connect_args = {}
            if is_sqlite:
                connect_args["check_same_thread"] = False
                if ":memory:" in url:
                    engine = sqlalchemy.create_engine(
                        url,
                        connect_args=connect_args,
                        poolclass=StaticPool,
                    )
                else:
                    engine = sqlalchemy.create_engine(
                        url,
                        connect_args=connect_args,
                        pool_pre_ping=True,
                    )
            else:
                # PostgreSQL or MySQL with fast connect timeout
                if "postgres" in url:
                    connect_args["connect_timeout"] = 5
                elif "mysql" in url:
                    connect_args["connect_timeout"] = 5
                engine = sqlalchemy.create_engine(
                    url,
                    connect_args=connect_args,
                    poolclass=QueuePool,
                    pool_size=pool_size,
                    max_overflow=max_overflow,
                    pool_recycle=1800,
                    pool_pre_ping=True,
                    pool_timeout=5,
                )

            cls._instances[key] = engine
            return engine

    @classmethod
    def dispose_engine(cls, url: str) -> None:
        """Safely dispose of an engine and remove from pool registry."""
        with cls._lock:
            engine = cls._instances.pop(cls._key(url), None)
            if engine:
                try:
                    engine.dispose()
                except Exception:
                    pass

    @classmethod
    def dispose_all(cls) -> None:
        """Dispose of all active pooled engines."""
        with cls._lock:
            for url, engine in list(cls._instances.items()):
                try:
                    engine.dispose()
                except Exception:
                    pass
            cls._instances.clear()
