"""DataGuard Main Pipeline Runner Script.

Usage:
    python scripts/run_pipeline.py --input data/sample/transactions_corrupted.csv --ledger data/sample/target_ledger.csv
"""

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from dataguard.orchestration.pipeline import run_dataguard_pipeline


def main():
    parser = argparse.ArgumentParser(description="DataGuard Financial Pipeline Runner")
    parser.add_argument("--input", "-i", default="data/sample/transactions_corrupted.csv", help="Path to input transactions CSV")
    parser.add_argument("--ledger", "-l", default="data/sample/target_ledger.csv", help="Path to reconciliation ledger CSV")
    parser.add_argument("--source-system", default="CORE_BANKING_A", help="Source system name")
    parser.add_argument("--no-reports", action="store_true", help="Skip report generation")

    args = parser.parse_args()

    input_path = BASE_DIR / args.input if not Path(args.input).is_absolute() else Path(args.input)
    ledger_path = BASE_DIR / args.ledger if args.ledger and not Path(args.ledger).is_absolute() else (Path(args.ledger) if args.ledger else None)

    if not input_path.exists():
        print(f"Error: Input file does not exist: {input_path}")
        sys.exit(1)

    print(f"Running DataGuard pipeline for input: {input_path.name}")
    res = run_dataguard_pipeline(
        input_file=input_path,
        ledger_file=ledger_path,
        source_system=args.source_system,
        generate_reports=not args.no_reports
    )

    print("\n" + "=" * 60)
    print(f"DATAGUARD EXECUTION SUMMARY | BATCH: {res['batch_id']}")
    print("=" * 60)
    print(f"Records Ingested:      {res['records_ingested']}")
    print(f"Passed Clean Records:  {res['quality_metrics']['passed_records']}")
    print(f"Failed Records:        {res['quality_metrics']['failed_records']}")
    print(f"Total Exceptions:      {res['exceptions_detected']}")
    print("-" * 60)
    print(f"Completeness Score:    {res['quality_metrics']['completeness_score']:.2f}%")
    print(f"Validity Score:        {res['quality_metrics']['validity_score']:.2f}%")
    print(f"Uniqueness Score:      {res['quality_metrics']['uniqueness_score']:.2f}%")
    print(f"Integrity Score:       {res['quality_metrics']['integrity_score']:.2f}%")
    print(f"OVERALL QUALITY SCORE: {res['quality_metrics']['overall_quality_score']:.2f}%")
    print("-" * 60)
    print(f"Reconciliation Matches:{res['reconciliation_matches']}")
    if res.get("excel_report"):
        print(f"Excel Report Created:  {res['excel_report']}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
