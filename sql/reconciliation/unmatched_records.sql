-- =============================================================================
-- SQL Reconciliation: Unmatched Records (Breaks)
-- Description: Filters specifically for reconciliation breaks (Source-only or Target-only)
--              requiring manual investigation or clearing operations.
-- =============================================================================

SELECT
    recon_id,
    batch_id,
    recon_type,
    source_id,
    target_id,
    currency,
    source_amount,
    target_amount,
    signed_difference,
    match_status,
    reconciled_at
FROM reconciliation_results
WHERE match_status IN ('SOURCE_ONLY', 'TARGET_ONLY', 'AMOUNT_MISMATCH')
ORDER BY absolute_difference DESC;
