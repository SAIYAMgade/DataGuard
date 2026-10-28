-- =============================================================================
-- SQL Reconciliation: Source vs. Target Ledger Detailed Comparison
-- Description: Performs FULL OUTER JOIN between source feed and target ledger.
--              Computes signed difference = source_amount - target_amount
--              and classifies match status (EXACT_MATCH, WITHIN_TOLERANCE, AMOUNT_MISMATCH, etc.)
-- =============================================================================

WITH recon_base AS (
    SELECT
        COALESCE(st.transaction_id, tl.ledger_id) AS recon_key,
        st.batch_id,
        st.transaction_id AS source_id,
        tl.ledger_id AS target_id,
        COALESCE(st.currency, tl.currency) AS currency,
        st.amount AS source_amount,
        tl.amount AS target_amount,
        (COALESCE(st.amount, 0.00) - COALESCE(tl.amount, 0.00)) AS signed_difference,
        ABS(COALESCE(st.amount, 0.00) - COALESCE(tl.amount, 0.00)) AS absolute_difference,
        0.01::NUMERIC(18, 4) AS tolerance
    FROM stg_transactions st
    FULL OUTER JOIN target_ledger_transactions tl
        ON st.transaction_id = tl.ledger_id
        OR (st.transaction_id = tl.external_ref AND st.currency = tl.currency)
)
SELECT
    recon_key,
    batch_id,
    source_id,
    target_id,
    currency,
    source_amount,
    target_amount,
    signed_difference,
    absolute_difference,
    tolerance,
    CASE
        WHEN source_id IS NOT NULL AND target_id IS NULL THEN 'SOURCE_ONLY'
        WHEN source_id IS NULL AND target_id IS NOT NULL THEN 'TARGET_ONLY'
        WHEN absolute_difference = 0.00 THEN 'EXACT_MATCH'
        WHEN absolute_difference <= tolerance THEN 'WITHIN_TOLERANCE'
        ELSE 'AMOUNT_MISMATCH'
    END AS match_status
FROM recon_base
ORDER BY absolute_difference DESC;
