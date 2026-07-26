"""stdlib sqlite3, no ORM. Row factory returns dicts. ~60 lines, as planned.

The rule that matters: SQLite persists, it never computes. No business logic in
SQL — derive() takes and returns typed Python objects, which is what makes the
rulebook unit-testable.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .paths import DB_PATH          # repo root locally, the mounted disk in prod

SCHEMA = Path(__file__).resolve().parent / "schema.sql"


def _dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict[str, Any]:
    return {col[0]: row[i] for i, col in enumerate(cursor.description)}


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = _dict_factory
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init() -> None:
    """Idempotent. If the file is ever corrupted mid-demo: rm titlechain.db."""
    with connect() as conn:
        conn.executescript(SCHEMA.read_text())


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def q(sql: str, params: Iterable = ()) -> list[dict]:
    with connect() as conn:
        return conn.execute(sql, tuple(params)).fetchall()


def one(sql: str, params: Iterable = ()) -> dict | None:
    rows = q(sql, params)
    return rows[0] if rows else None


def execute(sql: str, params: Iterable = ()) -> int:
    """Returns lastrowid."""
    with connect() as conn:
        cur = conn.execute(sql, tuple(params))
        conn.commit()
        return cur.lastrowid


def insert(table: str, **cols: Any) -> int:
    keys = ", ".join(cols)
    marks = ", ".join("?" for _ in cols)
    return execute(f"INSERT INTO {table} ({keys}) VALUES ({marks})", list(cols.values()))


def set_status(case_id: int, status: str, detail: str = "", **extra: Any) -> None:
    sets = ["status = ?", "status_detail = ?"]
    vals: list[Any] = [status, detail]
    for k, v in extra.items():
        sets.append(f"{k} = ?")
        vals.append(v)
    vals.append(case_id)
    execute(f"UPDATE cases SET {', '.join(sets)} WHERE id = ?", vals)
