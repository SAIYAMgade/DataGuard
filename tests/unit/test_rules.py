"""Unit Tests for DataGuard Quality Rules (DQ001 - DQ017)."""

from datetime import date, timedelta
import pandas as pd
import pytest

from dataguard.quality.rules import QualityRuleEvaluator


def test_clean_records_pass_all_rules(sample_valid_df, sample_valid_accounts):
    evaluator = QualityRuleEvaluator("RUN_TEST", "BATCH_TEST", sample_valid_accounts)
    assert len(evaluator.evaluate_dq001(sample_valid_df)) == 0
    assert len(evaluator.evaluate_dq002(sample_valid_df)) == 0
    assert len(evaluator.evaluate_dq003(sample_valid_df)) == 0
    assert len(evaluator.evaluate_dq004(sample_valid_df)) == 0
    assert len(evaluator.evaluate_dq005(sample_valid_df)) == 0
    assert len(evaluator.evaluate_dq006(sample_valid_df)) == 0
    assert len(evaluator.evaluate_dq007(sample_valid_df)) == 0
    assert len(evaluator.evaluate_dq008(sample_valid_df)) == 0
    assert len(evaluator.evaluate_dq009(sample_valid_df)) == 0
    assert len(evaluator.evaluate_dq010(sample_valid_df)) == 0
    assert len(evaluator.evaluate_dq011(sample_valid_df)) == 0
    assert len(evaluator.evaluate_dq012(sample_valid_df)) == 0
    assert len(evaluator.evaluate_dq013(sample_valid_df)) == 0
    assert len(evaluator.evaluate_dq014(sample_valid_df)) == 0
    assert len(evaluator.evaluate_dq015(sample_valid_df)) == 0
    assert len(evaluator.evaluate_dq016(sample_valid_df)) == 0
    assert len(evaluator.evaluate_dq017(sample_valid_df)) == 0


def test_dq001_missing_transaction_id(sample_valid_df):
    evaluator = QualityRuleEvaluator("RUN_TEST", "BATCH_TEST")
    df = sample_valid_df.copy()
    df.loc[0, "transaction_id"] = ""
    exceptions = evaluator.evaluate_dq001(df)
    assert len(exceptions) == 1
    assert exceptions[0].rule_id == "DQ001"
    assert exceptions[0].severity == "CRITICAL"


def test_dq002_missing_account_id(sample_valid_df):
    evaluator = QualityRuleEvaluator("RUN_TEST", "BATCH_TEST")
    df = sample_valid_df.copy()
    df.loc[1, "account_id"] = None
    exceptions = evaluator.evaluate_dq002(df)
    assert len(exceptions) == 1
    assert exceptions[0].rule_id == "DQ002"
    assert exceptions[0].record_reference == "TXN_002"


def test_dq004_missing_amount(sample_valid_df):
    evaluator = QualityRuleEvaluator("RUN_TEST", "BATCH_TEST")
    df = sample_valid_df.copy()
    df.loc[0, "amount"] = None
    exceptions = evaluator.evaluate_dq004(df)
    assert len(exceptions) == 1
    assert exceptions[0].rule_id == "DQ004"


def test_dq007_exact_duplicate_payload(sample_valid_df):
    evaluator = QualityRuleEvaluator("RUN_TEST", "BATCH_TEST")
    dup_row = sample_valid_df.iloc[[0]].copy()
    df = pd.concat([sample_valid_df, dup_row], ignore_index=True)
    exceptions = evaluator.evaluate_dq007(df)
    assert len(exceptions) == 1
    assert exceptions[0].rule_id == "DQ007"
    assert exceptions[0].severity == "HIGH"


def test_dq008_duplicate_transaction_id(sample_valid_df):
    evaluator = QualityRuleEvaluator("RUN_TEST", "BATCH_TEST")
    dup_id_row = sample_valid_df.iloc[[0]].copy()
    dup_id_row["amount"] = 999.00
    df = pd.concat([sample_valid_df, dup_id_row], ignore_index=True)
    exceptions = evaluator.evaluate_dq008(df)
    assert len(exceptions) == 1
    assert exceptions[0].rule_id == "DQ008"


def test_dq009_potential_business_duplicate(sample_valid_df):
    evaluator = QualityRuleEvaluator("RUN_TEST", "BATCH_TEST")
    biz_dup_row = sample_valid_df.iloc[[0]].copy()
    biz_dup_row["transaction_id"] = "TXN_NEW_UNIQUE"
    df = pd.concat([sample_valid_df, biz_dup_row], ignore_index=True)
    exceptions = evaluator.evaluate_dq009(df)
    assert len(exceptions) == 1
    assert exceptions[0].rule_id == "DQ009"
    assert exceptions[0].severity == "MEDIUM"


def test_dq010_invalid_decimal_precision(sample_valid_df):
    evaluator = QualityRuleEvaluator("RUN_TEST", "BATCH_TEST")
    df = sample_valid_df.copy()
    df.loc[0, "raw_amount"] = "250.1234"
    exceptions = evaluator.evaluate_dq010(df)
    assert len(exceptions) == 1
    assert exceptions[0].rule_id == "DQ010"
    assert "250.1234" in str(exceptions[0].invalid_value)


def test_dq011_sign_inconsistency(sample_valid_df):
    evaluator = QualityRuleEvaluator("RUN_TEST", "BATCH_TEST")
    df = sample_valid_df.copy()
    df.loc[0, "transaction_type"] = "DEPOSIT"
    df.loc[0, "amount"] = -100.00
    exceptions = evaluator.evaluate_dq011(df)
    assert len(exceptions) == 1
    assert exceptions[0].rule_id == "DQ011"
    assert exceptions[0].severity == "HIGH"


def test_dq012_extreme_outlier_amount(sample_valid_df):
    evaluator = QualityRuleEvaluator("RUN_TEST", "BATCH_TEST")
    df = sample_valid_df.copy()
    df.loc[0, "amount"] = 5000000.00
    exceptions = evaluator.evaluate_dq012(df)
    assert len(exceptions) == 1
    assert exceptions[0].rule_id == "DQ012"


def test_dq013_future_date(sample_valid_df):
    evaluator = QualityRuleEvaluator("RUN_TEST", "BATCH_TEST")
    df = sample_valid_df.copy()
    df.loc[0, "transaction_date"] = date.today() + timedelta(days=10)
    exceptions = evaluator.evaluate_dq013(df)
    assert len(exceptions) == 1
    assert exceptions[0].rule_id == "DQ013"


def test_dq014_excessive_latency(sample_valid_df):
    evaluator = QualityRuleEvaluator("RUN_TEST", "BATCH_TEST")
    df = sample_valid_df.copy()
    df.loc[0, "transaction_date"] = date.today() - timedelta(days=120)
    exceptions = evaluator.evaluate_dq014(df)
    assert len(exceptions) == 1
    assert exceptions[0].rule_id == "DQ014"


def test_dq015_unknown_account_reference(sample_valid_df, sample_valid_accounts):
    evaluator = QualityRuleEvaluator("RUN_TEST", "BATCH_TEST", sample_valid_accounts)
    df = sample_valid_df.copy()
    df.loc[0, "account_id"] = "ACC_UNKNOWN_9999"
    exceptions = evaluator.evaluate_dq015(df)
    assert len(exceptions) == 1
    assert exceptions[0].rule_id == "DQ015"
    assert exceptions[0].severity == "CRITICAL"


def test_dq016_invalid_transaction_type_or_status(sample_valid_df):
    evaluator = QualityRuleEvaluator("RUN_TEST", "BATCH_TEST")
    df = sample_valid_df.copy()
    df.loc[0, "transaction_type"] = "CRYPTO_MINING"
    df.loc[1, "transaction_status"] = "PENDING_UNKNOWN"
    exceptions = evaluator.evaluate_dq016(df)
    assert len(exceptions) == 2
    assert all(e.rule_id == "DQ016" for e in exceptions)


def test_dq017_reversal_missing_original_reference(sample_valid_df):
    evaluator = QualityRuleEvaluator("RUN_TEST", "BATCH_TEST")
    df = sample_valid_df.copy()
    df.loc[0, "transaction_type"] = "REVERSAL"
    df.loc[0, "reference_id"] = ""
    exceptions = evaluator.evaluate_dq017(df)
    assert len(exceptions) == 1
    assert exceptions[0].rule_id == "DQ017"
