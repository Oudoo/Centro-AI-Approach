"""
Aura (by Centro) — Employee requests store.

Persists every submitted request (shift swap, annual/casual leave, break-timing
change) to a local SQLite database so Workforce Management can review and export
them. Uses the stdlib `sqlite3` driver off the event loop via `asyncio.to_thread`
(no extra dependency). Export is offered as CSV, which opens directly in Excel.
"""
from __future__ import annotations

import asyncio
import csv
import io
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from config import get_settings

COLUMNS = [
    "id",
    "created_at",
    "request_type",
    "target_system",
    "employee_id",
    "employee_name",
    "account_scope",
    "department",
    "details",
    "status",
    "notified_email",
]


def _connect() -> sqlite3.Connection:
    path = Path(get_settings().requests_db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def _init() -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                request_type TEXT NOT NULL,
                target_system TEXT,
                employee_id TEXT,
                employee_name TEXT,
                account_scope TEXT,
                department TEXT,
                details TEXT,
                status TEXT DEFAULT 'submitted',
                notified_email TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _insert(row: dict) -> int:
    conn = _connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO requests (created_at, request_type, target_system,
                employee_id, employee_name, account_scope, department,
                details, status, notified_email)
            VALUES (:created_at, :request_type, :target_system, :employee_id,
                :employee_name, :account_scope, :department, :details, :status,
                :notified_email)
            """,
            row,
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def _all() -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute("SELECT * FROM requests ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


async def init_store() -> None:
    await asyncio.to_thread(_init)


async def record_request(
    request_type: str,
    target_system: str,
    user,  # UserContext
    details: dict,
    notified_email: str = "",
) -> dict:
    row = {
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "request_type": request_type,
        "target_system": target_system,
        "employee_id": str(details.get("employee_id", "") or getattr(user, "user_id", "")),
        "employee_name": getattr(user, "display_name", ""),
        "account_scope": getattr(user, "account_scope", ""),
        "department": getattr(user, "department", ""),
        "details": json.dumps(details, ensure_ascii=False),
        "status": "submitted",
        "notified_email": notified_email,
    }
    new_id = await asyncio.to_thread(_insert, row)
    row["id"] = new_id
    return row


async def list_requests() -> list[dict]:
    return await asyncio.to_thread(_all)


async def export_csv() -> str:
    rows = await asyncio.to_thread(_all)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
    return buf.getvalue()
