"""DataGuard Database Connection and Engine Management."""

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Connection
from sqlalchemy.orm import sessionmaker, Session

from dataguard.config.settings import load_settings

logger = logging.getLogger("dataguard.database")

_engine: Engine | None = None
_session_factory = None


def get_engine() -> Engine:
    """Returns singleton SQLAlchemy Engine."""
    global _engine, _session_factory
    if _engine is None:
        settings = load_settings()
        _engine = create_engine(
            settings.database_url,
            pool_size=settings.db_pool_size,
            pool_pre_ping=True
        )
        _session_factory = sessionmaker(bind=_engine, autocommit=False, autoflush=False)
    return _engine


def get_session() -> Session:
    """Creates a new SQLAlchemy session."""
    get_engine()
    return _session_factory()


@contextmanager
def get_db_connection() -> Generator[Connection, None, None]:
    """Provides a transactional database connection scope."""
    engine = get_engine()
    with engine.begin() as conn:
        yield conn


def execute_sql_file(file_path: Path | str) -> None:
    """Executes a SQL file against the configured database."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"SQL file not found at {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Split on semicolon or execute blocks
    with get_db_connection() as conn:
        # PostgreSQL executes multi-statement SQL strings directly in one text() execution
        conn.execute(text(sql_content))
    logger.info("Successfully executed SQL script: %s", file_path.name)
