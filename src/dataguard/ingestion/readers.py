"""DataGuard File Readers Module.

Handles source file inspection, encoding detection, structural parsing,
and preservation of raw row data.
"""

import csv
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Tuple
import pandas as pd


def detect_file_encoding(file_path: Path) -> str:
    """Detects encoding by attempting reads in priority order."""
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                f.read(4096)
            return enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    return "utf-8"


def compute_record_hash(row: Dict[str, Any]) -> str:
    """Generates a deterministic SHA-256 fingerprint for a raw source record."""
    serialized = "|".join(f"{k}:{str(v).strip()}" for k, v in sorted(row.items()) if k != "record_hash")
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def read_transaction_csv(file_path: Path | str) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    """
    Reads a transaction CSV file into a list of raw dictionaries.
    Returns:
        (raw_records, headers, structural_errors)
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    encoding = detect_file_encoding(file_path)
    raw_records: List[Dict[str, Any]] = []
    structural_errors: List[str] = []

    with open(file_path, "r", encoding=encoding, errors="replace") as f:
        reader = csv.reader(f)
        try:
            headers = [h.strip() for h in next(reader)]
        except StopIteration:
            return [], [], ["Empty file encountered: no header row"]

        expected_col_count = len(headers)
        for line_num, row in enumerate(reader, start=2):
            if not row or all(c.strip() == "" for c in row):
                continue  # skip completely blank lines
            if len(row) != expected_col_count:
                structural_errors.append(
                    f"Line {line_num}: Column count mismatch (expected {expected_col_count}, got {len(row)})"
                )
                continue

            row_dict = dict(zip(headers, [c.strip() for c in row]))
            row_dict["record_hash"] = compute_record_hash(row_dict)
            raw_records.append(row_dict)

    return raw_records, headers, structural_errors
