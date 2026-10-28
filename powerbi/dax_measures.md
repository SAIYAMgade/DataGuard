# DataGuard | Power BI DAX Measures Library

This document provides the exact DAX measures used across the DataGuard dashboard.
Every measure is engineered to maintain **100% mathematical parity** with the Python metrics engine (`dataguard.quality.metrics`) and the PostgreSQL views (`vw_executive_kpis`, `vw_reconciliation_summary`).

Create a dedicated disconnected table named **`_Measures`** to organize these formulas.

---

## 1. Volume & Baseline Metrics

### `Total Records Ingested`
```dax
Total Records Ingested = 
COUNTROWS(stg_transactions)
```

### `Clean Records Passed`
```dax
Clean Records Passed = 
VAR TotalTxs = [Total Records Ingested]
VAR FailedTxs = DISTINCTCOUNT(exception_register[record_reference])
RETURN
    MAX(0, TotalTxs - FailedTxs)
```

### `Failed Records Count`
```dax
Failed Records Count = 
DISTINCTCOUNT(exception_register[record_reference])
```

### `Data Quality Pass Rate %`
```dax
Data Quality Pass Rate % = 
DIVIDE([Clean Records Passed], [Total Records Ingested], 0) * 100
```

---

## 2. Quality Dimension Scores (0.0% to 100.0%)

### `Completeness Score %`
```dax
Completeness Score % = 
VAR TotalRecs = [Total Records Ingested]
VAR CompFailures = 
    CALCULATE(
        DISTINCTCOUNT(exception_register[record_reference]),
        quality_rules[dimension] = "COMPLETENESS"
    )
RETURN
    IF(TotalRecs = 0, 100.0, MAX(0.0, (1 - DIVIDE(CompFailures, TotalRecs, 0)) * 100))
```

### `Validity Score %`
```dax
Validity Score % = 
VAR TotalRecs = [Total Records Ingested]
VAR ValidFailures = 
    CALCULATE(
        DISTINCTCOUNT(exception_register[record_reference]),
        quality_rules[dimension] = "VALIDITY"
    )
RETURN
    IF(TotalRecs = 0, 100.0, MAX(0.0, (1 - DIVIDE(ValidFailures, TotalRecs, 0)) * 100))
```

### `Uniqueness Score %`
```dax
Uniqueness Score % = 
VAR TotalRecs = [Total Records Ingested]
VAR UniqFailures = 
    CALCULATE(
        DISTINCTCOUNT(exception_register[record_reference]),
        quality_rules[dimension] = "UNIQUENESS"
    )
RETURN
    IF(TotalRecs = 0, 100.0, MAX(0.0, (1 - DIVIDE(UniqFailures, TotalRecs, 0)) * 100))
```

### `Integrity Score %`
```dax
Integrity Score % = 
VAR TotalRecs = [Total Records Ingested]
VAR IntegFailures = 
    CALCULATE(
        DISTINCTCOUNT(exception_register[record_reference]),
        quality_rules[dimension] = "INTEGRITY"
    )
RETURN
    IF(TotalRecs = 0, 100.0, MAX(0.0, (1 - DIVIDE(IntegFailures, TotalRecs, 0)) * 100))
```

### `Overall Composite Quality Score %`
```dax
Overall Composite Quality Score % = 
(0.25 * [Completeness Score %]) +
(0.35 * [Validity Score %]) +
(0.20 * [Uniqueness Score %]) +
(0.20 * [Integrity Score %])
```

---

## 3. Exception & Operational Risk Measures

### `Total Exceptions Detected`
```dax
Total Exceptions Detected = 
COUNTROWS(exception_register)
```

### `Open Critical Exceptions`
```dax
Open Critical Exceptions = 
CALCULATE(
    COUNTROWS(exception_register),
    exception_register[severity] = "CRITICAL",
    exception_register[resolution_status] = "OPEN"
)
```

### `Open High Exceptions`
```dax
Open High Exceptions = 
CALCULATE(
    COUNTROWS(exception_register),
    exception_register[severity] = "HIGH",
    exception_register[resolution_status] = "OPEN"
)
```

### `Exception Resolution Rate %`
```dax
Exception Resolution Rate % = 
VAR TotalExc = COUNTROWS(exception_register)
VAR ResolvedExc = 
    CALCULATE(
        COUNTROWS(exception_register),
        exception_register[resolution_status] IN {"RESOLVED", "FALSE_POSITIVE"}
    )
RETURN
    DIVIDE(ResolvedExc, TotalExc, 0) * 100
```

### `Average Exception Age (Days)`
```dax
Average Exception Age (Days) = 
AVERAGEX(
    FILTER(exception_register, exception_register[resolution_status] IN {"OPEN", "UNDER_REVIEW"}),
    DATEDIFF(exception_register[detected_at], NOW(), DAY)
)
```

---

## 4. Financial Reconciliation Measures

### `Reconciliation Total Comparisons`
```dax
Reconciliation Total Comparisons = 
COUNTROWS(reconciliation_results)
```

### `Reconciliation Exact Matches`
```dax
Reconciliation Exact Matches = 
CALCULATE(
    COUNTROWS(reconciliation_results),
    reconciliation_results[match_status] = "EXACT_MATCH"
)
```

### `Reconciliation Matched Within Tolerance`
```dax
Reconciliation Matched Within Tolerance = 
CALCULATE(
    COUNTROWS(reconciliation_results),
    reconciliation_results[match_status] = "WITHIN_TOLERANCE"
)
```

### `Reconciliation Match Rate %`
```dax
Reconciliation Match Rate % = 
VAR Matched = 
    CALCULATE(
        COUNTROWS(reconciliation_results),
        reconciliation_results[match_status] IN {"EXACT_MATCH", "WITHIN_TOLERANCE"}
    )
VAR Total = COUNTROWS(reconciliation_results)
RETURN
    DIVIDE(Matched, Total, 0) * 100
```

### `Total Source Amount (Isolated by Currency)`
```dax
Total Source Amount = 
IF(
    HASONEVALUE(stg_transactions[currency]) || HASONEVALUE(reconciliation_results[currency]),
    SUM(reconciliation_results[source_amount]),
    BLANK() -- Prevents illegal cross-currency aggregation
)
```

### `Total Target Amount (Isolated by Currency)`
```dax
Total Target Amount = 
IF(
    HASONEVALUE(stg_transactions[currency]) || HASONEVALUE(reconciliation_results[currency]),
    SUM(reconciliation_results[target_amount]),
    BLANK() -- Prevents illegal cross-currency aggregation
)
```

### `Net Signed Variance`
```dax
Net Signed Variance = 
IF(
    HASONEVALUE(reconciliation_results[currency]),
    SUM(reconciliation_results[signed_difference]),
    BLANK()
)
```

### `Total Absolute Variance`
```dax
Total Absolute Variance = 
SUM(reconciliation_results[absolute_difference])
```
