"""DataGuard Validation Rules Implementation.

Contains individual rule logic (DQ001 to DQ017). Each rule evaluates a batch
DataFrame and returns a list of QualityException objects.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Set
import numpy as np
import pandas as pd

from dataguard.quality.exceptions import QualityException

ALLOWED_TYPES = {"DEPOSIT", "WITHDRAWAL", "PAYMENT", "REFUND", "TRANSFER", "FEE", "REVERSAL"}
ALLOWED_STATUSES = {"COMPLETED", "PENDING", "FAILED", "REVERSED", "CANCELLED"}


class QualityRuleEvaluator:
    """Evaluates business and technical data quality rules against transactions."""

    def __init__(self, run_id: str, batch_id: str, valid_accounts: Set[str] | None = None):
        self.run_id = run_id
        self.batch_id = batch_id
        self.valid_accounts = valid_accounts or set()

    def get_ref(self, row: pd.Series) -> str:
        tx_id = str(row.get("transaction_id", "")).strip()
        if tx_id:
            return tx_id
        src_id = str(row.get("source_record_id", "")).strip()
        if src_id:
            return src_id
        return f"ROW_INDEX_{row.name}"

    # -------------------------------------------------------------------------
    # Completeness (DQ001 - DQ006)
    # -------------------------------------------------------------------------
    def evaluate_dq001(self, df: pd.DataFrame) -> List[QualityException]:
        """Missing Transaction Identifier."""
        exceptions = []
        mask = df["transaction_id"].isna() | (df["transaction_id"].astype(str).str.strip() == "")
        for _, row in df[mask].iterrows():
            exceptions.append(QualityException(
                run_id=self.run_id, batch_id=self.batch_id, rule_id="DQ001",
                record_reference=self.get_ref(row), field_name="transaction_id",
                invalid_value=None, severity="CRITICAL",
                issue_description="Missing mandatory transaction identifier"
            ))
        return exceptions

    def evaluate_dq002(self, df: pd.DataFrame) -> List[QualityException]:
        """Missing Account Identifier."""
        exceptions = []
        mask = df["account_id"].isna() | (df["account_id"].astype(str).str.strip() == "")
        for _, row in df[mask].iterrows():
            exceptions.append(QualityException(
                run_id=self.run_id, batch_id=self.batch_id, rule_id="DQ002",
                record_reference=self.get_ref(row), field_name="account_id",
                invalid_value=None, severity="CRITICAL",
                issue_description="Missing mandatory account identifier"
            ))
        return exceptions

    def evaluate_dq003(self, df: pd.DataFrame) -> List[QualityException]:
        """Missing Transaction Date."""
        exceptions = []
        mask = df["transaction_date"].isna()
        for _, row in df[mask].iterrows():
            raw_val = row.get("raw_transaction_date")
            exceptions.append(QualityException(
                run_id=self.run_id, batch_id=self.batch_id, rule_id="DQ003",
                record_reference=self.get_ref(row), field_name="transaction_date",
                invalid_value=str(raw_val) if raw_val else None, severity="HIGH",
                issue_description="Missing or unparseable transaction date"
            ))
        return exceptions

    def evaluate_dq004(self, df: pd.DataFrame) -> List[QualityException]:
        """Missing Monetary Amount."""
        exceptions = []
        mask = df["amount"].isna()
        for _, row in df[mask].iterrows():
            raw_val = row.get("raw_amount")
            exceptions.append(QualityException(
                run_id=self.run_id, batch_id=self.batch_id, rule_id="DQ004",
                record_reference=self.get_ref(row), field_name="amount",
                invalid_value=str(raw_val) if raw_val else None, severity="CRITICAL",
                issue_description="Missing or unparseable monetary amount"
            ))
        return exceptions

    def evaluate_dq005(self, df: pd.DataFrame) -> List[QualityException]:
        """Missing Currency Code."""
        exceptions = []
        mask = df["currency"].isna() | (df["currency"].astype(str).str.strip() == "")
        for _, row in df[mask].iterrows():
            exceptions.append(QualityException(
                run_id=self.run_id, batch_id=self.batch_id, rule_id="DQ005",
                record_reference=self.get_ref(row), field_name="currency",
                invalid_value=None, severity="HIGH",
                issue_description="Missing mandatory currency code"
            ))
        return exceptions

    def evaluate_dq006(self, df: pd.DataFrame) -> List[QualityException]:
        """Missing Transaction Status."""
        exceptions = []
        mask = df["transaction_status"].isna() | (df["transaction_status"].astype(str).str.strip() == "")
        for _, row in df[mask].iterrows():
            exceptions.append(QualityException(
                run_id=self.run_id, batch_id=self.batch_id, rule_id="DQ006",
                record_reference=self.get_ref(row), field_name="transaction_status",
                invalid_value=None, severity="HIGH",
                issue_description="Missing mandatory transaction status"
            ))
        return exceptions

    # -------------------------------------------------------------------------
    # Uniqueness (DQ007 - DQ009)
    # -------------------------------------------------------------------------
    def evaluate_dq007(self, df: pd.DataFrame) -> List[QualityException]:
        """Exact Duplicate Source Record."""
        exceptions = []
        if "record_hash" not in df.columns:
            return exceptions
        dup_mask = df.duplicated(subset=["record_hash"], keep="first")
        for _, row in df[dup_mask].iterrows():
            exceptions.append(QualityException(
                run_id=self.run_id, batch_id=self.batch_id, rule_id="DQ007",
                record_reference=self.get_ref(row), field_name="record_hash",
                invalid_value=str(row["record_hash"]), severity="HIGH",
                issue_description="Exact duplicate source payload ingested repeatedly"
            ))
        return exceptions

    def evaluate_dq008(self, df: pd.DataFrame) -> List[QualityException]:
        """Duplicate Transaction Identifier."""
        exceptions = []
        valid_ids = df[df["transaction_id"].str.strip() != ""]
        dup_mask = valid_ids.duplicated(subset=["transaction_id"], keep="first")
        for _, row in valid_ids[dup_mask].iterrows():
            exceptions.append(QualityException(
                run_id=self.run_id, batch_id=self.batch_id, rule_id="DQ008",
                record_reference=self.get_ref(row), field_name="transaction_id",
                invalid_value=str(row["transaction_id"]), severity="CRITICAL",
                issue_description="Duplicate transaction identifier found within batch"
            ))
        return exceptions

    def evaluate_dq009(self, df: pd.DataFrame) -> List[QualityException]:
        """Potential Business Duplicate."""
        exceptions = []
        subset_cols = ["account_id", "amount", "transaction_date", "transaction_type"]
        valid_rows = df.dropna(subset=subset_cols)
        # Exclude rows where amount or account_id is blank string
        valid_rows = valid_rows[(valid_rows["account_id"].str.strip() != "")]
        dup_mask = valid_rows.duplicated(subset=subset_cols, keep="first")
        for _, row in valid_rows[dup_mask].iterrows():
            val = f"account={row['account_id']}, amount={row['amount']}, date={row['transaction_date']}, type={row['transaction_type']}"
            exceptions.append(QualityException(
                run_id=self.run_id, batch_id=self.batch_id, rule_id="DQ009",
                record_reference=self.get_ref(row),
                field_name="account_id,amount,transaction_date,transaction_type",
                invalid_value=val, severity="MEDIUM",
                issue_description="Potential business duplicate: matching account, amount, date, and transaction type"
            ))
        return exceptions

    # -------------------------------------------------------------------------
    # Monetary Validity (DQ010 - DQ012)
    # -------------------------------------------------------------------------
    def evaluate_dq010(self, df: pd.DataFrame) -> List[QualityException]:
        """Invalid Decimal Precision."""
        exceptions = []
        for _, row in df.iterrows():
            raw_amt = str(row.get("raw_amount", "")).strip()
            if not raw_amt:
                continue
            if "." in raw_amt:
                decimals = len(raw_amt.split(".")[1])
                curr = str(row.get("currency", "")).upper()
                if curr in ["USD", "EUR", "GBP"] and decimals > 2:
                    exceptions.append(QualityException(
                        run_id=self.run_id, batch_id=self.batch_id, rule_id="DQ010",
                        record_reference=self.get_ref(row), field_name="amount",
                        invalid_value=raw_amt, severity="MEDIUM",
                        issue_description=f"Amount exceeds 2-decimal precision ({decimals} decimals): {raw_amt}"
                    ))
        return exceptions

    def evaluate_dq011(self, df: pd.DataFrame) -> List[QualityException]:
        """Sign Inconsistency for Transaction Type."""
        exceptions = []
        # Deposits and standard payments must be strictly positive (> 0)
        mask = (
            df["transaction_type"].isin(["DEPOSIT", "PAYMENT", "TRANSFER"]) &
            df["amount"].notna() &
            (df["amount"] <= 0.0)
        )
        for _, row in df[mask].iterrows():
            exceptions.append(QualityException(
                run_id=self.run_id, batch_id=self.batch_id, rule_id="DQ011",
                record_reference=self.get_ref(row), field_name="amount,transaction_type",
                invalid_value=f"type={row['transaction_type']}, amount={row['amount']}",
                severity="HIGH",
                issue_description=f"Transaction type {row['transaction_type']} cannot have non-positive amount ({row['amount']})"
            ))
        return exceptions

    def evaluate_dq012(self, df: pd.DataFrame) -> List[QualityException]:
        """Extreme Outlier Amount."""
        exceptions = []
        mask = df["amount"].notna() & (df["amount"].abs() > 1000000.00)
        for _, row in df[mask].iterrows():
            exceptions.append(QualityException(
                run_id=self.run_id, batch_id=self.batch_id, rule_id="DQ012",
                record_reference=self.get_ref(row), field_name="amount",
                invalid_value=str(row["amount"]), severity="MEDIUM",
                issue_description=f"Transaction amount exceeds $1,000,000 threshold: {row['amount']}"
            ))
        return exceptions

    # -------------------------------------------------------------------------
    # Timeliness / Date Checks (DQ013 - DQ014)
    # -------------------------------------------------------------------------
    def evaluate_dq013(self, df: pd.DataFrame) -> List[QualityException]:
        """Future-Dated Transaction."""
        exceptions = []
        today = date.today()
        for _, row in df.iterrows():
            tx_date = row.get("transaction_date")
            if tx_date and isinstance(tx_date, date) and tx_date > today:
                exceptions.append(QualityException(
                    run_id=self.run_id, batch_id=self.batch_id, rule_id="DQ013",
                    record_reference=self.get_ref(row), field_name="transaction_date",
                    invalid_value=str(tx_date), severity="HIGH",
                    issue_description=f"Transaction date is in the future relative to ingestion: {tx_date}"
                ))
        return exceptions

    def evaluate_dq014(self, df: pd.DataFrame) -> List[QualityException]:
        """Excessive Ingestion Latency."""
        exceptions = []
        cutoff = date.today() - timedelta(days=90)
        for _, row in df.iterrows():
            tx_date = row.get("transaction_date")
            if tx_date and isinstance(tx_date, date) and tx_date < cutoff:
                exceptions.append(QualityException(
                    run_id=self.run_id, batch_id=self.batch_id, rule_id="DQ014",
                    record_reference=self.get_ref(row), field_name="transaction_date",
                    invalid_value=str(tx_date), severity="LOW",
                    issue_description=f"Transaction date is over 90 days older than ingestion ({tx_date})"
                ))
        return exceptions

    # -------------------------------------------------------------------------
    # Referential Integrity (DQ015)
    # -------------------------------------------------------------------------
    def evaluate_dq015(self, df: pd.DataFrame) -> List[QualityException]:
        """Unknown Account Reference."""
        exceptions = []
        if not self.valid_accounts:
            return exceptions
        for _, row in df.iterrows():
            acc_id = str(row.get("account_id", "")).strip()
            if acc_id and acc_id not in self.valid_accounts:
                exceptions.append(QualityException(
                    run_id=self.run_id, batch_id=self.batch_id, rule_id="DQ015",
                    record_reference=self.get_ref(row), field_name="account_id",
                    invalid_value=acc_id, severity="CRITICAL",
                    issue_description=f"Account ID '{acc_id}' not found in account master dimension"
                ))
        return exceptions

    # -------------------------------------------------------------------------
    # Allowed Values & Consistency (DQ016 - DQ017)
    # -------------------------------------------------------------------------
    def evaluate_dq016(self, df: pd.DataFrame) -> List[QualityException]:
        """Invalid Transaction Type or Status."""
        exceptions = []
        for _, row in df.iterrows():
            tt = str(row.get("transaction_type", "")).strip().upper()
            ts = str(row.get("transaction_status", "")).strip().upper()
            if tt and tt not in ALLOWED_TYPES:
                exceptions.append(QualityException(
                    run_id=self.run_id, batch_id=self.batch_id, rule_id="DQ016",
                    record_reference=self.get_ref(row), field_name="transaction_type",
                    invalid_value=tt, severity="HIGH",
                    issue_description=f"Unrecognized transaction type: '{tt}'"
                ))
            if ts and ts not in ALLOWED_STATUSES:
                exceptions.append(QualityException(
                    run_id=self.run_id, batch_id=self.batch_id, rule_id="DQ016",
                    record_reference=self.get_ref(row), field_name="transaction_status",
                    invalid_value=ts, severity="HIGH",
                    issue_description=f"Unrecognized transaction status: '{ts}'"
                ))
        return exceptions

    def evaluate_dq017(self, df: pd.DataFrame) -> List[QualityException]:
        """Reversal Missing Original Reference."""
        exceptions = []
        mask = (df["transaction_type"] == "REVERSAL") & (
            df["reference_id"].isna() | (df["reference_id"].astype(str).str.strip() == "")
        )
        for _, row in df[mask].iterrows():
            exceptions.append(QualityException(
                run_id=self.run_id, batch_id=self.batch_id, rule_id="DQ017",
                record_reference=self.get_ref(row), field_name="reference_id,transaction_type",
                invalid_value=None, severity="HIGH",
                issue_description="Reversal transaction requires originating reference_id"
            ))
        return exceptions
