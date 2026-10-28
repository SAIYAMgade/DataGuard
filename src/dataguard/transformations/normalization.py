"""DataGuard Normalization Utilities."""

def normalize_currency(currency_str: str | None) -> str | None:
    """Normalizes currency code to 3-letter uppercase ISO 4217."""
    if not currency_str:
        return None
    cleaned = currency_str.strip().upper()
    return cleaned if len(cleaned) == 3 else None


def normalize_status(status_str: str | None) -> str | None:
    """Normalizes status string to standard uppercase."""
    if not status_str:
        return None
    return status_str.strip().upper()
