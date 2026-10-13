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
    def get_table_schema(
        engine: Engine,
        table_name: str,
        include_row_count: bool = False,
    ) -> TableSchema:
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

        # 5. Exact counts are deliberately opt-in. COUNT(*) during connection
        # setup can scan every table and is especially wasteful on remote DBs.
        row_count = None
        if include_row_count:
            try:
                preparer = engine.dialect.identifier_preparer
                quoted_table = preparer.quote(table_name)
                with engine.connect() as conn:
                    row_count = conn.execute(
                        sqlalchemy.text(f"SELECT COUNT(*) FROM {quoted_table}")
                    ).scalar()
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
    def get_relationships(
        cls,
        engine: Engine,
        tables: Optional[Dict[str, TableSchema]] = None,
    ) -> List[DatabaseRelationship]:
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

        if tables:
            relationships.extend(cls._infer_relationships(tables, relationships))
        return relationships

    @staticmethod
    def _infer_relationships(
        tables: Dict[str, TableSchema],
        existing: List[DatabaseRelationship],
    ) -> List[DatabaseRelationship]:
        """Infer conventional joins when imported data has no FK constraints."""
        inferred: List[DatabaseRelationship] = []
        existing_keys = {
            (r.from_table, tuple(r.from_columns), r.to_table, tuple(r.to_columns))
            for r in existing
        }

        preferred = {
            "customer_id": ("customers", "customer_id"),
            "order_id": ("orders", "order_id"),
            "product_id": ("products", "product_id"),
            "seller_id": ("sellers", "seller_id"),
            "product_category_name": (
                "product_category_name_translation",
                "product_category_name",
            ),
        }

        for from_name, from_schema in tables.items():
            for column in from_schema.columns:
                column_name = column.name.lower()
                candidates = []
                if column_name in preferred:
                    candidates.append(preferred[column_name])
                elif column_name.endswith("_id"):
                    prefix = column_name[:-3]
                    for candidate_name, candidate_schema in tables.items():
                        if candidate_name == from_name:
                            continue
                        candidate_columns = {c.name.lower() for c in candidate_schema.columns}
                        normalized_table = candidate_name.lower().rstrip("s")
                        if column_name in candidate_columns and (
                            prefix in normalized_table or normalized_table in prefix
                        ):
                            candidates.append((candidate_name, column_name))

                for to_name, to_column in candidates:
                    if to_name == from_name or to_name not in tables:
                        continue
                    if tables[to_name].get_column(to_column) is None:
                        continue
                    key = (from_name, (column.name,), to_name, (to_column,))
                    reverse_key = (to_name, (to_column,), from_name, (column.name,))
                    if key in existing_keys or reverse_key in existing_keys:
                        continue
                    inferred.append(
                        DatabaseRelationship(
                            from_table=from_name,
                            from_columns=[column.name],
                            to_table=to_name,
                            to_columns=[to_column],
                            constraint_name="inferred_convention",
                        )
                    )
                    existing_keys.add(key)
                    break

        return inferred

    @classmethod
    def get_database_schema(
        cls,
        engine: Engine,
        include_row_counts: bool = False,
    ) -> DatabaseSchema:
        """Introspect all tables and relationships for the connected database."""
        dialect = engine.dialect.name
        table_names = cls.get_tables(engine)
        tables: Dict[str, TableSchema] = {}

        for tname in table_names:
            tables[tname] = cls.get_table_schema(
                engine, tname, include_row_count=include_row_counts
            )

        if not include_row_counts:
            estimates = cls._get_row_count_estimates(engine)
            for table_name, estimate in estimates.items():
                if table_name in tables:
                    tables[table_name].row_count_estimate = estimate

        relationships = cls.get_relationships(engine, tables=tables)

        return DatabaseSchema(
            dialect=dialect,
            tables=tables,
            relationships=relationships,
        )

    @staticmethod
    def _get_row_count_estimates(engine: Engine) -> Dict[str, int]:
        """Read optimizer statistics without scanning application tables."""
        estimates: Dict[str, int] = {}
        dialect = engine.dialect.name.lower()
        try:
            with engine.connect() as conn:
                if dialect == "sqlite":
                    rows = conn.execute(
                        sqlalchemy.text("SELECT tbl, stat FROM sqlite_stat1")
                    )
                    for table_name, stat in rows:
                        try:
                            estimate = int(str(stat).split()[0])
                            estimates[table_name] = max(
                                estimate, estimates.get(table_name, 0)
                            )
                        except (TypeError, ValueError, IndexError):
                            continue
                elif dialect == "postgresql":
                    rows = conn.execute(sqlalchemy.text(
                        "SELECT relname, GREATEST(reltuples, 0)::bigint "
                        "FROM pg_class WHERE relkind = 'r'"
                    ))
                    estimates.update({name: int(count) for name, count in rows})
                elif dialect == "mysql":
                    rows = conn.execute(sqlalchemy.text(
                        "SELECT table_name, table_rows FROM information_schema.tables "
                        "WHERE table_schema = DATABASE()"
                    ))
                    estimates.update({name: int(count or 0) for name, count in rows})
        except Exception:
            return {}
        return estimates


# Convenience module-level functions
def get_tables(engine: Engine) -> List[str]:
    return SchemaIntrospector.get_tables(engine)


def get_table_schema(engine: Engine, table_name: str) -> TableSchema:
    return SchemaIntrospector.get_table_schema(engine, table_name)


def get_database_schema(engine: Engine) -> DatabaseSchema:
    return SchemaIntrospector.get_database_schema(engine)


def get_relationships(engine: Engine) -> List[DatabaseRelationship]:
    return SchemaIntrospector.get_relationships(engine)
