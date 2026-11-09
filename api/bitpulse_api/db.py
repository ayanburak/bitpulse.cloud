"""
file: bitpulse_api/db.py
importable: connect

connect opens the database and brings its tables up to the newest version. Each thread or request
opens its own connection.

description: Defines the SQLite schema, its migrations and opens connections to it.
"""

# NOTE: story_versions and audit_log refuse every update and delete at database level. A bug or a
# stolen key can add a bad version, but it can not rewrite what was already recorded.
#
# NOTE: A migration is only ever added at the end of MIGRATIONS, and PRAGMA user_version counts how
# many of them this file has had. The first one uses IF NOT EXISTS because databases created before
# versioning already have those tables and still count as zero.

import sqlite3
import time
from collections.abc import Iterator
from pathlib import Path

# --- Schema ---

BASE = """
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

# SQLite can not change a CHECK rule in place, so the table is copied. Nothing references jobs,
# which makes dropping the old one safe while foreign keys are on.
WITHDRAW_JOBS = """
CREATE TABLE jobs_next (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL CHECK (kind IN ('publish', 'rebuild', 'withdraw')),
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

INSERT INTO jobs_next SELECT * FROM jobs;

DROP TABLE jobs;

ALTER TABLE jobs_next RENAME TO jobs;
"""

# Times are whole seconds here. Sessions and challenges expire within minutes, and the minute form
# used by the story tables is too coarse for that.
PANEL = """
CREATE TABLE panel_admin (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    password TEXT NOT NULL,
    user_id BLOB NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE panel_passkeys (
    id TEXT PRIMARY KEY,
    public_key BLOB NOT NULL,
    sign_count INTEGER NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    used_at TEXT
);

CREATE TABLE panel_backup_codes (
    digest TEXT PRIMARY KEY,
    used_at TEXT
);

CREATE TABLE panel_enrolment (
    digest TEXT PRIMARY KEY,
    challenge BLOB,
    expires INTEGER NOT NULL
);

CREATE TABLE panel_sessions (
    digest TEXT PRIMARY KEY,
    csrf TEXT NOT NULL,
    full INTEGER NOT NULL,
    started INTEGER NOT NULL,
    seen INTEGER NOT NULL
);

CREATE TABLE panel_challenges (
    session TEXT NOT NULL REFERENCES panel_sessions (digest) ON DELETE CASCADE,
    purpose TEXT NOT NULL,
    challenge BLOB,
    granted INTEGER NOT NULL DEFAULT 0,
    expires INTEGER NOT NULL,
    PRIMARY KEY (session, purpose)
);

CREATE TABLE panel_lock (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    failures INTEGER NOT NULL,
    until INTEGER NOT NULL
);

INSERT INTO panel_lock (id, failures, until) VALUES (1, 0, 0);
"""

# The relay starts after the newest entry, so older history is never sent as new notices.
NOTIFY = """
CREATE TABLE notify_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    last_audit INTEGER NOT NULL
);

INSERT INTO notify_state (id, last_audit) SELECT 1, COALESCE(MAX(id), 0) FROM audit_log;
"""

MIGRATIONS = (BASE, WITHDRAW_JOBS, PANEL, NOTIFY)

WAL_TRIES = 100
WAL_WAIT_SECONDS = 0.05

# --- Migrations ---

# Trigger bodies have semicolons inside them, so a plain split would cut them apart.
def _statements(script: str) -> Iterator[str]:
    current = ""
    for line in script.splitlines(keepends=True):
        current += line
        if sqlite3.complete_statement(current):
            yield current
            current = ""


# executescript would commit on its own, so each statement runs alone and a failure leaves the
# database as it was. The version is read again after taking the lock, because two processes can
# arrive here together and the second one must find the work done. A database newer than this code
# is left alone, which is what lets a code release be undone.
def _migrate(conn: sqlite3.Connection) -> None:
    if conn.execute("PRAGMA user_version").fetchone()[0] >= len(MIGRATIONS):
        return
    conn.execute("BEGIN IMMEDIATE")
    try:
        done = conn.execute("PRAGMA user_version").fetchone()[0]
        for script in MIGRATIONS[done:]:
            for statement in _statements(script):
                conn.execute(statement)
        conn.execute(f"PRAGMA user_version = {max(done, len(MIGRATIONS))}")
    except sqlite3.Error:
        conn.rollback()
        raise
    conn.commit()

# --- Connection ---

# Moving a file into WAL mode needs it alone for a moment, and SQLite does not wait for that even
# with a timeout set. A file already in WAL mode needs no lock here, so this only matters once.
def _use_wal(conn: sqlite3.Connection) -> None:
    for _ in range(WAL_TRIES):
        try:
            conn.execute("PRAGMA journal_mode = WAL")
            return
        except sqlite3.OperationalError:
            time.sleep(WAL_WAIT_SECONDS)
    conn.execute("PRAGMA journal_mode = WAL")

# check_same_thread is off because FastAPI may run a dependency and its route on different threads.
# A connection is still used by one request at a time. WAL lets the job thread read while a request
# writes.
def connect(path: Path) -> sqlite3.Connection:
    """Opens the database and applies any migration it has not had.

    Args:
        path: Database file. It is created if missing.

    Returns:
        A connection whose rows can be read by column name.
    """
    conn = sqlite3.connect(path, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _use_wal(conn)
    conn.execute("PRAGMA foreign_keys = ON")
    _migrate(conn)
    return conn
