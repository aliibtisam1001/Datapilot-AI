# DataPilot AI — Universal Evaluation & Benchmark Report

**Evaluation Date:** 2026-08-26  
**Engines Evaluated:** SQLite, PostgreSQL (normalized), MySQL (normalized)  
**LLM Engine:** Groq Accelerated (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.6-27b`)  
**Test Suite Coverage:** 100 Automated Unit, Security & Integration Tests (100% Pass Rate)

---

## 🏆 Universal System Performance Benchmark

| Metric | Measured Score | Enterprise Target | Status |
|---|---|---|---|
| **Overall Unit & Integration Tests** | **100.0%** (100/100) | 100% | ✅ PASSED |
| **SQL Security & Attack Pass Rate** | **100.0%** (34/34 vectors) | 100% | ✅ PASSED |
| **Multi-Database Support** | **SQLite, PostgreSQL, MySQL** | Multi-DB | ✅ PASSED |
| **Cold End-to-End Query Latency** | **2.13s** | ≤ 3.50s | ✅ PASSED |
| **Cached Query Roundtrip Latency** | **0.01ms - 49.1ms** | ≤ 150ms | ✅ PASSED |
| **Schema Introspection Latency** | **4.6ms - 190.6ms** | ≤ 500ms | ✅ PASSED |
| **Dynamic Schema Pruning Latency** | **0.01ms - 0.28ms** | ≤ 10ms | ✅ PASSED |
| **Dynamic Metric Discovery** | **100.0%** across 4 domains | ≥ 95% | ✅ PASSED |

---

## 📊 Multi-Domain Benchmark Summary

Evaluated across 4 distinct business domains and schema topologies:

| Domain | Database Engine | Tables | Columns | Introspection | Pruning | Discovered KPIs | Security Status |
|---|---|---|---|---|---|---|---|
| **E-Commerce (Olist)** | SQLite (100k+ rows) | 9 | 52 | 190.61 ms | 0.28 ms | 4 KPIs (Revenue, Orders, Review, Delivery) | 🛡️ Verified Read-Only |
| **SaaS CRM & Subscriptions** | SQLite / Postgres | 3 | 14 | 4.60 ms | 0.01 ms | 3 KPIs (ARR, Accounts, Plans) | 🛡️ Verified Read-Only |
| **Healthcare & Patients** | SQLite / MySQL | 3 | 12 | 4.60 ms | 0.01 ms | 4 KPIs (Patients, Cost, Depts, Doctors) | 🛡️ Verified Read-Only |
| **Supply Chain & Logistics** | SQLite / Postgres | 3 | 13 | 4.87 ms | 0.01 ms | 4 KPIs (Warehouses, Inventory, Stock, Transit) | 🛡️ Verified Read-Only |

---

## 🛡️ Enterprise SQL Security & Attack Test Suite

All 34 penetration test vectors were validated against `app/guardrails.py`:

- **Destructive DDL/DML**: `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, `GRANT`, `REVOKE`, `VACUUM`, `REINDEX` ── **100% REJECTED**
- **Statement-Chaining / Semicolon Bypass**: `SELECT 1; DROP TABLE users;` ── **100% REJECTED**
- **Comment-Hiding Injections**: `SELECT * FROM products; --\nDROP TABLE products;` ── **100% REJECTED**
- **CTE-Embedded Writes**: `WITH d AS (DELETE FROM users) SELECT * FROM d;` ── **100% REJECTED**
- **PostgreSQL Exploits**: `PG_SLEEP`, `PG_READ_FILE`, `DBLINK` ── **100% REJECTED**
- **MySQL Exploits**: `INTO OUTFILE`, `LOAD DATA INFILE`, `BENCHMARK`, `SLEEP` ── **100% REJECTED**
- **SQLite Exploits**: `ATTACH DATABASE`, `PRAGMA` ── **100% REJECTED**
- **Credential & Path Sanitization**: Passwords masked as `***` and filesystem paths redacted as `[internal_path]`.
