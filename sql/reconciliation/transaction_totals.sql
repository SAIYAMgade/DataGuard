-- =============================================================================
-- SQL Reconciliation: Transaction Totals & Multi-Currency Aggregation
-- Description: Calculates financial aggregates grouped strictly by currency.
--              NEVER sums across currency boundaries without FX conversion.
-- =============================================================================

SELECT
    batch_id,
    currency,
    COUNT(*) AS transaction_count,
    COUNT(DISTINCT account_id) AS distinct_accounts,
    SUM(amount) AS total_amount,
    AVG(amount) AS average_amount,
    MIN(amount) AS min_amount,
    MAX(amount) AS max_amount,
    MIN(transaction_date) AS earliest_date,
    MAX(transaction_date) AS latest_date
FROM stg_transactions
WHERE amount IS NOT NULL AND currency IS NOT NULL
GROUP BY batch_id, currency
ORDER BY batch_id, currency;
