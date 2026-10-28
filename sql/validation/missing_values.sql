-- =============================================================================
-- SQL Validation: Missing Mandatory Values
-- Description: Identifies null or blank values in required fields.
-- CTE-based query returning record references, rule IDs, and field details.
-- =============================================================================

WITH missing_tx_id AS (
    SELECT
        staging_id,
        batch_id,
        COALESCE(source_record_id, 'UNKNOWN_SRC_' || staging_id::text) AS record_reference,
        'DQ001' AS rule_id,
        'transaction_id' AS field_name,
        'NULL or Empty' AS invalid_value,
        'CRITICAL' AS severity,
        'Missing mandatory transaction identifier' AS issue_description
    FROM stg_transactions
    WHERE transaction_id IS NULL OR TRIM(transaction_id) = ''
),
missing_acc_id AS (
    SELECT
        staging_id,
        batch_id,
        COALESCE(transaction_id, source_record_id) AS record_reference,
        'DQ002' AS rule_id,
        'account_id' AS field_name,
        'NULL or Empty' AS invalid_value,
        'CRITICAL' AS severity,
        'Missing mandatory account identifier' AS issue_description
    FROM stg_transactions
    WHERE account_id IS NULL OR TRIM(account_id) = ''
),
missing_date AS (
    SELECT
        staging_id,
        batch_id,
        COALESCE(transaction_id, source_record_id) AS record_reference,
        'DQ003' AS rule_id,
        'transaction_date' AS field_name,
        'NULL' AS invalid_value,
        'HIGH' AS severity,
        'Missing mandatory transaction date' AS issue_description
    FROM stg_transactions
    WHERE transaction_date IS NULL
),
missing_amount AS (
    SELECT
        staging_id,
        batch_id,
        COALESCE(transaction_id, source_record_id) AS record_reference,
        'DQ004' AS rule_id,
        'amount' AS field_name,
        'NULL' AS invalid_value,
        'CRITICAL' AS severity,
        'Missing mandatory transaction amount' AS issue_description
    FROM stg_transactions
    WHERE amount IS NULL
),
missing_currency AS (
    SELECT
        staging_id,
        batch_id,
        COALESCE(transaction_id, source_record_id) AS record_reference,
        'DQ005' AS rule_id,
        'currency' AS field_name,
        'NULL or Empty' AS invalid_value,
        'HIGH' AS severity,
        'Missing mandatory currency code' AS issue_description
    FROM stg_transactions
    WHERE currency IS NULL OR TRIM(currency) = ''
)
SELECT * FROM missing_tx_id
UNION ALL
SELECT * FROM missing_acc_id
UNION ALL
SELECT * FROM missing_date
UNION ALL
SELECT * FROM missing_amount
UNION ALL
SELECT * FROM missing_currency;
