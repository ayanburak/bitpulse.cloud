"""
file: bitpulse_api/keys.py
importable: create_key, actor_for, LIFETIME_DAYS, DEVICE, RADAR, INSIGHTS

create_key makes a new device key and shows it once. actor_for turns a presented key into the name
of its device, or None when the key can not be used. A key belongs to one scope and works only on
the routes of that scope.

description: Creates and checks the device keys used to reach the API.
"""

# NOTE: Only a hash of each key is stored. A leaked database or backup does not give anyone a key
# that works. A plain hash is enough because the key is long and random, it is not a password that
# someone could guess.

import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

from . import store

# --- Constants ---

LIFETIME_DAYS = 90
DEVICE = "device"
RADAR = "radar"
INSIGHTS = "insights"
FORMAT = "%Y-%m-%d %H:%M"

# --- Keys ---

def _digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# The key is returned and never kept, so losing it means making a new one.
def create_key(
    conn: sqlite3.Connection, name: str, days: int = LIFETIME_DAYS, actor: str = "server", scope: str = DEVICE
) -> str:
    """Creates a device key.

    Args:
        conn: Open connection.
        name: Device name. It appears in the audit log.
        days: How long the key works.
        actor: Who made it, for the audit log.
        scope: Which routes the key opens.

    Returns:
        The key text, shown only this once.
    """
    token = secrets.token_urlsafe(32)
    expires = (datetime.now(timezone.utc) + timedelta(days=days)).strftime(FORMAT)
    with conn:
        store.add_key(conn, name, _digest(token), expires, scope)
        store.add_audit(conn, actor, "key.create", name, scope)
    return token


# Times have one form everywhere, so comparing them as text is enough.
def actor_for(conn: sqlite3.Connection, token: str, scope: str = DEVICE) -> Optional[str]:
    """Finds the device that owns a key.

    Args:
        conn: Open connection.
        token: Key text from the request.
        scope: The scope the route needs.

    Returns:
        Device name, or None for an unknown, expired or revoked key or one of another scope.
    """
    row = store.find_key(conn, _digest(token))
    if row is None or row["scope"] != scope or row["revoked_at"] is not None or row["expires_at"] <= store.minute():
        return None
    return str(row["name"])
