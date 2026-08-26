"""
Engine Pool & Lifecycle Manager.
Provides thread-safe SQLAlchemy engine pooling, pre-ping validation, and clean resource disposal.
"""
import os
import threading
from typing import Dict, Optional
import sqlalchemy
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool, StaticPool, NullPool


class EnginePool:
    """Thread-safe engine pool manager for multi-database connections."""

    _instances: Dict[str, Engine] = {}
    _lock = threading.Lock()

    @classmethod
    def get_or_create_engine(cls, url: str, is_sqlite: bool = False, pool_size: int = 5, max_overflow: int = 10) -> Engine:
        """Get an existing engine for the URL or create a new pooled engine."""
        with cls._lock:
            if url in cls._instances:
                return cls._instances[url]

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
                # PostgreSQL or MySQL
                engine = sqlalchemy.create_engine(
                    url,
                    poolclass=QueuePool,
                    pool_size=pool_size,
                    max_overflow=max_overflow,
                    pool_recycle=1800,
                    pool_pre_ping=True,
                    pool_timeout=10,
                )

            cls._instances[url] = engine
            return engine

    @classmethod
    def dispose_engine(cls, url: str) -> None:
        """Safely dispose of an engine and remove from pool registry."""
        with cls._lock:
            engine = cls._instances.pop(url, None)
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
