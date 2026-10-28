"""DataGuard Financial Reconciliation Engine.

Orchestrates record-level and aggregate reconciliations, tracks tolerance thresholds,
and stores traceable match results in the database.
"""

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple
import pandas as pd
from sqlalchemy import text

from dataguard.config.settings import load_settings
from dataguard.database.connection import get_db_connection
from dataguard.database.repositories import ReconciliationRepository
from dataguard.reconciliation.comparisons import reconcile_records, reconcile_aggregates_by_currency

logger = logging.getLogger("dataguard.reconciliation")


class ReconciliationEngine:
    """Executes financial reconciliation between source transactions and target ledger."""

    def __init__(self, tolerance: float | None = None):
        settings = load_settings()
        self.tolerance = tolerance if tolerance is not None else settings.default_tolerance

    def fetch_target_ledger_df(self) -> pd.DataFrame:
        """Loads target ledger from PostgreSQL database."""
        with get_db_connection() as conn:
            query = text("SELECT ledger_id, account_id, transaction_date, amount, currency, external_ref FROM target_ledger_transactions;")
            result = conn.execute(query)
            rows = result.fetchall()
            if not rows:
                return pd.DataFrame(columns=["ledger_id", "account_id", "transaction_date", "amount", "currency", "external_ref"])
            return pd.DataFrame(rows, columns=["ledger_id", "account_id", "transaction_date", "amount", "currency", "external_ref"])

    def run_reconciliation(
        self,
        run_id: str,
        batch_id: str,
        source_df: pd.DataFrame,
        target_df: pd.DataFrame | None = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Executes record-level and aggregate reconciliation.
        Returns:
            (record_results, aggregate_results)
        """
        if target_df is None or target_df.empty:
            target_df = self.fetch_target_ledger_df()

        logger.info(
            "Running reconciliation for batch %s (source: %d records, target: %d records, tolerance: %.4f)",
            batch_id, len(source_df), len(target_df), self.tolerance
        )

        record_matches = reconcile_records(
            source_df=source_df,
            target_df=target_df,
            match_key="transaction_id",
            target_key="ledger_id",
            tolerance=self.tolerance
        )

        aggregate_matches = reconcile_aggregates_by_currency(source_df, target_df)

        # Prepare persistence records
        now = datetime.now(timezone.utc)
        persisted_records = []

        for rec in record_matches:
            persisted_records.append({
                "recon_id": f"REC_{uuid.uuid4().hex[:12].upper()}",
                "run_id": run_id,
                "batch_id": batch_id,
                "recon_type": "RECORD_LEVEL",
                "source_id": rec.get("source_id"),
                "target_id": rec.get("target_id"),
                "currency": rec["currency"],
                "source_amount": rec.get("source_amount"),
                "target_amount": rec.get("target_amount"),
                "signed_difference": rec["signed_difference"],
                "absolute_difference": rec["absolute_difference"],
                "tolerance": self.tolerance,
                "match_status": rec["match_status"],
                "reconciled_at": now
            })

        for agg in aggregate_matches:
            persisted_records.append({
                "recon_id": f"AGG_{uuid.uuid4().hex[:12].upper()}",
                "run_id": run_id,
                "batch_id": batch_id,
                "recon_type": "AGGREGATE",
                "source_id": f"TOTAL_{agg['currency']}",
                "target_id": f"LEDGER_{agg['currency']}",
                "currency": agg["currency"],
                "source_amount": agg["source_amount"],
                "target_amount": agg["target_amount"],
                "signed_difference": agg["signed_difference"],
                "absolute_difference": agg["absolute_difference"],
                "tolerance": self.tolerance,
                "match_status": agg["match_status"],
                "reconciled_at": now
            })

        ReconciliationRepository.save_results(persisted_records)

        exact_cnt = sum(1 for r in record_matches if r["match_status"] == "EXACT_MATCH")
        within_tol = sum(1 for r in record_matches if r["match_status"] == "WITHIN_TOLERANCE")
        mismatch_cnt = sum(1 for r in record_matches if r["match_status"] == "AMOUNT_MISMATCH")
        src_only = sum(1 for r in record_matches if r["match_status"] == "SOURCE_ONLY")
        tgt_only = sum(1 for r in record_matches if r["match_status"] == "TARGET_ONLY")

        logger.info(
            "Reconciliation complete: %d exact matches, %d within tolerance, %d mismatches, %d source-only, %d target-only",
            exact_cnt, within_tol, mismatch_cnt, src_only, tgt_only
        )

        return record_matches, aggregate_matches
