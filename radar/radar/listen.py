"""
file: radar/listen.py
importable: listen, load_sources, tokens, clean_url, Source

Reads every feed in sources.toml, stores the stories it has not seen before and puts each one
into a cluster with the other stories about the same event. A cluster that many separate
outlets pick up within a short time counts as a big event and is reported at once.

description: Collects new stories from the feeds and groups them by event.
"""

# NOTE: Clustering compares the words of the titles. It misses two titles that describe one event
# in different words, and that is accepted: the ranking step reads titles side by side anyway,
# and a missed match only costs a duplicate candidate, never a lost story.
#
# XXX: feedparser does its own downloading so it can send the cache headers, and it has no
# timeout of its own. The socket default timeout below is what keeps one slow feed from holding
# the whole run.

import calendar
import json
import re
import socket
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 on the server has no tomllib yet.
    import tomli as tomllib

import feedparser

# --- Constants ---

AGENT = "BitpulseRadar/0.1 (+https://bitpulse.cloud)"
TIMEOUT = 20
WORKERS = 12

# A story older than this when first seen is stored, so it is never seen as new again, but it
# can not open a cluster. The first run would otherwise flood the ranking with old stories.
FRESH = timedelta(hours=12)

# How long a cluster stays open for new stories about the same event.
OPEN_FOR = timedelta(hours=36)

# Two titles belong together when they share at least SHARED words and those words make up at
# least OVERLAP of the shorter title.
SHARED = 3
OVERLAP = 0.6

# A big event is BIG_SOURCES separate outlets within BIG_WINDOW of the first story.
BIG_SOURCES = 5
BIG_WINDOW = timedelta(minutes=90)

STOPWORDS = set(
    "the a an and or but of in on at to for from by with as is are was were be been has have had "
    "it its this that these those after before over under into about than then new says said say "
    "will would could can may might not no more most what who why how when where which their they "
    "he she his her you your we our us up out off amid via just also".split()
)

TRACKING = re.compile(r"^(utm_|fbclid|gclid|ocid|cmpid|ref$|src$)")


@dataclass
class Source:
    name: str
    url: str
    region: str


# --- Sources ---

def load_sources(path: str = "sources.toml") -> list[Source]:
    with open(path, "rb") as file:
        data = tomllib.load(file)
    return [Source(**item) for item in data["source"]]


# --- Text ---

def clean_url(url: str) -> str:
    """
    Drops tracking parameters and the fragment, so the same story shared with two different
    campaign tags is still stored once.
    """
    parts = urlsplit(url.strip())
    query = [(key, value) for key, value in parse_qsl(parts.query) if not TRACKING.match(key)]
    return urlunsplit((parts.scheme, parts.netloc.lower(), parts.path, urlencode(query), ""))


# Google News appends the outlet after a dash, which would make every title look unique.
def plain_title(title: str, source: str) -> str:
    if source == "Google News":
        title = re.sub(r"\s+-\s+[^-]+$", "", title)
    return re.sub(r"\s+", " ", title).strip()


def tokens(title: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", title.lower())
    return {word for word in words if len(word) > 2 and word not in STOPWORDS}


def strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()


def has_image(entry: dict) -> bool:
    if entry.get("media_content") or entry.get("media_thumbnail"):
        return True
    if any(link.get("type", "").startswith("image") for link in entry.get("links", [])):
        return True
    return "<img" in (entry.get("summary") or "")


def published(entry: dict) -> str | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    return datetime.fromtimestamp(calendar.timegm(parsed), timezone.utc).isoformat(timespec="seconds")


# --- Fetching ---

def fetch(source: Source, etag: str | None, modified: str | None) -> tuple[Source, dict | None, str | None]:
    try:
        feed = feedparser.parse(source.url, etag=etag, modified=modified, agent=AGENT)
    except Exception as error:  # A broken feed must never stop the others.
        return source, None, f"{type(error).__name__}: {error}"
    if feed.get("status", 200) >= 400:
        return source, None, f"HTTP {feed.status}"
    if feed.bozo and not feed.entries and feed.get("status") != 304:
        return source, None, f"unreadable: {feed.bozo_exception}"
    return source, feed, None


# --- Clustering ---

def find_cluster(db: sqlite3.Connection, words: set[str], now: datetime) -> int | None:
    since = (now - OPEN_FOR).isoformat(timespec="seconds")
    best, best_score = None, 0.0
    for row in db.execute("select id, tokens from clusters where last_seen >= ?", (since,)):
        other = set(json.loads(row["tokens"]))
        shared = len(words & other)
        if shared < SHARED:
            continue
        score = shared / min(len(words), len(other))
        if score >= OVERLAP and score > best_score:
            best, best_score = row["id"], score
    return best


def add_item(db: sqlite3.Connection, source: Source, entry: dict, now: datetime) -> int | None:
    """
    Stores one story and returns the cluster it joined or opened, or None when it was already
    known or too old to open a cluster.
    """
    url = clean_url(entry.get("link") or "")
    title = plain_title(entry.get("title") or "", source.name)
    if not url or not title or db.execute("select 1 from items where url = ?", (url,)).fetchone():
        return None

    stamp = now.isoformat(timespec="seconds")
    when = published(entry)
    words = tokens(title)
    fresh = when is None or datetime.fromisoformat(when) >= now - FRESH
    cluster = find_cluster(db, words, now) if words else None

    if cluster is None:
        # Old stories still get a cluster row, marked as sent, so they never reach the ranking.
        cur = db.execute(
            "insert into clusters(title, tokens, first_seen, last_seen, sent) values(?, ?, ?, ?, ?)",
            (title, json.dumps(sorted(words)), stamp, stamp, None if fresh else stamp),
        )
        cluster = cur.lastrowid
    else:
        db.execute("update clusters set last_seen = ? where id = ?", (stamp, cluster))

    db.execute(
        "insert into items(url, source, title, summary, image, published, seen, cluster) values(?, ?, ?, ?, ?, ?, ?, ?)",
        (url, source.name, title, strip_html(entry.get("summary") or "")[:400], int(has_image(entry)), when, stamp, cluster),
    )
    db.execute(
        "update clusters set sources = (select count(distinct source) from items where cluster = ?) where id = ?",
        (cluster, cluster),
    )
    return cluster if fresh else None


def big_events(db: sqlite3.Connection, touched: set[int], now: datetime) -> list[sqlite3.Row]:
    if not touched:
        return []
    marks = ",".join("?" * len(touched))
    rows = db.execute(
        f"select * from clusters where id in ({marks}) and alerted is null and sources >= ?",
        (*touched, BIG_SOURCES),
    ).fetchall()
    return [row for row in rows if now - datetime.fromisoformat(row["first_seen"]) <= BIG_WINDOW]


# --- Run ---

def listen(db: sqlite3.Connection, sources: list[Source], now: datetime | None = None) -> tuple[int, list[sqlite3.Row]]:
    """
    Reads every feed once.

    Args:
        db: Open radar database.
        sources: Feeds to read.
        now: Time of the run, given in tests.

    Returns:
        The number of new stories and the clusters that just became big events.
    """
    now = now or datetime.now(timezone.utc)
    socket.setdefaulttimeout(TIMEOUT)
    known = {row["name"]: row for row in db.execute("select * from feeds")}

    def job(source: Source):
        row = known.get(source.name)
        return fetch(source, row["etag"] if row else None, row["modified"] if row else None)

    with ThreadPoolExecutor(WORKERS) as pool:
        results = list(pool.map(job, sources))

    count, touched = 0, set()
    stamp = now.isoformat(timespec="seconds")
    for source, feed, error in results:
        etag = feed.get("etag") if feed else None
        modified = feed.get("modified") if feed else None
        db.execute(
            "insert into feeds(name, etag, modified, checked, error) values(?, ?, ?, ?, ?) "
            "on conflict(name) do update set etag = coalesce(excluded.etag, etag), "
            "modified = coalesce(excluded.modified, modified), checked = excluded.checked, error = excluded.error",
            (source.name, etag, modified, stamp, error),
        )
        if not feed:
            continue
        for entry in feed.entries:
            before = db.total_changes
            cluster = add_item(db, source, entry, now)
            if db.total_changes > before:
                count += 1
            if cluster is not None:
                touched.add(cluster)
    db.commit()
    return count, big_events(db, touched, now)
