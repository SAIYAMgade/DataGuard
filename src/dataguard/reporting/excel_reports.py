"""DataGuard Excel Workbook Report Generator.

Generates professional, 6-sheet business reports using openpyxl:
1. Executive Summary: High-level KPI cards and quality scorecard
2. Exception Register: Auto-filtered, frozen header, severity-colored exception audit log
3. Reconciliation: Currency-isolated financial totals and tolerance variance analysis
4. Quality Trends: Historical progression across sequential batches
5. Data Dictionary: Complete field definitions and technical specifications
6. Rule Catalogue: Comprehensive quality rule catalogue with investigation guidelines
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import openpyxl
import pandas as pd
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from dataguard.config.settings import load_quality_rules_config, load_settings
from dataguard.reporting.summaries import (
    fetch_all_exceptions,
    fetch_executive_kpis,
    fetch_quality_history,
    fetch_reconciliation_summary,
)

logger = logging.getLogger("dataguard.reporting.excel")

# Corporate Financial Styling Palette
NAVY_HEADER = "1B365D"
LIGHT_NAVY = "2E5B88"
WHITE = "FFFFFF"
GRAY_LIGHT = "F4F5F7"
GRAY_BORDER = "D1D5DB"

SEVERITY_COLORS = {
    "CRITICAL": {"fill": "FFD2D2", "font": "900000"},
    "HIGH": {"fill": "FFE4CC", "font": "8A3B00"},
    "MEDIUM": {"fill": "FFF8CC", "font": "736200"},
    "LOW": {"fill": "E0F2FE", "font": "0369A1"},
}


def apply_table_styles(ws, start_row: int, end_row: int, start_col: int, end_col: int):
    """Applies borders and alternating row shading."""
    thin_border = Border(
        left=Side(style="thin", color=GRAY_BORDER),
        right=Side(style="thin", color=GRAY_BORDER),
        top=Side(style="thin", color=GRAY_BORDER),
        bottom=Side(style="thin", color=GRAY_BORDER)
    )
    for row in range(start_row, end_row + 1):
        for col in range(start_col, end_col + 1):
            cell = ws.cell(row=row, column=col)
            cell.border = thin_border
            if row % 2 == 0 and cell.fill.fill_type is None:
                cell.fill = PatternFill(start_color=GRAY_LIGHT, end_color=GRAY_LIGHT, fill_type="solid")


def auto_fit_columns(ws, min_width: int = 12, max_width: int = 60):
    """Auto-adjusts column widths based on cell content length."""
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = 0
        for cell in col:
            val_str = str(cell.value or "")
            if "\n" in val_str:
                val_str = max(val_str.split("\n"), key=len)
            max_len = max(max_len, len(val_str))
        ws.column_dimensions[col_letter].width = max(min_width, min(max_len + 3, max_width))


def generate_excel_report(output_path: Path | str | None = None, batch_id: str | None = None) -> Path:
    """Generates the comprehensive 6-sheet DataGuard Excel report."""
    settings = load_settings()
    out_file = Path(output_path or settings.excel_output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    # -------------------------------------------------------------------------
    # Sheet 1: Executive Summary
    # -------------------------------------------------------------------------
    ws_exec = wb.create_sheet(title="Executive Summary")
    ws_exec.views.sheetView[0].showGridLines = True

    # Title Banner
    ws_exec.merge_cells("A1:G1")
    title_cell = ws_exec["A1"]
    title_cell.value = "DataGuard | Financial Data Quality & Transaction Monitoring Executive Summary"
    title_cell.font = Font(name="Segoe UI", size=15, bold=True, color=WHITE)
    title_cell.fill = PatternFill(start_color=NAVY_HEADER, end_color=NAVY_HEADER, fill_type="solid")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws_exec.row_dimensions[1].height = 40

    kpis = fetch_executive_kpis()

    # Metadata Subtitle
    ws_exec["A3"] = "Report Generated:"
    ws_exec["B3"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    ws_exec["A4"] = "Evaluated Batch:"
    ws_exec["B4"] = kpis.get("batch_id", batch_id or "N/A")
    ws_exec["A5"] = "Evaluation Run ID:"
    ws_exec["B5"] = kpis.get("run_id", "N/A")
    for r in range(3, 6):
        ws_exec[f"A{r}"].font = Font(bold=True, color="374151")

    # Scorecard Headers
    headers = ["Quality Dimension", "Score (%)", "Target Threshold", "Health Status", "Weight Rationale"]
    ws_exec.row_dimensions[7].height = 25
    for c_idx, h in enumerate(headers, start=1):
        cell = ws_exec.cell(row=7, column=c_idx, value=h)
        cell.font = Font(bold=True, color=WHITE)
        cell.fill = PatternFill(start_color=LIGHT_NAVY, end_color=LIGHT_NAVY, fill_type="solid")
        cell.alignment = Alignment(horizontal="center" if c_idx in [2, 3, 4] else "left", vertical="center")

    comp_s = kpis.get("completeness_score", 0.0)
    valid_s = kpis.get("validity_score", 0.0)
    uniq_s = kpis.get("uniqueness_score", 0.0)
    integ_s = kpis.get("integrity_score", 0.0)
    overall_s = kpis.get("overall_quality_score", 0.0)

    rows_scorecard = [
        ("Completeness", comp_s, ">= 99.00%", "HEALTHY" if comp_s >= 99 else "ATTENTION", "25% - Missing keys prevent transaction posting"),
        ("Validity", valid_s, ">= 98.00%", "HEALTHY" if valid_s >= 98 else "WARNING", "35% - Sign, decimal, or bounds errors corrupt ledger totals"),
        ("Uniqueness", uniq_s, ">= 99.50%", "HEALTHY" if uniq_s >= 99.5 else "WARNING", "20% - Duplicate transactions distort financial volumes"),
        ("Referential Integrity", integ_s, ">= 99.90%", "HEALTHY" if integ_s >= 99.9 else "WARNING", "20% - Orphaned accounts cannot clear or reconcile"),
        ("OVERALL COMPOSITE QUALITY", overall_s, ">= 98.50%", "PASS" if overall_s >= 98.5 else "INVESTIGATE", "100% Weighted Quality Index")
    ]

    for idx, (dim, score, target, status, note) in enumerate(rows_scorecard, start=8):
        ws_exec.cell(row=idx, column=1, value=dim).font = Font(bold=(idx == 12))
        sc_cell = ws_exec.cell(row=idx, column=2, value=float(score))
        sc_cell.number_format = "0.00"
        sc_cell.alignment = Alignment(horizontal="right")
        ws_exec.cell(row=idx, column=3, value=target).alignment = Alignment(horizontal="center")
        
        stat_cell = ws_exec.cell(row=idx, column=4, value=status)
        stat_cell.alignment = Alignment(horizontal="center")
        stat_cell.font = Font(bold=True)
        if status in ["HEALTHY", "PASS"]:
            stat_cell.fill = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")
        else:
            stat_cell.fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")

        ws_exec.cell(row=idx, column=5, value=note)

    apply_table_styles(ws_exec, 7, 12, 1, 5)

    # Operational Volume Summary Block
    ws_exec.cell(row=14, column=1, value="Operational Volume Summary").font = Font(bold=True, size=12, color=NAVY_HEADER)
    op_metrics = [
        ("Total Records Ingested", kpis.get("total_records", 0)),
        ("Clean Records Passed", kpis.get("passed_records", 0)),
        ("Records with Exceptions", kpis.get("failed_records", 0)),
        ("Open Critical Exceptions", kpis.get("open_critical_count", 0)),
        ("Reconciliation Variance Count", kpis.get("total_recon_exceptions", 0)),
        ("Reconciliation Net Absolute Variance", float(kpis.get("total_absolute_diff", 0.0)))
    ]
    for idx, (lbl, val) in enumerate(op_metrics, start=15):
        ws_exec.cell(row=idx, column=1, value=lbl).font = Font(color="4B5563")
        v_cell = ws_exec.cell(row=idx, column=2, value=val)
        v_cell.font = Font(bold=True)
        if isinstance(val, float):
            v_cell.number_format = "#,##0.00"
        else:
            v_cell.number_format = "#,##0"

    auto_fit_columns(ws_exec)

    # -------------------------------------------------------------------------
    # Sheet 2: Exception Register
    # -------------------------------------------------------------------------
    ws_exc = wb.create_sheet(title="Exception Register")
    ws_exc.views.sheetView[0].showGridLines = True
    ws_exc.freeze_panes = "A2"

    exc_df = fetch_all_exceptions(batch_id)
    exc_cols = [
        "exception_id", "batch_id", "record_reference", "rule_name",
        "severity", "field_name", "invalid_value", "issue_description",
        "resolution_status", "detected_at", "investigation_action"
    ]
    exc_headers = [
        "Exception ID", "Batch ID", "Record Reference", "Rule Name",
        "Severity", "Field Name", "Invalid Value", "Issue Description",
        "Resolution Status", "Detected Timestamp", "Investigation Action"
    ]

    for c_idx, h in enumerate(exc_headers, start=1):
        cell = ws_exc.cell(row=1, column=c_idx, value=h)
        cell.font = Font(bold=True, color=WHITE)
        cell.fill = PatternFill(start_color=NAVY_HEADER, end_color=NAVY_HEADER, fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws_exc.row_dimensions[1].height = 25

    row_idx = 2
    for _, row in exc_df.iterrows():
        ws_exc.row_dimensions[row_idx].height = 20
        for c_idx, col_name in enumerate(exc_cols, start=1):
            val = row.get(col_name)
            cell = ws_exc.cell(row=row_idx, column=c_idx, value=str(val) if pd.notna(val) else "")
            
            # Severity color coding
            if col_name == "severity" and val in SEVERITY_COLORS:
                cfg = SEVERITY_COLORS[val]
                cell.fill = PatternFill(start_color=cfg["fill"], end_color=cfg["fill"], fill_type="solid")
                cell.font = Font(bold=True, color=cfg["font"])
                cell.alignment = Alignment(horizontal="center")
            elif col_name == "resolution_status":
                cell.alignment = Alignment(horizontal="center")
                cell.font = Font(bold=True)
        row_idx += 1

    end_exc_row = max(2, row_idx - 1)
    apply_table_styles(ws_exc, 1, end_exc_row, 1, len(exc_headers))
    ws_exc.auto_filter.ref = f"A1:{get_column_letter(len(exc_headers))}{end_exc_row}"
    auto_fit_columns(ws_exc)

    # -------------------------------------------------------------------------
    # Sheet 3: Reconciliation
    # -------------------------------------------------------------------------
    ws_rec = wb.create_sheet(title="Reconciliation")
    ws_rec.views.sheetView[0].showGridLines = True
    ws_rec.freeze_panes = "A2"

    rec_df = fetch_reconciliation_summary(batch_id)
    rec_headers = [
        "Batch ID", "Currency", "Recon Type", "Comparisons", "Exact Matches",
        "Within Tolerance", "Amount Mismatches", "Source Only", "Target Only",
        "Source Total", "Target Total", "Net Signed Variance", "Absolute Variance", "Match Rate (%)"
    ]
    for c_idx, h in enumerate(rec_headers, start=1):
        cell = ws_rec.cell(row=1, column=c_idx, value=h)
        cell.font = Font(bold=True, color=WHITE)
        cell.fill = PatternFill(start_color=NAVY_HEADER, end_color=NAVY_HEADER, fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws_rec.row_dimensions[1].height = 25

    row_idx = 2
    for _, row in rec_df.iterrows():
        ws_rec.cell(row=row_idx, column=1, value=str(row["batch_id"]))
        ws_rec.cell(row=row_idx, column=2, value=str(row["currency"]))
        ws_rec.cell(row=row_idx, column=3, value=str(row["recon_type"]))
        ws_rec.cell(row=row_idx, column=4, value=int(row["total_comparisons"]))
        ws_rec.cell(row=row_idx, column=5, value=int(row["exact_matches"]))
        ws_rec.cell(row=row_idx, column=6, value=int(row["within_tolerance_matches"]))
        ws_rec.cell(row=row_idx, column=7, value=int(row["amount_mismatches"]))
        ws_rec.cell(row=row_idx, column=8, value=int(row["source_only_count"]))
        ws_rec.cell(row=row_idx, column=9, value=int(row["target_only_count"]))
        
        c10 = ws_rec.cell(row=row_idx, column=10, value=float(row["total_source_amount"]))
        c10.number_format = "#,##0.00"
        c11 = ws_rec.cell(row=row_idx, column=11, value=float(row["total_target_amount"]))
        c11.number_format = "#,##0.00"
        c12 = ws_rec.cell(row=row_idx, column=12, value=float(row["net_signed_difference"]))
        c12.number_format = "#,##0.00"
        c13 = ws_rec.cell(row=row_idx, column=13, value=float(row["total_absolute_difference"]))
        c13.number_format = "#,##0.00"
        c14 = ws_rec.cell(row=row_idx, column=14, value=float(row["reconciliation_match_rate_pct"]))
        c14.number_format = "0.00"

        row_idx += 1

    end_rec_row = max(2, row_idx - 1)
    apply_table_styles(ws_rec, 1, end_rec_row, 1, len(rec_headers))
    ws_rec.auto_filter.ref = f"A1:{get_column_letter(len(rec_headers))}{end_rec_row}"
    auto_fit_columns(ws_rec)

    # -------------------------------------------------------------------------
    # Sheet 4: Quality Trends
    # -------------------------------------------------------------------------
    ws_tr = wb.create_sheet(title="Quality Trends")
    ws_tr.views.sheetView[0].showGridLines = True
    ws_tr.freeze_panes = "A2"

    trends_df = fetch_quality_history()
    trend_headers = [
        "Batch ID", "Source System", "Started At", "Records Loaded",
        "Records Rejected", "Pass Rate (%)", "Completeness", "Validity",
        "Uniqueness", "Integrity", "Overall Score (%)"
    ]
    for c_idx, h in enumerate(trend_headers, start=1):
        cell = ws_tr.cell(row=1, column=c_idx, value=h)
        cell.font = Font(bold=True, color=WHITE)
        cell.fill = PatternFill(start_color=NAVY_HEADER, end_color=NAVY_HEADER, fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws_tr.row_dimensions[1].height = 25

    row_idx = 2
    for _, row in trends_df.iterrows():
        ws_tr.cell(row=row_idx, column=1, value=str(row["batch_id"]))
        ws_tr.cell(row=row_idx, column=2, value=str(row["source_system"]))
        ws_tr.cell(row=row_idx, column=3, value=str(row["started_at"]))
        ws_tr.cell(row=row_idx, column=4, value=int(row.get("records_loaded") or 0))
        ws_tr.cell(row=row_idx, column=5, value=int(row.get("records_rejected") or 0))

        tot = row.get("total_records") or 1
        passed = row.get("passed_records") or 0
        pr_cell = ws_tr.cell(row=row_idx, column=6, value=round((passed / tot) * 100.0, 2))
        pr_cell.number_format = "0.00"

        for offset, k in enumerate(["completeness_score", "validity_score", "uniqueness_score", "integrity_score", "overall_quality_score"], start=7):
            val = row.get(k)
            c = ws_tr.cell(row=row_idx, column=offset, value=float(val) if pd.notna(val) else 0.0)
            c.number_format = "0.00"

        row_idx += 1

    end_tr_row = max(2, row_idx - 1)
    apply_table_styles(ws_tr, 1, end_tr_row, 1, len(trend_headers))
    ws_tr.auto_filter.ref = f"A1:{get_column_letter(len(trend_headers))}{end_tr_row}"
    auto_fit_columns(ws_tr)

    # -------------------------------------------------------------------------
    # Sheet 5: Data Dictionary
    # -------------------------------------------------------------------------
    ws_dd = wb.create_sheet(title="Data Dictionary")
    ws_dd.views.sheetView[0].showGridLines = True
    ws_dd.freeze_panes = "A2"

    dd_headers = ["Table", "Field Name", "Data Type", "Nullable", "Key / Constraint", "Description", "Validation Rule"]
    for c_idx, h in enumerate(dd_headers, start=1):
        cell = ws_dd.cell(row=1, column=c_idx, value=h)
        cell.font = Font(bold=True, color=WHITE)
        cell.fill = PatternFill(start_color=NAVY_HEADER, end_color=NAVY_HEADER, fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws_dd.row_dimensions[1].height = 25

    dd_rows = [
        ("stg_transactions", "staging_id", "BIGSERIAL", "No", "Primary Key", "Surrogate sequence identifier", "Auto-incremented"),
        ("stg_transactions", "batch_id", "VARCHAR(64)", "No", "Foreign Key", "Ingestion batch identifier", "Must exist in ingestion_batches"),
        ("stg_transactions", "source_system", "VARCHAR(50)", "No", "None", "Originating upstream system code", "Allowed system list"),
        ("stg_transactions", "transaction_id", "VARCHAR(100)", "No", "Business Key", "Primary transaction identifier", "DQ001, DQ008"),
        ("stg_transactions", "account_id", "VARCHAR(50)", "No", "Foreign Key", "Originating bank account reference", "DQ002, DQ015"),
        ("stg_transactions", "transaction_date", "DATE", "No", "None", "Business effective transaction date", "DQ003, DQ013, DQ014"),
        ("stg_transactions", "transaction_type", "VARCHAR(30)", "No", "Enum", "Classification of monetary transaction", "DQ016, DQ011"),
        ("stg_transactions", "amount", "NUMERIC(18,4)", "No", "None", "Exact decimal monetary magnitude", "DQ004, DQ010, DQ011, DQ012"),
        ("stg_transactions", "currency", "VARCHAR(3)", "No", "ISO 4217", "Standardized three-letter currency code", "DQ005, Supported list"),
        ("stg_transactions", "transaction_status", "VARCHAR(30)", "No", "Enum", "Operational clearing state", "DQ006, DQ016"),
        ("stg_transactions", "reference_id", "VARCHAR(100)", "Yes", "None", "Parent transaction reference for reversals", "DQ017"),
        ("stg_transactions", "record_hash", "VARCHAR(64)", "No", "Index", "SHA-256 fingerprint of row payload", "DQ007 (Idempotency)"),
        ("exception_register", "exception_id", "VARCHAR(64)", "No", "Primary Key", "Traceable unique anomaly identifier", "Auto-generated UUID"),
        ("exception_register", "rule_id", "VARCHAR(20)", "No", "Foreign Key", "Violated quality rule reference", "Must exist in quality_rules"),
        ("exception_register", "severity", "VARCHAR(20)", "No", "Enum", "Operational impact level (CRITICAL/HIGH/MED/LOW)", "Checked enum"),
        ("exception_register", "resolution_status", "VARCHAR(20)", "No", "Workflow", "Current state (OPEN/UNDER_REVIEW/RESOLVED)", "Checked enum")
    ]

    for r_idx, row in enumerate(dd_rows, start=2):
        for c_idx, val in enumerate(row, start=1):
            ws_dd.cell(row=r_idx, column=c_idx, value=val)

    apply_table_styles(ws_dd, 1, len(dd_rows) + 1, 1, len(dd_headers))
    ws_dd.auto_filter.ref = f"A1:{get_column_letter(len(dd_headers))}{len(dd_rows) + 1}"
    auto_fit_columns(ws_dd)

    # -------------------------------------------------------------------------
    # Sheet 6: Rule Catalogue
    # -------------------------------------------------------------------------
    ws_rc = wb.create_sheet(title="Rule Catalogue")
    ws_rc.views.sheetView[0].showGridLines = True
    ws_rc.freeze_panes = "A2"

    rc_headers = ["Rule ID", "Rule Name", "Dimension", "Severity", "Target Field", "Technical Logic & Description", "Investigative Action"]
    for c_idx, h in enumerate(rc_headers, start=1):
        cell = ws_rc.cell(row=1, column=c_idx, value=h)
        cell.font = Font(bold=True, color=WHITE)
        cell.fill = PatternFill(start_color=NAVY_HEADER, end_color=NAVY_HEADER, fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws_rc.row_dimensions[1].height = 25

    rules_cfg = load_quality_rules_config().get("rules", [])
    row_idx = 2
    for r in rules_cfg:
        ws_rc.cell(row=row_idx, column=1, value=r["rule_id"])
        ws_rc.cell(row=row_idx, column=2, value=r["name"])
        ws_rc.cell(row=row_idx, column=3, value=r["dimension"])
        
        sev_cell = ws_rc.cell(row=row_idx, column=4, value=r["severity"])
        sev = r["severity"]
        if sev in SEVERITY_COLORS:
            cfg = SEVERITY_COLORS[sev]
            sev_cell.fill = PatternFill(start_color=cfg["fill"], end_color=cfg["fill"], fill_type="solid")
            sev_cell.font = Font(bold=True, color=cfg["font"])
            sev_cell.alignment = Alignment(horizontal="center")

        ws_rc.cell(row=row_idx, column=5, value=r.get("target_field", ""))
        ws_rc.cell(row=row_idx, column=6, value=r["description"])
        ws_rc.cell(row=row_idx, column=7, value=r["investigation_action"])
        row_idx += 1

    end_rc_row = max(2, row_idx - 1)
    apply_table_styles(ws_rc, 1, end_rc_row, 1, len(rc_headers))
    ws_rc.auto_filter.ref = f"A1:{get_column_letter(len(rc_headers))}{end_rc_row}"
    auto_fit_columns(ws_rc)

    # Save complete workbook
    wb.save(out_file)
    logger.info("Successfully generated 6-sheet Excel report at %s", out_file)
    return out_file
