"""
file: bitpulse_api/images.py
importable: InvalidImage, accept_upload, keep_original, MAX_UPLOAD

accept_upload rebuilds an uploaded picture and stores the clean copy under its own hash.
keep_original stores trusted bytes unchanged, which only the one time story import needs.

description: Checks, cleans and stores cover images.
"""

# NOTE: A picture is decoded and written out again because the file itself is untrusted. What
# reaches the disk is pixels the API produced, with no metadata and no bytes from the upload.

import hashlib
import io
import os
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

# --- Constants ---

MAX_UPLOAD = 15 * 1024 * 1024
MIN_WIDTH = 1200
MAX_WIDTH = 2000
MAX_PIXELS = 40_000_000
ALLOWED = ("JPEG", "PNG", "WEBP")
QUALITY = 90

# --- Errors ---

class InvalidImage(Exception):
    """Raised when an uploaded file is not a usable cover image."""

# --- Storing ---

# The file is written next to its final place and renamed, a crash can not leave half an image
# under a valid hash.
def _write(folder: Path, data: bytes) -> str:
    sha = hashlib.sha256(data).hexdigest()
    target = folder / f"{sha}.jpg"
    if not target.exists():
        partial = folder / f".{sha}.part"
        partial.write_bytes(data)
        os.replace(partial, target)
    return sha


# Image.open only reads the header, so the size limit runs before any pixel is decoded and a tiny
# file that expands to a huge picture is refused cheaply.
def accept_upload(folder: Path, raw: bytes) -> tuple[str, int, int]:
    """Decodes an upload, rebuilds it as a clean JPEG and stores it.

    Args:
        folder: Image folder.
        raw: Uploaded bytes.

    Returns:
        Hash of the stored file, then its width and height.

    Raises:
        InvalidImage: If the file is too large, of another type or too small for a cover.
    """
    if len(raw) > MAX_UPLOAD:
        raise InvalidImage("image is too large")
    try:
        with Image.open(io.BytesIO(raw), formats=ALLOWED) as source:
            if source.width * source.height > MAX_PIXELS:
                raise InvalidImage("image has too many pixels")
            picture = ImageOps.exif_transpose(source).convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise InvalidImage("file is not a supported image") from error

    if picture.width < MIN_WIDTH:
        raise InvalidImage(f"image must be at least {MIN_WIDTH} pixels wide")
    if picture.width > MAX_WIDTH:
        picture = picture.resize((MAX_WIDTH, round(picture.height * MAX_WIDTH / picture.width)), Image.Resampling.LANCZOS)

    output = io.BytesIO()
    picture.save(output, "JPEG", quality=QUALITY, optimize=True)
    return _write(folder, output.getvalue()), picture.width, picture.height


# Rebuilding the published images would change their bytes and make the old and new site differ
# in the comparison that proves the import is correct.
def keep_original(folder: Path, raw: bytes) -> tuple[str, int, int]:
    """Stores already published image bytes unchanged.

    Args:
        folder: Image folder.
        raw: Bytes of the published image.

    Returns:
        Hash of the stored file, then its width and height.
    """
    with Image.open(io.BytesIO(raw)) as source:
        width, height = source.size
    return _write(folder, raw), width, height
