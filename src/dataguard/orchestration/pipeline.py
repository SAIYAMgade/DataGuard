"""DataGuard Pipeline Orchestration Module.

Orchestrates the entire connected workflow:
Source File Ingestion -> Standardization -> PostgreSQL Staging -> Quality Validation Engine ->
Reconciliation Engine -> Reporting and Excel Generation.
"""

import logging
from pathlib import Path
from typing import Any, Dict
import pandas as pd

from dataguard.database.repositories import ReconciliationRepository
from dataguard.ingestion.loader import ingest_file
from dataguard.quality.engine import ValidationEngine
from dataguard.reconciliation.engine import ReconciliationEngine
from dataguard.reporting.excel_reports import generate_excel_report
from dataguard.reporting.summaries import (
    fetch_all_exceptions,
    fetch_executive_kpis,
    fetch_quality_history,
    fetch_reconciliation_summary,
)

logger = logging.getLogger("dataguard.pipeline")


def run_dataguard_pipeline(
    input_file: Path | str,
    ledger_file: Path | str | None = None,
    source_system: str = "CORE_BANKING_A",
    generate_reports: bool = True
) -> Dict[str, Any]:
    """
    Executes the end-to-end DataGuard pipeline:
    1. Ingestion: Reads CSV, stores raw JSONB, stages records idempotently.
    2. Quality Validation: Synchronizes rules, executes DQ001-DQ017, calculates scores, persists exceptions.
    3. Reconciliation: Matches against target ledger, identifies breaks, checks tolerances.
    4. Reporting: Generates 6-sheet Excel report and Power BI CSV extracts.
    """
    input_file = Path(input_file)
    logger.info("Executing DataGuard pipeline on: %s", input_file)

    # 1. Ingestion
    batch_id, staged_df = ingest_file(input_file, source_system=source_system)

    # 2. Validation
    val_engine = ValidationEngine()
    val_engine.sync_rule_catalog()
    run_id, metrics, exceptions = val_engine.run_validation(batch_id=batch_id, df=staged_df)

    # 3. Reconciliation
    target_df = None
    if ledger_file and Path(ledger_file).exists():
        ReconciliationRepository.load_target_ledger(ledger_file)
        target_df = pd.read_csv(ledger_file)

    recon_engine = ReconciliationEngine()
    record_matches, aggregate_matches = recon_engine.run_reconciliation(
        run_id=run_id,
        batch_id=batch_id,
        source_df=staged_df,
        target_df=target_df
    )

    # 4. Reporting
    excel_path = None
    if generate_reports:
        excel_path = generate_excel_report(batch_id=batch_id)
        
        # Export CSVs for Power BI import
        export_dir = Path("reports/sample_outputs")
        export_dir.mkdir(parents=True, exist_ok=True)
        
        fetch_all_exceptions(batch_id).to_csv(export_dir / "exceptions_export.csv", index=False)
        fetch_reconciliation_summary(batch_id).to_csv(export_dir / "reconciliation_export.csv", index=False)
        fetch_quality_history().to_csv(export_dir / "quality_runs_export.csv", index=False)
        
        kpi_df = pd.DataFrame([fetch_executive_kpis()])
        kpi_df.to_csv(export_dir / "kpis_export.csv", index=False)
        logger.info("Exported reporting CSVs to %s for Power BI ingestion", export_dir)

    result = {
        "batch_id": batch_id,
        "run_id": run_id,
        "records_ingested": len(staged_df),
        "quality_metrics": metrics,
        "exceptions_detected": len(exceptions),
        "reconciliation_matches": len(record_matches),
        "aggregate_currencies": len(aggregate_matches),
        "excel_report": str(excel_path) if excel_path else None
    }
    return result
