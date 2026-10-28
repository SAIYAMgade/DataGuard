# DataGuard | Data Dictionary

This document details the schema definitions, data types, nullability, and business rules for every field in the DataGuard data model.

---

## 1. Table: `stg_transactions`

| Field Name | Data Type | Nullable | Primary Key | Foreign Key | Description | Validation Rule |
|---|---|---|---|---|---|---|
| `staging_id` | BIGSERIAL | No | Yes | No | Surrogate auto-incrementing identifier | Auto-generated |
| `batch_id` | VARCHAR(64) | No | No | Yes (`ingestion_batches`) | Identifier of ingestion batch | Valid batch reference |
| `source_system` | VARCHAR(50) | No | No | No | Originating source application | Non-empty string |
| `source_record_id` | VARCHAR(100) | Yes | No | No | Identifier from originating system | Alphanumeric |
| `transaction_id` | VARCHAR(100) | Yes | No | No | Primary business transaction identifier | DQ001 (Not null), DQ008 (Unique) |
| `account_id` | VARCHAR(50) | Yes | No | Yes (`dim_accounts`) | Associated customer account identifier | DQ002 (Not null), DQ015 (Valid account) |
| `customer_id` | VARCHAR(50) | Yes | No | Yes (`dim_customers`) | Associated customer identifier | Valid customer reference |
| `transaction_date` | DATE | Yes | No | No | Effective calendar transaction date | DQ003 (Not null), DQ013 (<= today), DQ014 (>= today-90d) |
| `transaction_type` | VARCHAR(30) | Yes | No | No | Transaction category (DEPOSIT, PAYMENT, etc.) | DQ016 (Allowed enum list), DQ011 (Sign check) |
| `amount` | NUMERIC(18, 4) | Yes | No | No | Monetary transaction value | DQ004 (Not null), DQ010 (<= 2 decimals), DQ012 (<= 1M) |
| `currency` | VARCHAR(3) | Yes | No | No | ISO 4217 three-letter currency code | DQ005 (Not null), Supported list |
| `transaction_status` | VARCHAR(30) | Yes | No | No | Operational clearing state | DQ006 (Not null), DQ016 (Allowed enum list) |
| `reference_id` | VARCHAR(100) | Yes | No | No | Originating parent transaction reference | DQ017 (Mandatory for REVERSAL) |
| `description` | TEXT | Yes | No | No | Free-form transaction description | Text string |
| `record_hash` | VARCHAR(64) | No | No | No | SHA-256 hash of raw payload | DQ007 (Exact duplicate check) |
| `ingestion_timestamp`| TIMESTAMPTZ | No | No | No | System timestamp of staging insertion | Default CURRENT_TIMESTAMP |

---

## 2. Table: `exception_register`

| Field Name | Data Type | Nullable | Primary Key | Foreign Key | Description |
|---|---|---|---|---|---|
| `exception_id` | VARCHAR(64) | No | Yes | No | Unique exception identifier (`EXC_...`) |
| `run_id` | VARCHAR(64) | No | No | Yes (`quality_run_history`) | Parent quality validation run |
| `batch_id` | VARCHAR(64) | No | No | Yes (`ingestion_batches`) | Ingestion batch where anomaly was detected |
| `rule_id` | VARCHAR(20) | No | No | Yes (`quality_rules`) | Quality rule triggered (e.g. `DQ001`) |
| `record_reference` | VARCHAR(100) | No | No | No | Transaction ID or source record identifier |
| `field_name` | VARCHAR(100) | Yes | No | No | Target column evaluated |
| `invalid_value` | TEXT | Yes | No | No | Specific offending value |
| `severity` | VARCHAR(20) | No | No | No | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `issue_description`| TEXT | No | No | No | Human-readable explanation of rule failure |
| `detected_at` | TIMESTAMPTZ | No | No | No | Detection timestamp |
| `resolution_status`| VARCHAR(20) | No | No | No | `OPEN`, `UNDER_REVIEW`, `RESOLVED`, `FALSE_POSITIVE` |
| `resolution_notes` | TEXT | Yes | No | No | Operational resolution explanation |
| `resolved_at` | TIMESTAMPTZ | Yes | No | No | Timestamp of status transition to resolved |
| `resolved_by` | VARCHAR(100) | Yes | No | No | Username of resolving analyst |

---

## 3. Table: `reconciliation_results`

| Field Name | Data Type | Nullable | Primary Key | Foreign Key | Description |
|---|---|---|---|---|---|
| `recon_id` | VARCHAR(64) | No | Yes | No | Unique reconciliation identifier (`REC_...`) |
| `run_id` | VARCHAR(64) | No | No | Yes (`quality_run_history`) | Associated quality evaluation run |
| `batch_id` | VARCHAR(64) | No | No | Yes (`ingestion_batches`) | Ingestion batch evaluated |
| `recon_type` | VARCHAR(30) | No | No | No | `RECORD_LEVEL` or `AGGREGATE` |
| `source_id` | VARCHAR(100) | Yes | No | No | Source transaction ID or group label |
| `target_id` | VARCHAR(100) | Yes | No | No | Target ledger ID or group label |
| `currency` | VARCHAR(3) | No | No | No | ISO currency code (isolated) |
| `source_amount` | NUMERIC(18, 4) | Yes | No | No | Amount from transaction feed |
| `target_amount` | NUMERIC(18, 4) | Yes | No | No | Amount from target ledger |
| `signed_difference`| NUMERIC(18, 4) | Yes | No | No | `source_amount - target_amount` |
| `absolute_difference`| NUMERIC(18, 4)| Yes | No | No | `ABS(source_amount - target_amount)` |
| `tolerance` | NUMERIC(18, 4) | No | No | No | Approved tolerance threshold (default 0.01) |
| `match_status` | VARCHAR(30) | No | No | No | `EXACT_MATCH`, `WITHIN_TOLERANCE`, `AMOUNT_MISMATCH`, `SOURCE_ONLY`, `TARGET_ONLY` |
| `reconciled_at` | TIMESTAMPTZ | No | No | No | Timestamp of reconciliation execution |
