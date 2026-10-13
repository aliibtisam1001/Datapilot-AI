"""
Normalized Internal Schema Representation Data Models for DataPilot AI.
Represents tables, columns, primary keys, foreign keys, relationships, and indexes.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
import hashlib


@dataclass
class ColumnInfo:
    """Represents a database column's metadata."""
    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False
    default: Optional[str] = None
    comment: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ForeignKeyInfo:
    """Represents a foreign key constraint."""
    constrained_columns: List[str]
    referred_table: str
    referred_columns: List[str]
    name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IndexInfo:
    """Represents a table index."""
    name: str
    columns: List[str]
    unique: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DatabaseRelationship:
    """Represents a directional foreign key relationship between two tables."""
    from_table: str
    from_columns: List[str]
    to_table: str
    to_columns: List[str]
    constraint_name: Optional[str] = None

    def __str__(self) -> str:
        from_cols = ", ".join(self.from_columns)
        to_cols = ", ".join(self.to_columns)
        return f"{self.from_table}({from_cols}) ──► {self.to_table}({to_cols})"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TableSchema:
    """Represents a single table's complete schema."""
    name: str
    columns: List[ColumnInfo] = field(default_factory=list)
    primary_keys: List[str] = field(default_factory=list)
    foreign_keys: List[ForeignKeyInfo] = field(default_factory=list)
    indexes: List[IndexInfo] = field(default_factory=list)
    row_count_estimate: Optional[int] = None

    @property
    def column_names(self) -> List[str]:
        return [c.name for c in self.columns]

    def get_column(self, col_name: str) -> Optional[ColumnInfo]:
        for c in self.columns:
            if c.name.lower() == col_name.lower():
                return c
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "columns": [c.to_dict() for c in self.columns],
            "primary_keys": self.primary_keys,
            "foreign_keys": [fk.to_dict() for fk in self.foreign_keys],
            "indexes": [idx.to_dict() for idx in self.indexes],
            "row_count_estimate": self.row_count_estimate,
        }

    def to_compact_summary(self) -> str:
        """Returns a single-line compact representation of table columns."""
        cols_repr = []
        for c in self.columns:
            prefix = "PK:" if c.primary_key else ""
            cols_repr.append(f"{prefix}{c.name} ({c.type})")
        return f"{self.name}: " + ", ".join(cols_repr)


@dataclass
class DatabaseSchema:
    """Normalized internal representation of an entire database schema."""
    dialect: str
    tables: Dict[str, TableSchema] = field(default_factory=dict)
    relationships: List[DatabaseRelationship] = field(default_factory=list)

    @property
    def table_names(self) -> List[str]:
        return list(self.tables.keys())

    def get_table(self, table_name: str) -> Optional[TableSchema]:
        for k, v in self.tables.items():
            if k.lower() == table_name.lower():
                return v
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dialect": self.dialect,
            "tables": {name: t.to_dict() for name, t in self.tables.items()},
            "relationships": [r.to_dict() for r in self.relationships],
            "total_tables": len(self.tables),
            "total_relationships": len(self.relationships),
        }

    def to_compact_schema_string(self) -> str:
        """Generates a clean, token-efficient schema description for LLM prompts."""
        lines = [f"=== DATABASE SCHEMA (Dialect: {self.dialect.upper()}) ==="]
        for tname, tschema in self.tables.items():
            lines.append(tschema.to_compact_summary())
        
        if self.relationships:
            lines.append("\n=== FOREIGN KEY RELATIONSHIPS ===")
            for r in self.relationships:
                lines.append(str(r))
        return "\n".join(lines)

    def fingerprint(self) -> str:
        """Stable cache version for table, column, and relationship metadata."""
        payload = self.to_compact_schema_string().encode("utf-8")
        return hashlib.sha256(payload).hexdigest()
