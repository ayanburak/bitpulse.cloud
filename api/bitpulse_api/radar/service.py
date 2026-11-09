"""
file: bitpulse_api/radar/service.py
importable: decide, link_story, require, label

decide records a Do or Skip from the panel or from Telegram. link_story ties a saved story to the
event it was written from.

description: Records decisions on radar events and ties stories to them.
"""

import sqlite3

from .. import service, store as main_store
from . import store

# --- Helpers ---

def label(number: int) -> str:
    """Returns the name people use for an event, such as R-0142."""
    return f"R-{number:04d}"


def require(conn: sqlite3.Connection, number: int) -> None:
    """Checks that an event exists.

    Args:
        conn: Open connection.
        number: Event number.

    Raises:
        NotFound: If the radar never reported it.
    """
    if store.event(conn, number) is None:
        raise service.NotFound(f"no such event: {label(number)}")

# --- Decisions ---

# The panel leaves seen false so the radar updates the Telegram post, a press in Telegram already did.
def decide(conn: sqlite3.Connection, number: int, decision: str, actor: str, by: str, seen: bool) -> None:
    """Records a decision on an event.

    Args:
        conn: Open connection.
        number: Event number.
        decision: Do or skip.
        actor: Name for the audit log.
        by: Where the decision was made, telegram or panel.
        seen: Whether the Telegram post already shows it.

    Raises:
        NotFound: If the event does not exist.
    """
    require(conn, number)
    with conn:
        store.set_decision(conn, number, decision, by, main_store.minute(), seen)
        main_store.add_audit(conn, actor, "candidate.decision", label(number), f"{decision}, {by}")


def link_story(conn: sqlite3.Connection, number: int, handle: str, actor: str) -> None:
    """Records which story was written from an event.

    Args:
        conn: Open connection.
        number: Event number.
        handle: Lasting name of the story.
        actor: Name for the audit log.
    """
    with conn:
        store.set_handle(conn, number, handle)
        main_store.add_audit(conn, actor, "candidate.link", label(number), handle)
