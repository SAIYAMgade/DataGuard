-- =============================================================================
-- DataGuard: Financial Data Quality & Transaction Monitoring System
-- Views: reporting_views.sql
-- Description: Business and analytical views for Power BI, Excel, and SQL reports.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Executive KPIs (Latest Run or Overall Active Snapshot)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_executive_kpis AS
WITH latest_batch AS (
    SELECT batch_id
    FROM ingestion_batches
    WHERE status = 'COMPLETED'
    ORDER BY completed_at DESC
    LIMIT 1
),
latest_run AS (
    SELECT qrh.*
    FROM quality_run_history qrh
    JOIN latest_batch lb ON qrh.batch_id = lb.batch_id
    ORDER BY qrh.evaluated_at DESC
    LIMIT 1
),
open_crit AS (
    SELECT COUNT(*) AS open_critical_count
    FROM exception_register
    WHERE resolution_status = 'OPEN' AND severity = 'CRITICAL'
),
recon_diffs AS (
    SELECT
        COUNT(*) AS total_recon_exceptions,
        COALESCE(SUM(absolute_difference), 0.00) AS total_absolute_diff
    FROM reconciliation_results rr
    JOIN latest_batch lb ON rr.batch_id = lb.batch_id
    WHERE rr.match_status IN ('AMOUNT_MISMATCH', 'SOURCE_ONLY', 'TARGET_ONLY')
)
SELECT
    lr.batch_id,
    lr.run_id,
    lr.total_records,
    lr.passed_records,
    lr.failed_records,
    ROUND((lr.passed_records::NUMERIC / NULLIF(lr.total_records, 0)) * 100.0, 2) AS pass_rate_pct,
    lr.completeness_score,
    lr.validity_score,
    lr.uniqueness_score,
    lr.integrity_score,
    lr.overall_quality_score,
    oc.open_critical_count,
    rd.total_recon_exceptions,
    rd.total_absolute_diff,
    lr.evaluated_at
FROM latest_run lr
CROSS JOIN open_crit oc
CROSS JOIN recon_diffs rd;

-- -----------------------------------------------------------------------------
-- 2. Batch Quality Summary (Historical Run Progression)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_batch_quality_summary AS
SELECT
    ib.batch_id,
    ib.source_system,
    ib.source_file,
    ib.started_at,
    ib.completed_at,
    ib.records_received,
    ib.records_loaded,
    ib.records_rejected,
    qrh.run_id,
    qrh.evaluated_at,
    qrh.total_records,
    qrh.passed_records,
    qrh.failed_records,
    qrh.total_exceptions,
    qrh.completeness_score,
    qrh.validity_score,
    qrh.uniqueness_score,
    qrh.integrity_score,
    qrh.overall_quality_score
FROM ingestion_batches ib
LEFT JOIN quality_run_history qrh ON ib.batch_id = qrh.batch_id
ORDER BY ib.started_at DESC;

-- -----------------------------------------------------------------------------
-- 3. Rule Failure Distribution & Performance
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_rule_failure_distribution AS
SELECT
    qr.rule_id,
    qr.name AS rule_name,
    qr.dimension,
    qr.severity,
    COUNT(er.exception_id) AS total_exceptions,
    COUNT(CASE WHEN er.resolution_status = 'OPEN' THEN 1 END) AS open_exceptions,
    COUNT(CASE WHEN er.resolution_status = 'UNDER_REVIEW' THEN 1 END) AS under_review_exceptions,
    COUNT(CASE WHEN er.resolution_status = 'RESOLVED' THEN 1 END) AS resolved_exceptions,
    MIN(er.detected_at) AS first_detected_at,
    MAX(er.detected_at) AS last_detected_at,
    qr.investigation_action
FROM quality_rules qr
LEFT JOIN exception_register er ON qr.rule_id = er.rule_id
GROUP BY qr.rule_id, qr.name, qr.dimension, qr.severity, qr.investigation_action
ORDER BY total_exceptions DESC, qr.severity ASC;

-- -----------------------------------------------------------------------------
-- 4. Exception Aging Analysis (Unresolved Exceptions)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_exception_aging AS
SELECT
    exception_id,
    batch_id,
    rule_id,
    record_reference,
    severity,
    issue_description,
    detected_at,
    resolution_status,
    ROUND(EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - detected_at)) / 86400.0, 1) AS age_days,
    CASE
        WHEN EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - detected_at)) / 86400.0 <= 1 THEN '0-1 Days (New)'
        WHEN EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - detected_at)) / 86400.0 <= 7 THEN '2-7 Days (Active)'
        WHEN EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - detected_at)) / 86400.0 <= 30 THEN '8-30 Days (Aging)'
        ELSE '30+ Days (Critical Backlog)'
    END AS aging_bracket
FROM exception_register
WHERE resolution_status IN ('OPEN', 'UNDER_REVIEW')
ORDER BY detected_at ASC;

-- -----------------------------------------------------------------------------
-- 5. Reconciliation Summary by Currency & Batch (Never Summing Across Currencies)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_reconciliation_summary AS
SELECT
    batch_id,
    currency,
    recon_type,
    COUNT(*) AS total_comparisons,
    COUNT(CASE WHEN match_status = 'EXACT_MATCH' THEN 1 END) AS exact_matches,
    COUNT(CASE WHEN match_status = 'WITHIN_TOLERANCE' THEN 1 END) AS within_tolerance_matches,
    COUNT(CASE WHEN match_status = 'AMOUNT_MISMATCH' THEN 1 END) AS amount_mismatches,
    COUNT(CASE WHEN match_status = 'SOURCE_ONLY' THEN 1 END) AS source_only_count,
    COUNT(CASE WHEN match_status = 'TARGET_ONLY' THEN 1 END) AS target_only_count,
    COALESCE(SUM(source_amount), 0.00) AS total_source_amount,
    COALESCE(SUM(target_amount), 0.00) AS total_target_amount,
    COALESCE(SUM(signed_difference), 0.00) AS net_signed_difference,
    COALESCE(SUM(absolute_difference), 0.00) AS total_absolute_difference,
    ROUND(
        (COUNT(CASE WHEN match_status IN ('EXACT_MATCH', 'WITHIN_TOLERANCE') THEN 1 END)::NUMERIC / NULLIF(COUNT(*), 0)) * 100.0,
        2
    ) AS reconciliation_match_rate_pct
FROM reconciliation_results
GROUP BY batch_id, currency, recon_type
ORDER BY batch_id DESC, currency ASC;

-- -----------------------------------------------------------------------------
-- 6. Source System Quality Comparison
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_source_system_quality AS
SELECT
    st.source_system,
    COUNT(DISTINCT st.batch_id) AS total_batches,
    COUNT(DISTINCT st.transaction_id) AS total_transactions,
    COUNT(DISTINCT er.exception_id) AS total_exceptions,
    COUNT(DISTINCT CASE WHEN er.severity = 'CRITICAL' THEN er.exception_id END) AS critical_exceptions,
    COUNT(DISTINCT CASE WHEN er.severity = 'HIGH' THEN er.exception_id END) AS high_exceptions,
    ROUND(
        (1.0 - (COUNT(DISTINCT er.record_reference)::NUMERIC / NULLIF(COUNT(DISTINCT st.transaction_id), 0))) * 100.0,
        2
    ) AS source_clean_record_rate_pct
FROM stg_transactions st
LEFT JOIN exception_register er ON st.transaction_id = er.record_reference
GROUP BY st.source_system;
