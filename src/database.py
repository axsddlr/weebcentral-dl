"""SQLite database for tracked manga series."""
import os
import sqlite3
from datetime import datetime
from typing import Optional

DB_PATH = os.environ.get("WEEBCENTRAL_DB_PATH") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "weebcentral.db"
)


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
            last_checked_at TEXT,
            cover_url TEXT
        )
    """)
    try:
        conn.execute("ALTER TABLE tracked_manga ADD COLUMN cover_url TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE tracked_manga ADD COLUMN status TEXT DEFAULT 'reading'")
    except sqlite3.OperationalError:
        pass

    conn.execute("""
        CREATE TABLE IF NOT EXISTS series_metadata (
            series_id TEXT PRIMARY KEY,
            description TEXT DEFAULT '',
            authors TEXT DEFAULT '[]',
            tags TEXT DEFAULT '[]',
            status TEXT DEFAULT '',
            type TEXT DEFAULT '',
            release_year TEXT DEFAULT '',
            anime_adaptation INTEGER DEFAULT 0,
            official_translation INTEGER DEFAULT 0,
            adult INTEGER DEFAULT 0,
            updated_at TEXT NOT NULL
        )
    """)
    try:
        conn.execute("ALTER TABLE series_metadata ADD COLUMN release_year TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass

    conn.execute("""
        CREATE TABLE IF NOT EXISTS reading_progress (
            series_id TEXT NOT NULL,
            chapter_path TEXT NOT NULL,
            page INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (series_id, chapter_path)
        )
    """)
    conn.commit()


def add_tracked(series_id: str, title: str, cover_url: str | None = None, status: str = "reading") -> bool:
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO tracked_manga (series_id, title, added_at, cover_url, status) VALUES (?, ?, ?, ?, ?)",
                (series_id.upper(), title, datetime.utcnow().isoformat(), cover_url, status),
            )
            conn.commit()
        return True
    except sqlite3.Error:
        return False


def update_tracked_status(series_id: str, status: str) -> bool:
    try:
        with _connect() as conn:
            conn.execute("UPDATE tracked_manga SET status = ? WHERE series_id = ?", (status, series_id.upper()))
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


def get_all_tracked(status: str | None = None) -> list[dict]:
    try:
        with _connect() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM tracked_manga WHERE status = ? ORDER BY added_at DESC", (status,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM tracked_manga ORDER BY added_at DESC").fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error:
        return []


def save_series_metadata(series_id: str, metadata: dict) -> bool:
    try:
        import json
        with _connect() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO series_metadata
                    (series_id, description, authors, tags, status, type,
                     release_year, anime_adaptation, official_translation, adult, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                series_id.upper(),
                metadata.get("description", ""),
                json.dumps(metadata.get("authors", [])),
                json.dumps(metadata.get("tags", [])),
                metadata.get("status", ""),
                metadata.get("type", ""),
                metadata.get("release_year", ""),
                int(metadata.get("anime_adaptation", False)),
                int(metadata.get("official_translation", False)),
                int(metadata.get("adult", False)),
                datetime.utcnow().isoformat(),
            ))
            conn.commit()
        return True
    except sqlite3.Error:
        return False


def get_series_metadata(series_id: str) -> dict | None:
    try:
        import json
        with _connect() as conn:
            row = conn.execute("SELECT * FROM series_metadata WHERE series_id = ?", (series_id.upper(),)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["authors"] = json.loads(d.get("authors", "[]"))
        d["tags"] = json.loads(d.get("tags", "[]"))
        d["anime_adaptation"] = bool(d.get("anime_adaptation", 0))
        d["official_translation"] = bool(d.get("official_translation", 0))
        d["adult"] = bool(d.get("adult", 0))
        return d
    except sqlite3.Error:
        return None


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


def update_cover_url(series_id: str, cover_url: str) -> bool:
    try:
        with _connect() as conn:
            conn.execute("UPDATE tracked_manga SET cover_url = ? WHERE series_id = ?", (cover_url, series_id.upper()))
            conn.commit()
        return True
    except sqlite3.Error:
        return False


def get_tracked_without_covers() -> list[dict]:
    try:
        with _connect() as conn:
            rows = conn.execute("SELECT series_id, title FROM tracked_manga WHERE cover_url IS NULL").fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error:
        return []


def save_reading_progress(series_id: str, chapter_path: str, page: int) -> bool:
    try:
        with _connect() as conn:
            conn.execute("""
                INSERT INTO reading_progress (series_id, chapter_path, page, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(series_id, chapter_path) DO UPDATE SET
                    page = excluded.page,
                    updated_at = excluded.updated_at
            """, (series_id, chapter_path, page, datetime.utcnow().isoformat()))
            conn.commit()
        return True
    except sqlite3.Error:
        return False


def get_reading_progress(series_id: str, chapter_path: str) -> int:
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT page FROM reading_progress WHERE series_id = ? AND chapter_path = ?",
                (series_id, chapter_path),
            ).fetchone()
        return row["page"] if row else 0
    except sqlite3.Error:
        return 0


def get_all_reading_progress(series_id: str) -> dict[str, int]:
    try:
        with _connect() as conn:
            rows = conn.execute(
                "SELECT chapter_path, page FROM reading_progress WHERE series_id = ?",
                (series_id,),
            ).fetchall()
        return {r["chapter_path"]: r["page"] for r in rows}
    except sqlite3.Error:
        return {}


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
