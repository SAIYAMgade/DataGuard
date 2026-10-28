"""DataGuard Database Repositories.

Provides explicit, parameterized database interactions for:
- Ingestion batch tracking
- Raw transaction payload preservation
- Staging transaction persistence with idempotency
- Quality rules synchronization
- Quality run history logging
- Exception register logging and resolution
- Reconciliation results storage
- Reference dimension loading
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from sqlalchemy import text

from dataguard.database.connection import get_db_connection

logger = logging.getLogger("dataguard.repository")


class IngestionRepository:
    """Manages ingestion batch metadata and raw payloads."""

    @staticmethod
    def create_batch(batch_id: str, source_file: str, source_system: str, records_received: int) -> None:
        sql = text("""
            INSERT INTO ingestion_batches (
                batch_id, source_file, source_system, started_at, status, records_received
            ) VALUES (
                :batch_id, :source_file, :source_system, :started_at, 'STARTED', :records_received
            )
            ON CONFLICT (batch_id) DO UPDATE SET
                started_at = EXCLUDED.started_at,
                status = 'STARTED',
                records_received = EXCLUDED.records_received;
        """)
        with get_db_connection() as conn:
            conn.execute(sql, {
                "batch_id": batch_id,
                "source_file": source_file,
                "source_system": source_system,
                "started_at": datetime.now(timezone.utc),
                "records_received": records_received
            })

    @staticmethod
    def complete_batch(batch_id: str, records_loaded: int, records_rejected: int, status: str = "COMPLETED", error_msg: Optional[str] = None) -> None:
        sql = text("""
            UPDATE ingestion_batches
            SET completed_at = :completed_at,
                status = :status,
                records_loaded = :records_loaded,
                records_rejected = :records_rejected,
                error_message = :error_msg
            WHERE batch_id = :batch_id;
        """)
        with get_db_connection() as conn:
            conn.execute(sql, {
                "batch_id": batch_id,
                "completed_at": datetime.now(timezone.utc),
                "status": status,
                "records_loaded": records_loaded,
                "records_rejected": records_rejected,
                "error_msg": error_msg
            })

    @staticmethod
    def save_raw_transactions(batch_id: str, records: List[Dict[str, Any]]) -> None:
        """Preserves original raw payload records without modification."""
        if not records:
            return
        sql = text("""
            INSERT INTO raw_transactions (batch_id, source_record_id, raw_payload)
            VALUES (:batch_id, :source_record_id, CAST(:raw_payload AS jsonb));
        """)
        params = [
            {
                "batch_id": batch_id,
                "source_record_id": str(r.get("source_record_id") or r.get("transaction_id") or f"ROW_{idx}"),
                "raw_payload": json.dumps(r, default=str)
            }
            for idx, r in enumerate(records, 1)
        ]
        with get_db_connection() as conn:
            conn.execute(sql, params)


class TransactionRepository:
    """Manages staging transactions with strict typing and idempotency."""

    @staticmethod
    def save_staging_transactions(batch_id: str, df: pd.DataFrame) -> int:
        """
        Inserts normalized records into stg_transactions.
        Deletes existing staging records for the same batch first to guarantee idempotency.
        """
        if df.empty:
            return 0

        with get_db_connection() as conn:
            # Idempotent cleanup for this specific batch
            conn.execute(text("DELETE FROM stg_transactions WHERE batch_id = :batch_id;"), {"batch_id": batch_id})
            
            # Prepare rows
            records = []
            for _, row in df.iterrows():
                records.append({
                    "batch_id": batch_id,
                    "source_system": str(row.get("source_system", "UNKNOWN")),
                    "source_record_id": str(row.get("source_record_id", "")) if pd.notna(row.get("source_record_id")) else None,
                    "transaction_id": str(row.get("transaction_id", "")) if pd.notna(row.get("transaction_id")) and str(row.get("transaction_id", "")).strip() else None,
                    "account_id": str(row.get("account_id", "")) if pd.notna(row.get("account_id")) and str(row.get("account_id", "")).strip() else None,
                    "customer_id": str(row.get("customer_id", "")) if pd.notna(row.get("customer_id")) and str(row.get("customer_id", "")).strip() else None,
                    "transaction_date": row.get("transaction_date") if pd.notna(row.get("transaction_date")) else None,
                    "transaction_type": str(row.get("transaction_type", "")) if pd.notna(row.get("transaction_type")) else None,
                    "amount": float(row.get("amount")) if pd.notna(row.get("amount")) and row.get("amount") is not None else None,
                    "currency": str(row.get("currency", "")) if pd.notna(row.get("currency")) else None,
                    "transaction_status": str(row.get("transaction_status", "")) if pd.notna(row.get("transaction_status")) else None,
                    "reference_id": str(row.get("reference_id", "")) if pd.notna(row.get("reference_id")) and str(row.get("reference_id", "")).strip() else None,
                    "description": str(row.get("description", "")) if pd.notna(row.get("description")) else None,
                    "record_hash": str(row.get("record_hash", ""))
                })

            sql = text("""
                INSERT INTO stg_transactions (
                    batch_id, source_system, source_record_id, transaction_id,
                    account_id, customer_id, transaction_date, transaction_type,
                    amount, currency, transaction_status, reference_id,
                    description, record_hash
                ) VALUES (
                    :batch_id, :source_system, :source_record_id, :transaction_id,
                    :account_id, :customer_id, :transaction_date, :transaction_type,
                    :amount, :currency, :transaction_status, :reference_id,
                    :description, :record_hash
                );
            """)
            conn.execute(sql, records)
        return len(records)


class QualityRepository:
    """Manages quality rule catalog, validation history, and exception register."""

    @staticmethod
    def sync_rules(rules: List[Dict[str, Any]]) -> None:
        sql = text("""
            INSERT INTO quality_rules (
                rule_id, name, dimension, severity, target_field, description, investigation_action, enabled
            ) VALUES (
                :rule_id, :name, :dimension, :severity, :target_field, :description, :investigation_action, :enabled
            )
            ON CONFLICT (rule_id) DO UPDATE SET
                name = EXCLUDED.name,
                dimension = EXCLUDED.dimension,
                severity = EXCLUDED.severity,
                target_field = EXCLUDED.target_field,
                description = EXCLUDED.description,
                investigation_action = EXCLUDED.investigation_action,
                enabled = EXCLUDED.enabled;
        """)
        with get_db_connection() as conn:
            conn.execute(sql, rules)

    @staticmethod
    def save_run_history(run_data: Dict[str, Any]) -> None:
        sql = text("""
            INSERT INTO quality_run_history (
                run_id, batch_id, evaluated_at, total_records, passed_records, failed_records,
                total_exceptions, completeness_score, validity_score, uniqueness_score,
                integrity_score, overall_quality_score, execution_duration_ms, status
            ) VALUES (
                :run_id, :batch_id, :evaluated_at, :total_records, :passed_records, :failed_records,
                :total_exceptions, :completeness_score, :validity_score, :uniqueness_score,
                :integrity_score, :overall_quality_score, :execution_duration_ms, :status
            )
            ON CONFLICT (run_id) DO NOTHING;
        """)
        with get_db_connection() as conn:
            conn.execute(sql, run_data)

    @staticmethod
    def save_exceptions(exceptions: List[Dict[str, Any]]) -> None:
        if not exceptions:
            return
        sql = text("""
            INSERT INTO exception_register (
                exception_id, run_id, batch_id, rule_id, record_reference, field_name,
                invalid_value, severity, issue_description, detected_at, resolution_status
            ) VALUES (
                :exception_id, :run_id, :batch_id, :rule_id, :record_reference, :field_name,
                :invalid_value, :severity, :issue_description, :detected_at, 'OPEN'
            )
            ON CONFLICT (exception_id) DO NOTHING;
        """)
        with get_db_connection() as conn:
            conn.execute(sql, exceptions)


class ReconciliationRepository:
    """Manages target ledger data and reconciliation results."""

    @staticmethod
    def load_target_ledger(csv_path: Path | str) -> int:
        df = pd.read_csv(csv_path)
        records = []
        for _, row in df.iterrows():
            records.append({
                "ledger_id": str(row["ledger_id"]),
                "account_id": str(row["account_id"]),
                "transaction_date": str(row["transaction_date"]),
                "amount": float(row["amount"]),
                "currency": str(row["currency"]),
                "external_ref": str(row["external_ref"]) if pd.notna(row.get("external_ref")) else None,
                "posted_date": str(row["posted_date"])
            })

        sql = text("""
            INSERT INTO target_ledger_transactions (
                ledger_id, account_id, transaction_date, amount, currency, external_ref, posted_date
            ) VALUES (
                :ledger_id, :account_id, :transaction_date, :amount, :currency, :external_ref, :posted_date
            )
            ON CONFLICT (ledger_id) DO UPDATE SET
                amount = EXCLUDED.amount,
                posted_date = EXCLUDED.posted_date;
        """)
        with get_db_connection() as conn:
            conn.execute(sql, records)
        return len(records)

    @staticmethod
    def save_results(results: List[Dict[str, Any]]) -> None:
        if not results:
            return
        sql = text("""
            INSERT INTO reconciliation_results (
                recon_id, run_id, batch_id, recon_type, source_id, target_id, currency,
                source_amount, target_amount, signed_difference, absolute_difference,
                tolerance, match_status, reconciled_at
            ) VALUES (
                :recon_id, :run_id, :batch_id, :recon_type, :source_id, :target_id, :currency,
                :source_amount, :target_amount, :signed_difference, :absolute_difference,
                :tolerance, :match_status, :reconciled_at
            )
            ON CONFLICT (recon_id) DO NOTHING;
        """)
        with get_db_connection() as conn:
            conn.execute(sql, results)


class DimensionRepository:
    """Loads customer and account reference dimensions."""

    @staticmethod
    def load_customers(csv_path: Path | str) -> int:
        df = pd.read_csv(csv_path)
        records = [
            {
                "customer_id": str(r["customer_id"]),
                "customer_name": str(r["customer_name"]),
                "customer_type": str(r["customer_type"]),
                "country": str(r["country"]),
                "kyc_status": str(r["kyc_status"])
            }
            for _, r in df.iterrows()
        ]
        sql = text("""
            INSERT INTO dim_customers (customer_id, customer_name, customer_type, country, kyc_status)
            VALUES (:customer_id, :customer_name, :customer_type, :country, :kyc_status)
            ON CONFLICT (customer_id) DO UPDATE SET
                customer_name = EXCLUDED.customer_name,
                kyc_status = EXCLUDED.kyc_status;
        """)
        with get_db_connection() as conn:
            conn.execute(sql, records)
        return len(records)

    @staticmethod
    def load_accounts(csv_path: Path | str) -> int:
        df = pd.read_csv(csv_path)
        records = [
            {
                "account_id": str(r["account_id"]),
                "customer_id": str(r["customer_id"]),
                "account_type": str(r["account_type"]),
                "currency": str(r["currency"]),
                "status": str(r["status"]),
                "opened_date": str(r["opened_date"])
            }
            for _, r in df.iterrows()
        ]
        sql = text("""
            INSERT INTO dim_accounts (account_id, customer_id, account_type, currency, status, opened_date)
            VALUES (:account_id, :customer_id, :account_type, :currency, :status, :opened_date)
            ON CONFLICT (account_id) DO UPDATE SET
                status = EXCLUDED.status,
                currency = EXCLUDED.currency;
        """)
        with get_db_connection() as conn:
            conn.execute(sql, records)
        return len(records)
