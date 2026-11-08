"""
file: reels/collect/pages.py
importable: Picture, pictures

The pages of the organizations in a story often hold the real document, a poster, a statement
or an official photograph, and the story's own sources hold the news photographs of the agencies.
Every large image on a page is downloaded and measured, small ones, icons and logos, are dropped.
Each picture carries its credit as the page gives it, so the reel can name the photographer's
agency.

description: Downloads the large images of a web page with their credits.
"""

# NOTE: srcset lists the same image in several sizes, the widest is taken. og:image is the image
# the page itself chose to stand for it and comes first. A page often shows a small preview
# that links to the full image, as the reward poster of the first reel did, so links to image
# files are taken too, before the previews. Favicons and logos are left out by their names.
#
# NOTE: The same photograph comes in several sizes under the same file name, only the first is
# kept. BBC's branded copies carry its logo over the picture and are left out.
#
# NOTE: A credit sits near the image on the page, in a caption such as "Image source, Getty
# Images", in a copyright field of the page's data, or in the file name itself as Al Jazeera's
# AFP__ names do. The text after each mention of the file name is searched for it. When none is
# found the credit is left empty and said so, the site's name would read like an owner. On a news
# page these are mostly the previews of other stories at its side.

import re
import urllib.parse
import warnings
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image

from reels.collect.web import get
from reels.media import MediaError

SMALLEST = 600
MOST = 12
SKIP = re.compile(r"favicon|logo|icon|sprite")
SKIP_PATH = re.compile(r"/branded")
AGENCIES = re.compile(r"Getty Images|AFP|Reuters|Associated Press|AP Photo|EPA|PA Images|PA Media|Imagn|USA TODAY Sports|"
                      r"Shutterstock|Anadolu|Xinhua|Bloomberg|NurPhoto|SOPA Images|Sipa|Alamy|dpa")
# A copyright field of the page's data, its quotes sometimes escaped inside a script.
FIELD = re.compile(r"""copyright(?:Holder)?\\?["']\s*:\s*\\?["']([^"'\\<]{2,60})""", re.I)
NEAR = 1500


@dataclass(frozen=True)
class Picture:
    page: str
    url: str
    path: Path
    width: int
    height: int
    credit: str


def addresses(page: str, html: str) -> list[str]:
    found = re.findall(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', html)
    found += re.findall(r'<a\b[^>]+href=["\']([^"\']+\.(?:jpe?g|png|webp)(?:\?[^"\']*)?)["\']', html, flags=re.I)
    for tag in re.findall(r"<img\b[^>]*>", html, flags=re.I):
        srcset = re.search(r'srcset=["\']([^"\']+)', tag)
        if srcset:
            options = [part.strip().split() for part in srcset.group(1).split(",") if part.strip()]
            found.append(max(options, key=lambda o: int(re.sub(r"\D", "", o[1]) or 0) if len(o) > 1 else 0)[0])
        source = re.search(r'\ssrc=["\']([^"\']+)', tag)
        if source:
            found.append(source.group(1))
    urls, names = [], set()
    for url in found:
        url = urllib.parse.urljoin(page, url.replace("&amp;", "&"))
        name = url.lower().split("?")[0].rsplit("/", 1)[-1]
        if (url.startswith("http") and not name.endswith((".svg", ".gif")) and not SKIP.search(name)
                and not SKIP_PATH.search(url.lower()) and name not in names):
            urls.append(url)
            names.add(name)
    return urls


def credit(html: str, url: str, page: str) -> str:
    name = urllib.parse.unquote(urllib.parse.urlparse(url).path.rsplit("/", 1)[-1])
    agency = AGENCIES.search(name)
    if agency:
        return agency.group(0)
    for mention in re.finditer(re.escape(name), html):
        near = html[mention.end():mention.end() + NEAR]
        # The next image's credit is not this one's.
        near = near[:near.find("<img")] if "<img" in near else near
        found = [match for match in (AGENCIES.search(near), FIELD.search(near)) if match]
        if found:
            first = min(found, key=lambda match: match.start())
            return (first.group(1) if first.re is FIELD else first.group(0)).strip()
    return ""


def pictures(page: str, folder: Path, first: int, credited: bool = False) -> list[Picture]:
    """Downloads the large images of a page into folder, numbered from first.

    Args:
        page: The page's address.
        folder: Where the images go.
        first: The number of the first image.
        credited: Keep only images whose credit the page names, for a news page whose other
            images are previews of other stories.

    Raises:
        MediaError: The page could not be fetched.
    """
    html = get(page).decode("utf-8", "replace")
    found = []
    for url in addresses(page, html):
        if len(found) >= MOST:
            break
        if credited and not credit(html, url, page):
            continue
        try:
            data = get(url)
            # A palette image with transparency makes Pillow warn on every open, the size is
            # all that is read here.
            with warnings.catch_warnings(), Image.open(BytesIO(data)) as image:
                warnings.simplefilter("ignore")
                width, height = image.size
                extension = (image.format or "jpg").lower().replace("jpeg", "jpg")
        except (MediaError, OSError):
            continue
        if max(width, height) < SMALLEST:
            continue
        path = folder / f"P{first + len(found)}.{extension}"
        folder.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        found.append(Picture(page, url, path, width, height, credit(html, url, page)))
    return found
