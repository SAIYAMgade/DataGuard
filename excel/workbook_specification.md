# DataGuard | Excel Workbook Technical Specification

## 1. Overview & Purpose

The DataGuard Excel workbook is designed for business operators, auditors, and financial analysts who require an auditable, filterable view of data quality without executing SQL queries or Python scripts.

Generated programmatically via `dataguard.reporting.excel_reports` using `openpyxl`, the workbook adheres to corporate financial styling and data integrity standards.

---

## 2. Worksheet Directory

| Sheet # | Sheet Name | Target Audience | Primary Function |
|---|---|---|---|
| **Sheet 1** | `Executive Summary` | VP Finance, Head of Data | High-level scorecard, batch KPIs, dimensional ratings, volume tallies |
| **Sheet 2** | `Exception Register` | Data Stewards, FinOps | Line-item anomaly investigation, severity tagging, filterable audit log |
| **Sheet 3** | `Reconciliation` | Clearing & Settlement | Multi-currency isolated balance comparison, signed differences |
| **Sheet 4** | `Quality Trends` | Analytics Engineers | Historical batch score progression and trend lines |
| **Sheet 5** | `Data Dictionary` | Business Analysts | Complete field definitions, types, constraints, and validation rules |
| **Sheet 6** | `Rule Catalogue` | Compliance / QA | Full inventory of quality rules DQ001 to DQ017 with resolution guidance |

---

## 3. Formatting & Usability Features

1. **Header Freezing:** Header rows are frozen across Sheets 2, 3, 4, 5, and 6 so column labels remain visible during vertical scrolling.
2. **Auto-Filters:** Excel auto-filters (`A1:K...`) are activated on every tabular sheet, allowing instant filtering by severity, rule, status, or date.
3. **Severity Highlighting:**
   - **CRITICAL:** Red fill (`#FFD2D2`), Dark Red text (`#900000`).
   - **HIGH:** Orange fill (`#FFE4CC`), Dark Orange text (`#8A3B00`).
   - **MEDIUM:** Yellow fill (`#FFF8CC`), Dark Yellow text (`#736200`).
   - **LOW:** Light Blue fill (`#E0F2FE`), Dark Blue text (`#0369A1`).
4. **Number & Date Formatting:**
   - Monetary values formatted as `#,##0.00`.
   - Percentage scores formatted as `0.00%`.
   - Counts formatted as `#,##0`.
   - Timestamps formatted in standard ISO/UTC strings.
5. **No Blind Cross-Currency Sums:** Sheet 3 enforces strict currency isolation. Totals are never summed across USD, EUR, or GBP.
