"""DataGuard Data Standardization and Normalization Module.

Provides deterministic type parsing and formatting without silent data loss.
Raw source values are preserved alongside parsed outputs.
"""

from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List
import pandas as pd


def safe_parse_decimal(value: Any) -> Decimal | None:
    """Attempts to parse value into Decimal. Returns None if invalid or blank."""
    if value is None:
        return None
    val_str = str(value).strip().replace(",", "")
    if not val_str:
        return None
    try:
        return Decimal(val_str)
    except (InvalidOperation, ValueError):
        return None


def safe_parse_date(value: Any) -> date | None:
    """Attempts to parse ISO or common date formats. Returns None if invalid or blank."""
    if value is None:
        return None
    val_str = str(value).strip()
    if not val_str:
        return None
    formats = ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"]
    for fmt in formats:
        try:
            return datetime.strptime(val_str, fmt).date()
        except ValueError:
            continue
    return None


def standardize_records(raw_records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Transforms raw dictionaries into a standardized DataFrame suitable for
    staging and validation, preserving original invalid strings where parsing fails.
    """
    rows = []
    for r in raw_records:
        parsed_amount = safe_parse_decimal(r.get("amount"))
        parsed_date = safe_parse_date(r.get("transaction_date"))

        row = {
            "source_record_id": r.get("source_record_id", ""),
            "source_system": (r.get("source_system") or "UNKNOWN").strip().upper(),
            "transaction_id": str(r.get("transaction_id", "")).strip(),
            "account_id": str(r.get("account_id", "")).strip(),
            "customer_id": str(r.get("customer_id", "")).strip(),
            "transaction_date": parsed_date,
            "raw_transaction_date": r.get("transaction_date"),
            "transaction_type": (r.get("transaction_type") or "").strip().upper(),
            "amount": float(parsed_amount) if parsed_amount is not None else None,
            "raw_amount": r.get("amount"),
            "currency": (r.get("currency") or "").strip().upper(),
            "transaction_status": (r.get("transaction_status") or "").strip().upper(),
            "reference_id": str(r.get("reference_id", "")).strip(),
            "description": r.get("description", ""),
            "record_hash": r.get("record_hash", "")
        }
        rows.append(row)

    return pd.DataFrame(rows)
