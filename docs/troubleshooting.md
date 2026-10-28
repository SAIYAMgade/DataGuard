# DataGuard | Troubleshooting & Operational Runbook

This guide covers resolution steps for operational errors, database issues, and data pipeline failures.

---

## 1. Database Connection Failures

### Symptom: `psycopg2.OperationalError: could not connect to server`
**Root Cause:** PostgreSQL service is stopped or port 5432 is blocked.
**Resolution:**
1. Check Windows service status:
   ```powershell
   Get-Service *postgres*
   ```
2. Start the service if stopped:
   ```powershell
   Start-Service postgresql*
   ```
3. Test local connection:
   ```bash
   python -c "import psycopg2; psycopg2.connect('dbname=dataguard user=postgres host=localhost port=5432')"
   ```

---

## 2. Ingestion Failures

### Symptom: `ValueError: Missing required columns: ['account_id', 'amount']`
**Root Cause:** Source CSV file contains unexpected column headers or alternate delimiter.
**Resolution:**
1. Check headers of source file:
   ```powershell
   Get-Content -Head 2 data/sample/transactions_corrupted.csv
   ```
2. Check `config/settings.yaml` under `ingestion.required_columns`.
3. If source file uses semicolon `;` instead of comma `,`, update reader settings.

### Symptom: Batch Marked as `FAILED` in `ingestion_batches`
**Root Cause:** A critical error occurred during raw preservation or staging insertion.
**Resolution:**
1. Query the error message directly from PostgreSQL:
   ```sql
   SELECT batch_id, source_file, started_at, error_message
   FROM ingestion_batches
   WHERE status = 'FAILED'
   ORDER BY started_at DESC LIMIT 5;
   ```
2. DataGuard transactions rollback automatically on error, preventing half-loaded batches.
3. Fix the offending file or mapping and rerun with the same command.

---

## 3. Reconciliation Discrepancies

### Symptom: Large number of `SOURCE_ONLY` or `TARGET_ONLY` records
**Root Cause:** Timing difference between upstream transaction generation and nightly ledger settlement.
**Resolution:**
1. Inspect unmatched records query:
   ```sql
   SELECT * FROM reconciliation_results
   WHERE match_status IN ('SOURCE_ONLY', 'TARGET_ONLY');
   ```
2. Verify whether target ledger file covers the same calendar date range as transaction batch.
3. Check if external settlement reference (`external_ref`) matches `source_record_id`.
