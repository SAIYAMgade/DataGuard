"""Database Initialization Script for DataGuard.

Executes schema DDL, indexes, reporting views, and loads reference dimensions.
"""

import sys
from pathlib import Path

# Add src to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from dataguard.database.connection import execute_sql_file
from dataguard.database.repositories import DimensionRepository


def main():
    print("Initializing DataGuard PostgreSQL Database...")
    schema_dir = BASE_DIR / "sql" / "schema"
    views_file = BASE_DIR / "sql" / "views" / "reporting_views.sql"
    cust_file = BASE_DIR / "data" / "sample" / "dim_customers.csv"
    acc_file = BASE_DIR / "data" / "sample" / "dim_accounts.csv"

    print("1. Executing 001_create_tables.sql...")
    execute_sql_file(schema_dir / "001_create_tables.sql")

    print("2. Executing 002_create_indexes.sql...")
    execute_sql_file(schema_dir / "002_create_indexes.sql")

    print("3. Executing reporting_views.sql...")
    execute_sql_file(views_file)

    if cust_file.exists():
        print("4. Loading Customer Dimension...")
        c_count = DimensionRepository.load_customers(cust_file)
        print(f"   Loaded {c_count} customers.")

    if acc_file.exists():
        print("5. Loading Account Dimension...")
        a_count = DimensionRepository.load_accounts(acc_file)
        print(f"   Loaded {a_count} accounts.")

    print("Database initialization completed successfully!")


if __name__ == "__main__":
    main()
