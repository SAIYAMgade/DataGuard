-- =============================================================================
-- DataGuard: Financial Data Quality & Transaction Monitoring System
-- Migration: 002_create_indexes.sql
-- Description: Targeted indexes supporting high-throughput lookups, joins,
--              window functions, reconciliation queries, and exception queries.
-- =============================================================================

-- Ingestion & Raw Tables
CREATE INDEX idx_raw_tx_batch ON raw_transactions(batch_id);
CREATE INDEX idx_raw_tx_src_rec ON raw_transactions(source_record_id);

-- Staging Transactions: Lookups, Joins, and Deduplication
CREATE INDEX idx_stg_tx_batch ON stg_transactions(batch_id);
CREATE INDEX idx_stg_tx_id ON stg_transactions(transaction_id);
CREATE INDEX idx_stg_tx_account ON stg_transactions(account_id);
CREATE INDEX idx_stg_tx_date ON stg_transactions(transaction_date);
CREATE INDEX idx_stg_tx_currency ON stg_transactions(currency);
CREATE INDEX idx_stg_tx_type_status ON stg_transactions(transaction_type, transaction_status);
-- Idempotency and duplicate detection index
CREATE INDEX idx_stg_tx_hash ON stg_transactions(batch_id, record_hash);
CREATE INDEX idx_stg_tx_business_dup ON stg_transactions(account_id, amount, transaction_date, transaction_type);

-- Dimension Tables
CREATE INDEX idx_dim_acc_cust ON dim_accounts(customer_id);
CREATE INDEX idx_dim_acc_status ON dim_accounts(status);
CREATE INDEX idx_dim_cust_country ON dim_customers(country);

-- Exception Register: Filtering by status, severity, rule, and batch
CREATE INDEX idx_exc_reg_batch ON exception_register(batch_id);
CREATE INDEX idx_exc_reg_run ON exception_register(run_id);
CREATE INDEX idx_exc_reg_status_sev ON exception_register(resolution_status, severity);
CREATE INDEX idx_exc_reg_rule ON exception_register(rule_id);
CREATE INDEX idx_exc_reg_rec_ref ON exception_register(record_reference);
CREATE INDEX idx_exc_reg_detected ON exception_register(detected_at);

-- Reconciliation: Fast matching between source transactions and ledger
CREATE INDEX idx_target_ledger_acc_date ON target_ledger_transactions(account_id, transaction_date);
CREATE INDEX idx_target_ledger_curr ON target_ledger_transactions(currency);
CREATE INDEX idx_target_ledger_ext_ref ON target_ledger_transactions(external_ref);

CREATE INDEX idx_recon_res_run ON reconciliation_results(run_id);
CREATE INDEX idx_recon_res_batch ON reconciliation_results(batch_id);
CREATE INDEX idx_recon_res_status ON reconciliation_results(match_status);
CREATE INDEX idx_recon_res_curr ON reconciliation_results(currency);
