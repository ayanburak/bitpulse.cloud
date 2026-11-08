"""
file: reels/collect/screen.py
importable: prepare, join

Readies the gathered candidates for Haiku and joins what Haiku writes back. prepare splits the
candidates into a few task files. Each file holds the same short instructions, and for every
candidate its facts, the parts of its captions most likely to matter and the sheet to look at.
The model that writes the edit starts one Haiku per task file, each Haiku writes its notes, and
join puts all notes into candidates.md, the one file the model reads next.

description: Prepares Haiku's screening of the candidates and joins its notes.
"""

# NOTE: Haiku never reads a long video whole. The captions are cut into windows of about 45
# seconds and every window is scored by how many of the story's own words it holds, names,
# words of the quotes, the title and the summary. A long speech gives Haiku its best few windows
# and the windows around a found quote, a short clip is given whole.
#
# NOTE: A live stream often plays the same speech several times. A window that reads almost like
# one already picked is skipped, the first reel's Kennedy stream held its speech four times.
#
# NOTE: The instructions are the same for every task and are written here, not by the model,
# so the model only has to start the tasks.

import json
import re
from collections import Counter
from pathlib import Path

from reels.collect.quotes import find_quote
from reels.collect.story import names, quotes, read_story
from reels.collect.youtube import read_json3
from reels.fields import CutError
from reels.transcript import key

WINDOW = 45.0
STEP = 15.0
SHORT = 300.0
REPEAT = 0.7

# A window that scores under this share of the best one is filler, not a lesser match.
RELEVANT = 0.4
BEST_WINDOWS = 6
PER_TASK = 4

STOP = set("""a an the and or but if of to in on at by for with from as is are was were be been being it its this that
these those he she they we you i his her their our your them him us not no so do does did has have had will would can could
should may might than then there here what which who whom whose when where why how all any each more most some such only
own same too very just also about into over after before again further once said says say""".split())

INSTRUCTIONS = """You are screening video and image candidates for a short news reel on Instagram. Read the
story summary below, then every candidate in this file, and look at each sheet image it names with
the Read tool. Do not open any other file, do not search the web, do not run commands.

For every candidate write a block in this exact form, nothing before or after the blocks:

## <id>
use: yes | maybe | no
why: one sentence, what in it serves the story
speech: one line per useful passage, "<start>-<end> s: <the words, as said>", or "none"
picture: one sentence on what the frames show
marks: logos, tickers or text burned onto the picture, or "none"
quality: sharp | fine | poor

A passage is useful when a person in the story says something about the story's subject, also
when it is not one of the story's quotes. Give its seconds from the caption times, a little
before the first word and a little after the last. Footage without speech is useful when it
shows a person, place, object or event that the story or a useful passage names, even when it
is years older than the story: it can play under the words that name it. A video is "no" when
it is off the subject or only a news anchor talking. Keep every line short.
Write the blocks into the notes file named at the top, with the Write tool."""


# --- Scoring ---


def story_words(story) -> Counter:
    words: Counter[str] = Counter()
    text = " ".join([story.title, story.summary] + [quote.words for quote in quotes(story)])
    for token in re.findall(r"[A-Za-z0-9'-]+", text):
        if key(token) and key(token) not in STOP:
            words[key(token)] += 1
    for name, count in names(story):
        for part in name.split():
            if key(part) not in STOP:
                words[key(part)] += count
    return words


def windows(words: list[tuple[float, str]], wanted: Counter) -> list[tuple[float, float, float]]:
    if not words:
        return []
    end = words[-1][0]
    found = []
    start = 0.0
    while start <= end:
        inside = [key(text) for second, text in words if start <= second < start + WINDOW]
        score = sum(1 + min(wanted[k], 3) for k in set(inside) if k in wanted)
        found.append((score, start, start + WINDOW))
        start += STEP
    return found


def best(found: list[tuple[float, float, float]], around: list[float], count: int,
         words: list[tuple[float, str]]) -> list[tuple[float, float]]:
    picked: list[tuple[float, float]] = [(max(0.0, second - 10), second + WINDOW - 10) for second in around]
    texts = [plain(words, a, b) for a, b in picked]
    top = max((score for score, _, _ in found), default=0)
    for score, start, end in sorted(found, reverse=True):
        if len(picked) >= count + len(around) or score == 0 or score < top * RELEVANT:
            break
        text = plain(words, start, end)
        if all(end <= a or start >= b for a, b in picked) and all(shared(text, seen) < REPEAT for seen in texts):
            picked.append((start, end))
            texts.append(text)
    return sorted(picked)


def plain(words: list[tuple[float, str]], start: float, end: float) -> set[str]:
    return {key(text) for second, text in words if start <= second < end}


# The share of the smaller window's words that the other holds as well. Word order is left out,
# a repeat falls into the windows at a different offset each time.
def shared(a: set[str], b: set[str]) -> float:
    return len(a & b) / max(1, min(len(a), len(b)))


def excerpt(words: list[tuple[float, str]], start: float, end: float) -> str:
    inside = [(second, text) for second, text in words if start <= second < end]
    lines = []
    for i in range(0, len(inside), 14):
        part = inside[i:i + 14]
        lines.append(f"[{part[0][0]:.1f}] " + " ".join(text for _, text in part))
    return "\n".join(lines)


# --- Tasks ---


def prepare(story_key: str, work: Path) -> list[Path]:
    """Writes the task files for Haiku and returns them.

    Raises:
        CutError: gather has not run yet.
    """
    index_path = work / "gathered" / "gathered.json"
    if not index_path.exists():
        raise CutError("no gathered.json, run reels gather first")
    story = read_story(story_key)
    wanted = story_words(story)
    entries = json.loads(index_path.read_text())
    folder = work / "screen"
    for old in folder.glob("*.md"):
        old.unlink()
    folder.mkdir(parents=True, exist_ok=True)

    blocks = []
    for name, entry in entries.items():
        lines = [f"### {name}: {entry.get('title', '')}", f"kind: {entry['kind']}"]
        sheet = work / "gathered" / "sheets" / f"{name}.jpg"
        if entry["kind"] == "picture" and not sheet.exists():
            sheet = work / "gathered" / "pages" / Path(entry["path"]).name
        if sheet.exists():
            lines.append(f"sheet: {sheet}")
        if entry["kind"] == "youtube":
            words = captions_of(work, entry["url"])
            if words:
                length = words[-1][0]
                if length <= SHORT:
                    parts = [(0.0, length + 1)]
                else:
                    around = [m.second for q in quotes(story) if (m := find_quote(q.words, words))]
                    parts = best(windows(words, wanted), around, BEST_WINDOWS, words)
                    lines.append(f"captions: {len(parts)} parts of a {length / 60:.0f} minute video, chosen for the story's words")
                lines += [excerpt(words, a, b) for a, b in parts]
            else:
                lines.append("captions: none")
        blocks.append("\n".join(lines))

    tasks = []
    for number, start in enumerate(range(0, len(blocks), PER_TASK), 1):
        notes = folder / f"notes-{number}.md"
        path = folder / f"task-{number}.md"
        path.write_text(f"Notes file: {notes}\n\n{INSTRUCTIONS}\n\n# Story\n\n{story.title}\n{story.summary}\n\n"
                        f"# Candidates\n\n" + "\n\n".join(blocks[start:start + PER_TASK]) + "\n")
        tasks.append(path)
    return tasks


def captions_of(work: Path, url: str) -> list[tuple[float, str]]:
    video = url.rsplit("=", 1)[-1]
    for language in ("en-orig", "en"):
        path = work / "gathered" / "captions" / f"{video}.{language}.json3"
        if path.exists():
            return read_json3(path)
    return []


# --- Joining ---


def join(work: Path) -> Path:
    """Joins the quote matches of gathered.md and Haiku's notes into candidates.md.

    Raises:
        CutError: A task has no notes yet.
    """
    folder = work / "screen"
    tasks = sorted(folder.glob("task-*.md"))
    missing = [task.name for task in tasks if not (folder / task.name.replace("task", "notes")).exists()]
    if not tasks or missing:
        raise CutError(f"notes missing for {', '.join(missing) or 'every task'}, run the Haiku tasks first")
    gathered = (work / "gathered.md").read_text()
    quoted = gathered.split("## YouTube")[0].strip()
    notes = "\n\n".join((folder / task.name.replace("task", "notes")).read_text().strip() for task in tasks)
    facts = dict(re.findall(r"(?m)^([YCP]\d+)\. (.+\n    .+)$", gathered))
    keep, dropped = [], []
    for block in re.split(r"(?m)^(?=## )", notes):
        if not block.startswith("## "):
            continue
        name = block.split("\n", 1)[0][3:].strip()
        if "use: no" in block:
            dropped.append(name)
            continue
        head, _, rest = block.strip().partition("\n")
        keep.append(f"{head}\n{facts.get(name, '').strip()}\n{rest}\n")
    out = work / "candidates.md"
    out.write_text(f"{quoted}\n\n# Candidates\n\n" + "\n".join(keep) + f"\nLeft out by screening: {', '.join(dropped) or 'none'}\n")
    return out
