"""
file: bitpulse_api/panel/store.py
importable: now, admin, set_admin, clear_account, passkeys, passkey, add_passkey, mark_passkey_used,
            remove_passkey, unused_backup_codes, add_backup_codes, use_backup_code, add_enrolment, enrolment, set_enrolment_challenge,
            drop_enrolment, add_session, session, touch_session, drop_session, drop_full_sessions,
            drop_old_sessions, put_challenge, take_challenge, grant, take_grant, lock_state,
            add_failure, lock_until, clear_failures

Every function takes an open connection. None of them commits, the caller groups writes that must
happen together inside one with conn block.

description: Holds all SQL used by the panel login.
"""

import sqlite3
import time
from typing import Optional

# --- Time ---

# Everything that expires asks this one function, so a test can move the clock.
def now() -> int:
    return int(time.time())

# --- Account ---

def admin(conn: sqlite3.Connection) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM panel_admin WHERE id = 1").fetchone()


def set_admin(conn: sqlite3.Connection, password: str, user_id: bytes, created_at: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO panel_admin (id, password, user_id, created_at) VALUES (1, ?, ?, ?)",
        (password, user_id, created_at),
    )


# Sessions go too, and their challenges follow them through the foreign key.
def clear_account(conn: sqlite3.Connection) -> None:
    for table in ("panel_passkeys", "panel_backup_codes", "panel_enrolment", "panel_sessions"):
        conn.execute(f"DELETE FROM {table}")
    clear_failures(conn)

# --- Passkeys ---

def passkeys(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM panel_passkeys ORDER BY created_at").fetchall()


def passkey(conn: sqlite3.Connection, key_id: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM panel_passkeys WHERE id = ?", (key_id,)).fetchone()


def add_passkey(
    conn: sqlite3.Connection, key_id: str, public_key: bytes, sign_count: int, name: str, created_at: str
) -> None:
    conn.execute(
        "INSERT INTO panel_passkeys (id, public_key, sign_count, name, created_at) VALUES (?, ?, ?, ?, ?)",
        (key_id, public_key, sign_count, name, created_at),
    )


def mark_passkey_used(conn: sqlite3.Connection, key_id: str, sign_count: int, used_at: str) -> None:
    conn.execute("UPDATE panel_passkeys SET sign_count = ?, used_at = ? WHERE id = ?", (sign_count, used_at, key_id))


def remove_passkey(conn: sqlite3.Connection, key_id: str) -> bool:
    return conn.execute("DELETE FROM panel_passkeys WHERE id = ?", (key_id,)).rowcount > 0

# --- Backup Codes ---

def unused_backup_codes(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM panel_backup_codes WHERE used_at IS NULL").fetchone()[0])


def add_backup_codes(conn: sqlite3.Connection, digests: list[str]) -> None:
    conn.executemany("INSERT INTO panel_backup_codes (digest) VALUES (?)", [(item,) for item in digests])


# One statement checks and spends the code, so two requests can not both use it.
def use_backup_code(conn: sqlite3.Connection, digest: str, used_at: str) -> bool:
    cursor = conn.execute(
        "UPDATE panel_backup_codes SET used_at = ? WHERE digest = ? AND used_at IS NULL", (used_at, digest)
    )
    return cursor.rowcount > 0

# --- Enrolment ---

def add_enrolment(conn: sqlite3.Connection, digest: str, expires: int) -> None:
    conn.execute("INSERT INTO panel_enrolment (digest, expires) VALUES (?, ?)", (digest, expires))


def enrolment(conn: sqlite3.Connection, digest: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM panel_enrolment WHERE digest = ? AND expires > ?", (digest, now())).fetchone()


def set_enrolment_challenge(conn: sqlite3.Connection, digest: str, challenge: bytes) -> None:
    conn.execute("UPDATE panel_enrolment SET challenge = ? WHERE digest = ?", (challenge, digest))


def drop_enrolment(conn: sqlite3.Connection, digest: str) -> None:
    conn.execute("DELETE FROM panel_enrolment WHERE digest = ?", (digest,))

# --- Sessions ---

def add_session(conn: sqlite3.Connection, digest: str, csrf: str, full: bool) -> None:
    moment = now()
    conn.execute(
        "INSERT INTO panel_sessions (digest, csrf, full, started, seen) VALUES (?, ?, ?, ?, ?)",
        (digest, csrf, int(full), moment, moment),
    )


def session(conn: sqlite3.Connection, digest: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM panel_sessions WHERE digest = ?", (digest,)).fetchone()


def touch_session(conn: sqlite3.Connection, digest: str) -> None:
    conn.execute("UPDATE panel_sessions SET seen = ? WHERE digest = ?", (now(), digest))


def drop_session(conn: sqlite3.Connection, digest: str) -> None:
    conn.execute("DELETE FROM panel_sessions WHERE digest = ?", (digest,))


def drop_full_sessions(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM panel_sessions WHERE full = 1")


def drop_old_sessions(conn: sqlite3.Connection, started_before: int) -> None:
    conn.execute("DELETE FROM panel_sessions WHERE started < ?", (started_before,))

# --- Challenges and Grants ---

def put_challenge(conn: sqlite3.Connection, session_digest: str, purpose: str, challenge: bytes, expires: int) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO panel_challenges (session, purpose, challenge, granted, expires) VALUES (?, ?, ?, 0, ?)",
        (session_digest, purpose, challenge, expires),
    )


# A challenge works once, whether the answer was right or wrong.
def take_challenge(conn: sqlite3.Connection, session_digest: str, purpose: str) -> Optional[bytes]:
    row = conn.execute(
        "DELETE FROM panel_challenges WHERE session = ? AND purpose = ? AND granted = 0 AND expires > ? "
        "RETURNING challenge",
        (session_digest, purpose, now()),
    ).fetchone()
    return None if row is None else bytes(row["challenge"])


def grant(conn: sqlite3.Connection, session_digest: str, purpose: str, expires: int) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO panel_challenges (session, purpose, challenge, granted, expires) VALUES (?, ?, NULL, 1, ?)",
        (session_digest, purpose, expires),
    )


def take_grant(conn: sqlite3.Connection, session_digest: str, purpose: str) -> bool:
    row = conn.execute(
        "DELETE FROM panel_challenges WHERE session = ? AND purpose = ? AND granted = 1 AND expires > ? RETURNING 1",
        (session_digest, purpose, now()),
    ).fetchone()
    return row is not None

# --- Lock ---

def lock_state(conn: sqlite3.Connection) -> sqlite3.Row:
    return conn.execute("SELECT * FROM panel_lock WHERE id = 1").fetchone()


def add_failure(conn: sqlite3.Connection) -> int:
    conn.execute("UPDATE panel_lock SET failures = failures + 1 WHERE id = 1")
    return int(lock_state(conn)["failures"])


def lock_until(conn: sqlite3.Connection, until: int) -> None:
    conn.execute("UPDATE panel_lock SET failures = 0, until = ? WHERE id = 1", (until,))


def clear_failures(conn: sqlite3.Connection) -> None:
    conn.execute("UPDATE panel_lock SET failures = 0, until = 0 WHERE id = 1")
