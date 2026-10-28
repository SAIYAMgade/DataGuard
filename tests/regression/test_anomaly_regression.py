"""Regression Tests for DataGuard Against Injected Anomaly Manifest."""

import json
from pathlib import Path
import pandas as pd
import pytest

from dataguard.ingestion.readers import read_transaction_csv
from dataguard.quality.engine import ValidationEngine, fetch_account_dimension_keys
from dataguard.transformations.standardization import standardize_records

BASE_DIR = Path(__file__).resolve().parent.parent.parent


@pytest.mark.regression
def test_all_injected_anomalies_detected_with_zero_false_negatives():
    manifest_path = BASE_DIR / "data" / "sample" / "anomaly_manifest.json"
    corrupted_csv = BASE_DIR / "data" / "sample" / "transactions_corrupted.csv"

    assert manifest_path.exists(), "Anomaly manifest must exist"
    assert corrupted_csv.exists(), "Corrupted transactions CSV must exist"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    raw_records, headers, _ = read_transaction_csv(corrupted_csv)
    df = standardize_records(raw_records)
    df["batch_id"] = "BATCH_REGRESSION_TEST"

    accounts = fetch_account_dimension_keys()
    from dataguard.database.repositories import IngestionRepository
    IngestionRepository.create_batch("BATCH_REGRESSION_TEST", "transactions_corrupted.csv", "TEST_SYS", len(df))

    val_engine = ValidationEngine()
    val_engine.sync_rule_catalog()
    run_id, metrics, exceptions = val_engine.run_validation("BATCH_REGRESSION_TEST", df, valid_accounts=accounts)

    # Index exceptions by (record_reference, rule_id)
    detected_pairs = {(e.record_reference, e.rule_id) for e in exceptions}

    missing_detections = []
    for expected in manifest:
        expected_ref = expected["record_reference"]
        expected_rule = expected["rule_id"]

        pair = (expected_ref, expected_rule)
        if pair not in detected_pairs:
            missing_detections.append(f"Missing detection for record '{expected_ref}' expected rule '{expected_rule}'")

    assert len(missing_detections) == 0, f"Regression failure: {missing_detections}"
    assert metrics["failed_records"] == 17
    assert metrics["total_exceptions"] >= len(manifest)
