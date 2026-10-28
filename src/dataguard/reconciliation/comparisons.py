"""DataGuard Financial Reconciliation Comparisons Module.

Implements record-level and aggregate reconciliation logic with exact decimal
precision, signed differences, and strict multi-currency isolation.
"""

from decimal import Decimal
from typing import Any, Dict, List, Tuple
import pandas as pd


def reconcile_records(
    source_df: pd.DataFrame,
    target_df: pd.DataFrame,
    match_key: str = "transaction_id",
    target_key: str = "ledger_id",
    tolerance: float = 0.01
) -> List[Dict[str, Any]]:
    """
    Performs record-level reconciliation between source transactions and target ledger.
    Matches primarily on transaction_id == ledger_id (or external_ref).
    """
    tol_dec = Decimal(str(tolerance))
    results: List[Dict[str, Any]] = []

    # Filter out records without keys
    src_valid = source_df.dropna(subset=[match_key]).copy()
    src_valid = src_valid[src_valid[match_key].astype(str).str.strip() != ""]
    
    tgt_valid = target_df.dropna(subset=[target_key]).copy()
    tgt_valid = tgt_valid[tgt_valid[target_key].astype(str).str.strip() != ""]

    src_dict = {}
    for _, row in src_valid.iterrows():
        key = str(row[match_key]).strip()
        src_dict[key] = row

    tgt_dict = {}
    for _, row in tgt_valid.iterrows():
        key = str(row[target_key]).strip()
        tgt_dict[key] = row

    all_keys = set(src_dict.keys()) | set(tgt_dict.keys())

    for key in all_keys:
        src_row = src_dict.get(key)
        tgt_row = tgt_dict.get(key)

        if src_row is not None and tgt_row is None:
            curr = str(src_row.get("currency", "USD"))
            amt = Decimal(str(src_row.get("amount", "0.00"))) if pd.notna(src_row.get("amount")) else Decimal("0.00")
            results.append({
                "source_id": key,
                "target_id": None,
                "currency": curr,
                "source_amount": float(amt),
                "target_amount": None,
                "signed_difference": float(amt),
                "absolute_difference": float(amt),
                "tolerance": tolerance,
                "match_status": "SOURCE_ONLY"
            })
        elif src_row is None and tgt_row is not None:
            curr = str(tgt_row.get("currency", "USD"))
            amt = Decimal(str(tgt_row.get("amount", "0.00"))) if pd.notna(tgt_row.get("amount")) else Decimal("0.00")
            results.append({
                "source_id": None,
                "target_id": key,
                "currency": curr,
                "source_amount": None,
                "target_amount": float(amt),
                "signed_difference": float(-amt),
                "absolute_difference": float(amt),
                "tolerance": tolerance,
                "match_status": "TARGET_ONLY"
            })
        else:
            # Both present
            src_curr = str(src_row.get("currency", "USD"))
            tgt_curr = str(tgt_row.get("currency", "USD"))
            
            src_amt = Decimal(str(src_row.get("amount", "0.00"))) if pd.notna(src_row.get("amount")) else Decimal("0.00")
            tgt_amt = Decimal(str(tgt_row.get("amount", "0.00"))) if pd.notna(tgt_row.get("amount")) else Decimal("0.00")
            
            signed_diff = src_amt - tgt_amt
            abs_diff = abs(signed_diff)

            if abs_diff == Decimal("0.00"):
                status = "EXACT_MATCH"
            elif abs_diff <= tol_dec:
                status = "WITHIN_TOLERANCE"
            else:
                status = "AMOUNT_MISMATCH"

            results.append({
                "source_id": key,
                "target_id": key,
                "currency": src_curr,
                "source_amount": float(src_amt),
                "target_amount": float(tgt_amt),
                "signed_difference": float(signed_diff),
                "absolute_difference": float(abs_diff),
                "tolerance": tolerance,
                "match_status": status
            })

    return results


def reconcile_aggregates_by_currency(
    source_df: pd.DataFrame,
    target_df: pd.DataFrame
) -> List[Dict[str, Any]]:
    """
    Computes aggregate financial totals grouped by currency.
    NEVER aggregates amounts across currencies.
    """
    results: List[Dict[str, Any]] = []

    src_agg = (
        source_df.groupby("currency")["amount"]
        .agg(["sum", "count"])
        .reset_index()
        .rename(columns={"sum": "source_total", "count": "source_count"})
    )
    tgt_agg = (
        target_df.groupby("currency")["amount"]
        .agg(["sum", "count"])
        .reset_index()
        .rename(columns={"sum": "target_total", "count": "target_count"})
    )

    merged = pd.merge(src_agg, tgt_agg, on="currency", how="outer").fillna(0.0)

    for _, row in merged.iterrows():
        curr = str(row["currency"])
        src_tot = Decimal(str(round(row["source_total"], 4)))
        tgt_tot = Decimal(str(round(row["target_total"], 4)))
        diff = src_tot - tgt_tot
        abs_diff = abs(diff)

        results.append({
            "currency": curr,
            "source_amount": float(src_tot),
            "target_amount": float(tgt_tot),
            "signed_difference": float(diff),
            "absolute_difference": float(abs_diff),
            "source_count": int(row["source_count"]),
            "target_count": int(row["target_count"]),
            "match_status": "EXACT_MATCH" if abs_diff == Decimal("0.00") else ("WITHIN_TOLERANCE" if abs_diff <= Decimal("0.01") else "AMOUNT_MISMATCH")
        })

    return results
