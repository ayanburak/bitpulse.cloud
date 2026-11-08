"""
file: radar/clip.py
importable: save, find_link

Saves a link the editor pastes into the bot from the phone as a candidate of its own, with a
brief written right away, so the research can start later on the computer from an R number.

description: Turns a link sent to the bot into a saved candidate.
"""

# NOTE: The title is read once here and the page is read again for the brief. Two requests for a
# link the editor saved by hand costs nothing, and keeping them apart keeps the brief code alone.

import json
import re
import sqlite3
from datetime import datetime, timezone
from urllib.parse import urlsplit

import trafilatura

from radar.brief import TWEET, build_brief, download, read_tweet
from radar.listen import clean_url, tokens

LINK = re.compile(r"https?://[^\s<>]+")
TITLE_LENGTH = 120


def find_link(text: str) -> str | None:
    match = LINK.search(text)
    return match.group(0).rstrip(".,;:!?)'\"") if match else None


# X share links carry tracking in the query and only the post number means anything.
def normal(url: str) -> str:
    match = TWEET.match(url)
    return f"https://x.com/{match.group(1)}/status/{match.group(2)}" if match else clean_url(url)


# A page that can not be read is still saved, the editor chose this link and can open it by hand.
def title_of(url: str) -> tuple[str, str]:
    try:
        if TWEET.match(url):
            text = read_tweet(url)["text"]
            return text[:TITLE_LENGTH], text
        meta = trafilatura.extract_metadata(download(url))
        return (meta.title if meta and meta.title else url), (meta.description if meta and meta.description else "")
    except Exception:  # Any failure here only costs the title.
        return url, ""


def save(db: sqlite3.Connection, url: str) -> tuple[int, str, bool]:
    """
    Stores a link as a candidate and writes its brief.

    Args:
        db: Open radar database.
        url: Address the editor sent.

    Returns:
        The R number, the title and whether the link was new.
    """
    url = normal(url)
    known = db.execute("select cluster, title from items where url = ?", (url,)).fetchone()
    if known:
        return known["cluster"], known["title"], False

    title, summary = title_of(url)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    source = urlsplit(url).netloc.removeprefix("www.")
    cur = db.execute(
        "insert into clusters(title, tokens, first_seen, last_seen, sent, decision, clip) values(?, ?, ?, ?, ?, 'do', 1)",
        (title, json.dumps(sorted(tokens(title))), now, now, now),
    )
    db.execute(
        "insert into items(url, source, title, summary, image, published, seen, cluster) values(?, ?, ?, ?, 0, ?, ?, ?)",
        (url, source, title, summary[:400], now, now, cur.lastrowid),
    )
    db.commit()
    build_brief(db, cur.lastrowid)
    return cur.lastrowid, title, True
