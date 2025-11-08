from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from .state import get_database_path


_SCHEMA = """
CREATE TABLE IF NOT EXISTS exchanges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    prompt TEXT NOT NULL,
    response TEXT NOT NULL
)
"""


def ensure_database(path: Optional[Path] = None) -> Path:
    """Ensure the SQLite database exists and return its path."""

    db_path = path or get_database_path()
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(_SCHEMA)
    return db_path


def save_exchange(prompt: str, response: str, path: Optional[Path] = None) -> None:
    """Persist an exchange into the database."""

    db_path = ensure_database(path)
    timestamp = datetime.utcnow().isoformat(timespec="seconds")
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            "INSERT INTO exchanges(created_at, prompt, response) VALUES (?, ?, ?)",
            (timestamp, prompt, response),
        )


def fetch_recent(limit: int = 200, path: Optional[Path] = None) -> List[Tuple[str, str, str]]:
    """Return recent exchanges as (created_at, prompt, response)."""

    db_path = ensure_database(path)
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT created_at, prompt, response FROM exchanges ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        (str(row["created_at"]), str(row["prompt"]), str(row["response"]))
        for row in rows
    ]
