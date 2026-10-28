-- =============================================================================
-- DataGuard: Financial Data Quality & Transaction Monitoring System
-- Migration: 001_create_tables.sql
-- Description: Core schema definitions for ingestion, reference data, staging,
--              quality rule tracking, exception register, and reconciliation.
-- =============================================================================

-- Drop tables in reverse dependency order if resetting
DROP TABLE IF EXISTS exception_resolution_history CASCADE;
DROP TABLE IF EXISTS reconciliation_results CASCADE;
DROP TABLE IF EXISTS target_ledger_transactions CASCADE;
DROP TABLE IF EXISTS exception_register CASCADE;
DROP TABLE IF EXISTS quality_run_history CASCADE;
DROP TABLE IF EXISTS quality_rules CASCADE;
DROP TABLE IF EXISTS stg_transactions CASCADE;
DROP TABLE IF EXISTS raw_transactions CASCADE;
DROP TABLE IF EXISTS dim_accounts CASCADE;
DROP TABLE IF EXISTS dim_customers CASCADE;
DROP TABLE IF EXISTS ingestion_batches CASCADE;

-- -----------------------------------------------------------------------------
-- 1. Ingestion Batches
-- -----------------------------------------------------------------------------
CREATE TABLE ingestion_batches (
    batch_id VARCHAR(64) PRIMARY KEY,
    source_file VARCHAR(255) NOT NULL,
    source_system VARCHAR(50) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'STARTED', -- STARTED, COMPLETED, FAILED
    records_received INT DEFAULT 0,
    records_loaded INT DEFAULT 0,
    records_rejected INT DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_batch_status CHECK (status IN ('STARTED', 'COMPLETED', 'FAILED'))
);

-- -----------------------------------------------------------------------------
-- 2. Raw Transactions (Preserves exact raw source representation as JSONB)
-- -----------------------------------------------------------------------------
CREATE TABLE raw_transactions (
    raw_id BIGSERIAL PRIMARY KEY,
    batch_id VARCHAR(64) NOT NULL REFERENCES ingestion_batches(batch_id) ON DELETE CASCADE,
    source_record_id VARCHAR(100),
    raw_payload JSONB NOT NULL,
    ingested_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- 3. Customer Reference Dimension
-- -----------------------------------------------------------------------------
CREATE TABLE dim_customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    customer_type VARCHAR(20) NOT NULL, -- INDIVIDUAL, CORPORATE
    country VARCHAR(3) NOT NULL,
    kyc_status VARCHAR(20) NOT NULL DEFAULT 'VERIFIED',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_customer_type CHECK (customer_type IN ('INDIVIDUAL', 'CORPORATE')),
    CONSTRAINT chk_kyc_status CHECK (kyc_status IN ('VERIFIED', 'PENDING', 'EXPIRED'))
);

-- -----------------------------------------------------------------------------
-- 4. Account Reference Dimension
-- -----------------------------------------------------------------------------
CREATE TABLE dim_accounts (
    account_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL REFERENCES dim_customers(customer_id),
    account_type VARCHAR(30) NOT NULL, -- CHECKING, SAVINGS, INVESTMENT, CREDIT
    currency VARCHAR(3) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, DORMANT, CLOSED
    opened_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_account_status CHECK (status IN ('ACTIVE', 'DORMANT', 'CLOSED'))
);

-- -----------------------------------------------------------------------------
-- 5. Standardized Staging Transactions
-- -----------------------------------------------------------------------------
CREATE TABLE stg_transactions (
    staging_id BIGSERIAL PRIMARY KEY,
    batch_id VARCHAR(64) NOT NULL REFERENCES ingestion_batches(batch_id) ON DELETE CASCADE,
    source_system VARCHAR(50) NOT NULL,
    source_record_id VARCHAR(100),
    transaction_id VARCHAR(100),
    account_id VARCHAR(50),
    customer_id VARCHAR(50),
    transaction_date DATE,
    transaction_timestamp TIMESTAMPTZ,
    transaction_type VARCHAR(30), -- DEPOSIT, WITHDRAWAL, PAYMENT, REFUND, TRANSFER, FEE, REVERSAL
    amount NUMERIC(18, 4),        -- Strict exact decimal representation
    currency VARCHAR(3),
    transaction_status VARCHAR(30), -- COMPLETED, PENDING, FAILED, REVERSED, CANCELLED
    reference_id VARCHAR(100),      -- Originating transaction for reversals/refunds
    description TEXT,
    record_hash VARCHAR(64) NOT NULL, -- SHA-256 idempotency fingerprint
    ingestion_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- 6. Quality Rules Catalog
-- -----------------------------------------------------------------------------
CREATE TABLE quality_rules (
    rule_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    dimension VARCHAR(50) NOT NULL, -- COMPLETENESS, UNIQUENESS, VALIDITY, TIMELINESS, INTEGRITY, CONSISTENCY
    severity VARCHAR(20) NOT NULL,  -- CRITICAL, HIGH, MEDIUM, LOW
    target_field VARCHAR(100),
    description TEXT NOT NULL,
    investigation_action TEXT NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_rule_dimension CHECK (dimension IN ('COMPLETENESS', 'UNIQUENESS', 'VALIDITY', 'TIMELINESS', 'INTEGRITY', 'CONSISTENCY')),
    CONSTRAINT chk_rule_severity CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW'))
);

-- -----------------------------------------------------------------------------
-- 7. Quality Run History
-- -----------------------------------------------------------------------------
CREATE TABLE quality_run_history (
    run_id VARCHAR(64) PRIMARY KEY,
    batch_id VARCHAR(64) NOT NULL REFERENCES ingestion_batches(batch_id) ON DELETE CASCADE,
    evaluated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    total_records INT NOT NULL,
    passed_records INT NOT NULL,
    failed_records INT NOT NULL,
    total_exceptions INT NOT NULL,
    completeness_score NUMERIC(5, 2) NOT NULL,
    validity_score NUMERIC(5, 2) NOT NULL,
    uniqueness_score NUMERIC(5, 2) NOT NULL,
    integrity_score NUMERIC(5, 2) NOT NULL,
    overall_quality_score NUMERIC(5, 2) NOT NULL,
    execution_duration_ms INT,
    status VARCHAR(20) NOT NULL DEFAULT 'COMPLETED',
    CONSTRAINT chk_run_status CHECK (status IN ('COMPLETED', 'FAILED'))
);

-- -----------------------------------------------------------------------------
-- 8. Exception Register
-- -----------------------------------------------------------------------------
CREATE TABLE exception_register (
    exception_id VARCHAR(64) PRIMARY KEY,
    run_id VARCHAR(64) NOT NULL REFERENCES quality_run_history(run_id) ON DELETE CASCADE,
    batch_id VARCHAR(64) NOT NULL REFERENCES ingestion_batches(batch_id) ON DELETE CASCADE,
    rule_id VARCHAR(20) NOT NULL REFERENCES quality_rules(rule_id),
    record_reference VARCHAR(100) NOT NULL,
    field_name VARCHAR(100),
    invalid_value TEXT,
    severity VARCHAR(20) NOT NULL,
    issue_description TEXT NOT NULL,
    detected_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    resolution_status VARCHAR(20) NOT NULL DEFAULT 'OPEN', -- OPEN, UNDER_REVIEW, RESOLVED, FALSE_POSITIVE
    resolution_notes TEXT,
    resolved_at TIMESTAMPTZ,
    resolved_by VARCHAR(100),
    CONSTRAINT chk_exception_severity CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    CONSTRAINT chk_resolution_status CHECK (resolution_status IN ('OPEN', 'UNDER_REVIEW', 'RESOLVED', 'FALSE_POSITIVE'))
);

-- -----------------------------------------------------------------------------
-- 9. Exception Resolution History (Audit Trail)
-- -----------------------------------------------------------------------------
CREATE TABLE exception_resolution_history (
    history_id BIGSERIAL PRIMARY KEY,
    exception_id VARCHAR(64) NOT NULL REFERENCES exception_register(exception_id) ON DELETE CASCADE,
    old_status VARCHAR(20) NOT NULL,
    new_status VARCHAR(20) NOT NULL,
    notes TEXT,
    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- 10. Target Ledger Transactions (Reconciliation Partner Source)
-- -----------------------------------------------------------------------------
CREATE TABLE target_ledger_transactions (
    ledger_id VARCHAR(100) PRIMARY KEY,
    account_id VARCHAR(50) NOT NULL,
    transaction_date DATE NOT NULL,
    amount NUMERIC(18, 4) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    external_ref VARCHAR(100),
    posted_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- 11. Reconciliation Results
-- -----------------------------------------------------------------------------
CREATE TABLE reconciliation_results (
    recon_id VARCHAR(64) PRIMARY KEY,
    run_id VARCHAR(64) NOT NULL REFERENCES quality_run_history(run_id) ON DELETE CASCADE,
    batch_id VARCHAR(64) NOT NULL REFERENCES ingestion_batches(batch_id) ON DELETE CASCADE,
    recon_type VARCHAR(30) NOT NULL, -- RECORD_LEVEL, AGGREGATE
    source_id VARCHAR(100),          -- transaction_id or group key
    target_id VARCHAR(100),          -- ledger_id or group key
    currency VARCHAR(3) NOT NULL,
    source_amount NUMERIC(18, 4),
    target_amount NUMERIC(18, 4),
    signed_difference NUMERIC(18, 4), -- source_amount - target_amount
    absolute_difference NUMERIC(18, 4),
    tolerance NUMERIC(18, 4) DEFAULT 0.01,
    match_status VARCHAR(30) NOT NULL, -- EXACT_MATCH, WITHIN_TOLERANCE, AMOUNT_MISMATCH, SOURCE_ONLY, TARGET_ONLY
    reconciled_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_recon_type CHECK (recon_type IN ('RECORD_LEVEL', 'AGGREGATE')),
    CONSTRAINT chk_match_status CHECK (match_status IN ('EXACT_MATCH', 'WITHIN_TOLERANCE', 'AMOUNT_MISMATCH', 'SOURCE_ONLY', 'TARGET_ONLY'))
);
