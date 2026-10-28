"""DataGuard Ingestion Structural Validation."""

from typing import List, Tuple


def validate_file_structure(headers: List[str], required_columns: List[str]) -> Tuple[bool, List[str], List[str]]:
    """
    Validates CSV header structure against required schema.
    Returns:
        (is_valid, missing_columns, unexpected_columns)
    """
    header_set = set(headers)
    required_set = set(required_columns)

    missing = sorted(list(required_set - header_set))
    unexpected = sorted(list(header_set - required_set))

    is_valid = len(missing) == 0
    return is_valid, missing, unexpected
