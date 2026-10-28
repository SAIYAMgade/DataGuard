"""Unit Tests for DataGuard Quality Metrics Calculation."""

import pandas as pd
import pytest

from dataguard.quality.exceptions import QualityException
from dataguard.quality.metrics import calculate_quality_metrics


def test_empty_dataframe_metrics():
    df = pd.DataFrame()
    metrics = calculate_quality_metrics(df, [])
    assert metrics["overall_quality_score"] == 100.0
    assert metrics["total_records"] == 0
    assert metrics["passed_records"] == 0


def test_perfect_dataframe_metrics(sample_valid_df):
    metrics = calculate_quality_metrics(sample_valid_df, [])
    assert metrics["completeness_score"] == 100.0
    assert metrics["validity_score"] == 100.0
    assert metrics["uniqueness_score"] == 100.0
    assert metrics["integrity_score"] == 100.0
    assert metrics["overall_quality_score"] == 100.0
    assert metrics["passed_records"] == 3
    assert metrics["failed_records"] == 0


def test_weighted_formula_calculation(sample_valid_df):
    # Create 1 completeness exception on TXN_001
    exc = QualityException(
        run_id="R1", batch_id="B1", rule_id="DQ001",
        record_reference="TXN_001", field_name="transaction_id",
        invalid_value=None, severity="CRITICAL", issue_description="Missing ID"
    )
    metrics = calculate_quality_metrics(sample_valid_df, [exc])

    # 1 out of 3 failed for completeness => (1 - 1/3) * 100 = 66.67%
    assert metrics["completeness_score"] == 66.67
    assert metrics["validity_score"] == 100.0
    assert metrics["uniqueness_score"] == 100.0
    assert metrics["integrity_score"] == 100.0

    # Expected overall = 0.25*66.67 + 0.35*100 + 0.20*100 + 0.20*100 = 16.6675 + 35 + 20 + 20 = 91.67
    expected = round((0.25 * 66.67) + 35.0 + 20.0 + 20.0, 2)
    assert metrics["overall_quality_score"] == expected
