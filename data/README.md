# DataGuard Data Directory

Contains synthetic transaction feeds and reference dimensions for DataGuard.

- `sample/dim_customers.csv`: Customer dimension (50 records)
- `sample/dim_accounts.csv`: Account dimension (100 records)
- `sample/transactions_baseline.csv`: Clean baseline dataset (500 records)
- `sample/transactions_corrupted.csv`: Anomaly-injected dataset (303 records, 17 documented rule failures)
- `sample/target_ledger.csv`: External reconciliation target ledger
- `sample/anomaly_manifest.json`: Exact ground truth tracking for automated regression assertions.
