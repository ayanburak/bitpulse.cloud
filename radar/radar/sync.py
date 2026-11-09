"""
file: radar/sync.py
importable: stage_of, payload, push_one, sync, sync_history, register_clip

The radar owns the feeds, the clusters and the scores. The API keeps a copy of each event for the
panel and is the only place that holds a decision. sync sends what changed since the last round.

description: Copies events from the radar database to the API.
"""

# NOTE: Failed sends need no queue of their own. The moment of the last good round moves only after
# a whole round went through, so whatever did not arrive is simply picked up by the next one.
#
# NOTE: The decision column here is only read to carry old answers across and to hand over a pasted
# link as already chosen. Telegram presses go straight to the API and never write it.

import sqlite3
from datetime import datetime, timezone
from urllib.parse import urlsplit

from radar import api
from radar.brief import brief_path
from radar.rank import BAR, NOISE, score_of
from radar.store import meta, set_meta

# --- Constants ---

LINKS = 8
TITLE = 400
SOURCE = 120
URL = 2000
SUMMARY = 500
REASON = 500
SYNCED = "api_synced_at"

# --- Events ---

# An old story at first sight has sent equal to first_seen and never was a candidate. A clip has the
# same two times on purpose, so it is asked about first.
def stage_of(row: sqlite3.Row) -> str | None:
    """
    Tells how far an event got.

    Args:
        row: Row from the clusters table.

    Returns:
        The stage name, or None for an old story that was never in the running.
    """
    if row["merged_into"]:
        return "merged"
    if row["clip"]:
        return "sent"
    if row["sent"]:
        return None if row["sent"] == row["first_seen"] else "sent"
    if NOISE.search(row["title"]):
        return "noise"
    if row["scored_at"] is None:
        return "unseen"
    return "reserve" if score_of(row).total >= BAR else "below"


def _links(db: sqlite3.Connection, number: int) -> list[dict]:
    items = db.execute(
        "select source, title, url from items where cluster = ? order by image desc, published desc limit ?", (number, LINKS * 2)
    ).fetchall()
    usable = [item for item in items if urlsplit(item["url"]).scheme in ("http", "https") and len(item["url"]) <= URL]
    return [{"source": item["source"][:SOURCE], "title": item["title"][:TITLE], "url": item["url"]} for item in usable[:LINKS]]


def payload(db: sqlite3.Connection, row: sqlite3.Row, stage: str) -> dict:
    """
    Builds the form of one event the API accepts.

    Args:
        db: Open radar database.
        row: Row from the clusters table.
        stage: Stage of the event.

    Returns:
        Plain data, cut to the lengths the API allows.
    """
    summary = db.execute("select summary from items where cluster = ? and summary <> '' limit 1", (row["id"],)).fetchone()
    scored = row["scored_at"] is not None
    return {
        "number": row["id"],
        "title": row["title"][:TITLE],
        "summary": summary["summary"][:SUMMARY] if summary else "",
        "first_seen": row["first_seen"],
        "last_seen": row["last_seen"],
        "sources": row["sources"],
        "stage": stage,
        "score": round(score_of(row).total, 2) if scored else -1,
        "importance": row["importance"],
        "shareable": row["shareable"],
        "visual": row["visual"],
        "category": row["category"],
        "reason": (row["reason"] or "")[:REASON],
        "merged_into": row["merged_into"],
        "clip": bool(row["clip"]),
        "links": _links(db, row["id"]),
        "decision": row["decision"],
    }

# --- Sending ---

def push_one(db: sqlite3.Connection, number: int) -> None:
    """
    Sends one event right away, so a press on its Telegram post has something to land on.

    Args:
        db: Open radar database.
        number: Cluster id.

    Raises:
        ApiError: When the API refuses it or is down.
    """
    row = db.execute("select * from clusters where id = ?", (number,)).fetchone()
    stage = stage_of(row) if row else None
    if stage:
        api.save_events([payload(db, row, stage)])


# The very first round has no earlier moment and starts from now. The list in the panel fills from
# here on, the days before have no scores to show.
def sync(db: sqlite3.Connection) -> int:
    """
    Sends every event that changed since the last good round.

    Args:
        db: Open radar database.

    Returns:
        Number of events sent.

    Raises:
        ApiError: When the API refuses them or is down. The next round sends them again.
    """
    if not api.enabled():
        return 0
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    since = meta(db, SYNCED) or started
    rows = db.execute(
        "select * from clusters where first_seen >= ?1 or last_seen >= ?1 or sent >= ?1 or scored_at >= ?1", (since,)
    ).fetchall()
    events = [payload(db, row, stage) for row in rows if (stage := stage_of(row))]
    api.save_events(events)
    set_meta(db, SYNCED, started)
    return len(events)


def _push_brief(number: int) -> None:
    path = brief_path(number)
    if path.exists():
        api.put_brief(number, text=path.read_text(encoding="utf-8")[:400_000])


# A pasted link is chosen by definition, so its answer and its brief go across together.
def register_clip(db: sqlite3.Connection, number: int) -> None:
    """
    Sends a saved link and its brief.

    Args:
        db: Open radar database.
        number: Cluster id of the link.

    Raises:
        ApiError: When the API refuses it or is down.
    """
    push_one(db, number)
    _push_brief(number)


def sync_history(db: sqlite3.Connection) -> int:
    """
    Copies every event that really reached the editor, once, when the API is connected.

    Args:
        db: Open radar database.

    Returns:
        Number of events sent.

    Raises:
        ApiError: When the API refuses them or is down.
    """
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = db.execute(
        "select * from clusters where clip = 1 or decision is not null or (sent is not null and sent <> first_seen and merged_into is null)"
    ).fetchall()
    events = [payload(db, row, stage) for row in rows if (stage := stage_of(row))]
    api.save_events(events)
    for event in events:
        if event["decision"] == "do":
            _push_brief(event["number"])
    set_meta(db, SYNCED, started)
    return len(events)
