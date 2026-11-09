"""
file: bitpulse_api/store.py
importable: minute, add_audit, add_image, has_image, story, ensure_story, stories, latest_version,
            version, add_version, live_versions, add_job, job, next_queued, dispatched, mark_dispatched,
            finish_job, set_live, add_key, find_key, revoke_key

Every function takes an open connection. None of them commits, the caller groups writes that must
happen together inside one with conn block.

description: Holds all SQL used by the API.
"""

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Optional

# --- Time ---

# Every stored time is UTC with minutes, the same form the story files have always used.
def minute() -> str:
    """Returns the current UTC time as YYYY-MM-DD HH:MM."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

# --- Audit ---

def add_audit(conn: sqlite3.Connection, actor: str, action: str, target: str, detail: str = "") -> None:
    conn.execute(
        "INSERT INTO audit_log (at, actor, action, target, detail) VALUES (?, ?, ?, ?, ?)",
        (minute(), actor, action, target, detail),
    )

# --- Images ---

# The same picture uploaded twice has the same hash, so the second insert is simply skipped.
def add_image(conn: sqlite3.Connection, sha: str, width: int, height: int) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO images (sha, width, height, added_at) VALUES (?, ?, ?, ?)",
        (sha, width, height, minute()),
    )


def has_image(conn: sqlite3.Connection, sha: str) -> bool:
    return conn.execute("SELECT 1 FROM images WHERE sha = ?", (sha,)).fetchone() is not None

# --- Stories ---

def story(conn: sqlite3.Connection, handle: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM stories WHERE handle = ?", (handle,)).fetchone()


def ensure_story(conn: sqlite3.Connection, handle: str) -> None:
    conn.execute("INSERT OR IGNORE INTO stories (handle, created_at) VALUES (?, ?)", (handle, minute()))


def stories(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT s.*, MAX(v.number) AS latest FROM stories s JOIN story_versions v USING (handle) "
        "GROUP BY s.handle ORDER BY s.published_at DESC, s.handle"
    ).fetchall()


def set_live(conn: sqlite3.Connection, handle: str, version_id: int, published_at: str) -> None:
    conn.execute(
        "UPDATE stories SET live_version = ?, published_at = ? WHERE handle = ?",
        (version_id, published_at, handle),
    )

# --- Versions ---

# Content is one JSON text, and only the API ever looks inside it.
def _version(row: Optional[sqlite3.Row]) -> Optional[dict[str, Any]]:
    return None if row is None else {**dict(row), "content": json.loads(row["content"])}


def latest_version(conn: sqlite3.Connection, handle: str) -> Optional[dict[str, Any]]:
    return _version(
        conn.execute("SELECT * FROM story_versions WHERE handle = ? ORDER BY number DESC LIMIT 1", (handle,)).fetchone()
    )


def version(conn: sqlite3.Connection, version_id: int) -> Optional[dict[str, Any]]:
    return _version(conn.execute("SELECT * FROM story_versions WHERE id = ?", (version_id,)).fetchone())


def add_version(conn: sqlite3.Connection, handle: str, content: dict[str, Any], image: str, actor: str) -> int:
    row = conn.execute("SELECT COALESCE(MAX(number), 0) + 1 FROM story_versions WHERE handle = ?", (handle,)).fetchone()
    cursor = conn.execute(
        "INSERT INTO story_versions (handle, number, content, image, actor, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (handle, row[0], json.dumps(content, ensure_ascii=False), image, actor, minute()),
    )
    return int(cursor.lastrowid)


def live_versions(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Returns the version readers currently see for every published story.

    Args:
        conn: Open connection.

    Returns:
        One record per story with its version fields and published_at.
    """
    rows = conn.execute(
        "SELECT v.*, s.published_at FROM stories s JOIN story_versions v ON v.id = s.live_version"
    ).fetchall()
    return [{**dict(row), "content": json.loads(row["content"])} for row in rows]

# --- Jobs ---

def add_job(
    conn: sqlite3.Connection, kind: str, handle: Optional[str], version_id: Optional[int], moment: str, go_live: bool
) -> int:
    cursor = conn.execute(
        "INSERT INTO jobs (kind, handle, version, moment, go_live, status) VALUES (?, ?, ?, ?, ?, 'queued')",
        (kind, handle, version_id, moment, int(go_live)),
    )
    return int(cursor.lastrowid)


def job(conn: sqlite3.Connection, job_id: int) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()


def next_queued(conn: sqlite3.Connection) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM jobs WHERE status = 'queued' ORDER BY id LIMIT 1").fetchone()


def dispatched(conn: sqlite3.Connection) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM jobs WHERE status = 'dispatched' ORDER BY id LIMIT 1").fetchone()


def mark_dispatched(conn: sqlite3.Connection, job_id: int) -> None:
    conn.execute(
        "UPDATE jobs SET status = 'dispatched', dispatched_at = ? WHERE id = ?",
        (datetime.now(timezone.utc).isoformat(), job_id),
    )


def finish_job(
    conn: sqlite3.Connection, job_id: int, ok: bool, release: Optional[str], error: Optional[str], ms: Optional[int]
) -> None:
    conn.execute(
        "UPDATE jobs SET status = ?, release = ?, error = ?, duration_ms = ?, finished_at = ? WHERE id = ?",
        ("succeeded" if ok else "failed", release, error, ms, minute(), job_id),
    )

# --- Keys ---

def add_key(conn: sqlite3.Connection, name: str, digest: str, expires_at: str) -> None:
    conn.execute(
        "INSERT INTO api_keys (name, digest, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (name, digest, minute(), expires_at),
    )


def find_key(conn: sqlite3.Connection, digest: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM api_keys WHERE digest = ?", (digest,)).fetchone()


def revoke_key(conn: sqlite3.Connection, name: str) -> bool:
    cursor = conn.execute(
        "UPDATE api_keys SET revoked_at = ? WHERE name = ? AND revoked_at IS NULL", (minute(), name)
    )
    return cursor.rowcount > 0
