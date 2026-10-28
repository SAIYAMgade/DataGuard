"""Integration Tests for DataGuard Database Operations and Pipeline Idempotency."""

from decimal import Decimal
import pandas as pd
import pytest
from sqlalchemy import text

from dataguard.database.connection import get_db_connection
from dataguard.database.repositories import IngestionRepository, TransactionRepository
from dataguard.orchestration.pipeline import run_dataguard_pipeline


@pytest.mark.integration
def test_database_tables_exist():
    expected_tables = {
        "ingestion_batches", "raw_transactions", "dim_customers", "dim_accounts",
        "stg_transactions", "quality_rules", "quality_run_history",
        "exception_register", "target_ledger_transactions", "reconciliation_results"
    }
    with get_db_connection() as conn:
        res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"))
        existing_tables = {row[0] for row in res.fetchall()}
    assert expected_tables.issubset(existing_tables)


@pytest.mark.integration
def test_pipeline_idempotency_on_rerun(sample_valid_df):
    """
    Verifies that rerunning a batch replaces existing staging records
    rather than duplicating them.
    """
    batch_id = "BATCH_TEST_IDEMPOTENCY_001"
    IngestionRepository.create_batch(batch_id, "test.csv", "TEST_SYS", len(sample_valid_df))
    
    # First save
    TransactionRepository.save_staging_transactions(batch_id, sample_valid_df)
    with get_db_connection() as conn:
        cnt1 = conn.execute(
            text("SELECT COUNT(*) FROM stg_transactions WHERE batch_id = :b;"), {"b": batch_id}
        ).scalar()
    assert cnt1 == len(sample_valid_df)

    # Reprocess the same batch with same records
    TransactionRepository.save_staging_transactions(batch_id, sample_valid_df)
    with get_db_connection() as conn:
        cnt2 = conn.execute(
            text("SELECT COUNT(*) FROM stg_transactions WHERE batch_id = :b;"), {"b": batch_id}
        ).scalar()
    # Count must remain exactly the same, proving idempotency
    assert cnt2 == len(sample_valid_df)


@pytest.mark.integration
def test_exception_persistence_foreign_key_integrity():
    with get_db_connection() as conn:
        # Check that all exceptions reference valid rules
        orphaned_rules = conn.execute(text("""
            SELECT er.exception_id, er.rule_id
            FROM exception_register er
            LEFT JOIN quality_rules qr ON er.rule_id = qr.rule_id
            WHERE qr.rule_id IS NULL;
        """)).fetchall()
        assert len(orphaned_rules) == 0

        # Check that all exceptions reference valid batches
        orphaned_batches = conn.execute(text("""
            SELECT er.exception_id, er.batch_id
            FROM exception_register er
            LEFT JOIN ingestion_batches ib ON er.batch_id = ib.batch_id
            WHERE ib.batch_id IS NULL;
        """)).fetchall()
        assert len(orphaned_batches) == 0
