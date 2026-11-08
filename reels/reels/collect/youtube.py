"""
file: reels/collect/youtube.py
importable: Video, listing, open_video, frames_of, fetch_section

Talks to YouTube through yt-dlp. A channel or a search gives a list of video ids, each video is
then opened once: for its date, its English captions, which are what quotes are searched in,
and its storyboard, the small frames YouTube shows over the timeline, one every few seconds.
Nothing is downloaded whole, a chosen part is fetched by its seconds only.

description: Lists, opens and cuts YouTube videos for the material of a reel.
"""

# NOTE: Listings carry no dates, only ids, titles and lengths. A channel lists its newest video
# first, so the videos are opened in that order and the walk stops at the first one older than
# the story's window.
#
# NOTE: Reading frames from the stream took a request per frame, sixteen frames of fifteen videos
# ran over ten minutes. The storyboard comes with the same call that brings the captions.
#
# XXX: YouTube answers too many caption requests with 429 Too Many Requests. Every request waits
# a moment, and a call that brought nothing back is tried once more after a longer pause. A video
# whose captions stay refused is still listed, without captions, and can be transcribed after a
# fetch. Without --ignore-errors a refused second caption language stopped yt-dlp before it wrote
# the info file and the storyboard, so 27 of 34 videos of the Messi story had no date and no
# sheet although their first captions had come.

import email
import io
import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

from reels.collect.web import AGENT
from reels.media import MediaError

PAUSE = 1.0
RETRY_PAUSE = 20.0


@dataclass
class Video:
    id: str
    title: str
    channel: str
    seconds: float
    day: str = ""
    words: list[tuple[float, str]] | None = None
    frames: list[tuple[float, Image.Image]] = field(default_factory=list)

    @property
    def url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.id}"


def ytdlp(args: list[str]) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["yt-dlp", "--no-warnings", *args], capture_output=True, text=True, timeout=300)
    except FileNotFoundError:
        raise MediaError("yt-dlp is not installed") from None


def listing(address: str, count: int) -> list[Video]:
    """Lists the first count videos of a channel page or a search.

    Args:
        address: A channel such as @WhiteHouse, or search words.
        count: How many videos to list.
    """
    target = f"https://www.youtube.com/{address}/videos" if address.startswith("@") else f"ytsearch{count}:{address}"
    result = ytdlp(["--flat-playlist", "--playlist-end", str(count), "--print", "%(id)s\t%(duration)s\t%(channel)s\t%(title)s", target])
    videos = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) == 4 and parts[1] not in ("NA", "None"):
            videos.append(Video(parts[0], parts[3], parts[2] if parts[2] != "NA" else address, float(parts[1])))
    return videos


# Automatic captions in the spoken language, en-orig, hold one word per segment with its own
# time. Uploaded captions, en, hold whole lines. The word version is preferred.
def open_video(video: Video, folder: Path) -> None:
    """Fills in the video's date, channel, caption words and storyboard frames.

    The files yt-dlp writes into folder are read and removed, only the captions stay.
    """
    folder.mkdir(parents=True, exist_ok=True)
    args = ["--ignore-errors", "-f", "sb0", "--write-info-json", "--write-auto-subs", "--write-subs", "--sub-langs",
            "en-orig,en", "--sub-format", "json3", "-o", str(folder / "%(id)s.%(ext)s"), "--force-overwrites", video.url]
    info_path = folder / f"{video.id}.info.json"
    for attempt in range(2):
        time.sleep(PAUSE if attempt == 0 else RETRY_PAUSE)
        result = ytdlp(args)
        if info_path.exists() or "429" not in result.stderr:
            break
    if info_path.exists():
        info = json.loads(info_path.read_text())
        video.day = info.get("upload_date") or ""
        video.channel = info.get("channel") or video.channel
        board = folder / f"{video.id}.mhtml"
        if board.exists():
            video.frames = storyboard(board, next((f for f in info.get("formats", []) if f.get("format_id") == "sb0"), {}))
            board.unlink()
        info_path.unlink()
    for language in ("en-orig", "en"):
        path = folder / f"{video.id}.{language}.json3"
        if path.exists():
            video.words = read_json3(path)
            return


# A storyboard is a row of grid images, each holding rows by columns frames that share the
# grid's duration evenly. The last grid may be cut short and hold fewer.
def storyboard(path: Path, layout: dict) -> list[tuple[float, Image.Image]]:
    message = email.message_from_bytes(path.read_bytes())
    grids = [Image.open(io.BytesIO(part.get_payload(decode=True))) for part in message.walk()
             if part.get_content_type().startswith("image/")]
    width, height = layout.get("width", 320), layout.get("height", 180)
    rows, columns = layout.get("rows", 1), layout.get("columns", 1)
    frames, start = [], 0.0
    for grid, fragment in zip(grids, layout.get("fragments", [])):
        length = fragment.get("duration") or 0
        step = length / (rows * columns)
        for index in range(rows * columns):
            x, y = index % columns * width, index // columns * height
            if y + height > grid.height or x + width > grid.width:
                break
            frames.append((start + index * step, grid.crop((x, y, x + width, y + height)).convert("RGB")))
        start += length
    return frames


def read_json3(path: Path) -> list[tuple[float, str]]:
    words = []
    for event in json.loads(path.read_text()).get("events", []):
        for segment in event.get("segs", []):
            text = segment.get("utf8", "").strip()
            if text:
                words.append(((event["tStartMs"] + segment.get("tOffsetMs", 0)) / 1000, text))
    return words


# Used for files on Commons, which allow a read at any second. YouTube videos use the storyboard.
# Wikimedia answers a request without a client name with 429, so ffmpeg sends ours.
def frames_of(url: str, seconds: list[float], folder: Path) -> list[Path]:
    """Grabs one small frame at each second from a direct video address without downloading it."""
    source = url
    folder.mkdir(parents=True, exist_ok=True)
    out = []
    for index, second in enumerate(seconds):
        path = folder / f"{index:03d}.jpg"
        result = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{second:.2f}", "-user_agent", AGENT, "-i", source, "-frames:v", "1",
                                 "-vf", "scale=240:-2", str(path)], capture_output=True, timeout=120)
        if result.returncode == 0 and path.exists():
            out.append(path)
    return out


def fetch_section(url: str, start: float, end: float, out: Path) -> Path:
    """Downloads the part of a YouTube video from start to end, at up to 1080 lines, as mp4.

    Raises:
        MediaError: yt-dlp failed.
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    result = ytdlp(["-f", "bv*[height<=1080][vcodec^=avc1]+ba/b[height<=1080]/b", "--download-sections", f"*{start}-{end}",
                    "--force-keyframes-at-cuts", "--merge-output-format", "mp4", "-o", str(out), "--force-overwrites", url])
    if result.returncode != 0 or not out.exists():
        raise MediaError(f"yt-dlp could not fetch {url}: {result.stderr.strip()[:300]}")
    return out
