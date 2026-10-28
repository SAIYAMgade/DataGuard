-- =============================================================================
-- SQL Reporting: Exception Summary by Rule & Severity
-- Description: Aggregates open, under review, and resolved exceptions.
-- =============================================================================

SELECT
    er.rule_id,
    qr.name AS rule_name,
    er.severity,
    qr.dimension,
    COUNT(*) AS total_exceptions,
    COUNT(CASE WHEN er.resolution_status = 'OPEN' THEN 1 END) AS open_exceptions,
    COUNT(CASE WHEN er.resolution_status = 'UNDER_REVIEW' THEN 1 END) AS under_review_exceptions,
    COUNT(CASE WHEN er.resolution_status = 'RESOLVED' THEN 1 END) AS resolved_exceptions,
    COUNT(CASE WHEN er.resolution_status = 'FALSE_POSITIVE' THEN 1 END) AS false_positive_exceptions
FROM exception_register er
JOIN quality_rules qr ON er.rule_id = qr.rule_id
GROUP BY er.rule_id, qr.name, er.severity, qr.dimension
ORDER BY
    CASE er.severity
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        WHEN 'LOW' THEN 4
        ELSE 5
    END,
    total_exceptions DESC;
