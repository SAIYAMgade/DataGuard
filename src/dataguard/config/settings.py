"""DataGuard Configuration Settings Module."""

import os
from pathlib import Path
from typing import Any, Dict
import yaml
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


def get_config_path(filename: str = "settings.yaml") -> Path:
    return BASE_DIR / "config" / filename


class Settings:
    def __init__(self, config_dict: Dict[str, Any]):
        self.raw = config_dict
        
        # Database
        db_cfg = config_dict.get("database", {})
        self.db_host = os.getenv("DB_HOST", db_cfg.get("host", "localhost"))
        self.db_port = int(os.getenv("DB_PORT", db_cfg.get("port", 5432)))
        self.db_name = os.getenv("DB_NAME", db_cfg.get("name", "dataguard"))
        self.db_user = os.getenv("DB_USER", db_cfg.get("user", "postgres"))
        self.db_password = os.getenv("DB_PASSWORD", db_cfg.get("password", ""))
        self.db_pool_size = int(db_cfg.get("pool_size", 5))

        # Ingestion
        ingest_cfg = config_dict.get("ingestion", {})
        self.supported_encodings = ingest_cfg.get("supported_encodings", ["utf-8", "utf-8-sig", "latin-1"])
        self.required_columns = ingest_cfg.get("required_columns", [
            "transaction_id", "account_id", "transaction_date",
            "transaction_type", "amount", "currency", "transaction_status"
        ])
        self.max_batch_size = int(os.getenv("MAX_BATCH_SIZE", ingest_cfg.get("max_batch_size", 50000)))

        # Reconciliation
        recon_cfg = config_dict.get("reconciliation", {})
        self.default_tolerance = float(os.getenv("DEFAULT_RECON_TOLERANCE", recon_cfg.get("default_tolerance", 0.01)))
        self.supported_currencies = recon_cfg.get("supported_currencies", ["USD", "EUR", "GBP"])
        self.match_key = recon_cfg.get("match_key", "transaction_id")

        # Reporting
        rep_cfg = config_dict.get("reporting", {})
        self.excel_output_path = BASE_DIR / rep_cfg.get("excel_output_path", "reports/DataGuard_Quality_Report.xlsx")
        self.csv_output_dir = BASE_DIR / rep_cfg.get("csv_output_dir", "reports/sample_outputs")

    @property
    def database_url(self) -> str:
        """Constructs SQLAlchemy database URL."""
        if self.db_password:
            return f"postgresql+psycopg2://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        return f"postgresql+psycopg2://{self.db_user}@{self.db_host}:{self.db_port}/{self.db_name}"


def load_settings(config_file: str = "settings.yaml") -> Settings:
    path = get_config_path(config_file)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    else:
        cfg = {}
    return Settings(cfg)


def load_quality_rules_config(config_file: str = "quality_rules.yaml") -> Dict[str, Any]:
    path = get_config_path(config_file)
    if not path.exists():
        raise FileNotFoundError(f"Quality rules configuration not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
