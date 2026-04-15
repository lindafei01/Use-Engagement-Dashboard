"""SQLite database setup and session factory."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from twin_dashboard_api.models import Base


def get_db_file_path() -> Path:
    """Return path to the SQLite file.

    Default is under the OS temp dir (often local disk). SQLite on NFS or some
    network mounts frequently raises ``disk I/O error`` on commit; set
    ``TWIN_DASHBOARD_DB`` to a path on local storage (e.g. ``/var/tmp/...``) if needed.
    """
    override = os.environ.get("TWIN_DASHBOARD_DB")
    if override:
        return Path(override).expanduser().resolve()
    base = Path(tempfile.gettempdir()) / "twin_dashboard"
    return (base / "twin_metrics.db").resolve()


def get_database_url() -> str:
    path = get_db_file_path()
    return f"sqlite:///{path}"


def get_engine():
    url = get_database_url()
    connect_args = {"check_same_thread": False, "timeout": 30} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    get_db_file_path().parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    # Lightweight migration for SQLite DBs created before `conversations.outcome` existed.
    insp = inspect(engine)
    if insp.has_table("conversations"):
        col_names = {c["name"] for c in insp.get_columns("conversations")}
        if "outcome" not in col_names:
            with engine.connect() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE conversations ADD COLUMN outcome VARCHAR(32) NOT NULL DEFAULT 'open'"
                    )
                )
                conn.commit()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
