-- =============================================================================
-- SQL Reporting: Historical Quality Trends
-- Description: Window-function-based trend analysis tracking quality progression
--              across sequential ingestion batches.
-- =============================================================================

SELECT
    qrh.run_id,
    qrh.batch_id,
    qrh.evaluated_at,
    qrh.total_records,
    qrh.overall_quality_score,
    LAG(qrh.overall_quality_score) OVER (ORDER BY qrh.evaluated_at ASC) AS prior_batch_score,
    ROUND(
        qrh.overall_quality_score - LAG(qrh.overall_quality_score) OVER (ORDER BY qrh.evaluated_at ASC),
        2
    ) AS score_delta_pct,
    qrh.total_exceptions,
    LAG(qrh.total_exceptions) OVER (ORDER BY qrh.evaluated_at ASC) AS prior_batch_exceptions,
    qrh.total_exceptions - COALESCE(LAG(qrh.total_exceptions) OVER (ORDER BY qrh.evaluated_at ASC), qrh.total_exceptions) AS exception_count_delta
FROM quality_run_history qrh
ORDER BY qrh.evaluated_at ASC;
