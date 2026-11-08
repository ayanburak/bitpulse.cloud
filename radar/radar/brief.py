"""
file: radar/brief.py
importable: build_brief, brief_path

When the editor presses Do, every story of the cluster is downloaded and reduced to its article
text, so the writing session starts from a ready file instead of opening pages one by one. Image
addresses and video links found in the pages are collected too, because a story needs both.

The brief is a plain Markdown file in the briefs folder next to the database.

description: Downloads the stories of a cluster and writes their text into one brief file.
"""

# NOTE: No model is used here. Reading pages is the most expensive part of writing a story when
# a model does it, and a library that strips menus and ads does it for free.
#
# XXX: Some outlets block scripts or put the text behind a paywall. Their entry in the brief then
# says so, and the source has to be opened by hand if it matters.

#
# NOTE: The server also runs other private services, and the editor can paste any link into the
# bot. So every address and every redirect has to resolve to the public internet before it is read.

import html as markup
import ipaddress
import json
import os
import re
import socket
import sqlite3
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import trafilatura

# --- Constants ---

AGENT = "Mozilla/5.0 (compatible; BitpulseRadar/0.1; +https://bitpulse.cloud)"
TIMEOUT = 20
MAX_SOURCES = 8
MAX_WORDS = 1500

TWEET = re.compile(r"https?://(?:www\.|mobile\.)?(?:x|twitter)\.com/(\w+)/status/(\d+)")

VIDEO = re.compile(
    r"https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=|embed/|shorts/)[\w-]{11}|youtu\.be/[\w-]{11}"
    r"|(?:x|twitter)\.com/\w+/status/\d+|vimeo\.com/\d+|[^\s\"'<>]+\.mp4)"
)


# --- Paths ---

def brief_path(number: int) -> Path:
    base = Path(os.environ.get("RADAR_DB", "data/radar.db")).parent / "briefs"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"R-{number:04d}.md"


# --- Pages ---

def public_url(url: str) -> str:
    """
    Checks that an address points to the public internet.

    Args:
        url: Address about to be read.

    Returns:
        The same address.

    Raises:
        ValueError: When the scheme is not web or the host is private, local or unknown.
    """
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ValueError(f"Not a web address: {url}")
    for *_, address in socket.getaddrinfo(parts.hostname, parts.port or 443):
        if not ipaddress.ip_address(address[0]).is_global:
            raise ValueError(f"Not a public address: {url}")
    return url


# A public page can still redirect to a private one, so each hop goes through the same check.
class PublicRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


OPENER = urllib.request.build_opener(PublicRedirect)


def download(url: str) -> str:
    request = urllib.request.Request(public_url(url), headers={"User-Agent": AGENT})
    with OPENER.open(request, timeout=TIMEOUT) as response:
        return response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")


# X shows nothing to a script without a login. Its public embed address still gives the post text.
def read_tweet(url: str) -> dict:
    query = urllib.parse.urlencode({"url": url, "omit_script": 1})
    body = json.loads(download(f"https://publish.x.com/oembed?{query}"))
    text = markup.unescape(re.sub(r"<[^>]+>", " ", body["html"]))
    return {"error": "", "text": " ".join(text.split()), "image": "", "videos": [url]}


def shorten(text: str) -> str:
    words = text.split()
    if len(words) <= MAX_WORDS:
        return text
    return " ".join(words[:MAX_WORDS]) + " [cut]"


def read_page(url: str) -> dict:
    """
    Returns the article text, its image and the video links of one page. A page that can not be
    read comes back with an error and empty fields instead of stopping the brief.
    """
    try:
        if TWEET.match(url):
            return read_tweet(url)
        html = download(url)
    except Exception as error:  # One blocked outlet must not stop the others.
        return {"error": f"{type(error).__name__}: {error}", "text": "", "image": "", "videos": []}
    text = trafilatura.extract(html, include_comments=False, include_tables=False) or ""
    meta = trafilatura.extract_metadata(html)
    videos = sorted(set(VIDEO.findall(html)))[:10]
    error = "" if text else "no article text found, maybe a paywall"
    return {"error": error, "text": shorten(text), "image": (meta.image if meta else "") or "", "videos": videos}


# --- Brief ---

def build_brief(db: sqlite3.Connection, number: int) -> Path:
    """
    Writes the brief of one cluster.

    Args:
        db: Open radar database.
        number: Cluster id, the number in R-0142.

    Returns:
        Path of the written file.

    Raises:
        LookupError: When the cluster does not exist.
    """
    cluster = db.execute("select * from clusters where id = ?", (number,)).fetchone()
    if not cluster:
        raise LookupError(f"No cluster R-{number:04d}")
    # Google News links only redirect, so they are read last and only when space is left.
    items = db.execute(
        "select * from items where cluster = ? order by source = 'Google News', published",
        (number,),
    ).fetchall()[:MAX_SOURCES]

    stamp = datetime.now(timezone.utc).isoformat(timespec="minutes")
    lines = [f"# R-{number:04d} {cluster['title']}", "", f"Brief written {stamp}, {len(items)} sources.", ""]
    sources = []
    for item in items:
        page = read_page(item["url"])
        sources.append(f'  - name: "{item["source"]}: {item["title"].replace(chr(34), chr(39))}"\n    url: {item["url"]}')
        lines += [f"## {item['source']}", "", f"Title: {item['title']}", f"Address: {item['url']}",
                  f"Published: {item['published'] or 'unknown'}"]
        if page["image"]:
            lines.append(f"Image: {page['image']}")
        if page["videos"]:
            lines.append("Videos: " + " ".join(page["videos"]))
        if page["error"]:
            lines.append(f"Could not read: {page['error']}")
        lines += ["", page["text"] or item["summary"], ""]

    # Ready to paste into a story, with the outlet named as the editorial policy asks.
    lines += ["## Sources block", "", "```yaml", "sources:", *sources, "```", ""]
    path = brief_path(number)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
