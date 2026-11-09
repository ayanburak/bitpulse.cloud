"""
file: radar/store.py
importable: connect, meta, set_meta

Everything the radar remembers lives in one SQLite file: the feeds with their cache headers,
every story seen, the clusters that group stories about the same event, and small values such
as the last ranking time. connect creates the tables on first use.

description: Opens the radar database and reads or writes its small key value table.
"""

# NOTE: SQLite is enough here. One process writes at a time, the timers never overlap by design,
# and the poll service only touches a few columns of a row. WAL mode keeps a reader from blocking a
# writer when the two do meet.

import os
import sqlite3
from pathlib import Path

# --- Schema ---

SCHEMA = """
create table if not exists feeds (
    name text primary key,
    etag text,
    modified text,
    checked text,
    error text
);

create table if not exists clusters (
    id integer primary key,
    title text not null,
    tokens text not null,
    first_seen text not null,
    last_seen text not null,
    sources integer not null default 1,
    sent text,
    alerted text,
    decision text
);

create table if not exists items (
    url text primary key,
    source text not null,
    title text not null,
    summary text not null,
    image integer not null,
    published text,
    seen text not null,
    cluster integer not null references clusters(id)
);

create index if not exists items_cluster on items(cluster);
create index if not exists clusters_last_seen on clusters(last_seen);

create table if not exists meta (
    key text primary key,
    value text not null
);
"""

DEFAULT_PATH = "data/radar.db"

# Columns added after the first release. The schema above never touches an existing table.
ADDED = {
    "scored_sources": "integer not null default 0",
    "merged_into": "integer",
    "clip": "integer not null default 0",
    "message_id": "integer",
    "importance": "integer",
    "shareable": "integer",
    "visual": "integer",
    "category": "text",
    "reason": "text",
    "scored_at": "text",
}


# --- Connection ---

def connect(path: str | None = None) -> sqlite3.Connection:
    """
    Opens the database and creates its tables when they are missing.

    Args:
        path: File to open. RADAR_DB wins over the default, so the server can keep it elsewhere.

    Returns:
        A connection whose rows can be read by column name.
    """
    target = Path(path or os.environ.get("RADAR_DB", DEFAULT_PATH))
    target.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(target, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("pragma journal_mode=wal")
    db.executescript(SCHEMA)
    present = {row["name"] for row in db.execute("pragma table_info(clusters)")}
    for name, kind in ADDED.items():
        if name not in present:
            db.execute(f"alter table clusters add column {name} {kind}")
    db.commit()
    return db


# --- Meta ---

def meta(db: sqlite3.Connection, key: str, default: str = "") -> str:
    row = db.execute("select value from meta where key = ?", (key,)).fetchone()
    return row["value"] if row else default


def set_meta(db: sqlite3.Connection, key: str, value: str) -> None:
    db.execute("insert into meta(key, value) values(?, ?) on conflict(key) do update set value = excluded.value", (key, value))
    db.commit()
