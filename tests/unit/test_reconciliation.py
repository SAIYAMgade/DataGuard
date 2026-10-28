"""Unit Tests for DataGuard Financial Reconciliation Engine."""

import pandas as pd
import pytest

from dataguard.reconciliation.comparisons import (
    reconcile_aggregates_by_currency,
    reconcile_records,
)


def test_reconcile_exact_match():
    src = pd.DataFrame([{
        "transaction_id": "T1", "amount": 100.00, "currency": "USD"
    }])
    tgt = pd.DataFrame([{
        "ledger_id": "T1", "amount": 100.00, "currency": "USD"
    }])
    results = reconcile_records(src, tgt, tolerance=0.01)
    assert len(results) == 1
    assert results[0]["match_status"] == "EXACT_MATCH"
    assert results[0]["signed_difference"] == 0.00
    assert results[0]["absolute_difference"] == 0.00


def test_reconcile_within_tolerance():
    src = pd.DataFrame([{
        "transaction_id": "T1", "amount": 100.005, "currency": "USD"
    }])
    tgt = pd.DataFrame([{
        "ledger_id": "T1", "amount": 100.000, "currency": "USD"
    }])
    results = reconcile_records(src, tgt, tolerance=0.01)
    assert len(results) == 1
    assert results[0]["match_status"] == "WITHIN_TOLERANCE"
    assert round(results[0]["signed_difference"], 3) == 0.005


def test_reconcile_amount_mismatch():
    src = pd.DataFrame([{
        "transaction_id": "T1", "amount": 150.00, "currency": "USD"
    }])
    tgt = pd.DataFrame([{
        "ledger_id": "T1", "amount": 100.00, "currency": "USD"
    }])
    results = reconcile_records(src, tgt, tolerance=0.01)
    assert len(results) == 1
    assert results[0]["match_status"] == "AMOUNT_MISMATCH"
    assert results[0]["signed_difference"] == 50.00


def test_reconcile_source_only_and_target_only():
    src = pd.DataFrame([{
        "transaction_id": "SRC_ONLY", "amount": 25.00, "currency": "EUR"
    }])
    tgt = pd.DataFrame([{
        "ledger_id": "TGT_ONLY", "amount": 40.00, "currency": "EUR"
    }])
    results = reconcile_records(src, tgt, tolerance=0.01)
    assert len(results) == 2
    status_map = {r["source_id"] or r["target_id"]: r["match_status"] for r in results}
    assert status_map["SRC_ONLY"] == "SOURCE_ONLY"
    assert status_map["TGT_ONLY"] == "TARGET_ONLY"


def test_multi_currency_aggregate_isolation():
    src = pd.DataFrame([
        {"currency": "USD", "amount": 100.00},
        {"currency": "USD", "amount": 200.00},
        {"currency": "EUR", "amount": 500.00},
    ])
    tgt = pd.DataFrame([
        {"currency": "USD", "amount": 300.00},
        {"currency": "EUR", "amount": 480.00},
    ])
    aggregates = reconcile_aggregates_by_currency(src, tgt)
    assert len(aggregates) == 2

    curr_map = {a["currency"]: a for a in aggregates}
    # USD: 300 vs 300 => exact match
    assert curr_map["USD"]["source_amount"] == 300.00
    assert curr_map["USD"]["target_amount"] == 300.00
    assert curr_map["USD"]["signed_difference"] == 0.00
    assert curr_map["USD"]["match_status"] == "EXACT_MATCH"

    # EUR: 500 vs 480 => mismatch of 20
    assert curr_map["EUR"]["source_amount"] == 500.00
    assert curr_map["EUR"]["target_amount"] == 480.00
    assert curr_map["EUR"]["signed_difference"] == 20.00
    assert curr_map["EUR"]["match_status"] == "AMOUNT_MISMATCH"


def test_empty_datasets_reconciliation():
    src = pd.DataFrame(columns=["transaction_id", "amount", "currency"])
    tgt = pd.DataFrame(columns=["ledger_id", "amount", "currency"])
    rec_res = reconcile_records(src, tgt)
    assert len(rec_res) == 0
    agg_res = reconcile_aggregates_by_currency(src, tgt)
    assert len(agg_res) == 0
