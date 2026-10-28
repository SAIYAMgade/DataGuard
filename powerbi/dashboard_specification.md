# DataGuard | Power BI Dashboard Layout & Visual Specification

This document details the visual configuration, geometry, palette, filtering mechanics, and drill-through pathways across the 3 primary pages of the DataGuard Power BI Dashboard.

---

## Canvas Settings & Styling Standard

- **Canvas Size:** 16:9 widescreen (1280 × 720 px or 1920 × 1080 px).
- **Background:** `#F8FAFC` (Slate 50).
- **Header Banner:** `#1B365D` (Corporate Navy), Height 70 px.
- **Card Background:** `#FFFFFF` (White), 8 px border-radius, soft drop shadow (`rgba(0,0,0,0.05)`).
- **Typography:** Segoe UI / Aptos.
- **Color Palette:**
  - Pass / Success: `#10B981` (Emerald 500)
  - Critical Severity: `#EF4444` (Red 500)
  - High Severity: `#F97316` (Orange 500)
  - Medium Severity: `#F59E0B` (Amber 500)
  - Low Severity: `#0284C7` (Sky 600)

---

## Page 1: Executive Data Quality Overview

**Goal:** Enable executive stakeholders and lead data engineers to immediately assess overall quality health, critical operational blockers, and multi-source variance.

### Global Filter Slicers (Top Ribbon: Y=80, Height=45)
- **Batch Identifier Dropdown:** Single/Multi-select (`ingestion_batches[batch_id]`)
- **Transaction Date Range:** Slider (`dim_date[Date]`)
- **Source System:** Pill buttons (`stg_transactions[source_system]`)
- **Currency:** Dropdown (`stg_transactions[currency]`)

### Row 1: KPI Cards (Y=140, Height=100)
1. **Total Records Ingested**
   - *Visual:* Multi-row Card
   - *Measure:* `[Total Records Ingested]` (Format: `#,##0`)
2. **Overall Quality Score %**
   - *Visual:* KPI Card with Target Gauge
   - *Measure:* `[Overall Composite Quality Score %]` (Format: `0.00%`, Target: `98.50%`)
   - *Color Logic:* Green if >= 98.5%, Amber if >= 95%, Red if < 95%
3. **Data Quality Pass Rate %**
   - *Visual:* Card
   - *Measure:* `[Data Quality Pass Rate %]` (Format: `0.00%`)
4. **Open Critical Exceptions**
   - *Visual:* Card with Warning Callout
   - *Measure:* `[Open Critical Exceptions]` (Format: `0`, Color: `#EF4444`)
5. **Reconciliation Match Rate %**
   - *Visual:* Card
   - *Measure:* `[Reconciliation Match Rate %]` (Format: `0.00%`)

### Row 2: Trend & Distribution Visuals (Y=260, Height=280)
- **Visual 1 (Left, Width=580): Historical Quality Score Progression**
  - *Type:* Line & Clustered Column Chart
  - *X-Axis:* `quality_run_history[evaluated_at]` (or `batch_id`)
  - *Columns (Y-Axis):* `[Clean Records Passed]`, `[Failed Records Count]`
  - *Line (Secondary Y-Axis):* `[Overall Composite Quality Score %]`
- **Visual 2 (Right, Width=580): Exceptions by Dimension & Severity**
  - *Type:* Stacked Bar Chart
  - *Y-Axis:* `quality_rules[dimension]`
  - *X-Axis:* `[Total Exceptions Detected]`
  - *Legend:* `quality_rules[severity]` (Custom color mapped: CRITICAL, HIGH, MEDIUM, LOW)

### Row 3: Source System Breakdown & Top Rule Failures (Y=560, Height=220)
- **Visual 3 (Left, Width=580): Quality Index by Source System**
  - *Type:* Clustered Column Chart
  - *X-Axis:* `stg_transactions[source_system]`
  - *Y-Axis:* `[Completeness Score %]`, `[Validity Score %]`, `[Uniqueness Score %]`, `[Integrity Score %]`
- **Visual 4 (Right, Width=580): Top 5 Violated Data Quality Rules**
  - *Type:* Horizontal Bar Chart
  - *Y-Axis:* `quality_rules[name]`
  - *X-Axis:* `[Total Exceptions Detected]` (Filtered to Top 5 by count)

---

## Page 2: Exception Investigation & Remediation

**Goal:** Enable financial operations and data stewards to inspect, filter, age, and resolve transaction anomalies with full record-level traceability.

### Row 1: Summary Slicers & Metrics (Y=80, Height=90)
- **Cards:**
  - `[Open Critical Exceptions]`
  - `[Open High Exceptions]`
  - `[Exception Resolution Rate %]`
  - `[Average Exception Age (Days)]`
- **Slicers:**
  - Severity Selector (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`)
  - Resolution State (`OPEN`, `UNDER_REVIEW`, `RESOLVED`)
  - Rule Dimension (`COMPLETENESS`, `VALIDITY`, `UNIQUENESS`, `INTEGRITY`, `CONSISTENCY`)

### Row 2: Aging & Workflow Visuals (Y=190, Height=240)
- **Visual 1 (Left, Width=400): Exception Aging Distribution**
  - *Type:* Clustered Column Chart
  - *X-Axis:* `vw_exception_aging[aging_bracket]` (`0-1 Days`, `2-7 Days`, `8-30 Days`, `30+ Days`)
  - *Y-Axis:* Count of Exceptions
  - *Legend:* `severity`
- **Visual 2 (Center, Width=400): Exception Volume by Resolution State**
  - *Type:* Donut Chart
  - *Legend:* `exception_register[resolution_status]`
  - *Values:* Count of Exceptions
- **Visual 3 (Right, Width=360): Exceptions by Account Type**
  - *Type:* Bar Chart
  - *Y-Axis:* `dim_accounts[account_type]`
  - *X-Axis:* Count of Exceptions

### Row 3: Detailed Exception Investigation Grid (Y=450, Height=330)
- *Type:* Table / Matrix with conditional formatting
- *Columns:*
  1. `exception_id`
  2. `batch_id`
  3. `record_reference` (Transaction or Source ID)
  4. `rule_name`
  5. `severity` (Background highlighted with soft red/orange/yellow)
  6. `field_name`
  7. `invalid_value`
  8. `issue_description`
  9. `resolution_status`
  10. `investigation_action`
- *Drill-Through Target:* Right-click any row to filter related transaction in `stg_transactions`.

---

## Page 3: Financial Reconciliation & Monitoring

**Goal:** Compare transaction feeds against accounting settlement ledgers, detect tolerance differences, and isolate multi-currency variances.

### Row 1: Reconciliation KPIs (Y=80, Height=90)
1. **Total Comparisons Evaluated:** `[Reconciliation Total Comparisons]`
2. **Exact Matches:** `[Reconciliation Exact Matches]`
3. **Within Tolerance Matches:** `[Reconciliation Matched Within Tolerance]`
4. **Reconciliation Break Rate %:** `100 - [Reconciliation Match Rate %]`
5. **Total Absolute Variance:** `[Total Absolute Variance]` (Formatted in Currency)

### Row 2: Currency-Isolated Aggregate Reconciliation (Y=190, Height=250)
- *Type:* Matrix
- *Rows:* `reconciliation_results[currency]`
- *Columns:* `reconciliation_results[recon_type]` (`RECORD_LEVEL`, `AGGREGATE`)
- *Values:*
  - `[Total Source Amount]`
  - `[Total Target Amount]`
  - `[Net Signed Variance]` (Conditional format: Red font if != 0)
  - `[Total Absolute Variance]`
  - `[Reconciliation Match Rate %]`

### Row 3: Break Classifications & Detailed Variance Log (Y=460, Height=320)
- **Visual 1 (Left, Width=380): Reconciliation Status Breakdown**
  - *Type:* Donut Chart
  - *Legend:* `reconciliation_results[match_status]` (`EXACT_MATCH`, `WITHIN_TOLERANCE`, `AMOUNT_MISMATCH`, `SOURCE_ONLY`, `TARGET_ONLY`)
  - *Values:* Count of Records
- **Visual 2 (Right, Width=780): Reconciliation Discrepancy Register**
  - *Type:* Table
  - *Columns:*
    1. `recon_id`
    2. `source_id`
    3. `target_id`
    4. `currency`
    5. `source_amount`
    6. `target_amount`
    7. `signed_difference`
    8. `tolerance`
    9. `match_status`
    10. `reconciled_at`
  - *Filter:* Visual-level filter applied where `match_status IN {"AMOUNT_MISMATCH", "SOURCE_ONLY", "TARGET_ONLY"}`
