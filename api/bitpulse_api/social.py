"""
file: bitpulse_api/social.py
importable: InvalidSocial, accept, accept_clip, decode, decode_clip, path_of, clip_path, read_text, pages, prune, MAX_UPLOAD,
            MAX_CLIP_UPLOAD

The device makes the social files of a story and uploads them together. accept checks them and puts
the new set in place in one step. A clip is a post that goes to Instagram only and has no story,
accept_clip stores it the same way under its own name and title.

description: Checks, stores and removes the finished social files of a story.
"""

# NOTE: The files are made on the device because the server has one core and the page needs a real
# browser. They are never built from anything here, so losing them only means uploading them again,
# which is why they stay out of the backup and go away after a month.

import base64
import binascii
import io
import json
import re
import shutil
import sqlite3
from pathlib import Path
from typing import Optional

from PIL import Image, UnidentifiedImageError

from . import content, service, store
from .config import Settings

# --- Constants ---

# The upload is one JSON body with the files in base64, which adds a third to their size.
MAX_UPLOAD = 32 * 1024 * 1024
MAX_PIXELS = 4_000_000
MAX_TEXT = 16 * 1024
MAX_VIDEO = 16 * 1024 * 1024
NAME = re.compile(r"^(x\.txt|caption\.txt|post\.mp4|page-([1-9]|1[0-9]|20)\.png)$")
REQUIRED = {"x.txt", "caption.txt", "post.mp4", "page-1.png"}

# A clip has no X post and one page, the first frame of its video, which the panel shows.
CLIP_FILES = {"caption.txt", "post.mp4", "page-1.png"}

# A clip carries real footage of up to about ninety seconds, the clip script keeps it under four
# megabits a second, so it gets more room than the still video of a story.
MAX_CLIP_VIDEO = 48 * 1024 * 1024
MAX_CLIP_UPLOAD = 72 * 1024 * 1024
MAX_TITLE = 200

# --- Errors ---

class InvalidSocial(Exception):
    """Raised when an upload is not a complete, valid set of social files."""

# --- Checks ---

def decode(raw: bytes) -> dict[str, bytes]:
    """Reads an upload body into separate files.

    Args:
        raw: Request body, JSON with a files object of names and base64 text.

    Returns:
        File name and content of each file.

    Raises:
        InvalidSocial: If the body has another form or a file is not valid base64.
    """
    try:
        files = json.loads(raw)["files"]
        return {str(name): base64.b64decode(text, validate=True) for name, text in files.items()}
    except (ValueError, KeyError, TypeError, AttributeError, binascii.Error) as error:
        raise InvalidSocial("the upload could not be read") from error


def decode_clip(raw: bytes) -> tuple[str, dict[str, bytes]]:
    """Reads a clip upload into its title and its files.

    Args:
        raw: Request body, JSON with a title text and a files object like the one decode reads.

    Returns:
        The title and the file name and content of each file.

    Raises:
        InvalidSocial: If the body has another form.
    """
    try:
        title = json.loads(raw)["title"]
    except (ValueError, KeyError, TypeError) as error:
        raise InvalidSocial("the upload could not be read") from error
    if not isinstance(title, str):
        raise InvalidSocial("the upload could not be read")
    return title, decode(raw)


# The picture is drawn again for the same reason as a cover image, what gets stored came from here.
def _clean_page(name: str, data: bytes) -> bytes:
    try:
        with Image.open(io.BytesIO(data), formats=("PNG",)) as source:
            if source.width * source.height > MAX_PIXELS:
                raise InvalidSocial(f"{name}: too many pixels")
            picture = source.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise InvalidSocial(f"{name}: not a PNG image") from error
    output = io.BytesIO()
    picture.save(output, "PNG")
    return output.getvalue()


# The server has no tool that could rebuild a video. It is checked by its signature and only ever
# leaves as a download, so the browser never plays it inside the panel.
def _checked(name: str, data: bytes, video_limit: int = MAX_VIDEO) -> bytes:
    if name.endswith(".png"):
        return _clean_page(name, data)
    if name.endswith(".mp4"):
        if len(data) > video_limit or data[4:8] != b"ftyp":
            raise InvalidSocial(f"{name}: not a usable video")
        return data
    if len(data) > MAX_TEXT:
        raise InvalidSocial(f"{name}: too long")
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise InvalidSocial(f"{name}: not text") from error
    return data

# --- Storing ---

# The set is finished under a hidden name and swapped in, the panel never sees half a post.
def _replace(root: Path, handle: str, files: dict[str, bytes]) -> None:
    partial, old, target = root / f".{handle}.new", root / f".{handle}.old", root / handle
    shutil.rmtree(partial, ignore_errors=True)
    shutil.rmtree(old, ignore_errors=True)
    partial.mkdir()
    for name, data in files.items():
        (partial / name).write_bytes(data)
    if target.exists():
        target.rename(old)
    partial.rename(target)
    shutil.rmtree(old, ignore_errors=True)


def _clean_set(files: dict[str, bytes], allowed: Optional[set[str]], required: set[str], video_limit: int = MAX_VIDEO) -> dict[str, bytes]:
    unknown = [name for name in files if not NAME.match(name) or (allowed is not None and name not in allowed)]
    if unknown:
        raise InvalidSocial(f"unknown file: {sorted(unknown)[0]}")
    if required - set(files):
        raise InvalidSocial(f"missing file: {sorted(required - set(files))[0]}")
    return {name: _checked(name, data, video_limit) for name, data in files.items()}


def accept(conn: sqlite3.Connection, settings: Settings, handle: str, files: dict[str, bytes], actor: str) -> list[str]:
    """Checks the social files of a story and stores them.

    Args:
        conn: Open connection.
        settings: Folder paths.
        handle: Lasting name of the story.
        files: File name and content of each file.
        actor: Name for the audit log.

    Returns:
        The stored file names.

    Raises:
        NotFound: If the story does not exist.
        InvalidSocial: If a file is missing, unknown or invalid.
    """
    if store.story(conn, handle) is None:
        raise service.NotFound(f"story not found: {handle}")
    _replace(settings.social, handle, _clean_set(files, None, REQUIRED))
    with conn:
        store.save_social(conn, handle)
        store.add_audit(conn, actor, "social.upload", handle, f"{len(files)} files")
    return sorted(files)

def accept_clip(conn: sqlite3.Connection, settings: Settings, handle: str, title: str, files: dict[str, bytes], actor: str) -> list[str]:
    """Checks the files of a clip and stores them under its name.

    Args:
        conn: Open connection.
        settings: Folder paths.
        handle: Name of the clip, lowercase words joined by dashes.
        title: What the panel shows above the clip.
        files: File name and content of each file.
        actor: Name for the audit log.

    Returns:
        The stored file names.

    Raises:
        InvalidSocial: If the name or the title can not be used, or a file is missing, unknown or invalid.
    """
    if not content.HANDLE.match(handle):
        raise InvalidSocial(f"invalid clip name: {handle}")
    title = title.strip()
    if not title or len(title) > MAX_TITLE:
        raise InvalidSocial("a clip needs a title of at most 200 characters")
    _replace(settings.clips, handle, _clean_set(files, CLIP_FILES, CLIP_FILES, MAX_CLIP_VIDEO))
    with conn:
        store.save_clip(conn, handle, title)
        store.add_audit(conn, actor, "clip.upload", handle, f"{len(files)} files")
    return sorted(files)


# --- Reading ---

def path_of(settings: Settings, handle: str, name: str) -> Path:
    """Returns where one stored file is.

    Args:
        settings: Folder paths.
        handle: A handle that came from the database.
        name: File name.

    Returns:
        Path of the file.

    Raises:
        NotFound: If the name is not one of the allowed file names or the file is missing.
    """
    return _file(settings.social, handle, name)


def clip_path(settings: Settings, handle: str, name: str) -> Path:
    """Returns where one stored file of a clip is, with the same checks as path_of."""
    return _file(settings.clips, handle, name)


def _file(root: Path, handle: str, name: str) -> Path:
    path = root / handle / name
    if not NAME.match(name) or not path.is_file():
        raise service.NotFound(f"no such file: {name}")
    return path


def read_text(settings: Settings, handle: str, name: str) -> str:
    return path_of(settings, handle, name).read_text(encoding="utf-8")


def pages(settings: Settings, handle: str) -> list[str]:
    names = [path.name for path in (settings.social / handle).glob("page-*.png")]
    return sorted(names, key=lambda name: int(name[5:-4]))

# --- Cleaning ---

def prune(conn: sqlite3.Connection, settings: Settings, before: str) -> None:
    """Removes the files of posts uploaded before a moment.

    Args:
        conn: Open connection.
        settings: Folder paths.
        before: Oldest upload time to keep, YYYY-MM-DD HH:MM.
    """
    for handle in store.old_social(conn, before):
        shutil.rmtree(settings.social / handle, ignore_errors=True)
        with conn:
            store.remove_social(conn, handle)
    for handle in store.old_clips(conn, before):
        shutil.rmtree(settings.clips / handle, ignore_errors=True)
        with conn:
            store.remove_clip(conn, handle)
