-- =============================================================================
-- SQL Validation: Monetary Validation
-- Description: Detects decimal precision violations, illegal signs for transaction
--              types, and extreme outlier values.
-- =============================================================================

-- 1. Invalid Decimal Precision (Excess fractional cents for 2-decimal currencies)
WITH invalid_precision AS (
    SELECT
        staging_id,
        batch_id,
        COALESCE(transaction_id, source_record_id) AS record_reference,
        'DQ010' AS rule_id,
        'amount' AS field_name,
        amount::text AS invalid_value,
        'MEDIUM' AS severity,
        'Amount exceeds standard 2-decimal precision: ' || amount::text AS issue_description
    FROM stg_transactions
    WHERE amount IS NOT NULL
      AND currency IN ('USD', 'EUR', 'GBP')
      AND (amount * 100.0) <> FLOOR(amount * 100.0)
),

-- 2. Sign Inconsistency by Transaction Type
-- Deposits and Payments must be strictly positive; negative values reserved for Refunds/Reversals/Fees
invalid_signs AS (
    SELECT
        staging_id,
        batch_id,
        COALESCE(transaction_id, source_record_id) AS record_reference,
        'DQ011' AS rule_id,
        'amount,transaction_type' AS field_name,
        'amount=' || amount::text || ', type=' || transaction_type AS invalid_value,
        'HIGH' AS severity,
        'Illegal sign for transaction type: ' || transaction_type || ' cannot have amount <= 0 (' || amount::text || ')' AS issue_description
    FROM stg_transactions
    WHERE amount IS NOT NULL
      AND transaction_type IN ('DEPOSIT', 'PAYMENT', 'TRANSFER')
      AND amount <= 0.00
),

-- 3. Extreme Outliers (> 1,000,000.00 without special authorization)
outlier_amounts AS (
    SELECT
        staging_id,
        batch_id,
        COALESCE(transaction_id, source_record_id) AS record_reference,
        'DQ012' AS rule_id,
        'amount' AS field_name,
        amount::text AS invalid_value,
        'MEDIUM' AS severity,
        'Transaction amount exceeds standard ceiling ($1,000,000.00): ' || amount::text AS issue_description
    FROM stg_transactions
    WHERE amount IS NOT NULL
      AND ABS(amount) > 1000000.00
)
SELECT * FROM invalid_precision
UNION ALL
SELECT * FROM invalid_signs
UNION ALL
SELECT * FROM outlier_amounts;
