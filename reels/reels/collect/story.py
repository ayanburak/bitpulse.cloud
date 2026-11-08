"""
file: reels/collect/story.py
importable: Story, read_story, dossier

Reads a published story from the site and pulls out what a reel can be built on: the quotes
with the sentence around each, the names that come up most, the date and the sources. The
dossier is the first thing the model reads, so it is kept short.

description: Turns a site story into the short dossier a reel starts from.
"""

# NOTE: Quotes are found by their quotation marks in the whole text, not sentence by sentence,
# because a quote may hold several sentences of its own. A quote of fewer than three words is a
# term, not something said, and is left out.
#
# NOTE: Names are runs of capitalized words that are not the first word of a sentence. It is a
# rough count, good enough to tell the model who and what the story is about.

import re
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

from reels.config import SITE
from reels.fields import CutError

STORIES = SITE / "src" / "content" / "stories"
QUOTE = re.compile(r"[\"“]([^\"”]{8,300})[\"”]")
NAME = re.compile(r"(?<![.!?]\s)(?<!^)\b([A-Z][\w-]+(?:\s+(?:of\s+|the\s+|for\s+|and\s+)?[A-Z][\w-]+)*)")
COMMON = {"The", "It", "He", "She", "They", "We", "In", "On", "Also", "Earlier", "President", "Friday", "Saturday",
          "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "January", "February", "March", "April", "May",
          "June", "July", "August", "September", "October", "November", "December", "What", "This", "That"}
TOP_NAMES = 15


@dataclass(frozen=True)
class Quote:
    words: str
    sentence: str


@dataclass(frozen=True)
class Story:
    key: str
    title: str
    summary: str
    day: date
    body: str
    sources: list[str]


def read_story(key: str) -> Story:
    """Reads the English version of a story from the site.

    Args:
        key: The story folder name, for example 2026-11-07-iran-nuclear-reward.

    Raises:
        CutError: The story does not exist.
    """
    path = STORIES / key / "en.md"
    if not path.exists():
        raise CutError(f"no story {key} in {STORIES}")
    _, front, body = path.read_text().split("---", 2)
    meta = yaml.safe_load(front)
    return Story(key, meta["title"], meta["summary"], meta["date"], body.strip(),
                 [source["url"] for source in meta.get("sources", [])])


def sentences(body: str) -> list[str]:
    plain = re.sub(r"^#+ .*$", "", body, flags=re.M)
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+|(?<=[.!?][\"”])\s+", plain) if part.strip()]


# The context of a quote is the text around it up to the sentence ends on both sides, where the
# speaker and the occasion are usually named.
def quotes(story: Story) -> list[Quote]:
    plain = re.sub(r"^#+ .*$", "", story.body, flags=re.M)
    found = []
    for match in QUOTE.finditer(plain):
        words = match.group(1).strip()
        if len(words.split()) < 3:
            continue
        start = max(plain.rfind(". ", 0, match.start()), plain.rfind("\n", 0, match.start())) + 1
        ends = [i for i in (plain.find(". ", match.end()), plain.find("\n", match.end())) if i != -1]
        end = min(ends) + 1 if ends else len(plain)
        found.append(Quote(words, plain[start:end].strip()))
    return found


def names(story: Story) -> list[tuple[str, int]]:
    counts: Counter[str] = Counter()
    for sentence in sentences(story.body):
        for match in NAME.finditer(sentence.replace("'s ", " ").replace("’s ", " ")):
            name = match.group(1)
            if name.split()[0] not in COMMON or len(name.split()) > 1:
                counts[name] += 1
    return counts.most_common(TOP_NAMES)


def dossier(story: Story) -> str:
    """Returns the dossier of a story as Markdown."""
    lines = [f"# {story.title}", "", f"Story: {story.key}, published {story.day}", "", story.summary, "", "## Quotes", ""]
    found = quotes(story)
    lines += [f"Q{n}. \"{quote.words}\"\n    in: {quote.sentence}" for n, quote in enumerate(found, 1)] or ["none"]
    lines += ["", "## Names", "", ", ".join(f"{name} {count}" for name, count in names(story)), "", "## Sources", ""]
    lines += [f"- {url}" for url in story.sources]
    lines += ["", "## Story", "", story.body]
    return "\n".join(lines) + "\n"
