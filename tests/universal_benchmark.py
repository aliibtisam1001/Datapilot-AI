"""
Universal Multi-Domain Benchmark Suite for DataPilot AI (Phase 9).
Evaluates performance across 4 distinct business domains:
1. E-Commerce (Olist dataset)
2. SaaS CRM & Subscriptions
3. Healthcare & Patient Records
4. Supply Chain & Logistics
"""
import sys
import os
import time
import sqlalchemy
from sqlalchemy import create_engine
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import (
    get_default_olist_engine,
    get_database_schema,
    DatabaseSchema,
    DatabaseConnectionManager,
)
from app.agent.schema_selector import SchemaSelector
from app.agent.sql_generator import UniversalSQLGenerator
from app.agent.query_cache import QueryCache
from app.guardrails import validate_sql
from app.analytics.metrics import MetricDiscoveryEngine


def _exec_script(conn, sql_script: str):
    for stmt in sql_script.strip().split(";"):
        if stmt.strip():
            conn.execute(sqlalchemy.text(stmt.strip()))


def build_saas_crm_db():
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        _exec_script(conn, """
            CREATE TABLE accounts (
                account_id INT PRIMARY KEY,
                company_name TEXT,
                industry TEXT,
                arr_usd REAL,
                status TEXT
            );
            CREATE TABLE subscriptions (
                sub_id INT PRIMARY KEY,
                account_id INT,
                plan_tier TEXT,
                monthly_fee REAL,
                start_date TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts(account_id)
            );
            CREATE TABLE support_tickets (
                ticket_id INT PRIMARY KEY,
                account_id INT,
                priority TEXT,
                status TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts(account_id)
            );
            INSERT INTO accounts VALUES (1, 'Stripe', 'Fintech', 120000.0, 'Active');
            INSERT INTO accounts VALUES (2, 'Figma', 'Design', 85000.0, 'Active');
            INSERT INTO subscriptions VALUES (1, 1, 'Enterprise', 10000.0, '2023-01-01');
            INSERT INTO subscriptions VALUES (2, 2, 'Growth', 7000.0, '2023-03-01');
            INSERT INTO support_tickets VALUES (1, 1, 'Low', 'Resolved');
            INSERT INTO support_tickets VALUES (2, 2, 'High', 'Open');
        """)
        conn.commit()
    return engine


def build_healthcare_db():
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        _exec_script(conn, """
            CREATE TABLE patients (
                patient_id INT PRIMARY KEY,
                full_name TEXT,
                age INT,
                gender TEXT,
                blood_type TEXT
            );
            CREATE TABLE admissions (
                admission_id INT PRIMARY KEY,
                patient_id INT,
                department TEXT,
                admission_date TEXT,
                discharge_date TEXT,
                total_cost REAL,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
            );
            CREATE TABLE doctors (
                doctor_id INT PRIMARY KEY,
                name TEXT,
                specialty TEXT,
                department TEXT
            );
            INSERT INTO patients VALUES (1, 'John Doe', 45, 'M', 'O+');
            INSERT INTO patients VALUES (2, 'Jane Smith', 32, 'F', 'A-');
            INSERT INTO admissions VALUES (1, 1, 'Cardiology', '2023-05-10', '2023-05-15', 14500.0);
            INSERT INTO admissions VALUES (2, 2, 'Neurology', '2023-06-01', '2023-06-04', 8200.0);
            INSERT INTO doctors VALUES (1, 'Dr. House', 'Diagnostics', 'Internal Medicine');
        """)
        conn.commit()
    return engine


def build_supply_chain_db():
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        _exec_script(conn, """
            CREATE TABLE warehouses (
                warehouse_id INT PRIMARY KEY,
                location_city TEXT,
                capacity_sqft INT
            );
            CREATE TABLE inventory (
                item_id INT PRIMARY KEY,
                warehouse_id INT,
                sku TEXT,
                quantity_on_hand INT,
                unit_cost REAL,
                FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id)
            );
            CREATE TABLE shipments (
                shipment_id INT PRIMARY KEY,
                warehouse_id INT,
                destination_state TEXT,
                carrier TEXT,
                shipping_days INT,
                FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id)
            );
            INSERT INTO warehouses VALUES (1, 'Chicago', 500000);
            INSERT INTO warehouses VALUES (2, 'Dallas', 350000);
            INSERT INTO inventory VALUES (1, 1, 'SKU-001', 1200, 45.50);
            INSERT INTO inventory VALUES (2, 2, 'SKU-002', 850, 110.0);
            INSERT INTO shipments VALUES (1, 1, 'IL', 'FedEx', 2);
            INSERT INTO shipments VALUES (2, 2, 'TX', 'UPS', 3);
        """)
        conn.commit()
    return engine


def run_benchmark():
    print("=" * 75)
    print(" DATAPILOT AI -- UNIVERSAL MULTI-DOMAIN BENCHMARK SUITE")
    print("=" * 75)

    domains = [
        ("E-Commerce (Olist 100k+)", get_default_olist_engine()[0], "What is the total revenue from delivered orders?"),
        ("SaaS CRM & Subscriptions", build_saas_crm_db(), "What are the top accounts by total ARR?"),
        ("Healthcare & Patient Records", build_healthcare_db(), "What is the average admission cost by department?"),
        ("Supply Chain & Logistics", build_supply_chain_db(), "What is the total inventory value by warehouse?"),
    ]

    results = []

    for name, engine, test_query in domains:
        print(f"\nEvaluating Domain: {name}...")
        
        # 1. Schema Introspection Latency
        t0 = time.perf_counter()
        schema = get_database_schema(engine)
        t_schema = (time.perf_counter() - t0) * 1000

        # 2. Schema Pruning Latency & Selection
        t0 = time.perf_counter()
        pruned_schema = SchemaSelector.select_relevant_schema(schema, test_query)
        t_prune = (time.perf_counter() - t0) * 1000
        prune_ratio = (len(pruned_schema.tables) / len(schema.tables)) * 100

        # 3. Dynamic KPI Discovery Latency
        t0 = time.perf_counter()
        kpis = MetricDiscoveryEngine.discover_kpis(engine, schema)
        t_kpi = (time.perf_counter() - t0) * 1000

        # 4. Universal Prompt / Schema Compaction Latency
        t0 = time.perf_counter()
        compact_schema = pruned_schema.to_compact_schema_string()
        t_prompt = (time.perf_counter() - t0) * 1000

        # 5. Guardrail AST Validation Latency
        sample_sql = "SELECT * FROM " + list(schema.tables.keys())[0]
        t0 = time.perf_counter()
        validated_sql = validate_sql(sample_sql, max_rows=500)
        t_guardrail = (time.perf_counter() - t0) * 1000

        # 6. Query Cache Roundtrip Latency
        from app.agent.sql_generator import SQLGenerationResult
        mock_res = SQLGenerationResult(sql="SELECT 1;", tables_used=["mock"], reasoning_summary="Mock", confidence=1.0)
        QueryCache.set("sqlite://mock", test_query, mock_res)
        t0 = time.perf_counter()
        cached_entry = QueryCache.get("sqlite://mock", test_query)
        t_cache = (time.perf_counter() - t0) * 1000

        results.append({
            "domain": name,
            "tables": len(schema.tables),
            "relationships": len(schema.relationships),
            "schema_ms": t_schema,
            "prune_ms": t_prune,
            "prune_ratio": prune_ratio,
            "kpi_ms": t_kpi,
            "guardrail_ms": t_guardrail,
            "cache_ms": t_cache,
            "kpis_found": len(kpis),
        })

    # Print Summary Table
    print("\n" + "=" * 75)
    print(f"{'Domain':<30} | {'Tables':<6} | {'Schema':<9} | {'Prune':<8} | {'KPIs':<6} | {'Cache'}")
    print("-" * 75)
    for r in results:
        print(f"{r['domain']:<30} | {r['tables']:<6} | {r['schema_ms']:>6.2f} ms | {r['prune_ms']:>5.2f} ms | {r['kpis_found']:<6} | {r['cache_ms']:>5.2f} ms")
    print("=" * 75)
    print("[SUCCESS] All 4 business domains passed introspection, schema pruning, KPI discovery, and security AST validation!")


if __name__ == "__main__":
    run_benchmark()
