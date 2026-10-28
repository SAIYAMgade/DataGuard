"""DataGuard Ingestion Loader Module.

Orchestrates file reading, raw payload persistence, schema validation,
staging load, and batch lifecycle tracking with full transaction safety.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple
import pandas as pd

from dataguard.config.settings import load_settings
from dataguard.database.repositories import IngestionRepository, TransactionRepository
from dataguard.ingestion.readers import read_transaction_csv
from dataguard.ingestion.validation import validate_file_structure
from dataguard.transformations.standardization import standardize_records

logger = logging.getLogger("dataguard.ingestion")


def generate_batch_id() -> str:
    """Generates a timestamped unique batch identifier."""
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"BATCH_{now_str}"


def ingest_file(file_path: Path | str, source_system: str = "CORE_BANKING_A") -> Tuple[str, pd.DataFrame]:
    """
    Ingests a transaction CSV file end-to-end:
    1. Reads and checks file encoding.
    2. Validates header structure.
    3. Creates batch record in ingestion_batches.
    4. Saves exact raw payloads in raw_transactions.
    5. Standardizes records into typed staging format.
    6. Loads staging records idempotently.
    7. Updates batch status.
    Returns:
        (batch_id, standardized_dataframe)
    """
    settings = load_settings()
    file_path = Path(file_path)
    batch_id = generate_batch_id()

    logger.info("Starting ingestion for %s with batch_id: %s", file_path.name, batch_id)

    raw_records, headers, structural_errors = read_transaction_csv(file_path)

    if structural_errors and not headers:
        IngestionRepository.create_batch(batch_id, str(file_path), source_system, 0)
        error_msg = "; ".join(structural_errors)
        IngestionRepository.complete_batch(batch_id, 0, 0, status="FAILED", error_msg=error_msg)
        raise ValueError(f"Structural ingestion failure: {error_msg}")

    # Validate required headers
    is_valid, missing_cols, unexpected_cols = validate_file_structure(headers, settings.required_columns)
    if not is_valid:
        IngestionRepository.create_batch(batch_id, str(file_path), source_system, len(raw_records))
        error_msg = f"Missing required columns: {missing_cols}"
        IngestionRepository.complete_batch(batch_id, 0, len(raw_records), status="FAILED", error_msg=error_msg)
        raise ValueError(f"Schema validation failure: {error_msg}")

    if unexpected_cols:
        logger.warning("Identified unexpected columns in source file: %s", unexpected_cols)

    # Initialize batch record
    total_received = len(raw_records) + len(structural_errors)
    IngestionRepository.create_batch(batch_id, str(file_path), source_system, total_received)

    try:
        # Save exact raw JSONB records
        IngestionRepository.save_raw_transactions(batch_id, raw_records)

        # Standardize and stage
        standardized_df = standardize_records(raw_records)
        standardized_df["batch_id"] = batch_id
        standardized_df["source_system"] = source_system

        records_loaded = TransactionRepository.save_staging_transactions(batch_id, standardized_df)
        records_rejected = len(structural_errors)

        IngestionRepository.complete_batch(
            batch_id,
            records_loaded=records_loaded,
            records_rejected=records_rejected,
            status="COMPLETED"
        )
        logger.info("Batch %s completed successfully: %d loaded, %d rejected", batch_id, records_loaded, records_rejected)
        return batch_id, standardized_df

    except Exception as exc:
        logger.error("Ingestion failed for batch %s: %s", batch_id, str(exc), exc_info=True)
        IngestionRepository.complete_batch(batch_id, 0, total_received, status="FAILED", error_msg=str(exc))
        raise
