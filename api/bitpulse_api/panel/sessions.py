"""
file: bitpulse_api/panel/sessions.py
importable: COOKIE, Current, start_pending, promote, load, end, purpose_of, grant_action, take_action

A pending session exists between the password and the second factor and can do nothing else. A full
session is made only after the second factor. grant_action and take_action hold the fresh proof
that a dangerous action needs.

description: Creates, checks and ends the browser sessions of the panel.
"""

# NOTE: The cookie holds a long random value and the database only its hash, the same reasoning as
# the device keys. A leaked backup does not give anyone a working session.

import secrets
import sqlite3
from dataclasses import dataclass
from typing import Optional

from . import accounts, store

# --- Constants ---

# The __Host- prefix makes the browser refuse this cookie unless it is secure and for the exact host.
COOKIE = "__Host-bitpulse"
IDLE_SECONDS = 30 * 60
FULL_SECONDS = 12 * 60 * 60
PENDING_SECONDS = 5 * 60
GRANT_SECONDS = 2 * 60

# --- Sessions ---

@dataclass(frozen=True)
class Current:
    """A session that passed its checks.

    Args:
        digest: Stored name of the session.
        csrf: Value the browser must send back on every change.
        full: True after the second factor.
    """

    digest: str
    csrf: str
    full: bool


def _create(conn: sqlite3.Connection, full: bool) -> tuple[str, Current]:
    token = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(32)
    digest = accounts.digest(token)
    store.add_session(conn, digest, csrf, full)
    return token, Current(digest, csrf, full)


def start_pending(conn: sqlite3.Connection) -> str:
    """Opens a session that only allows the second factor.

    Args:
        conn: Open connection.

    Returns:
        Value for the cookie.
    """
    with conn:
        store.drop_old_sessions(conn, store.now() - FULL_SECONDS)
        return _create(conn, False)[0]


# The value changes at this moment, so a value planted before the login is worth nothing. A new
# login also ends any older session, there is only one person who should be signed in.
def promote(conn: sqlite3.Connection, pending: Current) -> tuple[str, Current]:
    """Turns a pending session into a full one.

    Args:
        conn: Open connection.
        pending: Session that passed the second factor.

    Returns:
        Value for the cookie and the new session.
    """
    with conn:
        store.drop_session(conn, pending.digest)
        store.drop_full_sessions(conn)
        store.clear_failures(conn)
        return _create(conn, True)


def _expired(row: sqlite3.Row) -> bool:
    moment = store.now()
    if not row["full"]:
        return moment - row["started"] > PENDING_SECONDS
    return moment - row["seen"] > IDLE_SECONDS or moment - row["started"] > FULL_SECONDS


def load(conn: sqlite3.Connection, token: Optional[str]) -> Optional[Current]:
    """Finds the session behind a cookie and counts this as activity.

    Args:
        conn: Open connection.
        token: Cookie value, if there was one.

    Returns:
        The session, or None when there is none or it ran out.
    """
    if not token:
        return None
    digest = accounts.digest(token)
    row = store.session(conn, digest)
    if row is None:
        return None
    with conn:
        if _expired(row):
            store.drop_session(conn, digest)
            return None
        store.touch_session(conn, digest)
    return Current(digest, row["csrf"], bool(row["full"]))


def end(conn: sqlite3.Connection, current: Current) -> None:
    with conn:
        store.drop_session(conn, current.digest)

# --- Action Grants ---

def purpose_of(action: str, target: str) -> str:
    return f"action:{action}:{target}"


def grant_action(conn: sqlite3.Connection, current: Current, action: str, target: str) -> None:
    """Records that the second factor was given for one action on one target.

    Args:
        conn: Open connection.
        current: Full session.
        action: Name of the action.
        target: What it acts on.
    """
    with conn:
        store.grant(conn, current.digest, purpose_of(action, target), store.now() + GRANT_SECONDS)


# The grant is spent here, one passkey touch is good for exactly one action.
def take_action(conn: sqlite3.Connection, current: Current, action: str, target: str) -> bool:
    """Spends the grant for one action on one target.

    Args:
        conn: Open connection.
        current: Full session.
        action: Name of the action.
        target: What it acts on.

    Returns:
        True when a fresh grant existed.
    """
    with conn:
        return store.take_grant(conn, current.digest, purpose_of(action, target))
