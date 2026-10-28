-- =============================================================================
-- SQL Validation: Duplicate Transactions
-- Description: Differentiates exact source duplication, duplicate IDs,
--              and potential business duplicates using Window Functions & CTEs.
-- =============================================================================

-- 1. Exact Source Duplication (Identical Hash within batch)
WITH ranked_hashes AS (
    SELECT
        staging_id,
        batch_id,
        transaction_id,
        source_record_id,
        record_hash,
        ROW_NUMBER() OVER (
            PARTITION BY batch_id, record_hash
            ORDER BY staging_id ASC
        ) AS occurrence_rank
    FROM stg_transactions
),
exact_duplicates AS (
    SELECT
        staging_id,
        batch_id,
        COALESCE(transaction_id, source_record_id) AS record_reference,
        'DQ007' AS rule_id,
        'record_hash' AS field_name,
        record_hash AS invalid_value,
        'HIGH' AS severity,
        'Exact duplicate source payload ingested (occurrence #' || occurrence_rank::text || ')' AS issue_description
    FROM ranked_hashes
    WHERE occurrence_rank > 1
),

-- 2. Duplicate Transaction Identifier (Same ID with differing or duplicate records)
ranked_tx_ids AS (
    SELECT
        staging_id,
        batch_id,
        transaction_id,
        ROW_NUMBER() OVER (
            PARTITION BY transaction_id
            ORDER BY staging_id ASC
        ) AS id_rank
    FROM stg_transactions
    WHERE transaction_id IS NOT NULL AND TRIM(transaction_id) <> ''
),
duplicate_tx_ids AS (
    SELECT
        staging_id,
        batch_id,
        transaction_id AS record_reference,
        'DQ008' AS rule_id,
        'transaction_id' AS field_name,
        transaction_id AS invalid_value,
        'CRITICAL' AS severity,
        'Duplicate transaction identifier found (occurrence #' || id_rank::text || ')' AS issue_description
    FROM ranked_tx_ids
    WHERE id_rank > 1
),

-- 3. Potential Business Duplicates (Same account, amount, date, and type within batch)
ranked_business_dups AS (
    SELECT
        staging_id,
        batch_id,
        transaction_id,
        source_record_id,
        account_id,
        amount,
        transaction_date,
        transaction_type,
        ROW_NUMBER() OVER (
            PARTITION BY batch_id, account_id, amount, transaction_date, transaction_type
            ORDER BY staging_id ASC
        ) AS biz_rank,
        COUNT(*) OVER (
            PARTITION BY batch_id, account_id, amount, transaction_date, transaction_type
        ) AS biz_cluster_size
    FROM stg_transactions
    WHERE account_id IS NOT NULL AND amount IS NOT NULL AND transaction_date IS NOT NULL
)
SELECT * FROM exact_duplicates
UNION ALL
SELECT * FROM duplicate_tx_ids
UNION ALL
SELECT
    staging_id,
    batch_id,
    COALESCE(transaction_id, source_record_id) AS record_reference,
    'DQ009' AS rule_id,
    'account_id,amount,transaction_date,transaction_type' AS field_name,
    account_id || ' | ' || amount::text || ' | ' || transaction_date::text AS invalid_value,
    'MEDIUM' AS severity,
    'Potential business duplicate: matching account, amount, date, and type (cluster of ' || biz_cluster_size::text || ')' AS issue_description
FROM ranked_business_dups
WHERE biz_rank > 1;
