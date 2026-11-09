"""
file: bitpulse_api/service.py
importable: NotFound, save_draft, request_publish, request_rebuild, read_story, list_stories, story_key

These are the operations behind the HTTP routes. They know nothing about HTTP, and the one time
import and the server commands can call them too.

description: Saves story drafts and turns publishing requests into queued jobs.
"""

# NOTE: The publishing moment is decided when the request arrives, and is only written to the story
# after the worker reports success. A failed first publish leaves the story unpublished.

import sqlite3
from typing import Any, Optional

from . import content as story_text
from . import store

# --- Errors ---

class NotFound(Exception):
    """Raised when a story, image or job does not exist."""

# --- Helpers ---

# The key names the folder and the image files of a published story, and it never changes because
# the publishing moment never changes.
def story_key(handle: str, published_at: str) -> str:
    """Returns the folder name of a published story.

    Args:
        handle: Lasting name of the story.
        published_at: Publishing moment as YYYY-MM-DD HH:MM.

    Returns:
        The date, then the handle.
    """
    return f"{published_at.split(' ')[0]}-{handle}"

# --- Drafts ---

def save_draft(conn: sqlite3.Connection, handle: str, en: str, tr: str, social: str, image: str, actor: str) -> int:
    """Stores a draft as a new version of its story.

    Args:
        conn: Open connection.
        handle: Lasting name of the story.
        en: Text of en.md.
        tr: Text of tr.md.
        social: Text of social.yaml.
        image: Hash of an image already uploaded.
        actor: Device name for the audit log.

    Returns:
        Number of the new version.

    Raises:
        InvalidDraft: If the text is invalid.
        NotFound: If the image was not uploaded.
    """
    if not story_text.HANDLE.match(handle):
        raise story_text.InvalidDraft(f"invalid story name: {handle}")
    parsed = story_text.parse_draft(en, tr, social)
    if not store.has_image(conn, image):
        raise NotFound(f"image not found: {image}")
    with conn:
        store.ensure_story(conn, handle)
        version_id = store.add_version(conn, handle, parsed, image, actor)
        record = store.version(conn, version_id)
        store.add_audit(conn, actor, "draft.save", handle, f"version {record['number']}")
    return int(record["number"])


def read_story(conn: sqlite3.Connection, handle: str) -> dict[str, Any]:
    """Returns the newest version of a story as files.

    Args:
        conn: Open connection.
        handle: Lasting name of the story.

    Returns:
        Key, publishing moment, both Markdown files, social text and image hash. The key is None
        for a story that was never published.

    Raises:
        NotFound: If the story does not exist.
    """
    row = store.story(conn, handle)
    latest = store.latest_version(conn, handle)
    if row is None or latest is None:
        raise NotFound(f"story not found: {handle}")
    published = row["published_at"]
    moment = published or store.minute()
    return {
        "handle": handle,
        "key": story_key(handle, published) if published else None,
        "published_at": published,
        "version": latest["number"],
        "en": story_text.to_markdown(latest["content"]["en"], moment),
        "tr": story_text.to_markdown(latest["content"]["tr"], moment),
        "social": latest["content"]["social"],
        "image": latest["image"],
    }


def list_stories(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return [
        {
            "handle": row["handle"],
            "key": story_key(row["handle"], row["published_at"]) if row["published_at"] else None,
            "published_at": row["published_at"],
            "latest": row["latest"],
        }
        for row in store.stories(conn)
    ]

# --- Publishing ---

# A new version carries the stamped update times, so what was published stays on record exactly.
def request_publish(conn: sqlite3.Connection, handle: str, actor: str) -> int:
    """Queues the newest version of a story for publishing.

    Args:
        conn: Open connection.
        handle: Lasting name of the story.
        actor: Device name for the audit log.

    Returns:
        Id of the queued job.

    Raises:
        NotFound: If the story does not exist.
    """
    row = store.story(conn, handle)
    latest = store.latest_version(conn, handle)
    if row is None or latest is None:
        raise NotFound(f"story not found: {handle}")
    moment = store.minute()
    stamped = story_text.stamp_updates(latest["content"], row["published_at"] or moment, moment)
    with conn:
        version_id = store.add_version(conn, handle, stamped, latest["image"], actor)
        job_id = store.add_job(conn, "publish", handle, version_id, moment, True)
        store.add_audit(conn, actor, "publish.request", handle, f"job {job_id}")
    return job_id


def request_rebuild(conn: sqlite3.Connection, actor: str, go_live: bool = True, note: Optional[str] = None) -> int:
    """Queues a rebuild of the site from the published versions.

    Args:
        conn: Open connection.
        actor: Device name for the audit log.
        go_live: False builds the pages and leaves the live site alone.
        note: Extra text for the audit log.

    Returns:
        Id of the queued job.
    """
    with conn:
        job_id = store.add_job(conn, "rebuild", None, None, store.minute(), go_live)
        store.add_audit(conn, actor, "rebuild.request", f"job {job_id}", note or "")
    return job_id
