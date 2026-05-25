"""SQLite database for tracked manga series."""
import os
import sqlite3
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "weebcentral.db")


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    _init_db(conn)
    return conn


def _init_db(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tracked_manga (
            series_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            added_at TEXT NOT NULL DEFAULT (datetime('now')),
            last_checked_at TEXT
        )
    """)
    conn.commit()


def add_tracked(series_id: str, title: str) -> bool:
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO tracked_manga (series_id, title, added_at) VALUES (?, ?, ?)",
                (series_id.upper(), title, datetime.utcnow().isoformat()),
            )
            conn.commit()
        return True
    except sqlite3.Error:
        return False


def remove_tracked(series_id: str) -> bool:
    try:
        with _connect() as conn:
            cursor = conn.execute("DELETE FROM tracked_manga WHERE series_id = ?", (series_id.upper(),))
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error:
        return False


def get_all_tracked() -> list[dict]:
    try:
        with _connect() as conn:
            rows = conn.execute("SELECT * FROM tracked_manga ORDER BY added_at DESC").fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error:
        return []


def get_tracked(series_id: str) -> Optional[dict]:
    try:
        with _connect() as conn:
            row = conn.execute("SELECT * FROM tracked_manga WHERE series_id = ?", (series_id.upper(),)).fetchone()
        return dict(row) if row else None
    except sqlite3.Error:
        return None


def is_tracked(series_id: str) -> bool:
    try:
        with _connect() as conn:
            row = conn.execute("SELECT 1 FROM tracked_manga WHERE series_id = ?", (series_id.upper(),)).fetchone()
        return row is not None
    except sqlite3.Error:
        return False


def update_last_checked(series_id: str):
    try:
        with _connect() as conn:
            conn.execute(
                "UPDATE tracked_manga SET last_checked_at = ? WHERE series_id = ?",
                (datetime.utcnow().isoformat(), series_id.upper()),
            )
            conn.commit()
    except sqlite3.Error:
        pass


def count_tracked() -> int:
    try:
        with _connect() as conn:
            row = conn.execute("SELECT COUNT(*) as cnt FROM tracked_manga").fetchone()
        return row["cnt"]
    except sqlite3.Error:
        return 0


def import_from_file(filepath: str) -> tuple[int, int]:
    """Import entries from a manga.txt file. Returns (added, skipped)."""
    if not os.path.exists(filepath):
        return 0, 0
    import re
    SERIES_ID_PATTERN = re.compile(r'^[A-Z0-9]{26}$')

    added = 0
    skipped = 0
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            series_id = None
            title = None

            if "=" in line:
                series_id, title = line.split("=", 1)
                series_id = series_id.strip().upper()
                title = title.strip()
            elif "/" in line:
                cleaned = line
                if cleaned.startswith("http"):
                    cleaned = re.sub(r'^https?://[^/]+/series/', '', cleaned)
                series_id, title = cleaned.split("/", 1)
                series_id = series_id.strip().upper()
                title = title.strip()
            elif SERIES_ID_PATTERN.match(line.upper()):
                series_id = line.upper()
                title = line
            else:
                title = line

            if series_id and SERIES_ID_PATTERN.match(series_id):
                if add_tracked(series_id, title or series_id):
                    added += 1
                else:
                    skipped += 1
            elif title:
                if add_tracked(title, title):
                    added += 1
                else:
                    skipped += 1
    return added, skipped
