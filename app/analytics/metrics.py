"""
Dynamic Metric Discovery Engine for DataPilot AI.
Analyzes arbitrary database schemas to automatically identify key business entities,
financial aggregates, time dimensions, and generate smart suggested business questions.
"""
import re
from typing import List, Dict, Any, Optional
import sqlalchemy
from sqlalchemy.engine import Engine

from app.database.schema import DatabaseSchema, TableSchema


class MetricDiscoveryEngine:
    """Discovers business metrics, KPIs, and suggested queries from a database schema."""

    @classmethod
    def discover_kpis(cls, engine: Engine, db_schema: DatabaseSchema) -> List[Dict[str, Any]]:
        """
        Compute top 4 high-level KPI cards dynamically from the database.
        Identifies transaction counts, revenue/salary aggregates, and customer/entity volume.
        """
        kpis: List[Dict[str, Any]] = []
        dialect = db_schema.dialect.lower()

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
                with engine.connect() as conn:
                    cnt = conn.execute(sqlalchemy.text(f"SELECT COUNT(*) FROM {q(primary_table.name)}")).scalar()
                kpis.append({
                    "title": f"Total {primary_table.name.replace('_', ' ').title()}",
                    "value": f"{cnt:,}" if cnt is not None else "N/A",
                    "delta": "Live Database Record Count",
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

        return kpis

    @classmethod
    def generate_suggested_questions(cls, db_schema: DatabaseSchema) -> List[str]:
        """
        Synthesizes 5 smart, high-value business questions tailored specifically
        to the tables, columns, and relationships in the active database.
        """
        suggestions: List[str] = []
        tables = db_schema.tables

        # Check for Olist demo database specifically
        if "order_items" in tables and "products" in tables:
            return [
                "What is the total revenue from delivered orders?",
                "What are the top 5 product categories by revenue with English names?",
                "How many total orders are in the database?",
                "What is the average review score across all orders?",
                "What are the top 5 customer states by total order volume?",
            ]

        # Universal heuristic query synthesis
        # 1. Total counts on main tables
        for tname in list(tables.keys())[:2]:
            suggestions.append(f"How many total {tname.replace('_', ' ')} are in the database?")

        # 2. Top categories / rankings
        for tname, tschema in tables.items():
            cat_cols = [c.name for c in tschema.columns if any(k in c.name.lower() for k in ["name", "category", "region", "country", "status", "stage", "department", "dept_name"])]
            num_cols = [c.name for c in tschema.columns if any(k in c.name.lower() for k in ["price", "amount", "revenue", "salary", "value", "total", "score"])]
            
            if cat_cols and num_cols:
                suggestions.append(f"What are the top 5 {cat_cols[0].replace('_', ' ')} by total {num_cols[0].replace('_', ' ')}?")
                break

        # 3. Monthly / Time-series Trend
        for tname, tschema in tables.items():
            date_cols = [c.name for c in tschema.columns if any(k in c.name.lower() for k in ["date", "timestamp", "created", "at", "time"])]
            if date_cols:
                suggestions.append(f"What is the monthly trend of {tname.replace('_', ' ')} over time?")
                break

        # 4. Average metric
        for tname, tschema in tables.items():
            num_cols = [c.name for c in tschema.columns if any(k in c.name.lower() for k in ["price", "amount", "revenue", "salary", "value", "score", "days", "time"])]
            if num_cols:
                suggestions.append(f"What is the average {num_cols[0].replace('_', ' ')} across all records?")
                break

        # Ensure we have at least 4 suggestions
        if len(suggestions) < 4:
            for tname in list(tables.keys())[2:]:
                suggestions.append(f"Show me a breakdown of records in {tname}.")
                if len(suggestions) >= 4:
                    break

        return suggestions[:5]


def discover_kpis(engine: Engine, db_schema: DatabaseSchema) -> List[Dict[str, Any]]:
    return MetricDiscoveryEngine.discover_kpis(engine, db_schema)


def generate_suggested_questions(db_schema: DatabaseSchema) -> List[str]:
    return MetricDiscoveryEngine.generate_suggested_questions(db_schema)
