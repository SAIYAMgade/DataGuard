"""Standalone Report Generation Script for DataGuard."""

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from dataguard.reporting.excel_reports import generate_excel_report


def main():
    parser = argparse.ArgumentParser(description="Generate DataGuard Excel and CSV Reports")
    parser.add_argument("--batch-id", "-b", default=None, help="Specific Batch ID to report")
    parser.add_argument("--output", "-o", default=None, help="Output Excel file path")
    args = parser.parse_args()

    print("Generating DataGuard Excel quality report...")
    out_file = generate_excel_report(output_path=args.output, batch_id=args.batch_id)
    print(f"Report generated successfully: {out_file}")


if __name__ == "__main__":
    main()
