-- =============================================================================
-- SQL Validation: Date & Timeliness Validation
-- Description: Detects future-dated transactions and excessive ingestion delays.
-- =============================================================================

WITH future_dates AS (
    SELECT
        staging_id,
        batch_id,
        COALESCE(transaction_id, source_record_id) AS record_reference,
        'DQ013' AS rule_id,
        'transaction_date' AS field_name,
        transaction_date::text AS invalid_value,
        'HIGH' AS severity,
        'Transaction date is in the future relative to ingestion: ' || transaction_date::text AS issue_description
    FROM stg_transactions
    WHERE transaction_date IS NOT NULL
      AND transaction_date > CURRENT_DATE
),
stale_dates AS (
    SELECT
        staging_id,
        batch_id,
        COALESCE(transaction_id, source_record_id) AS record_reference,
        'DQ014' AS rule_id,
        'transaction_date,ingestion_timestamp' AS field_name,
        transaction_date::text AS invalid_value,
        'LOW' AS severity,
        'Transaction date is over 90 days older than ingestion timestamp (' || transaction_date::text || ')' AS issue_description
    FROM stg_transactions
    WHERE transaction_date IS NOT NULL
      AND transaction_date < (CURRENT_DATE - INTERVAL '90 days')
)
SELECT * FROM future_dates
UNION ALL
SELECT * FROM stale_dates;
