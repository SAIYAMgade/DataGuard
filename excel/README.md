# DataGuard | Excel Exception Reporting Module

This directory documents the Excel-based data quality reporting engine for business users, finance operations, and audit teams.

## Deliverables

- `reports/DataGuard_Quality_Report.xlsx`: Generated 6-sheet workbook created directly from PostgreSQL pipeline results using `openpyxl`.
- `excel/workbook_specification.md`: Architectural details, formatting conventions, color codes, and worksheet structures.

## How to Regenerate Reports

To generate a fresh Excel report from the latest pipeline batch, run:

```bash
python scripts/generate_reports.py
```

Or target a specific batch ID:

```bash
python scripts/generate_reports.py --batch-id BATCH_20261028_110224 --output reports/Custom_Quality_Report.xlsx
```
