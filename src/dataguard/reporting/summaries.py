"""DataGuard Reporting Summaries Module.

Extracts aggregated reporting datasets from database views and tables.
"""

from typing import Any, Dict, List
import pandas as pd
from sqlalchemy import text
from dataguard.database.connection import get_db_connection


def fetch_executive_kpis() -> Dict[str, Any]:
    """Fetches KPI summary from vw_executive_kpis view."""
    with get_db_connection() as conn:
        res = conn.execute(text("SELECT * FROM vw_executive_kpis;")).fetchone()
        if not res:
            return {}
        cols = [
            "batch_id", "run_id", "total_records", "passed_records", "failed_records",
            "pass_rate_pct", "completeness_score", "validity_score", "uniqueness_score",
            "integrity_score", "overall_quality_score", "open_critical_count",
            "total_recon_exceptions", "total_absolute_diff", "evaluated_at"
        ]
        return dict(zip(cols, res))


def fetch_all_exceptions(batch_id: str | None = None) -> pd.DataFrame:
    """Fetches exceptions joined with rule metadata."""
    query = """
        SELECT
            er.exception_id,
            er.batch_id,
            er.record_reference,
            qr.name AS rule_name,
            er.severity,
            er.field_name,
            er.invalid_value,
            er.issue_description,
            er.resolution_status,
            er.detected_at,
            qr.investigation_action
        FROM exception_register er
        JOIN quality_rules qr ON er.rule_id = qr.rule_id
    """
    params = {}
    if batch_id:
        query += " WHERE er.batch_id = :batch_id"
        params["batch_id"] = batch_id
    query += " ORDER BY er.detected_at DESC, er.severity ASC;"

    with get_db_connection() as conn:
        df = pd.read_sql_query(text(query), conn, params=params)
    return df


def fetch_reconciliation_summary(batch_id: str | None = None) -> pd.DataFrame:
    """Fetches multi-currency reconciliation summary."""
    query = "SELECT * FROM vw_reconciliation_summary"
    params = {}
    if batch_id:
        query += " WHERE batch_id = :batch_id"
        params["batch_id"] = batch_id
    query += " ORDER BY currency ASC;"

    with get_db_connection() as conn:
        df = pd.read_sql_query(text(query), conn, params=params)
    return df


def fetch_quality_history() -> pd.DataFrame:
    """Fetches historical batch runs for trend analysis."""
    with get_db_connection() as conn:
        df = pd.read_sql_query(text("SELECT * FROM vw_batch_quality_summary ORDER BY started_at ASC;"), conn)
    return df
