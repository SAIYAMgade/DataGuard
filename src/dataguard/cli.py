"""DataGuard Command Line Interface."""

import logging
import sys
from pathlib import Path
import click

from dataguard.database.connection import execute_sql_file
from dataguard.database.repositories import DimensionRepository
from dataguard.orchestration.pipeline import run_dataguard_pipeline
from dataguard.reporting.excel_reports import generate_excel_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("dataguard.cli")


@click.group()
def main():
    """DataGuard: Financial Data Quality & Transaction Monitoring System CLI."""
    pass


@main.command()
@click.option("--schema-dir", default="sql/schema", help="Path to schema SQL files.")
@click.option("--views-file", default="sql/views/reporting_views.sql", help="Path to views SQL file.")
@click.option("--cust-file", default="data/sample/dim_customers.csv", help="Path to customer dimension CSV.")
@click.option("--acc-file", default="data/sample/dim_accounts.csv", help="Path to account dimension CSV.")
def init_db(schema_dir: str, views_file: str, cust_file: str, acc_file: str):
    """Initializes PostgreSQL schema, tables, indexes, views, and reference data."""
    click.echo("Initializing DataGuard database schema and reference dimensions...")
    
    schema_path = Path(schema_dir)
    execute_sql_file(schema_path / "001_create_tables.sql")
    execute_sql_file(schema_path / "002_create_indexes.sql")
    
    views_path = Path(views_file)
    if views_path.exists():
        execute_sql_file(views_path)

    # Load reference dimensions
    if Path(cust_file).exists():
        cust_cnt = DimensionRepository.load_customers(cust_file)
        click.echo(f"Loaded {cust_cnt} customer dimension records.")
    if Path(acc_file).exists():
        acc_cnt = DimensionRepository.load_accounts(acc_file)
        click.echo(f"Loaded {acc_cnt} account dimension records.")

    click.secho("Database initialization completed successfully!", fg="green")


@main.command()
@click.option("--input", "-i", required=True, help="Path to transaction CSV file.")
@click.option("--ledger", "-l", default=None, help="Path to target ledger CSV file for reconciliation.")
@click.option("--source-system", default="CORE_BANKING_A", help="Source system name.")
@click.option("--reports/--no-reports", default=True, help="Generate Excel and CSV reports.")
def run(input: str, ledger: str | None, source_system: str, reports: bool):
    """Runs the full DataGuard ingestion, validation, and reconciliation pipeline."""
    click.echo(f"Running DataGuard pipeline for: {input}")
    try:
        res = run_dataguard_pipeline(
            input_file=input,
            ledger_file=ledger,
            source_system=source_system,
            generate_reports=reports
        )
        click.secho(f"\nPipeline Run Summary for Batch: {res['batch_id']}", fg="cyan", bold=True)
        click.echo(f"Records Ingested:    {res['records_ingested']}")
        click.echo(f"Passed Records:      {res['quality_metrics']['passed_records']}")
        click.echo(f"Failed Records:      {res['quality_metrics']['failed_records']}")
        click.echo(f"Total Exceptions:    {res['exceptions_detected']}")
        click.echo(f"Overall Score:       {res['quality_metrics']['overall_quality_score']}%")
        click.echo(f"Completeness Score:  {res['quality_metrics']['completeness_score']}%")
        click.echo(f"Validity Score:      {res['quality_metrics']['validity_score']}%")
        click.echo(f"Uniqueness Score:    {res['quality_metrics']['uniqueness_score']}%")
        click.echo(f"Integrity Score:     {res['quality_metrics']['integrity_score']}%")
        if res.get("excel_report"):
            click.secho(f"Excel Report:        {res['excel_report']}", fg="green")
    except Exception as exc:
        click.secho(f"Pipeline execution failed: {exc}", fg="red", err=True)
        sys.exit(1)


@main.command()
@click.option("--output", "-o", default=None, help="Output Excel file path.")
@click.option("--batch-id", default=None, help="Batch ID to report on.")
def report(output: str | None, batch_id: str | None):
    """Generates the 6-sheet DataGuard Excel audit workbook."""
    click.echo("Generating DataGuard Excel quality workbook...")
    out_file = generate_excel_report(output_path=output, batch_id=batch_id)
    click.secho(f"Excel report generated: {out_file}", fg="green")


if __name__ == "__main__":
    main()
