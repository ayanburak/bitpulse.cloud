"""
file: insights/round.py
importable: run, due, RECENT, DAILY

run does one round: it lists every post, reads the numbers of the posts that are due, sends them
to the API with the pictures it still lacks, then reads the account numbers of the last days.

description: Runs one round of reading Instagram and writing to the Bitpulse API.
"""

# NOTE: The service keeps no state of its own. When a post was last read comes from the API, so a
# round that dies halfway is simply picked up by the next one.
#
# NOTE: A new post is read every round because its first hours are the curve the editor wants to
# see. After a week the numbers barely move and once a day is enough.

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from . import http
from .api import Api
from .meta import Meta, kind_of

log = logging.getLogger(__name__)

# --- Constants ---

RECENT = timedelta(days=7)
DAILY = timedelta(hours=20)
PICTURE_HOSTS = ("cdninstagram.com", "fbcdn.net")
FORMAT = "%Y-%m-%d %H:%M"

# --- Round ---

def due(post: dict[str, Any], last: Optional[str], now: datetime) -> bool:
    """Tells whether a post should be read in this round.

    Args:
        post: A post as Meta describes it.
        last: When the API last stored its numbers, or None.
        now: Time of the round.

    Returns:
        True for a post younger than a week, one never read and one not read for most of a day.
    """
    if last is None:
        return True
    posted = datetime.strptime(post["timestamp"], "%Y-%m-%dT%H:%M:%S%z")
    if now - posted < RECENT:
        return True
    return now - datetime.strptime(last, FORMAT).replace(tzinfo=timezone.utc) >= DAILY


# One post that fails is logged and skipped, the others still reach the panel.
def run(meta: Meta, api: Api, days: int = 2, now: Optional[datetime] = None) -> dict[str, int]:
    """Does one round.

    Args:
        meta: Reader of the Instagram account.
        api: Client of the Bitpulse API.
        days: How many past days of account numbers to read.
        now: Time of the round, the current time when left out.

    Returns:
        How many posts were read, how many pictures were sent and how many posts failed.
    """
    now = now or datetime.now(timezone.utc)
    fetched = api.fetched()
    posts = [post for post in meta.posts() if due(post, fetched.get(post["id"]), now)]
    rows, sources, failed = [], {}, 0
    for post in posts:
        try:
            counts = meta.counts(post)
        except http.HttpError as error:
            log.warning("numbers of post %s could not be read: %s", post["id"], error)
            failed += 1
            continue
        rows.append(_row(post, counts))
        sources[post["id"]] = post.get("thumbnail_url") or post.get("media_url")

    sent = 0
    for post_id in api.save_posts(rows):
        if not sources.get(post_id):
            continue
        try:
            api.save_thumb(post_id, http.download(sources[post_id], PICTURE_HOSTS))
            sent += 1
        except http.HttpError as error:
            log.warning("picture of post %s could not be stored: %s", post_id, error)

    api.save_days(_days(meta, now, days))
    return {"posts": len(rows), "pictures": sent, "failed": failed}


def _row(post: dict[str, Any], counts: dict[str, Optional[int]]) -> dict[str, Any]:
    return {
        "id": post["id"],
        "kind": kind_of(post),
        "posted_at": post["timestamp"],
        "permalink": post["permalink"],
        "caption": (post.get("caption") or "")[:2200],
        "counts": counts,
    }


# Today has no finished totals yet, so the days end with yesterday. The follower count has no
# history in Meta, it is the number of right now and is filed under today.
def _days(meta: Meta, now: datetime, count: int) -> list[dict[str, Any]]:
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    rows = [{"day": midnight.strftime("%Y-%m-%d"), "followers": meta.profile().get("followers_count")}]
    for back in range(1, count + 1):
        start = midnight - timedelta(days=back)
        try:
            numbers = meta.day(int(start.timestamp()), int((start + timedelta(days=1)).timestamp()))
        except http.HttpError as error:
            log.warning("account numbers of %s could not be read: %s", start.date(), error)
            continue
        rows.append({"day": start.strftime("%Y-%m-%d"), **numbers})
    return rows
