"""
Automatic Schema Introspector using SQLAlchemy Inspector.
Discovers tables, column types, primary keys, foreign keys, relationships, and indexes.
"""
from typing import List, Dict, Optional
import sqlalchemy
from sqlalchemy.engine import Engine
from sqlalchemy import inspect

from app.database.schema import (
    ColumnInfo,
    ForeignKeyInfo,
    IndexInfo,
    TableSchema,
    DatabaseRelationship,
    DatabaseSchema,
)


class SchemaIntrospector:
    """Introspects SQL database schemas using SQLAlchemy Inspector without loading row data."""

    @staticmethod
    def get_tables(engine: Engine) -> List[str]:
        """Discover and return all table names in the database."""
        inspector = inspect(engine)
        return sorted(inspector.get_table_names())

    @staticmethod
    def get_table_schema(engine: Engine, table_name: str) -> TableSchema:
        """Introspect a single table's complete schema."""
        inspector = inspect(engine)
        
        # 1. Primary keys
        pk_dict = inspector.get_pk_constraint(table_name) or {}
        primary_keys = pk_dict.get("constrained_columns", [])

        # 2. Columns
        raw_cols = inspector.get_columns(table_name)
        columns: List[ColumnInfo] = []
        for col in raw_cols:
            col_name = col["name"]
            col_type = str(col.get("type", "TEXT"))
            is_pk = col_name in primary_keys or col.get("primary_key", False)
            if is_pk and col_name not in primary_keys:
                primary_keys.append(col_name)

            columns.append(
                ColumnInfo(
                    name=col_name,
                    type=col_type,
                    nullable=col.get("nullable", True),
                    primary_key=is_pk,
                    default=str(col.get("default", "")) if col.get("default") is not None else None,
                    comment=col.get("comment"),
                )
            )

        # 3. Foreign Keys
        raw_fks = inspector.get_foreign_keys(table_name)
        foreign_keys: List[ForeignKeyInfo] = []
        for fk in raw_fks:
            foreign_keys.append(
                ForeignKeyInfo(
                    constrained_columns=fk.get("constrained_columns", []),
                    referred_table=fk.get("referred_table", ""),
                    referred_columns=fk.get("referred_columns", []),
                    name=fk.get("name"),
                )
            )

        # 4. Indexes
        indexes: List[IndexInfo] = []
        try:
            raw_indexes = inspector.get_indexes(table_name)
            for idx in raw_indexes:
                indexes.append(
                    IndexInfo(
                        name=idx.get("name", ""),
                        columns=idx.get("column_names", []),
                        unique=idx.get("unique", False),
                    )
                )
        except Exception:
            pass  # Some engines/views don't support get_indexes

        # 5. Row count estimate (fast count if available)
        row_count = None
        try:
            with engine.connect() as conn:
                dialect = engine.dialect.name.lower()
                if dialect == "sqlite":
                    row_count = conn.execute(sqlalchemy.text(f"SELECT COUNT(*) FROM [{table_name}]")).scalar()
                else:
                    row_count = conn.execute(sqlalchemy.text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        except Exception:
            row_count = None

        return TableSchema(
            name=table_name,
            columns=columns,
            primary_keys=primary_keys,
            foreign_keys=foreign_keys,
            indexes=indexes,
            row_count_estimate=row_count,
        )

    @classmethod
    def get_relationships(cls, engine: Engine) -> List[DatabaseRelationship]:
        """Extract all inter-table foreign key relationships across the database."""
        relationships: List[DatabaseRelationship] = []
        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        for tname in table_names:
            try:
                raw_fks = inspector.get_foreign_keys(tname)
                for fk in raw_fks:
                    ref_table = fk.get("referred_table")
                    if ref_table:
                        relationships.append(
                            DatabaseRelationship(
                                from_table=tname,
                                from_columns=fk.get("constrained_columns", []),
                                to_table=ref_table,
                                to_columns=fk.get("referred_columns", []),
                                constraint_name=fk.get("name"),
                            )
                        )
            except Exception:
                continue

        return relationships

    @classmethod
    def get_database_schema(cls, engine: Engine) -> DatabaseSchema:
        """Introspect all tables and relationships for the connected database."""
        dialect = engine.dialect.name
        table_names = cls.get_tables(engine)
        tables: Dict[str, TableSchema] = {}

        for tname in table_names:
            tables[tname] = cls.get_table_schema(engine, tname)

        relationships = cls.get_relationships(engine)

        return DatabaseSchema(
            dialect=dialect,
            tables=tables,
            relationships=relationships,
        )


# Convenience module-level functions
def get_tables(engine: Engine) -> List[str]:
    return SchemaIntrospector.get_tables(engine)


def get_table_schema(engine: Engine, table_name: str) -> TableSchema:
    return SchemaIntrospector.get_table_schema(engine, table_name)


def get_database_schema(engine: Engine) -> DatabaseSchema:
    return SchemaIntrospector.get_database_schema(engine)


def get_relationships(engine: Engine) -> List[DatabaseRelationship]:
    return SchemaIntrospector.get_relationships(engine)
