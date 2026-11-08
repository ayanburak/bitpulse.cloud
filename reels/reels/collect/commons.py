"""
file: reels/collect/commons.py
importable: Media, search

Wikimedia Commons holds a great deal of free footage and photographs, among them the public
domain material of the US armed forces. A search returns files with their address, size,
length, date and licence, all read from the Commons API, and for a picture the address of a
small copy for its sheet.

description: Searches Wikimedia Commons for videos and images.
"""

import re
import urllib.parse
from dataclasses import dataclass

from reels.collect.web import get_json

API = "https://commons.wikimedia.org/w/api.php"
# Commons scales a picture down on its own servers, a photograph of 5000 pixels would otherwise
# be downloaded whole only to be shown 240 pixels wide on a sheet.
THUMB = 480


@dataclass(frozen=True)
class Media:
    title: str
    url: str
    kind: str
    width: int
    height: int
    seconds: float
    day: str
    licence: str
    thumb: str = ""


def query(params: dict) -> dict:
    return get_json(f"{API}?{urllib.parse.urlencode({**params, 'format': 'json', 'formatversion': 2})}")


def search(words: str, kind: str, count: int) -> list[Media]:
    """Searches Commons files.

    Args:
        words: What to search for.
        kind: video or image.
        count: How many files to return at most.
    """
    filetype = "video" if kind == "video" else "bitmap"
    hits = query({"action": "query", "list": "search", "srnamespace": 6, "srlimit": count,
                  "srsearch": f"{words} filetype:{filetype}"})["query"]["search"]
    if not hits:
        return []
    pages = query({"action": "query", "prop": "imageinfo", "titles": "|".join(hit["title"] for hit in hits),
                   "iiprop": "url|size|mime|extmetadata", "iiurlwidth": THUMB})["query"]["pages"]
    found = []
    for page in pages:
        info = (page.get("imageinfo") or [{}])[0]
        if "url" not in info:
            continue
        meta = info.get("extmetadata", {})
        day = re.sub(r"<[^>]+>", "", meta.get("DateTimeOriginal", {}).get("value", ""))[:10]
        found.append(Media(page["title"].removeprefix("File:"), info["url"], kind, info.get("width", 0), info.get("height", 0),
                           float(info.get("duration") or 0), day, meta.get("LicenseShortName", {}).get("value", ""),
                           info.get("thumburl", "")))
    return found
