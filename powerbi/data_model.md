# DataGuard | Power BI Star Schema Data Model Specification

## 1. Dimensional Architecture

The DataGuard Power BI model is structured as a **hybrid star/snowflake schema** optimized for fast dimensional slicing, exception drill-down, and cross-batch historical comparisons.

```
                  ┌──────────────────────┐
                  │    dim_customers     │
                  │ (Customer Reference) │
                  └──────────┬───────────┘
                             │ 1
                             │
                             │ *
                  ┌──────────┴───────────┐
                  │     dim_accounts     │
                  │  (Account Reference) │
                  └──────────┬───────────┘
                             │ 1
                             │
                             │ *
 ┌─────────────────┐       ┌─┴────────────────┐       ┌──────────────────────┐
 │ quality_rules   ├─1──*──┤exception_register├──*──1─┤ ingestion_batches    │
 │ (Rule Metadata) │       │ (Fact: Anomaly)  │       │ (Ingestion Metadata) │
 └─────────────────┘       └──────────────────┘       └──────────┬───────────┘
                                                                 │ 1
                                                                 │
                                                                 │ *
 ┌──────────────────────┐       ┌────────────────────┐       ┌───┴──────────────┐
 │ reconciliation_res   ├──*──1─┤ quality_run_history├──1──*─┤ stg_transactions │
 │ (Fact: Recon Break)  │       │ (Fact: Batch Score)│       │ (Fact: Tx Ledger)│
 └──────────────────────┘       └────────────────────┘       └──────────────────┘
```

---

## 2. Table Classifications and Cardinality

### Dimension Tables

1. **`dim_customers`** (Dimension)
   - **Primary Key:** `customer_id`
   - **Role:** Customer demographics, entity classification (Corporate vs. Individual), KYC tier, country.

2. **`dim_accounts`** (Dimension)
   - **Primary Key:** `account_id`
   - **Foreign Key:** `customer_id` → `dim_customers.customer_id` (Many-to-One `*:1`, Single direction)
   - **Role:** Account type (Checking, Savings, Investment), base currency, operational account state.

3. **`quality_rules`** (Dimension)
   - **Primary Key:** `rule_id`
   - **Role:** Rule definitions (DQ001 to DQ017), quality dimensions, default severity levels, investigation guidelines.

4. **`dim_date`** (Auto-generated or Standard Power BI Date Table)
   - **Primary Key:** `Date`
   - **Role:** Time intelligence, calendar slicing, batch chronological trend lines.

### Fact Tables

1. **`stg_transactions`** (Transactional Fact)
   - **Primary Key:** `staging_id`
   - **Foreign Keys:**
     - `batch_id` → `ingestion_batches.batch_id` (Many-to-One `*:1`)
     - `account_id` → `dim_accounts.account_id` (Many-to-One `*:1`)
   - **Measures:** Transaction volume, monetary amounts, currency isolation.

2. **`exception_register`** (Accumulating Snapshot Fact)
   - **Primary Key:** `exception_id`
   - **Foreign Keys:**
     - `rule_id` → `quality_rules.rule_id` (Many-to-One `*:1`)
     - `batch_id` → `ingestion_batches.batch_id` (Many-to-One `*:1`)
     - `run_id` → `quality_run_history.run_id` (Many-to-One `*:1`)
   - **Measures:** Open critical count, exception aging, resolution velocity.

3. **`reconciliation_results`** (Reconciliation Break Fact)
   - **Primary Key:** `recon_id`
   - **Foreign Keys:**
     - `batch_id` → `ingestion_batches.batch_id` (Many-to-One `*:1`)
     - `run_id` → `quality_run_history.run_id` (Many-to-One `*:1`)
   - **Measures:** Source amounts, target amounts, signed difference, absolute difference, tolerance checks.

4. **`quality_run_history`** (Periodic Snapshot Fact)
   - **Primary Key:** `run_id`
   - **Foreign Key:** `batch_id` → `ingestion_batches.batch_id` (Many-to-One `*:1`)
   - **Measures:** Batch scores (Completeness, Validity, Uniqueness, Integrity, Composite Score).

---

## 3. Relationship Specifications

| From Table | From Column | To Table | To Column | Cardinality | Cross Filter Direction | Security Filter |
|---|---|---|---|---|---|---|
| `dim_accounts` | `customer_id` | `dim_customers` | `customer_id` | Many to One (`*:1`) | Single | Both |
| `stg_transactions` | `account_id` | `dim_accounts` | `account_id` | Many to One (`*:1`) | Single | Both |
| `stg_transactions` | `batch_id` | `ingestion_batches` | `batch_id` | Many to One (`*:1`) | Single | Both |
| `exception_register` | `rule_id` | `quality_rules` | `rule_id` | Many to One (`*:1`) | Single | Both |
| `exception_register` | `batch_id` | `ingestion_batches` | `batch_id` | Many to One (`*:1`) | Single | Both |
| `quality_run_history` | `batch_id` | `ingestion_batches` | `batch_id` | Many to One (`*:1`) | Single | Both |
| `reconciliation_results` | `batch_id` | `ingestion_batches` | `batch_id` | Many to One (`*:1`) | Single | Both |
| `stg_transactions` | `transaction_date` | `dim_date` | `Date` | Many to One (`*:1`) | Single | Both |

---

## 4. Handling of Blank and Null Values

- **Missing Primary Keys:** Records with missing `transaction_id` or `account_id` are loaded into staging with `NULL` to preserve observability in the data quality layer.
- **Foreign Key Integrity Violations:** Where `account_id` does not exist in `dim_accounts`, Power BI automatically routes orphaned rows to a blank dimension row. In DataGuard, rule `DQ015` immediately flags these orphans as `CRITICAL` exceptions before downstream aggregation.
