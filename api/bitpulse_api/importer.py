"""
file: bitpulse_api/importer.py
importable: import_stories

import_stories copies published story folders into an empty database. It runs once, when the site
moves off the repository.

description: Moves already published stories from their folders into the database.
"""

# NOTE: Publishing times and image bytes are kept exactly, because the old and new site are compared
# file by file afterwards. Any difference there has to mean a real mistake.

import re
import sqlite3
from pathlib import Path

from . import content as story_text
from . import images, store
from .config import Settings

# --- Helpers ---

# A kept story may link to one that was left out. The words stay and only the link goes, otherwise
# readers land on a page that no longer exists.
def _unlink(body: str, lang: str, slugs: set[str]) -> str:
    for slug in slugs:
        body = re.sub(rf"\[([^\]]+)\]\(/{lang}/stories/{re.escape(slug)}/?\)", r"\1", body)
    return body


def _skipped_slugs(root: Path, skip: set[str], lang: str) -> set[str]:
    slugs = set()
    for key in skip:
        fields, _, _, _ = story_text.parse_file((root / key / f"{lang}.md").read_text(encoding="utf-8"), key)
        slugs.add(fields["slug"])
    return slugs

# --- Import ---

def import_stories(conn: sqlite3.Connection, settings: Settings, root: Path, skip: set[str]) -> list[str]:
    """Imports every story folder under root except the skipped ones.

    Args:
        conn: Open connection to a database without stories.
        settings: Folder paths.
        root: Folder that holds one folder per story.
        skip: Folder names to leave out.

    Returns:
        Folder names that were imported.

    Raises:
        InvalidDraft: If a story is invalid. Nothing is imported in that case.
        ValueError: If the database already has stories or a skipped folder does not exist.
    """
    if store.stories(conn):
        raise ValueError("the database already has stories")
    missing = [key for key in skip if not (root / key).is_dir()]
    if missing:
        raise ValueError(f"no such story to skip: {', '.join(sorted(missing))}")

    removed = {lang: _skipped_slugs(root, skip, lang) for lang in ("en", "tr")}
    imported = []
    with conn:
        for folder in sorted(path for path in root.iterdir() if path.is_dir() and path.name not in skip):
            parsed: dict = {}
            moment = ""
            for lang in ("en", "tr"):
                fields, body, date, clock = story_text.parse_file((folder / f"{lang}.md").read_text(encoding="utf-8"), folder.name)
                parsed[lang] = {**fields, "body": _unlink(body, lang, removed[lang])}
                moment = f"{date} {clock}"
            social = folder / "social.yaml"
            parsed["social"] = social.read_text(encoding="utf-8") if social.exists() else ""

            sha, width, height = images.keep_original(settings.images, (folder / "image.jpg").read_bytes())
            handle = story_text.handle_of(folder.name)
            store.add_image(conn, sha, width, height)
            store.ensure_story(conn, handle)
            version_id = store.add_version(conn, handle, parsed, sha, "import")
            store.set_live(conn, handle, version_id, moment)
            store.add_audit(conn, "import", "story.import", handle, moment)
            imported.append(folder.name)
    return imported
