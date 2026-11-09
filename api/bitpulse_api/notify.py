"""
file: bitpulse_api/notify.py
importable: relay, NOTIFIED

relay copies the audit entries worth a notice into one file each. The notify service picks those
files up and sends them.

description: Hands audit entries that deserve a notice to the notify service.
"""

# NOTE: The API is not allowed to open a connection to the internet, so the message leaves through
# a second service with its own user. Reading from the audit log means a notice is written only for
# something that was really committed.
#
# NOTE: A crash between writing a file and moving the cursor sends one notice twice. That is better
# than a change nobody hears about.

import json
import sqlite3

from . import store
from .config import Settings

# --- Constants ---

BATCH = 50
NOTIFIED = frozenset(
    {
        "login.ok",
        "login.locked",
        "backup_code.used",
        "passkey.add",
        "passkey.remove",
        "key.create",
        "key.revoke",
        "admin.init",
        "admin.reset",
        "admin.unlock",
        "publish.done",
        "publish.failed",
        "undo.request",
        "withdraw.request",
    }
)

# --- Relay ---

# The file is finished under a hidden name and renamed, the service can only see a complete one.
def _write(settings: Settings, row: sqlite3.Row) -> None:
    fields = {key: row[key] for key in ("at", "actor", "action", "target", "detail")}
    hidden = settings.notify / f".{row['id']}"
    hidden.write_text(json.dumps(fields, ensure_ascii=False), encoding="utf-8")
    hidden.rename(settings.notify / f"{row['id']:012d}.json")


def relay(conn: sqlite3.Connection, settings: Settings) -> None:
    """Writes the waiting notices.

    Args:
        conn: Open connection.
        settings: Folder paths.
    """
    rows = store.audit_after(conn, store.notify_cursor(conn), BATCH)
    for row in rows:
        if row["action"] in NOTIFIED:
            _write(settings, row)
    if rows:
        with conn:
            store.set_notify_cursor(conn, rows[-1]["id"])
