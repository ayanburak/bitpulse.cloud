"""
file: bitpulse_api/social.py
importable: InvalidSocial, accept, decode, path_of, read_text, pages, prune, MAX_UPLOAD

The device makes the social files of a story and uploads them together. accept checks them and puts
the new set in place in one step.

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

from PIL import Image, UnidentifiedImageError

from . import service, store
from .config import Settings

# --- Constants ---

# The upload is one JSON body with the files in base64, which adds a third to their size.
MAX_UPLOAD = 32 * 1024 * 1024
MAX_PIXELS = 4_000_000
MAX_TEXT = 16 * 1024
MAX_VIDEO = 16 * 1024 * 1024
NAME = re.compile(r"^(x\.txt|caption\.txt|post\.mp4|page-([1-9]|1[0-9]|20)\.png)$")
REQUIRED = {"x.txt", "caption.txt", "post.mp4", "page-1.png"}

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
def _checked(name: str, data: bytes) -> bytes:
    if name.endswith(".png"):
        return _clean_page(name, data)
    if name.endswith(".mp4"):
        if len(data) > MAX_VIDEO or data[4:8] != b"ftyp":
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
    unknown = [name for name in files if not NAME.match(name)]
    if unknown:
        raise InvalidSocial(f"unknown file: {sorted(unknown)[0]}")
    if REQUIRED - set(files):
        raise InvalidSocial(f"missing file: {sorted(REQUIRED - set(files))[0]}")
    _replace(settings.social, handle, {name: _checked(name, data) for name, data in files.items()})
    with conn:
        store.save_social(conn, handle)
        store.add_audit(conn, actor, "social.upload", handle, f"{len(files)} files")
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
    path = settings.social / handle / name
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
