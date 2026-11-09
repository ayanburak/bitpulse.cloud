"""
file: bitpulse_api/db.py
importable: connect

connect opens the database and creates the tables on first use. Each thread or request opens its
own connection.

description: Defines the SQLite schema and opens connections to it.
"""

# NOTE: story_versions and audit_log refuse every update and delete at database level. A bug or a
# stolen key can add a bad version, but it can not rewrite what was already recorded.

import sqlite3
from pathlib import Path

# --- Schema ---

SCHEMA = """
CREATE TABLE IF NOT EXISTS images (
    sha TEXT PRIMARY KEY,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    added_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stories (
    handle TEXT PRIMARY KEY,
    published_at TEXT,
    live_version INTEGER REFERENCES story_versions (id),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS story_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    handle TEXT NOT NULL REFERENCES stories (handle),
    number INTEGER NOT NULL,
    content TEXT NOT NULL,
    image TEXT NOT NULL REFERENCES images (sha),
    actor TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (handle, number)
);

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL CHECK (kind IN ('publish', 'rebuild')),
    handle TEXT REFERENCES stories (handle),
    version INTEGER REFERENCES story_versions (id),
    moment TEXT NOT NULL,
    go_live INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL CHECK (status IN ('queued', 'dispatched', 'succeeded', 'failed')),
    release TEXT,
    error TEXT,
    duration_ms INTEGER,
    dispatched_at TEXT,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    digest TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    revoked_at TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    at TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    target TEXT NOT NULL,
    detail TEXT NOT NULL DEFAULT ''
);

CREATE TRIGGER IF NOT EXISTS versions_no_update BEFORE UPDATE ON story_versions
BEGIN SELECT RAISE(ABORT, 'story versions can not be changed'); END;

CREATE TRIGGER IF NOT EXISTS versions_no_delete BEFORE DELETE ON story_versions
BEGIN SELECT RAISE(ABORT, 'story versions can not be deleted'); END;

CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit entries can not be changed'); END;

CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit entries can not be deleted'); END;
"""

# --- Connection ---

# check_same_thread is off because FastAPI may run a dependency and its route on different threads.
# A connection is still used by one request at a time. WAL lets the job thread read while a request
# writes.
def connect(path: Path) -> sqlite3.Connection:
    """Opens the database and creates any missing table.

    Args:
        path: Database file. It is created if missing.

    Returns:
        A connection whose rows can be read by column name.
    """
    conn = sqlite3.connect(path, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn
