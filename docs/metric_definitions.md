# DataGuard | Data Quality Metric Definitions & Mathematical Foundations

In compliance with DataGuard Engineering Rule 3 (*"Every metric must have a definition"*), this document specifies the exact mathematical formulae, numerators, denominators, and treatment of missing data for all calculated metrics.

---

## 1. Completeness Rate (%)

Measures the proportion of eligible records possessing all mandatory primary identifiers and values.

$$\text{Completeness Rate} = \left( 1 - \frac{\text{Records with Completeness Rule Violations}}{\text{Total Records Ingested}} \right) \times 100$$

- **Completeness Rules:** `DQ001` (transaction_id), `DQ002` (account_id), `DQ003` (date), `DQ004` (amount), `DQ005` (currency), `DQ006` (status).
- **Numerator:** Distinct count of records failing at least one completeness rule.
- **Denominator:** Total records in the batch (`stg_transactions`).
- **Edge Cases:** If `Total Records == 0`, rate defaults to `100.0%`.

---

## 2. Validity Rate (%)

Measures the proportion of records whose attribute values conform to domain business constraints, valid enumerations, and mathematical limits.

$$\text{Validity Rate} = \left( 1 - \frac{\text{Records with Validity Rule Violations}}{\text{Total Records Ingested}} \right) \times 100$$

- **Validity Rules:** `DQ010` (decimal precision), `DQ011` (sign consistency), `DQ012` (outliers), `DQ013` (future dates), `DQ014` (latency), `DQ016` (enum validation), `DQ017` (reversal references).
- **Numerator:** Distinct count of records failing at least one validity rule.
- **Denominator:** Total records in the batch.

---

## 3. Uniqueness Rate (%)

Measures the proportion of records that are distinct and free from duplicate ingestion or key collisions.

$$\text{Uniqueness Rate} = \left( 1 - \frac{\text{Records Flagged as Duplicates}}{\text{Total Records Ingested}} \right) \times 100$$

- **Uniqueness Rules:** `DQ007` (exact payload duplicates), `DQ008` (identifier collisions), `DQ009` (potential business duplicates).
- **Numerator:** Distinct count of duplicate occurrences (`rank > 1`).
- **Denominator:** Total records in the batch.

---

## 4. Referential Integrity Rate (%)

Measures the proportion of foreign key entity references that successfully resolve against active master dimension tables.

$$\text{Integrity Rate} = \left( 1 - \frac{\text{Records Referencing Unknown Accounts}}{\text{Total Records Ingested}} \right) \times 100$$

- **Integrity Rule:** `DQ015` (account_id in dim_accounts).
- **Numerator:** Distinct count of records with orphaned `account_id`.
- **Denominator:** Total records in the batch.

---

## 5. Overall Composite Quality Score (%)

The composite score synthesizes the four individual quality dimensions into a single index.

$$\text{Overall Score} = (0.25 \times \text{Completeness}) + (0.35 \times \text{Validity}) + (0.20 \times \text{Uniqueness}) + (0.20 \times \text{Integrity})$$

### Dimension Weighting Rationale
1. **Validity (35%):** Carries the highest weight because invalid signs (negative deposits), corrupted decimal precision, or bad enumerations directly corrupt ledger balance calculations and financial statements.
2. **Completeness (25%):** Missing account keys or missing amounts halt transaction clearing entirely.
3. **Uniqueness (20%):** Duplicate transactions distort transaction volume and customer billing.
4. **Integrity (20%):** Orphaned account IDs prevent reconciliation against core customer ledgers.

---

## 6. Financial Reconciliation Match Rate (%)

Measures the proportion of transactional comparisons that match target settlement ledgers within approved tolerance.

$$\text{Reconciliation Match Rate} = \frac{\text{Count}(\text{EXACT\_MATCH}) + \text{Count}(\text{WITHIN\_TOLERANCE})}{\text{Total Comparisons}} \times 100$$

- **Signed Difference:**
  $$\text{Signed Difference} = \text{source\_amount} - \text{target\_amount}$$
- **Absolute Difference:**
  $$\text{Absolute Difference} = |\text{source\_amount} - \text{target\_amount}|$$
- **Tolerance Threshold:** Default $\pm 0.01$ currency units.
