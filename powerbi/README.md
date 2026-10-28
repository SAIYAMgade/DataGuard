# DataGuard | Power BI Implementation Guide

This directory contains the complete data architecture, dimensional modeling, DAX measure catalogue, and visual layout specifications for the interactive **DataGuard Power BI Dashboard**.

## Deliverables Status

| Deliverable | Format | Status | Execution Method |
|---|---|---|---|
| Reporting SQL Views | `.sql` | **Executable & Verified** | Created natively in PostgreSQL (`sql/views/reporting_views.sql`) |
| CSV Data Feeds | `.csv` | **Executable & Generated** | Auto-exported to `reports/sample_outputs/` |
| Star Schema Data Model | `.md` | **Documented Specification** | Import via PostgreSQL Connector or CSV folder |
| DAX Measures Library | `.md` | **Documented Specification** | 20+ copy-paste DAX formulas with exact mathematical parity |
| 3-Page Dashboard Layout | `.md` | **Documented Specification** | Step-by-step visual configuration guide |
| Native `.pbix` File | `.pbix` | **Manual Creation Required** | Power BI Desktop GUI required on desktop client |

---

## How to Build the Dashboard in Power BI Desktop

### Method A: Direct Connection to PostgreSQL (Recommended)
1. Open **Power BI Desktop**.
2. Select **Get Data** > **PostgreSQL database**.
3. Server: `localhost:5432`, Database: `dataguard`.
4. Select Data Connectivity mode: **Import** (or **DirectQuery** for real-time monitoring).
5. In the Navigator dialog, select the following views and tables:
   - `vw_executive_kpis`
   - `vw_batch_quality_summary`
   - `vw_rule_failure_distribution`
   - `vw_exception_aging`
   - `vw_reconciliation_summary`
   - `stg_transactions`
   - `exception_register`
   - `quality_rules`
   - `dim_accounts`
   - `dim_customers`
6. Click **Load**.

### Method B: Standalone CSV Import (Offline / Sandbox Mode)
If running without a local PostgreSQL instance:
1. Select **Get Data** > **Text/CSV**.
2. Navigate to `reports/sample_outputs/`:
   - `kpis_export.csv`
   - `exceptions_export.csv`
   - `reconciliation_export.csv`
   - `quality_runs_export.csv`
3. Click **Load**.

---

## Next Steps
- Review [data_model.md](data_model.md) to set table relationships and cardinality.
- Review [dax_measures.md](dax_measures.md) to create the calculated measures table.
- Review [dashboard_specification.md](dashboard_specification.md) to assemble Pages 1, 2, and 3.
