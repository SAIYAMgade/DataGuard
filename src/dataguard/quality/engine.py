"""DataGuard Validation Engine.

Coordinates configuration loading, rule evaluation, metric calculation,
and persistence of validation run history and exceptions into PostgreSQL.
"""

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Set, Tuple
import pandas as pd
from sqlalchemy import text

from dataguard.config.settings import load_quality_rules_config
from dataguard.database.connection import get_db_connection
from dataguard.database.repositories import QualityRepository
from dataguard.quality.exceptions import QualityException
from dataguard.quality.metrics import calculate_quality_metrics
from dataguard.quality.rules import QualityRuleEvaluator

logger = logging.getLogger("dataguard.quality")


def fetch_account_dimension_keys() -> Set[str]:
    """Fetches valid account_ids from dim_accounts table."""
    try:
        with get_db_connection() as conn:
            result = conn.execute(text("SELECT account_id FROM dim_accounts WHERE status = 'ACTIVE';"))
            return {row[0] for row in result.fetchall()}
    except Exception as exc:
        logger.warning("Could not fetch accounts from database (falling back to empty set): %s", exc)
        return set()


class ValidationEngine:
    """Executes configured quality rules and persists audit-ready findings."""

    def __init__(self, rules_config_file: str = "quality_rules.yaml"):
        self.config = load_quality_rules_config(rules_config_file)
        self.rules_meta = self.config.get("rules", [])

    def sync_rule_catalog(self) -> None:
        """Synchronizes rules metadata into the quality_rules database table."""
        QualityRepository.sync_rules(self.rules_meta)

    def run_validation(
        self,
        batch_id: str,
        df: pd.DataFrame,
        valid_accounts: Set[str] | None = None
    ) -> Tuple[str, Dict[str, Any], List[QualityException]]:
        """
        Executes all active rules against the batch DataFrame.
        Returns:
            (run_id, metrics_dict, list_of_exceptions)
        """
        start_time = time.time()
        run_id = f"RUN_{uuid.uuid4().hex[:12].upper()}"

        if valid_accounts is None:
            valid_accounts = fetch_account_dimension_keys()

        evaluator = QualityRuleEvaluator(run_id=run_id, batch_id=batch_id, valid_accounts=valid_accounts)
        all_exceptions: List[QualityException] = []

        # Map rule IDs to evaluator methods
        rule_methods = {
            "DQ001": evaluator.evaluate_dq001,
            "DQ002": evaluator.evaluate_dq002,
            "DQ003": evaluator.evaluate_dq003,
            "DQ004": evaluator.evaluate_dq004,
            "DQ005": evaluator.evaluate_dq005,
            "DQ006": evaluator.evaluate_dq006,
            "DQ007": evaluator.evaluate_dq007,
            "DQ008": evaluator.evaluate_dq008,
            "DQ009": evaluator.evaluate_dq009,
            "DQ010": evaluator.evaluate_dq010,
            "DQ011": evaluator.evaluate_dq011,
            "DQ012": evaluator.evaluate_dq012,
            "DQ013": evaluator.evaluate_dq013,
            "DQ014": evaluator.evaluate_dq014,
            "DQ015": evaluator.evaluate_dq015,
            "DQ016": evaluator.evaluate_dq016,
            "DQ017": evaluator.evaluate_dq017,
        }

        # Execute enabled rules
        for rule_meta in self.rules_meta:
            rule_id = rule_meta["rule_id"]
            if not rule_meta.get("enabled", True):
                continue
            if rule_id in rule_methods:
                rule_exceptions = rule_methods[rule_id](df)
                all_exceptions.extend(rule_exceptions)

        # Calculate metrics
        metrics = calculate_quality_metrics(df, all_exceptions, valid_accounts)
        duration_ms = int((time.time() - start_time) * 1000)

        # Persist run history
        run_record = {
            "run_id": run_id,
            "batch_id": batch_id,
            "evaluated_at": datetime.now(timezone.utc),
            "total_records": metrics["total_records"],
            "passed_records": metrics["passed_records"],
            "failed_records": metrics["failed_records"],
            "total_exceptions": metrics["total_exceptions"],
            "completeness_score": metrics["completeness_score"],
            "validity_score": metrics["validity_score"],
            "uniqueness_score": metrics["uniqueness_score"],
            "integrity_score": metrics["integrity_score"],
            "overall_quality_score": metrics["overall_quality_score"],
            "execution_duration_ms": duration_ms,
            "status": "COMPLETED",
        }
        QualityRepository.save_run_history(run_record)

        # Persist exceptions
        exc_records = [
            {
                "exception_id": e.exception_id,
                "run_id": e.run_id,
                "batch_id": e.batch_id,
                "rule_id": e.rule_id,
                "record_reference": e.record_reference,
                "field_name": e.field_name,
                "invalid_value": e.invalid_value,
                "severity": e.severity,
                "issue_description": e.issue_description,
                "detected_at": e.detected_at,
            }
            for e in all_exceptions
        ]
        QualityRepository.save_exceptions(exc_records)

        logger.info(
            "Validation run %s completed: %d records, %d exceptions, score=%.2f%% in %d ms",
            run_id, metrics["total_records"], len(all_exceptions), metrics["overall_quality_score"], duration_ms
        )

        return run_id, metrics, all_exceptions
