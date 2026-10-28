-- =============================================================================
-- SQL Reporting: Quality Summary by Batch
-- Description: Aggregates quality dimensions and pass rates across batches.
-- =============================================================================

SELECT
    qrh.batch_id,
    ib.source_system,
    qrh.total_records,
    qrh.passed_records,
    qrh.failed_records,
    ROUND((qrh.passed_records::NUMERIC / NULLIF(qrh.total_records, 0)) * 100.0, 2) AS pass_rate_pct,
    qrh.completeness_score,
    qrh.validity_score,
    qrh.uniqueness_score,
    qrh.integrity_score,
    qrh.overall_quality_score,
    qrh.total_exceptions,
    qrh.evaluated_at
FROM quality_run_history qrh
JOIN ingestion_batches ib ON qrh.batch_id = ib.batch_id
ORDER BY qrh.evaluated_at DESC;
