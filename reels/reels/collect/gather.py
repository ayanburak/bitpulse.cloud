"""
file: reels/collect/gather.py
importable: gather, fetch

Carries out the model's search plan, plan.yaml in the story's work folder, and lays every
candidate out in gathered.md with an id: Y for YouTube, C for Commons, P for page images. The
story's own sources are always searched for pictures, after the pages the plan names.

    window: 3
    channels: ["@WhiteHouse"]
    search: ["Trump Palm Beach Iran deal"]
    commons:
      video: ["B-2 Spirit"]
      image: ["Natanz"]
    pages: ["https://rewardsforjustice.net/rewards/iran-nuclear-program/"]

window is how many days before the story a channel video may be. Each candidate gets a sheet of
frames, and the story's quotes are searched in every caption. fetch then brings a chosen
candidate into the sources, a YouTube video only for the seconds asked for, and transcribes it.

description: Gathers candidate material by a plan and fetches the chosen pieces.
"""

# NOTE: gathered.json keeps every candidate's address under its id, so fetch only needs the id
# the model read in gathered.md.
#
# NOTE: YouTube videos are opened three at a time, each open brings captions and storyboard
# together. Commons video sheets read single seconds of the file, four at a time, a Commons
# picture's sheet is its small copy. The log counts the sheets that were really made, a candidate
# without one can only be judged by its title.

import io
import json
import shutil
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from typing import Any

import yaml
from PIL import Image

from reels.collect import commons, pages, web, youtube
from reels.collect.quotes import find_quote
from reels.collect.sheet import tile
from reels.collect.story import quotes, read_story
from reels.fields import CutError, number, record
from reels.media import MediaError, duration, run
from reels.transcript import save, transcribe

CHANNEL_DEPTH = 20
SEARCH_COUNT = 5
COMMONS_COUNT = 6
FRAMES = 16
WORKERS = 4
OPENERS = 3

# --- Plan ---


def read_plan(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise CutError(f"no plan {path}, the model writes it after reading dossier.md")
    try:
        data = record(yaml.safe_load(path.read_text()), "plan.yaml", {"window", "channels", "search", "commons", "pages"})
    except yaml.YAMLError as error:
        raise CutError(f"plan.yaml: {error}") from None
    data["window"] = int(number(data, "window", "plan.yaml", 0, 60, 3))
    for field in ("channels", "search", "pages"):
        if not isinstance(data.get(field, []), list):
            raise CutError(f"plan.yaml: {field} must be a list")
    data["commons"] = record(data.get("commons"), "plan.yaml, commons", {"video", "image"})
    return data


# --- Gathering ---


def times(length: float, around: float | None) -> list[float]:
    if around is None:
        return [length * (0.02 + 0.96 * i / (FRAMES - 1)) for i in range(FRAMES)]
    overview = [length * (0.05 + 0.9 * i / 7) for i in range(8)]
    close = [max(0.0, around - 4 + i * 2) for i in range(8)]
    return sorted(overview + close)


def clock(second: float) -> str:
    return f"{int(second // 60)}:{int(second % 60):02d}"


def gather(story_key: str, work: Path, log) -> Path:
    """Gathers every candidate of the plan and writes gathered.md and gathered.json.

    Args:
        story_key: The story folder name.
        work: The story's work folder.
        log: Called with one short line of progress at a time.

    Returns:
        The path of gathered.md.
    """
    story = read_story(story_key)
    plan = read_plan(work / "plan.yaml")
    earliest = (story.day - timedelta(days=plan["window"])).strftime("%Y%m%d")
    folder = work / "gathered"
    shutil.rmtree(folder, ignore_errors=True)
    entries: dict[str, dict] = {}

    videos: list[youtube.Video] = []
    seen: set[str] = set()
    with ThreadPoolExecutor(OPENERS) as pool:
        for channel in plan.get("channels", []):
            listed = [video for video in youtube.listing(channel, CHANNEL_DEPTH) if video.id not in seen]
            # Opened in batches, newest first, until a batch reaches back past the window.
            for start in range(0, len(listed), OPENERS):
                batch = listed[start:start + OPENERS]
                list(pool.map(lambda video: youtube.open_video(video, folder / "captions"), batch))
                for video in batch:
                    if not video.day or video.day >= earliest:
                        seen.add(video.id)
                        videos.append(video)
                if any(video.day and video.day < earliest for video in batch):
                    break
            log(f"{channel}: {len(videos)} videos so far")
        for words in plan.get("search", []):
            listed = [video for video in youtube.listing(words, SEARCH_COUNT) if video.id not in seen]
            list(pool.map(lambda video: youtube.open_video(video, folder / "captions"), listed))
            seen.update(video.id for video in listed)
            videos += listed
            log(f"search {words!r}: {len(videos)} videos so far")

    found_quotes = quotes(story)
    lines = [f"# Gathered for {story.key}", "", "## Quotes", ""]
    heard: dict[str, float] = {}
    for n, quote in enumerate(found_quotes, 1):
        hits = []
        for index, video in enumerate(videos, 1):
            match = find_quote(quote.words, video.words or [])
            if match:
                hits.append(f"Y{index} at {match.second:.1f} s, {match.score:.0%} alike: \"{match.heard}\"")
                heard.setdefault(video.id, match.second)
        lines.append(f"Q{n}. \"{quote.words}\"")
        lines += [f"    {hit}" for hit in hits] or ["    not found in any caption"]

    lines += ["", "## YouTube", ""]
    jobs = {}
    sheets = 0
    with ThreadPoolExecutor(WORKERS) as pool:
        for index, video in enumerate(videos, 1):
            name = f"Y{index}"
            entries[name] = {"kind": "youtube", "url": video.url, "title": video.title}
            jobs[name] = pool.submit(board_sheet, video, heard.get(video.id), folder / "sheets" / f"{name}.jpg")
            if video.words:
                (folder / "captions" / f"{name}.txt").write_text(caption_text(video.words))
        for index, video in enumerate(videos, 1):
            name = f"Y{index}"
            sheet = jobs[name].result()
            captioned = f"gathered/captions/{name}.txt" if video.words else "no captions"
            sheets += bool(sheet)
            lines.append(f"{name}. {video.title}\n    {video.channel}, {clock(video.seconds)}, {video.day or 'date unknown'}, "
                         f"{captioned}, {f'gathered/sheets/{name}.jpg' if sheet else 'no sheet'}")
        log(f"YouTube: {len(videos)} videos, {sheets} with a sheet")

        lines += ["", "## Commons", ""]
        media = []
        for kind in ("video", "image"):
            for words in plan["commons"].get(kind, []) or []:
                media += commons.search(words, kind, COMMONS_COUNT)
        commons_jobs = {}
        for index, item in enumerate(media, 1):
            name = f"C{index}"
            entries[name] = {"kind": item.kind, "url": item.url, "title": item.title}
            if item.kind == "video" and item.seconds:
                commons_jobs[name] = pool.submit(sheet_of, item.url, times(item.seconds, None), folder / "frames" / name,
                                                 folder / "sheets" / f"{name}.jpg")
            elif item.kind == "image" and item.thumb:
                commons_jobs[name] = pool.submit(picture_sheet, item.thumb, name, folder / "sheets" / f"{name}.jpg")
        sheets = 0
        for index, item in enumerate(media, 1):
            name = f"C{index}"
            length = f"{clock(item.seconds)}, " if item.seconds else ""
            sheet = commons_jobs[name].result() if name in commons_jobs else None
            sheets += bool(sheet)
            lines.append(f"{name}. {item.title}\n    {item.kind}, {length}{item.width}x{item.height}, {item.day or 'date unknown'}, "
                         f"{item.licence}, {f'gathered/sheets/{name}.jpg' if sheet else 'no sheet'}")
        log(f"Commons: {len(media)} files, {sheets} with a sheet")

    lines += ["", "## Pages", ""]
    pictures = []
    # A news source's own photographs carry an agency credit, its uncredited images are mostly
    # previews of other stories and are left out.
    named = plan.get("pages", [])
    for page in dict.fromkeys([*named, *story.sources]):
        try:
            pictures += pages.pictures(page, folder / "pages", len(pictures) + 1, credited=page not in named)
        except MediaError as error:
            lines.append(f"{page}: {error}")
    for picture in pictures:
        name = picture.path.stem
        entries[name] = {"kind": "picture", "url": picture.url, "path": str(picture.path), "title": picture.page,
                         "credit": picture.credit}
        tile([picture.path], [name], folder / "sheets" / f"{name}.jpg")
        lines.append(f"{name}. {picture.width}x{picture.height} from {picture.page}, "
                     f"{f'credit {picture.credit}' if picture.credit else 'credit not found'}\n"
                     f"    gathered/pages/{picture.path.name}, gathered/sheets/{name}.jpg")
    if pictures:
        tile([p.path for p in pictures], [p.path.stem for p in pictures], folder / "sheets" / "pages.jpg")
        lines.append("    all of them on gathered/sheets/pages.jpg")
    log(f"pages: {len(pictures)} images")

    (folder / "gathered.json").write_text(json.dumps(entries, indent=1))
    shutil.rmtree(folder / "frames", ignore_errors=True)
    out = work / "gathered.md"
    out.write_text("\n".join(lines) + "\n")
    return out


# The storyboard holds a frame every few seconds. The sheet takes the frames nearest to the
# wanted seconds, so a quote's moment is shown close up and the rest of the video around it.
def board_sheet(video: youtube.Video, around: float | None, out: Path) -> Path | None:
    if not video.frames:
        return None
    picked = []
    for second in times(video.seconds, around):
        nearest = min(video.frames, key=lambda frame: abs(frame[0] - second))
        if nearest not in picked:
            picked.append(nearest)
    return tile([image for _, image in picked], [clock(second) for second, _ in picked], out)


# A picture gets a sheet of its own small copy, so the screening sees it like any other candidate.
def picture_sheet(url: str, name: str, out: Path) -> Path | None:
    try:
        image = Image.open(io.BytesIO(web.get(url)))
    except (MediaError, OSError):
        return None
    return tile([image], [name], out)


def sheet_of(url: str, seconds: list[float], frames: Path, out: Path) -> Path | None:
    try:
        grabbed = youtube.frames_of(url, seconds, frames)
    except MediaError:
        return None
    return tile(grabbed, [clock(s) for s in seconds[:len(grabbed)]], out)


# Captions as lines of about twelve words, each with its second, for a model to read.
def caption_text(words: list[tuple[float, str]]) -> str:
    lines = []
    for i in range(0, len(words), 12):
        part = words[i:i + 12]
        lines.append(f"[{part[0][0]:7.1f}] {' '.join(text for _, text in part)}")
    return "\n".join(lines) + "\n"


# --- Fetching ---


def fetch(work: Path, name: str, start: float | None, end: float | None, as_name: str) -> tuple[Path, str]:
    """Brings a gathered candidate into the story's sources and transcribes it when it speaks.

    Args:
        work: The story's work folder.
        name: The candidate's id in gathered.md, for example Y3.
        start: First second to keep of a YouTube video.
        end: Last second to keep of a YouTube video.
        as_name: The file name the source gets, without extension.

    Returns:
        The source file and a short note on its transcript.

    Raises:
        CutError: The id is unknown, or a YouTube video is fetched without its seconds.
        MediaError: The download failed.
    """
    index = json.loads((work / "gathered" / "gathered.json").read_text()) if (work / "gathered" / "gathered.json").exists() else {}
    if name not in index:
        raise CutError(f"no candidate {name} in gathered.md")
    entry = index[name]
    src = work / "src"
    if entry["kind"] == "youtube":
        if start is None or end is None or end <= start:
            raise CutError("a YouTube video is fetched with --from and --to, only the part that is needed")
        out = youtube.fetch_section(entry["url"], start, end, src / f"{as_name}.mp4")
    elif entry["kind"] == "picture":
        out = src / f"{as_name}{Path(entry['path']).suffix}"
        src.mkdir(parents=True, exist_ok=True)
        shutil.copy(entry["path"], out)
        return out, "an image, no transcript"
    else:
        from reels.collect.web import download  # only fetch needs whole files
        # Commons puts tracking words after the file name, the type is read from the path alone.
        out = download(entry["url"], src / f"{as_name}{Path(urllib.parse.urlparse(entry['url']).path).suffix.lower()}")
        if entry["kind"] == "image":
            return out, "an image, no transcript"
    if not has_sound(out):
        return out, f"{duration(out):.1f} s, no sound"
    transcript = transcribe(out)
    if not transcript.words:
        return out, f"{duration(out):.1f} s, no speech"
    readable = save(transcript, work / "transcripts" / f"{out.stem}.json")
    note = f"{duration(out):.1f} s, {len(transcript.words)} words in {readable.relative_to(work)}"
    if start:
        note += f", its second 0 is second {start:.0f} of the video"
    return out, note


def has_sound(path: Path) -> bool:
    return bool(run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", str(path)]).strip())
