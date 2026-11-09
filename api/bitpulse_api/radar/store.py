"""
file: bitpulse_api/radar/store.py
importable: save_events, event, browse, counts, set_decision, mark_seen, set_brief, retry_brief, wanted_briefs,
            unseen_decisions, set_handle, add_link, waiting_links, finish_link, recent_links, prune, candidates

Every function takes an open connection. None of them commits, the caller groups writes that must
happen together inside one with conn block.

description: Holds the SQL for the radar events, their decisions and briefs.
"""

# NOTE: The state a person sees, new or do or draft or published, is worked out from the row and the
# story it points at. It is never stored, so it can not disagree with the story itself.
#
# NOTE: A day is matched as a text range on first_seen. Every time from the radar has the same form,
# and the tilde sorts after every character that form can hold, so it closes the range.

import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Optional

# --- Constants ---

ELIMINATED = "eliminated"
CANDIDATES = "candidates"
STATUS = (
    "CASE WHEN s.live_version IS NOT NULL THEN 'published' WHEN e.handle IS NOT NULL THEN 'draft' "
    "ELSE COALESCE(e.decision, 'new') END"
)
LISTED = (
    "e.number, e.title, e.first_seen, e.sources, e.stage, e.score, e.category, e.reason, e.decision, e.clip, e.handle, "
    f"e.brief IS NOT NULL AS has_brief, {STATUS} AS status"
)
JOIN = "FROM radar_events e LEFT JOIN stories s ON s.handle = e.handle"

# --- Filters ---

@dataclass(frozen=True)
class Filters:
    """What a person asked to see.

    Args:
        group: Candidates or eliminated.
        stage: One stage, only used for eliminated events.
        status: One state, only used for candidates.
        since: Keeps events first seen at or after this moment.
        day: Keeps events first seen on this day, YYYY-MM-DD.
        category: One category.
        min_sources: Keeps events with at least this many outlets.
        text: Part of the title.
    """

    group: str
    stage: Optional[str] = None
    status: Optional[str] = None
    since: Optional[str] = None
    day: Optional[str] = None
    category: Optional[str] = None
    min_sources: int = 0
    text: Optional[str] = None


# The stage and the status stay out of the shared part, because the counts above the list must keep
# showing every stage while one of them is selected.
def _common(filters: Filters) -> tuple[list[str], list[Any]]:
    clauses = ["(e.stage = 'sent' OR e.decision IS NOT NULL)" if filters.group == CANDIDATES else "(e.stage <> 'sent' AND e.decision IS NULL)"]
    args: list[Any] = []
    if filters.since:
        clauses.append("e.first_seen >= ?")
        args.append(filters.since)
    if filters.day:
        clauses.append("e.first_seen >= ? AND e.first_seen < ?")
        args += [filters.day, f"{filters.day}~"]
    if filters.category:
        clauses.append("e.category = ?")
        args.append(filters.category)
    if filters.min_sources:
        clauses.append("e.sources >= ?")
        args.append(filters.min_sources)
    if filters.text:
        clauses.append("e.title LIKE ? ESCAPE '!'")
        escaped = filters.text.replace("!", "!!").replace("%", "!%").replace("_", "!_")
        args.append(f"%{escaped}%")
    return clauses, args

# --- Reading ---

def browse(conn: sqlite3.Connection, filters: Filters, after: Optional[tuple[float, int]], limit: int) -> list[sqlite3.Row]:
    """Returns one page of events.

    Args:
        conn: Open connection.
        filters: What to show.
        after: Score and number of the last row of the page before.
        limit: Most rows to return.

    Returns:
        Rows without their long text fields. Candidates come newest first, eliminated events best
        score first.
    """
    clauses, args = _common(filters)
    if filters.stage:
        clauses.append("e.stage = ?")
        args.append(filters.stage)
    if filters.status:
        clauses.append(f"{STATUS} = ?")
        args.append(filters.status)
    if after is not None and filters.group == CANDIDATES:
        clauses.append("e.number < ?")
        args.append(after[1])
    elif after is not None:
        clauses.append("(e.score, e.number) < (?, ?)")
        args += list(after)
    order = "e.number DESC" if filters.group == CANDIDATES else "e.score DESC, e.number DESC"
    return conn.execute(f"SELECT {LISTED} {JOIN} WHERE {' AND '.join(clauses)} ORDER BY {order} LIMIT ?", (*args, limit)).fetchall()


def counts(conn: sqlite3.Connection, filters: Filters) -> dict[str, int]:
    """Counts the events of each stage or state under the same filters as the list.

    Args:
        conn: Open connection.
        filters: What is shown.

    Returns:
        Number of events per stage for eliminated events, per state for candidates.
    """
    clauses, args = _common(filters)
    field = STATUS if filters.group == CANDIDATES else "e.stage"
    rows = conn.execute(f"SELECT {field} AS name, COUNT(*) AS total {JOIN} WHERE {' AND '.join(clauses)} GROUP BY name", args)
    return {row["name"]: row["total"] for row in rows}


def event(conn: sqlite3.Connection, number: int) -> Optional[dict[str, Any]]:
    row = conn.execute(
        f"SELECT {LISTED}, e.summary, e.last_seen, e.importance, e.shareable, e.visual, e.merged_into, e.links, "
        f"e.decided_by, e.decided_at, e.brief_error, e.brief_at {JOIN} WHERE e.number = ?",
        (number,),
    ).fetchone()
    return None if row is None else {**dict(row), "links": json.loads(row["links"])}


def brief(conn: sqlite3.Connection, number: int) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT brief, brief_at FROM radar_events WHERE number = ? AND brief IS NOT NULL", (number,)).fetchone()


# What a writing session may pick up: told to do, brief ready and no story made from it yet.
def candidates(conn: sqlite3.Connection, limit: int) -> list[sqlite3.Row]:
    return conn.execute(
        f"SELECT {LISTED} {JOIN} WHERE e.decision = 'do' AND e.handle IS NULL ORDER BY e.number DESC LIMIT ?", (limit,)
    ).fetchall()

# --- Writing From The Radar ---

# The decision is taken from the upload only when the row has none, which is how the old answers
# move across once. After that the column belongs to this side.
def save_events(conn: sqlite3.Connection, events: list[dict[str, Any]]) -> None:
    conn.executemany(
        "INSERT INTO radar_events (number, title, summary, first_seen, last_seen, sources, stage, score, importance, "
        "shareable, visual, category, reason, merged_into, clip, links, decision, decided_by) "
        "VALUES (:number, :title, :summary, :first_seen, :last_seen, :sources, :stage, :score, :importance, "
        ":shareable, :visual, :category, :reason, :merged_into, :clip, :links, :decision, :decided_by) "
        "ON CONFLICT (number) DO UPDATE SET title = excluded.title, summary = excluded.summary, "
        "last_seen = excluded.last_seen, sources = excluded.sources, stage = excluded.stage, score = excluded.score, "
        "importance = excluded.importance, shareable = excluded.shareable, visual = excluded.visual, "
        "category = excluded.category, reason = excluded.reason, merged_into = excluded.merged_into, "
        "clip = excluded.clip, links = excluded.links, decision = COALESCE(decision, excluded.decision), "
        "decided_by = COALESCE(decided_by, excluded.decided_by)",
        events,
    )


def set_brief(conn: sqlite3.Connection, number: int, text: Optional[str], error: Optional[str], at: str) -> None:
    conn.execute("UPDATE radar_events SET brief = ?, brief_error = ?, brief_at = ? WHERE number = ?", (text, error, at, number))


def retry_brief(conn: sqlite3.Connection, number: int) -> None:
    conn.execute("UPDATE radar_events SET brief_error = NULL WHERE number = ?", (number,))

# --- Decisions ---

# seen stays false when the panel decides, that is what tells the radar to update the Telegram post.
def set_decision(conn: sqlite3.Connection, number: int, decision: str, by: str, at: str, seen: bool) -> None:
    conn.execute(
        "UPDATE radar_events SET decision = ?, decided_by = ?, decided_at = ?, decision_seen = ?, brief_error = NULL WHERE number = ?",
        (decision, by, at, int(seen), number),
    )


def mark_seen(conn: sqlite3.Connection, number: int) -> None:
    conn.execute("UPDATE radar_events SET decision_seen = 1 WHERE number = ?", (number,))


def wanted_briefs(conn: sqlite3.Connection, limit: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT number, decided_by FROM radar_events WHERE decision = 'do' AND brief IS NULL AND brief_error IS NULL "
        "ORDER BY decided_at LIMIT ?",
        (limit,),
    ).fetchall()


def unseen_decisions(conn: sqlite3.Connection, limit: int) -> list[sqlite3.Row]:
    return conn.execute("SELECT number, decision FROM radar_events WHERE decision_seen = 0 LIMIT ?", (limit,)).fetchall()


def set_handle(conn: sqlite3.Connection, number: int, handle: str) -> None:
    conn.execute("UPDATE radar_events SET handle = ? WHERE number = ?", (handle, number))

# --- Links ---

def add_link(conn: sqlite3.Connection, url: str, at: str) -> int:
    cursor = conn.execute("INSERT INTO radar_links (url, state, added_at) VALUES (?, 'waiting', ?)", (url, at))
    return int(cursor.lastrowid)


def waiting_links(conn: sqlite3.Connection, limit: int) -> list[sqlite3.Row]:
    return conn.execute("SELECT id, url FROM radar_links WHERE state = 'waiting' ORDER BY id LIMIT ?", (limit,)).fetchall()


def finish_link(conn: sqlite3.Connection, link: int, number: Optional[int], error: Optional[str]) -> int:
    cursor = conn.execute(
        "UPDATE radar_links SET state = ?, number = ?, error = ? WHERE id = ? AND state = 'waiting'",
        ("done" if error is None else "failed", number, error, link),
    )
    return cursor.rowcount


def recent_links(conn: sqlite3.Connection, limit: int) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM radar_links ORDER BY id DESC LIMIT ?", (limit,)).fetchall()

# --- Cleaning ---

# Only what nobody acted on goes away. A candidate stays for good, it is the record of what was offered.
def prune(conn: sqlite3.Connection, before: str) -> None:
    conn.execute("DELETE FROM radar_events WHERE first_seen < ? AND stage <> 'sent' AND decision IS NULL AND handle IS NULL", (before,))
    conn.execute("DELETE FROM radar_links WHERE added_at < ? AND state <> 'waiting'", (before,))
