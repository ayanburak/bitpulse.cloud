"""
file: bitpulse_cli/fetch.py
importable: fetch_media

Downloads the video or the image behind a link into a clip folder, so the clip script can work
from a local file. yt-dlp knows YouTube, X and many other sites, an address that already points to
an image file is saved as it is.

description: Saves the media of a link next to a clip and names its owner.
"""

# NOTE: yt-dlp is imported inside the function. Every other command runs without it, and its import
# is slow.
#
# XXX: A post on X that holds only pictures has no video for yt-dlp to find. The skill then takes the
# picture address from the page and gives that address instead.

import json
import urllib.request
from pathlib import Path

# --- Constants ---

IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
HEADERS = {"User-Agent": "BitpulseClip/1.0 (+https://bitpulse.cloud)"}
TIMEOUT = 60

# The best mp4 video with its sound, so ffmpeg can cut it without turning it into another format first.
FORMAT = "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b"

# --- Fetching ---

def _image(url: str, folder: Path) -> dict[str, str]:
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        kind = response.headers.get_content_type()
        if kind not in IMAGE_TYPES:
            raise ValueError(f"{url} is not a video page or an image, it answered {kind}")
        path = folder / f"source{IMAGE_TYPES[kind]}"
        path.write_bytes(response.read())
    return {"file": path.name, "owner": "", "title": "", "duration": "", "page": url}


def fetch_media(url: str, folder: Path) -> dict[str, str]:
    """Downloads the media of a link into folder as source.mp4 or source.<image type>.

    Args:
        url: Address of a video page, a social post or an image file.
        folder: Clip folder, created when missing.

    Returns:
        The saved file name, the owner as the site names it, the title, the length in seconds and
        the page address. Owner and title are empty for a plain image.

    Raises:
        ValueError: If the link leads to neither a video nor an image.
    """
    folder.mkdir(parents=True, exist_ok=True)
    result = _image(url, folder) if _is_image(url) else _video(url, folder)
    (folder / "source.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


# A site that refuses HEAD is treated as a page, yt-dlp then decides what is there.
def _is_image(url: str) -> bool:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS, method="HEAD"), timeout=TIMEOUT) as response:
            return response.headers.get_content_type() in IMAGE_TYPES
    except OSError:
        return False


def _video(url: str, folder: Path) -> dict[str, str]:
    import yt_dlp
    from yt_dlp.utils import DownloadError

    options = {"format": FORMAT, "merge_output_format": "mp4", "outtmpl": str(folder / "source.%(ext)s"),
               "quiet": True, "no_warnings": True, "noprogress": True, "noplaylist": True, "overwrites": True}
    try:
        with yt_dlp.YoutubeDL(options) as loader:
            info = loader.extract_info(url, download=True)
    except DownloadError as error:
        raise ValueError(f"no video found at {url}: {error}") from error
    return {
        "file": "source.mp4",
        "owner": info.get("channel") or info.get("uploader") or "",
        "title": info.get("title") or "",
        "duration": str(info.get("duration") or ""),
        "page": info.get("webpage_url") or url,
    }
