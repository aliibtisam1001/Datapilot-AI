"""
Universal Database Connection Layer for DataPilot AI.
Provides unified SQLAlchemy abstraction, connection testing, sanitized error handling,
URL masking, and multi-database management (SQLite, PostgreSQL, MySQL).
"""
import os
import re
from enum import Enum
from typing import Optional, Tuple, Dict, Any
import sqlalchemy
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import (
    ArgumentError,
    OperationalError,
    NoSuchModuleError,
    ProgrammingError,
)
import pandas as pd

from app.database.pool import EnginePool


class DatabaseType(str, Enum):
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    UNKNOWN = "unknown"


# Custom Standardized Database Exceptions
class DatabaseConnectionError(Exception):
    """Base exception for all database connection errors."""
    pass


class InvalidURLError(DatabaseConnectionError):
    """Raised when the database connection URL format is invalid."""
    pass


class UnsupportedDatabaseError(DatabaseConnectionError):
    """Raised when an unsupported database dialect is requested."""
    pass


class AuthenticationError(DatabaseConnectionError):
    """Raised when database authentication fails (invalid username/password)."""
    pass


class HostUnavailableError(DatabaseConnectionError):
    """Raised when the remote database host/port is unreachable."""
    pass


class DatabaseNotFoundError(DatabaseConnectionError):
    """Raised when the target database does not exist on the server."""
    pass


def mask_url(url_str: str) -> str:
    """
    Safely mask passwords in database connection URLs.
    Example: postgresql://admin:secret123@localhost:5432/mydb -> postgresql://admin:***@localhost:5432/mydb
    """
    if not url_str:
        return ""
    try:
        u = make_url(url_str)
        return u.render_as_string(hide_password=True)
    except Exception:
        # Fallback regex masking if URL parsing fails
        return re.sub(r':([^:@/]+)@', ':***@', url_str)


def detect_database_type(url_str: str) -> DatabaseType:
    """Detect database dialect type from URL."""
    if not url_str or not isinstance(url_str, str):
        return DatabaseType.UNKNOWN
    clean = url_str.strip().lower()
    if clean.startswith("sqlite"):
        return DatabaseType.SQLITE
    elif clean.startswith("postgres"):
        return DatabaseType.POSTGRESQL
    elif clean.startswith("mysql"):
        return DatabaseType.MYSQL
    return DatabaseType.UNKNOWN


def normalize_connection_url(raw_url: str) -> str:
    """
    Ensure the connection URL uses appropriate, installed drivers.
    e.g., postgresql:// -> postgresql+psycopg2://
    mysql:// -> mysql+pymysql://
    """
    if not raw_url or not isinstance(raw_url, str):
        raise InvalidURLError("Connection URL cannot be empty.")

    url = raw_url.strip()
    
    # Handle PostgreSQL driver defaults
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)

    # Handle MySQL driver defaults
    elif url.startswith("mysql://") and not url.startswith("mysql+"):
        url = url.replace("mysql://", "mysql+pymysql://", 1)

    # Validate with SQLAlchemy make_url
    try:
        parsed = make_url(url)
        if not parsed.drivername:
            raise InvalidURLError(f"Invalid connection URL structure: {mask_url(url)}")
    except ArgumentError as e:
        raise InvalidURLError(f"Malformed connection URL: {e}")

    return url


class DatabaseConnectionManager:
    """
    Universal database connection manager for DataPilot AI.
    Handles lifecycle, pooled engines, connection testing, and clean error reporting.
    """

    def __init__(self, connection_url: Optional[str] = None, name: str = "Default"):
        self.name = name
        self._raw_url: Optional[str] = None
        self._normalized_url: Optional[str] = None
        self._db_type: DatabaseType = DatabaseType.UNKNOWN
        self._engine: Optional[Engine] = None

        if connection_url:
            self.set_connection(connection_url)

    @property
    def raw_url(self) -> Optional[str]:
        return self._raw_url

    @property
    def normalized_url(self) -> Optional[str]:
        return self._normalized_url

    @property
    def masked_url(self) -> str:
        return mask_url(self._normalized_url or self._raw_url or "")

    @property
    def db_type(self) -> DatabaseType:
        return self._db_type

    @property
    def engine(self) -> Optional[Engine]:
        return self._engine

    @property
    def is_connected(self) -> bool:
        if not self._engine:
            return False
        try:
            with self._engine.connect() as conn:
                conn.execute(sqlalchemy.text("SELECT 1"))
            return True
        except Exception:
            return False

    def set_connection(self, raw_url: str) -> None:
        """Configure and create an engine for the provided database URL."""
        if not raw_url or not raw_url.strip():
            raise InvalidURLError("Connection URL cannot be empty.")

        self._raw_url = raw_url.strip()
        self._db_type = detect_database_type(self._raw_url)

        if self._db_type == DatabaseType.UNKNOWN:
            raise UnsupportedDatabaseError(
                f"Unsupported database scheme in URL: '{self.masked_url}'. "
                "Supported databases: SQLite (sqlite:///...), PostgreSQL (postgresql://...), MySQL (mysql://...)"
            )

        self._normalized_url = normalize_connection_url(self._raw_url)
        is_sqlite = self._db_type == DatabaseType.SQLITE
        self._engine = EnginePool.get_or_create_engine(self._normalized_url, is_sqlite=is_sqlite)

    def test_connection(self) -> Tuple[bool, str]:
        """
        Test the active connection.
        Returns (True, "Connected successfully") or (False, "<Sanitized Error Message>").
        """
        if not self._engine or not self._normalized_url:
            return False, "No active database connection configured."

        try:
            with self._engine.connect() as conn:
                conn.execute(sqlalchemy.text("SELECT 1"))
            return True, f"Successfully connected to {self._db_type.value.upper()} database."
        except OperationalError as e:
            return False, self._classify_operational_error(e)
        except NoSuchModuleError as e:
            return False, f"Missing database driver: {e}"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def _classify_operational_error(self, err: OperationalError) -> str:
        """Classify operational errors into human-friendly, sanitized diagnostics."""
        err_msg = str(err).lower()

        # Password / Authentication failures
        if any(w in err_msg for w in ["password authentication failed", "access denied for user", "auth_failed"]):
            return "Authentication failed: Invalid username or password for database."

        # Host / Port / Connection refusal
        elif any(w in err_msg for w in ["could not connect to server", "connection refused", "can't connect to mysql server", "name or service not known", "nodename nor servname"]):
            return "Host unavailable: Could not reach the database server. Check host, port, and firewall."

        # Target database does not exist
        elif any(w in err_msg for w in ["database", "does not exist", "unknown database"]):
            return "Database not found: The specified database name does not exist on the server."

        # Timeout / network loss
        elif any(w in err_msg for w in ["timeout", "timed out"]):
            return "Connection timeout: The database server took too long to respond."

        # SQLite specific file missing/corrupt
        elif "unable to open database file" in err_msg:
            return "SQLite error: Unable to open database file. Check path permissions."

        return f"Database operational error: {str(err)}"

    def execute_query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Execute a read query and return results as a Pandas DataFrame."""
        if not self._engine:
            raise DatabaseConnectionError("Cannot execute query: No active database connection.")

        try:
            with self._engine.connect() as conn:
                if params:
                    df = pd.read_sql(sqlalchemy.text(sql), conn, params=params)
                else:
                    df = pd.read_sql(sqlalchemy.text(sql), conn)
            return df
        except Exception as e:
            raise DatabaseConnectionError(f"Query execution failed: {str(e)}")

    def dispose(self) -> None:
        """Dispose of the current connection engine."""
        if self._normalized_url:
            EnginePool.dispose_engine(self._normalized_url)
            self._engine = None


# ── Global Helper Functions ──

def get_default_olist_engine() -> Tuple[Engine, str]:
    """
    Get or create the fallback Olist SQLite demo database connection engine.
    Ensures the SQLite file exists on disk.
    """
    data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
    db_path = os.path.join(data_dir, "olist.db")

    if not os.path.exists(db_path):
        from app.load_data import create_sqlite_database
        create_sqlite_database()

    abs_path = os.path.abspath(db_path)
    url = f"sqlite:///{abs_path}"
    engine = EnginePool.get_or_create_engine(url, is_sqlite=True)
    return engine, url
