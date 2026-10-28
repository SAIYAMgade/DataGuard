# DataGuard | Data Quality Rule Catalogue

This document defines the 17 business and technical quality rules implemented in DataGuard.

---

## 1. Rule Catalogue Summary

| Rule ID | Rule Name | Dimension | Severity | Target Field | Primary Business Risk |
|---|---|---|---|---|---|
| **DQ001** | Missing Transaction Identifier | COMPLETENESS | CRITICAL | `transaction_id` | Unidentifiable transaction cannot settle or clear |
| **DQ002** | Missing Account Identifier | COMPLETENESS | CRITICAL | `account_id` | Transaction cannot post to customer ledger |
| **DQ003** | Missing Transaction Date | COMPLETENESS | HIGH | `transaction_date` | Financial period allocation cannot be determined |
| **DQ004** | Missing Monetary Amount | COMPLETENESS | CRITICAL | `amount` | Financial magnitude unknown; cannot balance ledger |
| **DQ005** | Missing Currency Code | COMPLETENESS | HIGH | `currency` | Monetary amount cannot be evaluated without currency |
| **DQ006** | Missing Transaction Status | COMPLETENESS | HIGH | `transaction_status` | Operational clearing state cannot be determined |
| **DQ007** | Exact Duplicate Source Record | UNIQUENESS | HIGH | `record_hash` | Duplicate ingestion distorts turnover and balances |
| **DQ008** | Duplicate Transaction Identifier | UNIQUENESS | CRITICAL | `transaction_id` | Conflicting records under same key break uniqueness |
| **DQ009** | Potential Business Duplicate | UNIQUENESS | MEDIUM | `account,amount,date,type` | Repeated swipe or accidental double click |
| **DQ010** | Invalid Decimal Precision | VALIDITY | MEDIUM | `amount` | Sub-cent values violate fiat currency conventions |
| **DQ011** | Sign Inconsistency for Type | VALIDITY | HIGH | `amount,type` | Negative deposit or positive refund corrupts reporting |
| **DQ012** | Extreme Outlier Amount | VALIDITY | MEDIUM | `amount` | Outsized amounts require high-value treasury signoff |
| **DQ013** | Future-Dated Transaction | TIMELINESS | HIGH | `transaction_date` | Backwards clock skew or unauthorized scheduled post |
| **DQ014** | Excessive Ingestion Latency | TIMELINESS | LOW | `transaction_date` | Backlogged or delayed batch ingestion (>90 days) |
| **DQ015** | Unknown Account Reference | INTEGRITY | CRITICAL | `account_id` | Orphaned foreign key; account missing in account master |
| **DQ016** | Invalid Type or Status | VALIDITY | HIGH | `type,status` | Unrecognized enumeration disrupts state machine |
| **DQ017** | Reversal Missing Reference | CONSISTENCY | HIGH | `reference_id,type` | Reversal cannot locate original parent transaction |

---

## 2. Rule Detail & Technical Logic

### DQ001: Missing Transaction Identifier
- **Dimension:** COMPLETENESS | **Severity:** CRITICAL
- **Logic:** `transaction_id IS NULL OR TRIM(transaction_id) = ''`
- **Investigation Action:** Inspect ingestion mapping; check source delimiter and column offsets.

### DQ007: Exact Duplicate Source Record
- **Dimension:** UNIQUENESS | **Severity:** HIGH
- **Logic:** `ROW_NUMBER() OVER (PARTITION BY batch_id, record_hash ORDER BY staging_id) > 1`
- **Investigation Action:** Verify upstream retry mechanism or upstream message bus replay.

### DQ009: Potential Business Duplicate
- **Dimension:** UNIQUENESS | **Severity:** MEDIUM
- **Logic:** Identical `account_id`, `amount`, `transaction_date`, and `transaction_type` within the same batch.
- **Investigation Action:** Do NOT automatically delete. Review customer transaction history to differentiate rapid intentional payments from double-clicks.

### DQ010: Invalid Decimal Precision
- **Dimension:** VALIDITY | **Severity:** MEDIUM
- **Logic:** For currencies `USD`, `EUR`, `GBP`, more than 2 digits exist after decimal point (`amount * 100 != FLOOR(amount * 100)`).
- **Investigation Action:** Check upstream rounding logic and prevent floating-point binary conversion leaks.

### DQ011: Sign Inconsistency for Transaction Type
- **Dimension:** VALIDITY | **Severity:** HIGH
- **Logic:** `transaction_type IN ('DEPOSIT', 'PAYMENT', 'TRANSFER') AND amount <= 0.00`. Negative signs are restricted to `REFUND`, `REVERSAL`, and `FEE`.
- **Investigation Action:** Verify whether upstream feed uses unsigned absolute values with direction indicators (`DR`/`CR`) or signed net amounts.

### DQ015: Unknown Account Reference
- **Dimension:** INTEGRITY | **Severity:** CRITICAL
- **Logic:** `stg_transactions.account_id NOT IN (SELECT account_id FROM dim_accounts WHERE status = 'ACTIVE')`.
- **Investigation Action:** Check account master onboarding feed; ensure account creation events are processed before transaction batches.
