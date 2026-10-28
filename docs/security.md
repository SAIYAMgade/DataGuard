# DataGuard | Security & Responsible Data Handling

DataGuard is engineered under strict defense-in-depth principles appropriate for financial data pipelines.

---

## 1. Credential Management & Secrets Hygiene

- **Zero Committed Credentials:** Passwords, API tokens, and production connection strings are strictly forbidden from source control. `.env` and `*.tmp` files are ignored via `.gitignore`.
- **Environment Configuration:** System settings are loaded dynamically via `python-dotenv` from system environment variables or local `.env` files.
- **Reference Templates:** A sanitized `.env.example` file documents required configuration keys without exposing credentials.

---

## 2. SQL Injection Prevention & Parameterization

- **Strict Parameterization:** Dynamic SQL string concatenation is strictly prohibited. All queries in `repositories.py` and pipeline scripts use SQLAlchemy parameterized expressions (`text("... WHERE id = :id")`) passed with dictionaries of bound parameters.
- **DDL Execution Safety:** Database migrations are loaded from static, verified `.sql` schema files with no external user input interpolation.

---

## 3. Data Sanitization & PII Handling

- **Synthetic Data Disclaimer:** All sample datasets (`transactions_corrupted.csv`, `dim_customers.csv`, `dim_accounts.csv`) are 100% synthetically generated with fixed random seeds. No real customer PII or banking account numbers exist in this repository.
- **Payload Masking in Logs:** Logging formatters omit sensitive account balances and raw card numbers. Error logs capture exception IDs and record references without printing full customer payloads.
- **Role-Based Reporting Views:** Analytical views (`reporting_views.sql`) aggregate data at batch and currency levels, obscuring individual account balances from high-level Power BI reports.

---

## 4. Auditability & Immutability

- **Non-Destructive Logging:** Detected anomalies in `exception_register` and `exception_resolution_history` maintain immutable audit records. Resolution of an exception updates its lifecycle state (`OPEN` → `RESOLVED`) while preserving the original detection timestamp, rule ID, and offending value.
- **Raw Traceability:** Raw source files are preserved verbatim in `raw_transactions` as `JSONB`, ensuring that downstream data cleaning can always be audited against original inputs.
