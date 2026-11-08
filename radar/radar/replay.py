"""
file: radar/replay.py
importable: replay, sent_that_day

Runs the hourly rounds of a past day on a copy of the database, seeing at each hour only what
the radar had seen by then. Nothing reaches Telegram, the picks are only returned, so the
selection can be judged before it goes live. The model is really called, so a replay costs a little.

description: Replays the ranking rounds of a past day on stored data without sending anything.
"""

import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from radar.rank import rank, stamp
from radar.store import connect


def open_source(path: str) -> sqlite3.Connection:
    source = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    source.row_factory = sqlite3.Row
    return source


# Only clusters the editor really received count. A stored old story has sent equal to first_seen.
def sent_that_day(path: str, day: str) -> list[sqlite3.Row]:
    return open_source(path).execute(
        "select * from clusters where sent like ? and sent <> first_seen order by sent", (f"{day}%",)
    ).fetchall()


# Copies everything visible at the moment of a round into the working database. Scores stay
# in the working copy between rounds, which is how a real day would have remembered them.
def advance(source: sqlite3.Connection, db: sqlite3.Connection, moment: str, day_start: str) -> None:
    for row in source.execute("select * from clusters where first_seen <= ?", (moment,)):
        sent = row["sent"] if row["sent"] and (row["sent"] == row["first_seen"] or row["sent"] < day_start) else None
        db.execute(
            "insert or ignore into clusters(id, title, tokens, first_seen, last_seen, sources, sent) values(?, ?, ?, ?, ?, 0, ?)",
            (row["id"], row["title"], row["tokens"], row["first_seen"], row["first_seen"], sent),
        )
    for item in source.execute("select * from items where seen <= ?", (moment,)):
        db.execute(
            "insert or ignore into items(url, source, title, summary, image, published, seen, cluster) values(?, ?, ?, ?, ?, ?, ?, ?)",
            tuple(item),
        )
    db.execute("update clusters set last_seen = coalesce((select max(seen) from items where cluster = clusters.id), last_seen), "
               "sources = (select count(distinct source) from items where cluster = clusters.id)")
    db.commit()


def replay(path: str, day: str, regions: dict[str, str], start: int = 6, end: int = 22, client=None) -> list[tuple[str, sqlite3.Row, str]]:
    """
    Runs one round for every hour of a day.

    Args:
        path: Radar database to read, it is never written.
        day: Day in the form 2026-11-08, in UTC.
        regions: Region of each outlet, by outlet name.
        start: First hour of the rounds.
        end: Last hour of the rounds.
        client: Anthropic client, given in tests.

    Returns:
        One entry per event that would have been sent: the round time, the cluster and the reason.
    """
    midnight = datetime.fromisoformat(f"{day}T00:00:00+00:00").astimezone(timezone.utc)
    source = open_source(path)
    results = []
    with tempfile.TemporaryDirectory() as folder:
        db = connect(str(Path(folder) / "replay.db"))
        for hour in range(start, end + 1):
            now = midnight + timedelta(hours=hour)
            advance(source, db, stamp(now), stamp(midnight))

            def send(db, cluster, reason):
                db.execute("update clusters set sent = ? where id = ?", (stamp(now), cluster["id"]))
                db.commit()

            for cluster, reason in rank(db, send, now=now, regions=regions, client=client):
                results.append((stamp(now), cluster, reason))
        db.close()
    return results
