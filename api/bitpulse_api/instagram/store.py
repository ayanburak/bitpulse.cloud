"""
file: bitpulse_api/instagram/store.py
importable: save_posts, missing_thumbs, set_thumb, fetched, save_days, posts_page, post, days

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

COUNTS = ("views", "reach", "likes", "comments", "saves", "shares", "watch_ms")
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


def save_days(conn: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        conn.execute(
            "INSERT INTO instagram_days (day, followers, profile_views, link_taps) VALUES (?, ?, ?, ?) "
            "ON CONFLICT (day) DO UPDATE SET followers = COALESCE(excluded.followers, followers), "
            "profile_views = COALESCE(excluded.profile_views, profile_views), "
            "link_taps = COALESCE(excluded.link_taps, link_taps)",
            (row["day"], row.get("followers"), row.get("profile_views"), row.get("link_taps")),
        )

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
