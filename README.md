# DataGuard
## Financial Data Quality & Transaction Monitoring System
*Production-Quality | GitHub-Ready | Interview-Defensible*

[![CI](https://github.com/DataGuard/dataguard/actions/workflows/tests.yml/badge.svg)](https://github.com/DataGuard/dataguard/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Database: PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL_16%2B-336791.svg)](https://www.postgresql.org/)

---

## 1. Project Overview

**DataGuard** is an end-to-end financial data quality and transaction monitoring system designed to validate transaction records using Python and SQL, detect data anomalies, reconcile financial totals against settlement ledgers, maintain an auditable exception register, and communicate data quality performance through Power BI dashboards and Excel workbooks.

Unlike isolated data-cleaning scripts or static dashboards, DataGuard connects every component—from raw CSV ingestion and non-destructive JSONB preservation to SQL window-function deduplication, exact decimal reconciliation, and openpyxl reporting—into one traceable, reproducible pipeline.

---

## 2. Business Problem & Solution

### The Challenge
In modern financial institutions, transaction feeds from payment gateways, core banking, and external clearinghouses frequently suffer from data quality issues:
- Dropped identifier columns or blank account keys.
- Duplicate transaction ingestion from upstream retry loops.
- Sign discrepancies (e.g. negative deposits) and fractional-cent rounding leaks.
- Timing mismatches and date clock skews.
- Ledger imbalances between transaction feeds and settlement ledgers.

If undetected, these errors distort financial reporting, breach regulatory compliance, and require costly manual reconciliation.

### The DataGuard Solution
DataGuard establishes an automated quality firewall:
1. **Raw Preservation:** Preserves original source records verbatim as JSONB before transformation.
2. **Deterministic Rules Engine:** Evaluates 17 documented rules (`DQ001`–`DQ017`) across Completeness, Validity, Uniqueness, Timeliness, Integrity, and Consistency.
3. **Auditable Exception Register:** Logs every failure with record references, severity, offending values, and lifecycle tracking (`OPEN` → `UNDER_REVIEW` → `RESOLVED`).
4. **Financial Reconciliation Engine:** Compares transaction feeds against settlement ledgers with strict multi-currency isolation and configurable tolerance ($\pm 0.01$).
5. **Business Reporting:** Produces a 6-sheet Excel report and Power BI dimensional views.

---

## 3. System Architecture & Data Lineage

![DataGuard Data Lineage Architecture](docs/images/dataguard_data_lineage.png)

```mermaid
flowchart TD
    subgraph Ingestion ["1. Non-Destructive Ingestion Layer"]
        A["Raw Transaction Feed (.csv)"] --> B["Ingestion Loader (readers.py)"]
        B --> C[("Raw Table (JSONB)")]
        B --> D["Standardization (standardization.py)"]
        D --> E[("Staging Table (stg_transactions)")]
    end

    subgraph QualityEngine ["2. Quality Validation Engine"]
        F[("Account & Customer Dimensions")] --> G["Validation Engine (engine.py)"]
        E --> G
        H["Rules Config (quality_rules.yaml)"] --> G
        G --> I[("Quality Run History")]
        G --> J[("Exception Register")]
    end

    subgraph Reconciliation ["3. Financial Reconciliation Engine"]
        E --> K["Reconciliation Engine (engine.py)"]
        L[("Target Settlement Ledger")] --> K
        K --> M[("Reconciliation Results")]
    end

    subgraph Reporting ["4. Multi-Channel Reporting"]
        I --> N["Analytical SQL Views"]
        J --> N
        M --> N
        N --> O["6-Sheet Excel Workbook (openpyxl)"]
        N --> P["Power BI DirectQuery / CSV Feeds"]
    end
```

---

## 4. Technology Stack

| Component | Technology | Responsibility |
|---|---|---|
| **Programming Language** | Python 3.12+ / 3.14 | Pipeline orchestration, data validation, and CLI |
| **Data Processing** | pandas, NumPy | High-performance vectorized checks and transformation |
| **Relational Database** | PostgreSQL 16+ / 18 | Persistent storage, ACID transactions, exact numeric types |
| **Query Language** | SQL (PostgreSQL Dialect) | Window functions, CTEs, referential integrity joins, views |
| **Database ORM & Driver** | SQLAlchemy, psycopg2 | Connection pooling, parameterized queries, migrations |
| **Testing Framework** | Pytest | Unit tests, integration tests, and ground-truth regression tests |
| **Excel Reporting** | openpyxl | Automated 6-sheet corporate financial workbook generation |
| **Business Intelligence** | Power BI Desktop | Interactive 3-page executive and operational dashboard |
| **Containerization** | Docker, Docker Compose | Containerized local execution and automated CI |
| **Continuous Integration** | GitHub Actions | Automated build, schema initialization, and test verification |

---

## 5. Repository Structure

```text
DataGuard/
├── README.md                           # Master documentation
├── LICENSE                             # MIT License
├── pyproject.toml                      # Build metadata and dependencies
├── docker-compose.yml                  # PostgreSQL and pipeline services
├── Dockerfile                          # Container specification
├── .env.example                        # Environment variables template
│
├── config/
│   ├── settings.yaml                   # Core app, database, and reconciliation settings
│   └── quality_rules.yaml              # Rule catalogue (DQ001 to DQ017 metadata)
│
├── data/
│   ├── sample/
│   │   ├── dim_customers.csv           # Customer dimension (50 records)
│   │   ├── dim_accounts.csv            # Account dimension (100 records)
│   │   ├── transactions_baseline.csv   # Clean baseline dataset (500 records)
│   │   ├── transactions_corrupted.csv  # Anomaly-injected dataset (303 records)
│   │   ├── target_ledger.csv           # Target reconciliation ledger (248 records)
│   │   └── anomaly_manifest.json       # Ground-truth audit log of injected anomalies
│   └── README.md
│
├── sql/
│   ├── schema/
│   │   ├── 001_create_tables.sql       # DDL: 11 core tables and constraints
│   │   └── 002_create_indexes.sql      # B-tree indexes for fast joins and lookups
│   ├── validation/
│   │   ├── missing_values.sql          # CTE queries for missing mandatory fields
│   │   ├── duplicate_transactions.sql  # Window function ranking for duplicate detection
│   │   ├── invalid_amounts.sql         # Precision, sign, and outlier checks
│   │   ├── date_validation.sql         # Future dates and stale transaction checks
│   │   └── referential_integrity.sql   # Orphaned foreign keys and enum validation
│   ├── reconciliation/
│   │   ├── transaction_totals.sql      # Multi-currency aggregate totals
│   │   ├── source_comparison.sql       # Full outer join comparison with signed diff
│   │   └── unmatched_records.sql       # Source-only and target-only breaks
│   ├── reporting/
│   │   ├── quality_summary.sql         # Batch-level dimensional pass rates
│   │   ├── exception_summary.sql       # Severity distribution of open anomalies
│   │   └── historical_trends.sql       # Window LAG queries tracking score deltas
│   └── views/
│       └── reporting_views.sql         # 6 production reporting views
│
├── src/
│   └── dataguard/
│       ├── __init__.py
│       ├── cli.py                      # Click command-line interface
│       ├── config/                     # Settings and YAML loaders
│       ├── database/                   # Connection pool and repositories
│       ├── ingestion/                  # CSV readers, structural validation, loader
│       ├── transformations/            # Type standardization and normalization
│       ├── quality/                    # Rules evaluator (DQ001-DQ017), metrics, engine
│       ├── reconciliation/             # Comparisons, tolerance logic, engine
│       ├── reporting/                  # openpyxl workbook generator and summaries
│       └── orchestration/              # End-to-end pipeline coordinator
│
├── powerbi/
│   ├── README.md                       # Setup and direct connection guide
│   ├── data_model.md                   # Star schema, cardinality, relationships
│   ├── dax_measures.md                 # 20+ documented DAX measures
│   └── dashboard_specification.md      # Visual layouts for Pages 1, 2, and 3
│
├── excel/
│   ├── README.md                       # Excel report overview
│   └── workbook_specification.md       # Styling palette, sheets, and formatting rules
│
├── reports/
│   ├── DataGuard_Quality_Report.xlsx   # Generated 6-sheet Excel audit workbook
│   └── sample_outputs/                 # CSV extracts for Power BI import
│
├── tests/
│   ├── conftest.py                     # Shared test fixtures
│   ├── unit/
│   │   ├── test_rules.py               # Unit tests for DQ001 to DQ017
│   │   ├── test_metrics.py             # Mathematical scoring tests
│   │   └── test_reconciliation.py      # Matching, tolerance, and currency tests
│   ├── integration/
│   │   └── test_database_integration.py# Schema, persistence, and idempotency tests
│   └── regression/
│       └── test_anomaly_regression.py  # 100% recall verification against manifest
│
├── scripts/
│   ├── generate_sample_data.py         # Deterministic synthetic data generator
│   ├── initialize_database.py          # DDL migrations and dimension loader
│   ├── run_pipeline.py                 # Main CLI pipeline execution script
│   └── generate_reports.py             # Standalone report generator
│
└── docs/
    ├── architecture.md                 # In-depth architectural design
    ├── data_dictionary.md              # Complete field-by-field dictionary
    ├── quality_rules.md                # Business purpose and logic of all rules
    ├── metric_definitions.md           # Mathematical formulas and weighting rationale
    ├── troubleshooting.md              # Operational runbook
    ├── security.md                     # Secrets management and least privilege
    └── interview_guide.md              # 16 technical interview defense Q&As
```

---

## 6. Data Quality Rules Catalogue

DataGuard implements 17 business and technical quality rules:

| Rule ID | Name | Dimension | Severity | Target Field | Technical Condition |
|---|---|---|---|---|---|
| `DQ001` | Missing Transaction ID | COMPLETENESS | CRITICAL | `transaction_id` | `IS NULL OR TRIM() = ''` |
| `DQ002` | Missing Account ID | COMPLETENESS | CRITICAL | `account_id` | `IS NULL OR TRIM() = ''` |
| `DQ003` | Missing Transaction Date | COMPLETENESS | HIGH | `transaction_date` | `IS NULL` |
| `DQ004` | Missing Monetary Amount | COMPLETENESS | CRITICAL | `amount` | `IS NULL` |
| `DQ005` | Missing Currency Code | COMPLETENESS | HIGH | `currency` | `IS NULL OR TRIM() = ''` |
| `DQ006` | Missing Transaction Status | COMPLETENESS | HIGH | `transaction_status` | `IS NULL OR TRIM() = ''` |
| `DQ007` | Exact Duplicate Record | UNIQUENESS | HIGH | `record_hash` | Identical SHA-256 payload hash |
| `DQ008` | Duplicate Transaction ID | UNIQUENESS | CRITICAL | `transaction_id` | Conflicting rows under same ID |
| `DQ009` | Potential Business Duplicate | UNIQUENESS | MEDIUM | `account,amount,date,type` | Same account, amount, date, type |
| `DQ010` | Invalid Decimal Precision | VALIDITY | MEDIUM | `amount` | >2 decimal places for USD/EUR/GBP |
| `DQ011` | Sign Inconsistency | VALIDITY | HIGH | `amount,type` | `DEPOSIT`/`PAYMENT` with `amount <= 0` |
| `DQ012` | Extreme Outlier Amount | VALIDITY | MEDIUM | `amount` | `ABS(amount) > 1,000,000.00` |
| `DQ013` | Future-Dated Transaction | TIMELINESS | HIGH | `transaction_date` | `transaction_date > CURRENT_DATE` |
| `DQ014` | Excessive Ingestion Delay | TIMELINESS | LOW | `transaction_date` | `transaction_date < CURRENT_DATE - 90d` |
| `DQ015` | Unknown Account Reference | INTEGRITY | CRITICAL | `account_id` | Foreign key not in `dim_accounts` |
| `DQ016` | Invalid Type or Status | VALIDITY | HIGH | `type,status` | Unrecognized enum values |
| `DQ017` | Reversal Missing Reference | CONSISTENCY | HIGH | `reference_id` | `type='REVERSAL'` without reference ID |

---

## 7. Mathematical Metric Definitions

1. **Completeness Rate (%):**
   $$\text{Completeness} = \left( 1 - \frac{\text{Records with Completeness Violations}}{\text{Total Ingested Records}} \right) \times 100$$
2. **Validity Rate (%):**
   $$\text{Validity} = \left( 1 - \frac{\text{Records with Validity Violations}}{\text{Total Ingested Records}} \right) \times 100$$
3. **Uniqueness Rate (%):**
   $$\text{Uniqueness} = \left( 1 - \frac{\text{Duplicate Records Identified}}{\text{Total Ingested Records}} \right) \times 100$$
4. **Referential Integrity Rate (%):**
   $$\text{Integrity} = \left( 1 - \frac{\text{Records Referencing Unknown Accounts}}{\text{Total Ingested Records}} \right) \times 100$$
5. **Overall Composite Quality Score (%):**
   $$\text{Overall Score} = (0.25 \times \text{Completeness}) + (0.35 \times \text{Validity}) + (0.20 \times \text{Uniqueness}) + (0.20 \times \text{Integrity})$$
   *Weighting Rationale: Validity (35%) carries the highest weight because sign errors and sub-cent corruption directly affect financial balance sheets. Completeness (25%) prevents unposted transactions. Uniqueness (20%) and Integrity (20%) prevent volume inflation and orphaned accounts.*

---

## 8. Quickstart & Execution Guide

### 8.1 Prerequisites
- Python 3.11+
- PostgreSQL 16+ running locally on port 5432 (or Docker)

### 8.2 Environment Configuration
Clone the repository and create `.env`:
```bash
cp .env.example .env
```

Install dependencies:
```bash
pip install -e .
```

### 8.3 Initialize the Database
Run migrations, create indexes, views, and seed customer/account dimensions:
```bash
python scripts/initialize_database.py
```

### 8.4 Generate Sample Datasets (Deterministic)
Generates clean baseline, anomaly-injected feeds, target ledger, and ground-truth manifest:
```bash
python scripts/generate_sample_data.py
```

### 8.5 Execute the End-to-End Pipeline
Run ingestion, validation, reconciliation, and report generation:
```bash
python scripts/run_pipeline.py --input data/sample/transactions_corrupted.csv --ledger data/sample/target_ledger.csv
```

### 8.6 Run the Automated Test Suite
Execute all 28 unit, integration, and regression tests:
```bash
python -m pytest -v
```

---

## 9. Actual Pipeline Execution Results

![DataGuard Quality Scorecard](docs/images/dataguard_quality_scorecard.png)

Below are the actual, verified results produced by DataGuard on the sample datasets:

### Clean Baseline Dataset (`transactions_baseline.csv` - 500 Records)
```text
Records Ingested:      500
Passed Clean Records:  500
Failed Records:        0
Total Exceptions:      0
------------------------------------------------------------
Completeness Score:    100.00%
Validity Score:        100.00%
Uniqueness Score:      100.00%
Integrity Score:       100.00%
OVERALL QUALITY SCORE: 100.00%
------------------------------------------------------------
Reconciliation Matches:520
```

### Anomaly-Injected Dataset (`transactions_corrupted.csv` - 303 Records)
```text
Records Ingested:      303
Passed Clean Records:  286
Failed Records:        17
Total Exceptions:      19
------------------------------------------------------------
Completeness Score:    98.02%
Validity Score:        97.69%
Uniqueness Score:      99.01%
Integrity Score:       99.67%
OVERALL QUALITY SCORE: 98.43%
------------------------------------------------------------
Reconciliation Matches:320
Excel Report Created:  reports/DataGuard_Quality_Report.xlsx
```

---

## 10. Reporting Deliverables

### Excel Audit Workbook (`reports/DataGuard_Quality_Report.xlsx`)
Generated via `openpyxl`:
- **Sheet 1 (Executive Summary):** KPI scorecard, pass/fail status, operational volume tallies.
- **Sheet 2 (Exception Register):** Auto-filtered, frozen header, severity-colored audit trail.
- **Sheet 3 (Reconciliation):** Multi-currency balance reconciliation with signed and absolute variances.
- **Sheet 4 (Quality Trends):** Historical batch progression and score deltas.
- **Sheet 5 (Data Dictionary):** Complete field specifications and constraints.
- **Sheet 6 (Rule Catalogue):** DQ001–DQ017 technical logic and investigation playbooks.

### Power BI Dashboard Architecture (`powerbi/`)
- Complete dimensional star-schema model ([data_model.md](powerbi/data_model.md)).
- 20+ validated DAX measures ([dax_measures.md](powerbi/dax_measures.md)).
- Visual specifications for 3 operational pages ([dashboard_specification.md](powerbi/dashboard_specification.md)):
  - **Page 1:** Executive Data Quality Overview
  - **Page 2:** Exception Investigation & Remediation
  - **Page 3:** Financial Reconciliation & Monitoring
- Pre-built CSV data extracts exported to `reports/sample_outputs/` for immediate import.

---

## 11. Known Limitations & Production Enhancements

1. **Single-Node Ingestion:** Current ingestion processes CSV batches via pandas. In a high-throughput enterprise environment (50M+ daily events), ingestion should transition to Apache Kafka with PySpark or Polars.
2. **Dynamic FX Conversion:** Multi-currency reconciliation isolates currencies strictly. In production, an external foreign exchange rate feed would enable cross-currency reporting.
3. **Power BI Native File:** Native `.pbix` compilation requires the Windows Power BI Desktop GUI; we provide the complete SQL views, DAX measures, and visual layout guides.

---

## 12. License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
