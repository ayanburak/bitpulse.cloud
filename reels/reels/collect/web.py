"""
file: reels/collect/web.py
importable: AGENT, get, get_json, download

description: Fetches pages, JSON and files from the web with one client name.
"""

# NOTE: Wikimedia refuses requests that do not name the client and a way to reach its owner,
# the site address is that way.

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from reels.media import MediaError

AGENT = "bitpulse-reels/0.1 (+https://bitpulse.cloud)"
TIMEOUT = 30


def get(url: str) -> bytes:
    """Returns the body at url.

    Raises:
        MediaError: The request failed or the server answered with an error.
    """
    request = urllib.request.Request(url, headers={"User-Agent": AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.read()
    except (urllib.error.URLError, TimeoutError) as error:
        raise MediaError(f"could not fetch {url}: {error}") from None


def get_json(url: str) -> Any:
    return json.loads(get(url))


def download(url: str, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(get(url))
    return out
