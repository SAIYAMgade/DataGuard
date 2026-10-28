# DataGuard | Technical Interview Defense Guide

This guide prepares senior data engineering and analytics candidates to defend the design, implementation, and architectural trade-offs of DataGuard.

---

### 1. Why did you choose PostgreSQL?
**Answer:** PostgreSQL was chosen because it natively supports ACID transactions, exact arbitrary-precision numeric types (`NUMERIC(18,4)`), structured and semi-structured data (`JSONB` for raw preservation), and advanced analytical SQL features including window functions (`ROW_NUMBER() OVER (...)`) and Common Table Expressions (CTEs). Unlike in-memory dataframes or document stores, PostgreSQL enforces relational integrity constraints, foreign key validation, and transactional isolation during batch ingestion.

---

### 2. Why use SQL and Python together?
**Answer:** DataGuard leverages Python for pipeline orchestration, file decoding, vectorized anomaly screening (via pandas), structured logging, and automated test automation (Pytest). It uses SQL for persistent state management, complex relational joins (foreign key checks against customer/account dimensions), and multi-currency aggregate reporting views. Python orchestrates the pipeline, while SQL ensures database-level constraints and high-performance querying directly inside the database engine.

---

### 3. How do you prevent duplicate ingestion?
**Answer:** Every incoming transaction record generates a deterministic SHA-256 fingerprint (`record_hash`) derived from its normalized attributes. When a batch is ingested, DataGuard performs an idempotent batch-scoped cleanup (`DELETE FROM stg_transactions WHERE batch_id = :batch_id`) before staging new records. This prevents duplicate record proliferation if an ingestion process retries.

---

### 4. How do you distinguish duplicates from legitimate repeated transactions?
**Answer:** We separate duplication into three distinct rules:
1. **DQ007 (Exact Duplicate Source Record):** Identical SHA-256 payload hash within the batch. This represents technical re-ingestion.
2. **DQ008 (Duplicate Transaction Identifier):** The same `transaction_id` assigned to conflicting records.
3. **DQ009 (Potential Business Duplicate):** Same `account_id`, `amount`, `transaction_date`, and `transaction_type`. These are flagged as `MEDIUM` severity review candidates rather than deleted, because legitimate repeat payments (e.g. two $5 coffees on the same day) can share these attributes.

---

### 5. How do you reconcile two transaction sources?
**Answer:** The Reconciliation Engine (`reconcile_records`) executes a FULL OUTER JOIN between the staging transaction feed and the target settlement ledger using `transaction_id == ledger_id` (with fallback to `external_ref`). It evaluates signed difference ($\text{source} - \text{target}$), absolute difference, and classifies each comparison into `EXACT_MATCH`, `WITHIN_TOLERANCE` (e.g. $\le \$0.01$), `AMOUNT_MISMATCH`, `SOURCE_ONLY`, or `TARGET_ONLY`.

---

### 6. How do you handle different currencies?
**Answer:** Financial amounts are strictly isolated by currency. The reconciliation engine groups aggregates by currency and refuses to compute a single cross-currency grand total without an explicit foreign exchange rate feed. In Power BI, DAX measures return `BLANK()` if multiple currencies are selected simultaneously without a currency slicer.

---

### 7. How do you calculate data completeness?
**Answer:** Completeness is calculated both at the field level and record level. A record is deemed complete only if all six mandatory fields are populated: `transaction_id`, `account_id`, `transaction_date`, `amount`, `currency`, and `transaction_status`. The batch completeness score is:
$$\text{Completeness Score} = \left( 1 - \frac{\text{Records with Completeness Failures}}{\text{Total Records Ingested}} \right) \times 100$$

---

### 8. What happens when a batch fails halfway through?
**Answer:** Database writes run inside explicit database transactions (`with get_db_connection() as conn:`). If an unhandled exception or structural failure occurs, the transaction rolls back, preventing partial or ambiguous writes. The batch lifecycle state is caught in an exception block and marked as `FAILED` in `ingestion_batches` with the exact error message preserved for troubleshooting.

---

### 9. How do you make the pipeline idempotent?
**Answer:** Ingestion creates a unique batch identifier or accepts an explicit batch identifier. Rerunning a batch cleans up staging records for that specific batch before re-inserting them. Dimension loads (`dim_customers`, `dim_accounts`, `quality_rules`) use `ON CONFLICT (id) DO UPDATE` (upsert) statements to avoid duplicate key exceptions.

---

### 10. How do you test financial calculations?
**Answer:** We enforce exact decimal arithmetic (`Decimal` in Python, `NUMERIC` in SQL) and write automated Pytest unit tests verifying signed difference conventions, absolute difference bounds, and tolerance boundaries ($\pm 0.01$). Tests evaluate exact floating/decimal boundary cases, negative values, and empty datasets.

---

### 11. How do you handle invalid records?
**Answer:** Invalid records are **never silently discarded or modified**. Raw source records are preserved in `raw_transactions` as JSONB. Staging records preserve the original invalid string in raw columns (e.g. `raw_amount`), and an auditable entry is logged in `exception_register` with the violated `rule_id`, `record_reference`, and `severity`.

---

### 12. How do you investigate a false positive?
**Answer:** Analysts query the `exception_register` and `quality_rules` catalog using the `exception_id` or `record_reference`. If a rule flagged a legitimate business event (e.g., an authorized high-value payment over $1,000,000 flagged by DQ012), the analyst updates the exception's status to `FALSE_POSITIVE` in `exception_register` and enters resolution notes without mutating the underlying transaction data.

---

### 13. How do you measure data quality over time?
**Answer:** Every execution records a snapshot in `quality_run_history` capturing the evaluated timestamp, total records, passed records, failed records, dimension scores, and overall composite score. The SQL view `vw_historical_trends` uses the SQL window function `LAG(overall_quality_score) OVER (ORDER BY evaluated_at ASC)` to calculate score deltas between consecutive runs.

---

### 14. How do you ensure SQL and Power BI metrics agree?
**Answer:** Both systems use identical mathematical definitions. For example, the composite score formula ($0.25 \times \text{Comp} + 0.35 \times \text{Valid} + 0.20 \times \text{Uniq} + 0.20 \times \text{Integ}$) is implemented consistently in `metrics.py`, `reporting_views.sql`, and `dax_measures.md`. Automated tests verify that SQL reporting views match independently computed expected metrics against known fixtures.

---

### 15. What happens if the input schema changes?
**Answer:** `validate_file_structure` in `readers.py` checks required columns on ingestion. If mandatory columns are missing, the pipeline halts immediately, marks the batch as `FAILED`, and logs the missing fields. If unexpected new columns appear, the reader logs a warning and stores the entire payload in the raw JSONB table, ensuring new upstream fields are never lost.

---

### 16. What would you improve before deploying this in a real financial organization?
**Answer:**
1. **Streaming & Asynchronous Queueing:** Replace batch CSV ingestion with Kafka or AWS SQS / Kinesis for real-time transaction streaming.
2. **Distributed Processing:** Migrate from pandas to PySpark or Polars for datasets exceeding single-node memory (e.g. 50M+ transactions daily).
3. **Automated SLA Alerting:** Integrate PagerDuty or Slack webhooks triggered when critical exceptions exceed approved thresholds.
4. **Data Contract Enforcement:** Use Great Expectations, dbt tests, or Protobuf / Avro schemas at ingestion boundaries.
