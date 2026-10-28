"""DataGuard Quality Metrics Engine.

Implements mathematically defensible quality scoring across the four core dimensions:
- Completeness (25% weight)
- Validity (35% weight)
- Uniqueness (20% weight)
- Integrity (20% weight)

Overall Quality Score = 0.25 * Completeness + 0.35 * Validity + 0.20 * Uniqueness + 0.20 * Integrity
"""

from typing import Dict, List, Set
import pandas as pd
from dataguard.quality.exceptions import QualityException


def calculate_quality_metrics(
    df: pd.DataFrame,
    exceptions: List[QualityException],
    valid_accounts: Set[str] | None = None
) -> Dict[str, float]:
    """
    Calculates dimension scores (0.0 to 100.0) and overall weighted score.
    """
    total_records = len(df)
    if total_records == 0:
        return {
            "completeness_score": 100.0,
            "validity_score": 100.0,
            "uniqueness_score": 100.0,
            "integrity_score": 100.0,
            "overall_quality_score": 100.0,
            "total_records": 0,
            "passed_records": 0,
            "failed_records": 0,
            "total_exceptions": 0,
        }

    # Group exceptions by rule dimension
    comp_rules = {"DQ001", "DQ002", "DQ003", "DQ004", "DQ005", "DQ006"}
    uniq_rules = {"DQ007", "DQ008", "DQ009"}
    valid_rules = {"DQ010", "DQ011", "DQ012", "DQ013", "DQ014", "DQ016", "DQ017"}
    integ_rules = {"DQ015"}

    comp_failures = len({e.record_reference for e in exceptions if e.rule_id in comp_rules})
    uniq_failures = len({e.record_reference for e in exceptions if e.rule_id in uniq_rules})
    valid_failures = len({e.record_reference for e in exceptions if e.rule_id in valid_rules})
    integ_failures = len({e.record_reference for e in exceptions if e.rule_id in integ_rules})

    all_failed_refs = {e.record_reference for e in exceptions}
    failed_record_count = len(all_failed_refs)
    passed_record_count = max(0, total_records - failed_record_count)

    completeness_score = round(max(0.0, (1.0 - (comp_failures / total_records))) * 100.0, 2)
    uniqueness_score = round(max(0.0, (1.0 - (uniq_failures / total_records))) * 100.0, 2)
    validity_score = round(max(0.0, (1.0 - (valid_failures / total_records))) * 100.0, 2)
    integrity_score = round(max(0.0, (1.0 - (integ_failures / total_records))) * 100.0, 2)

    # Weighted Composite Score
    overall_quality_score = round(
        (0.25 * completeness_score) +
        (0.35 * validity_score) +
        (0.20 * uniqueness_score) +
        (0.20 * integrity_score),
        2
    )

    return {
        "completeness_score": completeness_score,
        "validity_score": validity_score,
        "uniqueness_score": uniqueness_score,
        "integrity_score": integrity_score,
        "overall_quality_score": overall_quality_score,
        "total_records": total_records,
        "passed_records": passed_record_count,
        "failed_records": failed_record_count,
        "total_exceptions": len(exceptions),
    }
