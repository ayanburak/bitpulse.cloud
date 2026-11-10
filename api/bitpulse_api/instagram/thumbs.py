"""
file: bitpulse_api/instagram/thumbs.py
importable: InvalidThumb, accept, path_of, MAX_UPLOAD

accept rebuilds the small picture of an Instagram post and stores it under the post id. path_of
gives the stored file for the panel.

description: Checks, shrinks and stores the small pictures of Instagram posts.
"""

# NOTE: The picture comes from the Instagram servers through our own service, but it is still
# decoded and written out again like a cover image. What reaches the disk is pixels the API made.

import io
import os
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

# --- Constants ---

MAX_UPLOAD = 5 * 1024 * 1024
MAX_PIXELS = 20_000_000
WIDTH = 360
ALLOWED = ("JPEG", "PNG", "WEBP")
QUALITY = 82

# --- Errors ---

class InvalidThumb(Exception):
    """Raised when an uploaded file is not a usable picture."""

# --- Storing ---

# The id is checked by the route before it gets here, only digits ever become part of the path.
def accept(folder: Path, post_id: str, raw: bytes) -> None:
    """Decodes a picture, shrinks it to the panel width and stores it as JPEG.

    Args:
        folder: Folder of the small pictures.
        post_id: Instagram id of the post, digits only.
        raw: Uploaded bytes.

    Raises:
        InvalidThumb: If the file is too large or not a supported picture.
    """
    if len(raw) > MAX_UPLOAD:
        raise InvalidThumb("picture is too large")
    try:
        with Image.open(io.BytesIO(raw), formats=ALLOWED) as source:
            if source.width * source.height > MAX_PIXELS:
                raise InvalidThumb("picture has too many pixels")
            picture = ImageOps.exif_transpose(source).convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise InvalidThumb("file is not a supported picture") from error

    if picture.width > WIDTH:
        picture = picture.resize((WIDTH, max(1, round(picture.height * WIDTH / picture.width))), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    picture.save(output, "JPEG", quality=QUALITY, optimize=True)
    partial = folder / f".{post_id}.part"
    partial.write_bytes(output.getvalue())
    os.replace(partial, path_of(folder, post_id))


def path_of(folder: Path, post_id: str) -> Path:
    return folder / f"{post_id}.jpg"
