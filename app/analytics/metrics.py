"""
Dynamic Metric Discovery Engine for DataPilot AI.
Analyzes arbitrary database schemas to automatically identify key business entities,
financial aggregates, and time dimensions.
"""
import re
import threading
import time
from typing import List, Dict, Any, Optional
import sqlalchemy
from sqlalchemy.engine import Engine

from app.database.schema import DatabaseSchema, TableSchema


class MetricDiscoveryEngine:
    """Discovers business metrics and KPIs from a database schema."""

    _cache = {}
    _cache_lock = threading.Lock()
    _cache_ttl_seconds = 300

    @classmethod
    def discover_kpis(cls, engine: Engine, db_schema: DatabaseSchema) -> List[Dict[str, Any]]:
        """
        Compute top 4 high-level KPI cards dynamically from the database.
        Identifies transaction counts, revenue/salary aggregates, and customer/entity volume.
        """
        kpis: List[Dict[str, Any]] = []
        dialect = db_schema.dialect.lower()
        cache_key = (
            engine.url.render_as_string(hide_password=True),
            db_schema.fingerprint(),
        )
        with cls._cache_lock:
            cached = cls._cache.get(cache_key)
            if cached and time.time() - cached[0] < cls._cache_ttl_seconds:
                return [dict(item) for item in cached[1]]

        # Helper to safely quote table/column names for the dialect
        def q(name: str) -> str:
            if dialect == "sqlite":
                return f"[{name}]"
            elif dialect == "mysql":
                return f"`{name}`"
            return f'"{name}"'

        # 1. Total records / volume on primary transaction or fact table
        fact_keywords = ["order", "transaction", "deal", "sale", "invoice", "staff", "employee", "customer", "user"]
        primary_table: Optional[TableSchema] = None

        for kw in fact_keywords:
            for tname, tschema in db_schema.tables.items():
                if kw in tname.lower():
                    primary_table = tschema
                    break
            if primary_table:
                break

        # Fallback to first table with largest row count
        if not primary_table and db_schema.tables:
            primary_table = max(db_schema.tables.values(), key=lambda t: t.row_count_estimate or 0)

        if primary_table:
            try:
                cnt = primary_table.row_count_estimate
                delta = "Estimated from database statistics"
                if cnt is None:
                    with engine.connect() as conn:
                        cnt = conn.execute(sqlalchemy.text(f"SELECT COUNT(*) FROM {q(primary_table.name)}")).scalar()
                    delta = "Live Database Record Count"
                kpis.append({
                    "title": f"Total {primary_table.name.replace('_', ' ').title()}",
                    "value": f"{cnt:,}" if cnt is not None else "N/A",
                    "delta": delta,
                    "icon": "📦",
                })
            except Exception:
                pass

        # 2. Financial / Numerical Value Aggregate (price, revenue, amount, salary, value, total)
        agg_keywords = ["price", "revenue", "amount", "salary", "deal_value", "payment_value", "total", "budget", "cost"]
        for tname, tschema in db_schema.tables.items():
            if len(kpis) >= 4:
                break
            for col in tschema.columns:
                col_lower = col.name.lower()
                if any(kw in col_lower for kw in agg_keywords) and not col.primary_key:
                    try:
                        with engine.connect() as conn:
                            val = conn.execute(sqlalchemy.text(f"SELECT ROUND(SUM({q(col.name)}), 2) FROM {q(tname)}")).scalar()
                        if val is not None:
                            val_fmt = f"${val:,.2f}" if val > 1000 else f"{val:,.2f}"
                            kpis.append({
                                "title": f"Total {col.name.replace('_', ' ').title()}",
                                "value": val_fmt,
                                "delta": f"Aggregated from {tname}",
                                "icon": "💳",
                            })
                            break
                    except Exception:
                        continue

        # 3. Average Score / Metric or Unique Entities Count
        unique_keywords = ["customer_unique_id", "email", "rep_id", "seller_id", "department_id", "product_id"]
        for tname, tschema in db_schema.tables.items():
            if len(kpis) >= 4:
                break
            for col in tschema.columns:
                col_lower = col.name.lower()
                if any(kw in col_lower for kw in unique_keywords):
                    try:
                        with engine.connect() as conn:
                            ucnt = conn.execute(sqlalchemy.text(f"SELECT COUNT(DISTINCT {q(col.name)}) FROM {q(tname)}")).scalar()
                        if ucnt is not None:
                            kpis.append({
                                "title": f"Unique {col.name.replace('_', ' ').replace('id', '').strip().title() or 'Entities'}",
                                "value": f"{ucnt:,}",
                                "delta": f"Distinct from {tname}",
                                "icon": "👥",
                            })
                            break
                    except Exception:
                        continue

        # Fill with fallback generic table counts if fewer than 4 KPIs
        for tname, tschema in db_schema.tables.items():
            if len(kpis) >= 4:
                break
            if not any(k["title"].lower().endswith(tname.lower()) for k in kpis):
                try:
                    with engine.connect() as conn:
                        tcnt = conn.execute(sqlalchemy.text(f"SELECT COUNT(*) FROM {q(tname)}")).scalar()
                    kpis.append({
                        "title": f"{tname.replace('_', ' ').title()}",
                        "value": f"{tcnt:,}" if tcnt is not None else "—",
                        "delta": "Indexed Table Entities",
                        "icon": "📁",
                    })
                except Exception:
                    continue

        with cls._cache_lock:
            cls._cache[cache_key] = (time.time(), [dict(item) for item in kpis])
            if len(cls._cache) > 64:
                oldest = min(cls._cache, key=lambda item: cls._cache[item][0])
                cls._cache.pop(oldest, None)
        return kpis


def discover_kpis(engine: Engine, db_schema: DatabaseSchema) -> List[Dict[str, Any]]:
    return MetricDiscoveryEngine.discover_kpis(engine, db_schema)
