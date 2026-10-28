"""Pytest Shared Fixtures for DataGuard."""

from datetime import date
from decimal import Decimal
import pandas as pd
import pytest


@pytest.fixture
def sample_valid_accounts():
    return {"ACC_0001", "ACC_0002", "ACC_0003", "ACC_0004"}


@pytest.fixture
def sample_valid_df():
    data = [
        {
            "transaction_id": "TXN_001",
            "source_record_id": "SRC_001",
            "account_id": "ACC_0001",
            "customer_id": "CUST_0001",
            "transaction_date": date(2026, 9, 1),
            "raw_transaction_date": "2026-09-01",
            "transaction_type": "DEPOSIT",
            "amount": 250.00,
            "raw_amount": "250.00",
            "currency": "USD",
            "transaction_status": "COMPLETED",
            "reference_id": None,
            "record_hash": "hash_001"
        },
        {
            "transaction_id": "TXN_002",
            "source_record_id": "SRC_002",
            "account_id": "ACC_0002",
            "customer_id": "CUST_0002",
            "transaction_date": date(2026, 9, 2),
            "raw_transaction_date": "2026-09-02",
            "transaction_type": "PAYMENT",
            "amount": 75.50,
            "raw_amount": "75.50",
            "currency": "USD",
            "transaction_status": "COMPLETED",
            "reference_id": None,
            "record_hash": "hash_002"
        },
        {
            "transaction_id": "TXN_003",
            "source_record_id": "SRC_003",
            "account_id": "ACC_0003",
            "customer_id": "CUST_0003",
            "transaction_date": date(2026, 9, 3),
            "raw_transaction_date": "2026-09-03",
            "transaction_type": "REFUND",
            "amount": -50.00,
            "raw_amount": "-50.00",
            "currency": "EUR",
            "transaction_status": "COMPLETED",
            "reference_id": "TXN_001",
            "record_hash": "hash_003"
        }
    ]
    return pd.DataFrame(data)
