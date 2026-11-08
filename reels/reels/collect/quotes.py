"""
file: reels/collect/quotes.py
importable: Match, find_quote

Finds a quote of the story in the captions of a video. Captions are machine made and the story
may shorten a quote, so a quote is matched by likeness, not word for word.

description: Looks for the story's quotes in video captions.
"""

# NOTE: A full likeness test on every stretch of an hour of captions is slow. Only stretches
# that share at least half of the quote's words are scored.

import difflib
from dataclasses import dataclass

from reels.transcript import key

LIKENESS = 0.7


@dataclass(frozen=True)
class Match:
    second: float
    score: float
    heard: str


def find_quote(quote: str, words: list[tuple[float, str]]) -> Match | None:
    """Returns where in words the quote is said, or None when nothing is alike enough."""
    wanted = [k for k in (key(part) for part in quote.split()) if k]
    keys = [key(text) for _, text in words]
    if not wanted or not keys:
        return None
    target, needed = " ".join(wanted), set(wanted)
    best: tuple[float, int, int] | None = None
    for width in range(max(1, len(wanted) - 2), len(wanted) + 3):
        for i in range(0, len(keys) - width + 1):
            window = keys[i:i + width]
            if len(needed & set(window)) * 2 < len(needed):
                continue
            score = difflib.SequenceMatcher(None, " ".join(window), target).ratio()
            if best is None or score > best[0]:
                best = (score, i, width)
    if best is None or best[0] < LIKENESS:
        return None
    score, i, width = best
    return Match(words[i][0], score, " ".join(text for _, text in words[i:i + width]))
