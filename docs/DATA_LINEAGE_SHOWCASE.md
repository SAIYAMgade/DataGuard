# Building DataGuard: Financial Data Quality & Transaction Lineage

> **GitHub Repository:** [https://github.com/SAIYAMgade/DataGuard](https://github.com/SAIYAMgade/DataGuard)  
> *Production-Quality | GitHub-Ready | Interview-Defensible*

---

## 1. The Real-World Problem: Silent Financial Ledger Corruption

In banking and FinTech pipelines, data quality failures rarely trigger loud server crashes. Instead, they corrupt systems silently:
- A payment gateway retries a batch, creating **duplicate turnover**.
- A currency decimal parsing error silently maps `$145.8945` into a floating-point truncation.
- An account reference arrives out-of-order before customer onboarding, producing an **orphaned transaction** that cannot settle.
- A negative amount arrives on a deposit, distorting cash flow metrics.

Traditional data-cleaning scripts often compound the issue by silently dropping bad records or mutating raw values. **In financial systems, you cannot delete history to make a dashboard look green.**

**DataGuard** was built to solve this: an end-to-end data quality firewall and transaction monitoring platform that enforces strict **non-destructive lineage**, **deterministic validation**, and **traceable financial reconciliation**.

---

## 2. The 6-Stage End-to-End Data Lineage

Here is how data flows from ingestion to executive consumption:

![DataGuard Data Lineage Architecture](images/dataguard_data_lineage.png)

### Stage 1: Non-Destructive Raw Ingestion (`raw_transactions`)
- Source transaction files (CSV/JSON/stream) are ingested with automatic encoding detection (`utf-8`, `utf-8-sig`, `latin-1`).
- **Zero Data Loss:** Before any transformation occurs, the exact raw payload is preserved verbatim in PostgreSQL as `JSONB` alongside the source batch identifier. If an amount is malformed (e.g. `"$$1,450.89"`), the original string remains queryable forever.

### Stage 2: Standardization & Idempotency (`stg_transactions`)
- Fields are parsed into strict domain types:
  - Monetary values use exact **`NUMERIC(18, 4)`** in PostgreSQL and `Decimal` in Python (never binary floating point).
  - Dates are parsed to ISO 8601 calendar dates.
- **SHA-256 Fingerprinting:** Every record generates a deterministic payload hash. Reprocessing a batch executes an isolated partition refresh, guaranteeing **100% idempotency** without duplicate record inflation.

### Stage 3: The 17-Rule Quality Firewall
DataGuard screens every transaction against 17 deterministic rules across six quality dimensions:
1. **Completeness (DQ001–DQ006):** Mandatory transaction ID, account ID, date, amount, currency, status.
2. **Uniqueness (DQ007–DQ009):** Exact payload duplicates, colliding transaction IDs, and potential business duplicates (same account, amount, and date flagged for review without premature deletion).
3. **Validity (DQ010–DQ012):** Sub-cent precision violations, sign consistency (deposits $> 0$), and extreme transaction ceilings ($> \$1\text{M}$).
4. **Timeliness (DQ013–DQ014):** Future date bounds and backlogged latency ($> 90$ days).
5. **Referential Integrity (DQ015):** Orphaned account IDs verified via `LEFT JOIN dim_accounts`.
6. **Consistency (DQ016–DQ017):** Enumeration compliance and reversal parent references.

### Stage 4: Traceable Exception Register (`exception_register`)
- Violations do not abort the pipeline. Each anomaly is logged with a unique `exception_id`, the offending value, severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`), and investigation guidance.
- Anomalies enter an auditable status lifecycle:
  $$\text{OPEN} \longrightarrow \text{UNDER\_REVIEW} \longrightarrow \text{RESOLVED / FALSE\_POSITIVE}$$
- Underlying transaction records are never modified during resolution.

### Stage 5: Dual-Source Financial Reconciliation
- Matches transaction feeds against external settlement ledgers via FULL OUTER JOIN.
- Computes **Signed Difference** ($\text{Source} - \text{Target}$) and **Absolute Variance**.
- Classifies comparison into `EXACT_MATCH`, `WITHIN_TOLERANCE` ($\le \pm \$0.01$), `AMOUNT_MISMATCH`, `SOURCE_ONLY`, or `TARGET_ONLY`.
- **Strict Currency Isolation:** Aggregates are grouped strictly by currency. DataGuard never combines USD, EUR, and GBP into a single misleading grand total.

### Stage 6: Multi-Channel Business Consumption
- **Excel Audit Workbook (`openpyxl`):** Programmatically generated 6-sheet workbook with frozen headers, auto-filters, severity color highlights, data dictionary, and rule catalogue.
- **Power BI Star Schema:** Clean dimensional model with 20+ documented DAX measures for Executive Overview, Exception Aging, and Reconciliation Variance.

---

## 3. Verified Performance & Execution Results

![DataGuard Quality Scorecard](images/dataguard_quality_scorecard.png)

### Empirical Verification on Real PostgreSQL 18:
- **Baseline Dataset (500 records):** 100% clean records, 100% across all quality dimensions.
- **Corrupted Dataset (303 records, 17 injected anomaly categories):**
  - **100% Anomaly Detection Recall:** All 17 injected anomalies caught with zero false passes.
  - **Completeness Score:** `98.02%`
  - **Validity Score:** `97.69%`
  - **Uniqueness Score:** `99.01%`
  - **Integrity Score:** `99.67%`
  - **Overall Weighted Quality Index:** `98.43%`
  - **Reconciliation Comparisons:** `320` records verified.
- **Pytest Suite:** **28 out of 28 automated tests passing** (unit, integration, and manifest regression).

---

## 4. Key Architectural Trade-Offs

| Decision | Chosen Approach | Alternative Considered | Why |
|---|---|---|---|
| **Storage Engine** | PostgreSQL 18 | DuckDB / In-Memory | Required ACID guarantees, real relational constraints, and concurrent multi-user write isolation |
| **Monetary Types** | `NUMERIC(18,4)` & `Decimal` | `FLOAT` / `DOUBLE` | Binary floating point produces rounding errors ($0.1 + 0.2 \neq 0.3$) unacceptable in ledger settlement |
| **Idempotency** | SHA-256 Partition Reset | Blind Append | Eliminates duplicate transaction inflation on pipeline retries |
| **Duplicate Policy** | 3 Distinct DQ Rules | Auto-deleting duplicates | Legitimate repeat transactions (e.g. 2 identical payments on same day) must be reviewed, not deleted |
| **Reconciliation** | Currency-Isolated Matrix | Unified Sum | Cross-currency summation without market FX rates produces invalid financial reporting |

---

## 5. Try It Locally

```bash
git clone https://github.com/SAIYAMgade/DataGuard.git
cd DataGuard

# 1. Install dependencies
pip install -e .

# 2. Initialize database schema & seed dimensions
python scripts/initialize_database.py

# 3. Generate deterministic datasets
python scripts/generate_sample_data.py

# 4. Run pipeline
python scripts/run_pipeline.py --input data/sample/transactions_corrupted.csv --ledger data/sample/target_ledger.csv

# 5. Run test suite
python -m pytest -v
```

---

*Engineered with precision for data engineers, analytics engineers, and financial systems auditors.*  
**Repository:** [https://github.com/SAIYAMgade/DataGuard](https://github.com/SAIYAMgade/DataGuard)
