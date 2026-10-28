"""DataGuard Sample Data Generator.

Generates deterministic financial transaction datasets for DataGuard:
1. dim_customers.csv: Customer reference data
2. dim_accounts.csv: Account reference data
3. transactions_baseline.csv: 100% clean, valid financial transactions
4. transactions_corrupted.csv: Injected with documented, deterministic anomalies
5. target_ledger.csv: Target accounting ledger for financial reconciliation testing
6. anomaly_manifest.json: Ground-truth audit log of all injected anomalies
"""

import csv
import json
import os
import random
from datetime import date, datetime, timedelta
from decimal import Decimal

# Set fixed seeds for absolute reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sample")
os.makedirs(DATA_DIR, exist_ok=True)

CURRENCIES = ["USD", "EUR", "GBP"]
TX_TYPES = ["DEPOSIT", "WITHDRAWAL", "PAYMENT", "REFUND", "TRANSFER", "FEE", "REVERSAL"]
TX_STATUSES = ["COMPLETED", "PENDING", "FAILED", "REVERSED", "CANCELLED"]
ACCOUNT_TYPES = ["CHECKING", "SAVINGS", "INVESTMENT", "CREDIT"]
CUSTOMER_TYPES = ["INDIVIDUAL", "CORPORATE"]
COUNTRIES = ["USA", "GBR", "DEU", "FRA", "CAN"]


def generate_reference_data():
    """Generates customer and account reference dimensions."""
    customers = []
    for i in range(1, 51):
        cust_id = f"CUST_{i:04d}"
        cust_type = "CORPORATE" if i % 4 == 0 else "INDIVIDUAL"
        country = COUNTRIES[i % len(COUNTRIES)]
        customers.append({
            "customer_id": cust_id,
            "customer_name": f"Client {cust_id}",
            "customer_type": cust_type,
            "country": country,
            "kyc_status": "VERIFIED"
        })

    accounts = []
    for i in range(1, 101):
        acc_id = f"ACC_{i:04d}"
        cust_id = customers[(i - 1) % len(customers)]["customer_id"]
        acc_type = ACCOUNT_TYPES[i % len(ACCOUNT_TYPES)]
        currency = CURRENCIES[i % len(CURRENCIES)]
        opened_date = (date(2022, 1, 1) + timedelta(days=i * 10)).isoformat()
        accounts.append({
            "account_id": acc_id,
            "customer_id": cust_id,
            "account_type": acc_type,
            "currency": currency,
            "status": "ACTIVE",
            "opened_date": opened_date
        })

    # Save to CSV
    cust_file = os.path.join(DATA_DIR, "dim_customers.csv")
    with open(cust_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["customer_id", "customer_name", "customer_type", "country", "kyc_status"])
        writer.writeheader()
        writer.writerows(customers)

    acc_file = os.path.join(DATA_DIR, "dim_accounts.csv")
    with open(acc_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["account_id", "customer_id", "account_type", "currency", "status", "opened_date"])
        writer.writeheader()
        writer.writerows(accounts)

    return customers, accounts


def generate_baseline_transactions(accounts, count=500):
    """Generates 100% clean baseline transactions."""
    transactions = []
    base_date = date(2026, 9, 1)

    for i in range(1, count + 1):
        tx_id = f"TXN_BASE_{i:06d}"
        acc = accounts[(i - 1) % len(accounts)]
        tx_date = (base_date + timedelta(days=i % 45)).isoformat()
        tx_type = TX_TYPES[i % len(TX_TYPES)]
        
        # Valid amount rules: strictly positive for deposits/payments, negative for fees/refunds
        if tx_type in ["FEE", "REFUND"]:
            amount = f"-{round(random.uniform(5.00, 150.00), 2):.2f}"
        else:
            amount = f"{round(random.uniform(20.00, 5000.00), 2):.2f}"

        ref_id = f"REF_{i:06d}" if tx_type in ["REVERSAL", "REFUND"] else ""

        transactions.append({
            "transaction_id": tx_id,
            "source_record_id": f"SRC_REC_{i:06d}",
            "source_system": "CORE_BANKING_A",
            "account_id": acc["account_id"],
            "customer_id": acc["customer_id"],
            "transaction_date": tx_date,
            "transaction_type": tx_type,
            "amount": amount,
            "currency": acc["currency"],
            "transaction_status": "COMPLETED",
            "reference_id": ref_id,
            "description": f"Standard {tx_type.lower()} transaction"
        })

    tx_file = os.path.join(DATA_DIR, "transactions_baseline.csv")
    with open(tx_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "transaction_id", "source_record_id", "source_system", "account_id",
            "customer_id", "transaction_date", "transaction_type", "amount",
            "currency", "transaction_status", "reference_id", "description"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transactions)

    return transactions


def generate_corrupted_dataset(baseline_txs, accounts):
    """
    Creates an anomaly-injected dataset with a deterministic ground-truth manifest.
    Covers DQ001 to DQ017.
    """
    corrupted = [dict(t) for t in baseline_txs[:300]]
    manifest = []

    def log_anomaly(rec_ref, rule_id, field, expected_desc):
        manifest.append({
            "record_reference": rec_ref,
            "rule_id": rule_id,
            "target_field": field,
            "description": expected_desc
        })

    # 1. DQ001: Missing transaction_id
    corrupted[10]["transaction_id"] = ""
    log_anomaly(corrupted[10]["source_record_id"], "DQ001", "transaction_id", "Empty transaction_id")

    # 2. DQ002: Missing account_id
    corrupted[15]["account_id"] = ""
    log_anomaly(corrupted[15]["transaction_id"], "DQ002", "account_id", "Empty account_id")

    # 3. DQ003: Missing transaction_date
    corrupted[20]["transaction_date"] = ""
    log_anomaly(corrupted[20]["transaction_id"], "DQ003", "transaction_date", "Missing date")

    # 4. DQ004: Missing amount
    corrupted[25]["amount"] = ""
    log_anomaly(corrupted[25]["transaction_id"], "DQ004", "amount", "Missing amount")

    # 5. DQ005: Missing currency
    corrupted[30]["currency"] = ""
    log_anomaly(corrupted[30]["transaction_id"], "DQ005", "currency", "Missing currency")

    # 6. DQ006: Missing transaction_status
    corrupted[35]["transaction_status"] = ""
    log_anomaly(corrupted[35]["transaction_id"], "DQ006", "transaction_status", "Missing status")

    # 7. DQ007: Exact Duplicate Source Record
    exact_dup = dict(corrupted[40])
    corrupted.append(exact_dup)
    log_anomaly(exact_dup["transaction_id"], "DQ007", "record_hash", "Exact duplicate payload")

    # 8. DQ008: Duplicate Transaction Identifier
    id_dup = dict(corrupted[45])
    id_dup["source_record_id"] = "SRC_REC_DUP_9999"
    id_dup["amount"] = "999.99"
    corrupted.append(id_dup)
    log_anomaly(id_dup["transaction_id"], "DQ008", "transaction_id", "Duplicate transaction ID with different amount")

    # 9. DQ009: Potential Business Duplicate (same account, amount, date, type)
    biz_dup = dict(corrupted[50])
    biz_dup["transaction_id"] = "TXN_BIZ_DUP_0001"
    biz_dup["source_record_id"] = "SRC_REC_BIZ_0001"
    corrupted.append(biz_dup)
    log_anomaly(biz_dup["transaction_id"], "DQ009", "account_id,amount,transaction_date,transaction_type", "Potential business duplicate")

    # 10. DQ010: Invalid Decimal Precision (>2 decimal places)
    corrupted[60]["amount"] = "145.8945"
    log_anomaly(corrupted[60]["transaction_id"], "DQ010", "amount", "Fractional cents: 145.8945")

    # 11. DQ011: Sign Inconsistency (Negative Deposit)
    corrupted[70]["transaction_type"] = "DEPOSIT"
    corrupted[70]["amount"] = "-450.00"
    log_anomaly(corrupted[70]["transaction_id"], "DQ011", "amount,transaction_type", "Negative deposit")

    # 12. DQ012: Extreme Outlier Amount
    corrupted[80]["amount"] = "55000000.00"
    log_anomaly(corrupted[80]["transaction_id"], "DQ012", "amount", "Extreme outlier amount $55M")

    # 13. DQ013: Future-Dated Transaction
    corrupted[90]["transaction_date"] = (date.today() + timedelta(days=45)).isoformat()
    log_anomaly(corrupted[90]["transaction_id"], "DQ013", "transaction_date", "Future date")

    # 14. DQ014: Excessive Ingestion Latency (Old Date > 180 days)
    corrupted[100]["transaction_date"] = "2025-01-15"
    log_anomaly(corrupted[100]["transaction_id"], "DQ014", "transaction_date,ingestion_timestamp", "Stale transaction > 90 days")

    # 15. DQ015: Unknown Account Reference
    corrupted[110]["account_id"] = "ACC_UNKNOWN_9999"
    log_anomaly(corrupted[110]["transaction_id"], "DQ015", "account_id", "Unknown account ACC_UNKNOWN_9999")

    # 16. DQ016: Invalid Transaction Type
    corrupted[120]["transaction_type"] = "CRYPTO_STAKE"
    log_anomaly(corrupted[120]["transaction_id"], "DQ016", "transaction_type,transaction_status", "Invalid type CRYPTO_STAKE")

    # 17. DQ017: Reversal Missing Reference
    corrupted[130]["transaction_type"] = "REVERSAL"
    corrupted[130]["reference_id"] = ""
    log_anomaly(corrupted[130]["transaction_id"], "DQ017", "reference_id,transaction_type", "Reversal missing reference_id")

    # Write corrupted CSV
    corr_file = os.path.join(DATA_DIR, "transactions_corrupted.csv")
    with open(corr_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "transaction_id", "source_record_id", "source_system", "account_id",
            "customer_id", "transaction_date", "transaction_type", "amount",
            "currency", "transaction_status", "reference_id", "description"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(corrupted)

    # Write Manifest JSON
    manifest_file = os.path.join(DATA_DIR, "anomaly_manifest.json")
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return corrupted, manifest


def generate_reconciliation_ledger(transactions):
    """
    Generates target_ledger.csv for reconciliation comparisons:
    - 250 Exact Matches
    - 15 Records within tolerance ($0.005 difference)
    - 15 Records outside tolerance ($10 to $500 difference)
    - 20 Source-Only records (omitted from ledger)
    - 20 Target-Only records (present in ledger, absent in source feed)
    """
    ledger = []
    
    # 1. Exact matches (first 200)
    for tx in transactions[:200]:
        if not tx["transaction_id"] or not tx["amount"]:
            continue
        ledger.append({
            "ledger_id": tx["transaction_id"],
            "account_id": tx["account_id"] or "ACC_0001",
            "transaction_date": tx["transaction_date"] or "2026-09-15",
            "amount": tx["amount"],
            "currency": tx["currency"] or "USD",
            "external_ref": tx["source_record_id"],
            "posted_date": tx["transaction_date"] or "2026-09-15"
        })

    # 2. Within tolerance difference (e.g. 0.005 rounding diff)
    for tx in transactions[200:215]:
        if not tx["transaction_id"] or not tx["amount"]:
            continue
        try:
            amt = Decimal(tx["amount"]) + Decimal("0.005")
        except Exception:
            amt = Decimal("100.005")
        ledger.append({
            "ledger_id": tx["transaction_id"],
            "account_id": tx["account_id"],
            "transaction_date": tx["transaction_date"],
            "amount": f"{amt:.4f}",
            "currency": tx["currency"],
            "external_ref": tx["source_record_id"],
            "posted_date": tx["transaction_date"]
        })

    # 3. Outside tolerance mismatch
    for tx in transactions[215:230]:
        if not tx["transaction_id"] or not tx["amount"]:
            continue
        try:
            amt = Decimal(tx["amount"]) + Decimal("25.50")
        except Exception:
            amt = Decimal("125.50")
        ledger.append({
            "ledger_id": tx["transaction_id"],
            "account_id": tx["account_id"],
            "transaction_date": tx["transaction_date"],
            "amount": f"{amt:.2f}",
            "currency": tx["currency"],
            "external_ref": tx["source_record_id"],
            "posted_date": tx["transaction_date"]
        })

    # 4. Target-only records
    for i in range(1, 21):
        target_id = f"LEDGER_TGT_ONLY_{i:04d}"
        ledger.append({
            "ledger_id": target_id,
            "account_id": f"ACC_{(i % 50) + 1:04d}",
            "transaction_date": "2026-09-20",
            "amount": f"{round(random.uniform(50.00, 2000.00), 2):.2f}",
            "currency": CURRENCIES[i % len(CURRENCIES)],
            "external_ref": f"EXT_SETTLE_{i:04d}",
            "posted_date": "2026-09-20"
        })

    ledger_file = os.path.join(DATA_DIR, "target_ledger.csv")
    with open(ledger_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["ledger_id", "account_id", "transaction_date", "amount", "currency", "external_ref", "posted_date"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ledger)

    return ledger


def main():
    print("Generating DataGuard synthetic reference and transaction datasets...")
    customers, accounts = generate_reference_data()
    print(f"Generated {len(customers)} customers and {len(accounts)} accounts.")

    baseline = generate_baseline_transactions(accounts, count=500)
    print(f"Generated {len(baseline)} baseline transactions.")

    corrupted, manifest = generate_corrupted_dataset(baseline, accounts)
    print(f"Generated {len(corrupted)} corrupted transactions with {len(manifest)} injected anomalies.")

    ledger = generate_reconciliation_ledger(corrupted)
    print(f"Generated {len(ledger)} target ledger entries for reconciliation.")

    # Also place README in data/
    readme_path = os.path.join(os.path.dirname(DATA_DIR), "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("# DataGuard Data Directory\n\n"
                "Contains synthetic transaction feeds and reference dimensions for DataGuard.\n\n"
                "- `sample/dim_customers.csv`: Customer dimension (50 records)\n"
                "- `sample/dim_accounts.csv`: Account dimension (100 records)\n"
                "- `sample/transactions_baseline.csv`: Clean baseline dataset (500 records)\n"
                "- `sample/transactions_corrupted.csv`: Anomaly-injected dataset (303 records, 17 documented rule failures)\n"
                "- `sample/target_ledger.csv`: External reconciliation target ledger\n"
                "- `sample/anomaly_manifest.json`: Exact ground truth tracking for automated regression assertions.\n")

    print("Data generation completed successfully.")


if __name__ == "__main__":
    main()
