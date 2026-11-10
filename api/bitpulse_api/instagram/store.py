"""
file: bitpulse_api/instagram/store.py
importable: save_posts, missing_thumbs, set_thumb, fetched, save_days, save_audience, audience_day, posts_page,
            post, history, days, audience, COUNTS, DAY_FIELDS

Every function takes an open connection. None of them commits, the caller groups writes that must
happen together inside one with conn block.

description: Holds the SQL for Instagram posts, their counts and the daily account numbers.
"""

# NOTE: A post row is overwritten on every fetch because a caption can be edited on Instagram, but
# its counts are only ever added. The latest counts row is what the panel shows, the older ones are
# the curve.

import sqlite3
from typing import Any, Optional

# --- Constants ---

COUNTS = ("views", "reach", "likes", "comments", "saves", "shares", "watch_ms", "interactions", "watch_total_ms", "reposts")
DAY_FIELDS = (
    "followers", "profile_views", "link_taps", "contact_taps", "reach", "reach_followers", "reach_others", "views",
    "views_followers", "views_others", "engaged", "interactions", "likes", "comments", "shares", "saves", "follows", "unfollows",
)
LATEST = "SELECT * FROM instagram_counts WHERE post = ? ORDER BY at DESC LIMIT 1"

# --- Service ---

def save_posts(conn: sqlite3.Connection, rows: list[dict[str, Any]], at: str) -> None:
    for row in rows:
        conn.execute(
            "INSERT INTO instagram_posts (id, kind, posted_at, permalink, caption) VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT (id) DO UPDATE SET kind = excluded.kind, posted_at = excluded.posted_at, "
            "permalink = excluded.permalink, caption = excluded.caption",
            (row["id"], row["kind"], row["posted_at"], row["permalink"], row["caption"]),
        )
        counts = row["counts"]
        conn.execute(
            f"INSERT OR REPLACE INTO instagram_counts (post, at, {', '.join(COUNTS)}) VALUES (?, ?, {', '.join('?' * len(COUNTS))})",
            (row["id"], at, *(counts.get(name) for name in COUNTS)),
        )


def missing_thumbs(conn: sqlite3.Connection, ids: list[str]) -> list[str]:
    if not ids:
        return []
    marks = ", ".join("?" * len(ids))
    return [row["id"] for row in conn.execute(f"SELECT id FROM instagram_posts WHERE thumb = 0 AND id IN ({marks})", ids)]


def set_thumb(conn: sqlite3.Connection, post_id: str) -> None:
    conn.execute("UPDATE instagram_posts SET thumb = 1 WHERE id = ?", (post_id,))


# The service asks this to decide which old posts are due again, so it keeps no state of its own.
def fetched(conn: sqlite3.Connection) -> dict[str, str]:
    rows = conn.execute("SELECT post, MAX(at) AS at FROM instagram_counts GROUP BY post")
    return {row["post"]: row["at"] for row in rows}


# A number a round did not bring keeps the value an earlier round stored for that day.
def save_days(conn: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    updates = ", ".join(f"{name} = COALESCE(excluded.{name}, {name})" for name in DAY_FIELDS)
    for row in rows:
        conn.execute(
            f"INSERT INTO instagram_days (day, {', '.join(DAY_FIELDS)}) VALUES (?, {', '.join('?' * len(DAY_FIELDS))}) "
            f"ON CONFLICT (day) DO UPDATE SET {updates}",
            (row["day"], *(row.get(name) for name in DAY_FIELDS)),
        )


# A day is sent whole, so what Meta no longer lists for it does not stay behind.
def save_audience(conn: sqlite3.Connection, day: str, rows: list[dict[str, Any]]) -> None:
    conn.execute("DELETE FROM instagram_audience WHERE day = ?", (day,))
    conn.executemany(
        "INSERT INTO instagram_audience (day, audience, breakdown, key, value) VALUES (?, ?, ?, ?, ?)",
        [(day, row["audience"], row["breakdown"], row["key"], row["value"]) for row in rows],
    )


def audience_day(conn: sqlite3.Connection) -> Optional[str]:
    return conn.execute("SELECT MAX(day) FROM instagram_audience").fetchone()[0]

# --- Panel ---

def posts_page(conn: sqlite3.Connection, kind: Optional[str], limit: int, offset: int) -> list[dict[str, Any]]:
    condition, values = ("WHERE p.kind = ?", [kind]) if kind else ("", [])
    rows = conn.execute(
        f"SELECT p.* FROM instagram_posts p {condition} ORDER BY p.posted_at DESC, p.id DESC LIMIT ? OFFSET ?",
        (*values, limit, offset),
    ).fetchall()
    result = []
    for row in rows:
        latest = conn.execute(LATEST, (row["id"],)).fetchone()
        counts = {"at": latest["at"], **{name: latest[name] for name in COUNTS}} if latest else None
        result.append({**dict(row), "thumb": bool(row["thumb"]), "counts": counts})
    return result


def post(conn: sqlite3.Connection, post_id: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM instagram_posts WHERE id = ?", (post_id,)).fetchone()


def days(conn: sqlite3.Connection, limit: int) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM instagram_days ORDER BY day DESC LIMIT ?", (limit,))
    return [dict(row) for row in rows]


def history(conn: sqlite3.Connection, post_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(f"SELECT at, {', '.join(COUNTS)} FROM instagram_counts WHERE post = ? ORDER BY at", (post_id,))
    return [dict(row) for row in rows]


def audience(conn: sqlite3.Connection) -> dict[str, Any]:
    day = audience_day(conn)
    if day is None:
        return {"day": None, "rows": []}
    rows = conn.execute(
        "SELECT audience, breakdown, key, value FROM instagram_audience WHERE day = ? ORDER BY audience, breakdown, value DESC", (day,)
    )
    return {"day": day, "rows": [dict(row) for row in rows]}
