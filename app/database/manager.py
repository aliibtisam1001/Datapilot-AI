"""
Multi-Database Connection Manager for DataPilot AI.
Manages a collection of named database connections, enables seamless context switching,
and ensures strict state isolation and resource cleanup across multiple data sources.
"""
from typing import Dict, List, Optional, Any
from app.database.connection import DatabaseConnectionManager, get_default_olist_engine
from app.database.cache import SchemaCache
from app.agent.query_cache import QueryCache


class MultiDatabaseManager:
    """Manages multiple registered database connections with clean switching and state isolation."""

    def __init__(self):
        self._connections: Dict[str, DatabaseConnectionManager] = {}
        self._active_name: Optional[str] = None
        self._init_default_demo()

    def _init_default_demo(self) -> None:
        """Initialize default database connections (custom env var if present, plus fallback Olist demo)."""
        import os
        custom_env_url = os.getenv("DATABASE_URL") or os.getenv("DEFAULT_DB_URL")
        
        # 1. Fallback Olist Demo SQLite
        try:
            _, olist_url = get_default_olist_engine()
            demo_mgr = DatabaseConnectionManager(olist_url, name="Olist Brazilian E-Commerce (Demo)")
            self.register_database("Olist E-Commerce (Demo)", demo_mgr)
            self._active_name = "Olist E-Commerce (Demo)"
        except Exception:
            pass

        # 2. Custom environment database if specified
        if custom_env_url:
            try:
                custom_mgr = DatabaseConnectionManager(custom_env_url, name="Production Database")
                self.register_database("Production Database", custom_mgr)
                self._active_name = "Production Database"
            except Exception:
                pass

    def register_database(self, name: str, manager_or_url: Any) -> DatabaseConnectionManager:
        """Register a new named database connection."""
        if isinstance(manager_or_url, DatabaseConnectionManager):
            mgr = manager_or_url
        else:
            mgr = DatabaseConnectionManager(str(manager_or_url), name=name)

        self._connections[name] = mgr
        if not self._active_name:
            self._active_name = name
        return mgr

    def set_active(self, name: str) -> DatabaseConnectionManager:
        """Set the active database connection by name."""
        if name not in self._connections:
            raise KeyError(f"Database '{name}' is not registered in MultiDatabaseManager.")
        self._active_name = name
        return self._connections[name]

    def get_active(self) -> Optional[DatabaseConnectionManager]:
        """Get the currently active DatabaseConnectionManager."""
        if self._active_name and self._active_name in self._connections:
            return self._connections[self._active_name]
        if self._connections:
            first_name = next(iter(self._connections))
            self._active_name = first_name
            return self._connections[first_name]
        return None

    @property
    def active_name(self) -> Optional[str]:
        return self._active_name

    def get_database(self, name: str) -> Optional[DatabaseConnectionManager]:
        """Retrieve a registered connection manager by name."""
        return self._connections.get(name)

    def remove_database(self, name: str) -> bool:
        """Disconnect and remove a registered database."""
        if name in self._connections:
            mgr = self._connections.pop(name)
            mgr.dispose()
            if self._active_name == name:
                self._active_name = next(iter(self._connections)) if self._connections else None
            return True
        return False

    def list_databases(self) -> List[Dict[str, Any]]:
        """List all registered databases with status and metadata."""
        items = []
        for name, mgr in self._connections.items():
            items.append({
                "name": name,
                "db_type": mgr.db_type.value.upper(),
                "masked_url": mgr.masked_url,
                "is_active": (name == self._active_name),
                "is_connected": mgr.is_connected,
            })
        return items
