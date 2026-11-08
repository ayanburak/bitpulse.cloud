"""
file: tests/test_screen.py
importable: nothing, pytest loads this file

description: Checks how caption windows are picked for Haiku and how its notes are joined.
"""

from collections import Counter

import pytest

from reels.collect.screen import best, join, windows
from reels.fields import CutError

WANTED = Counter({"iran": 5, "nuclear": 3, "israel": 2, "deal": 2})


def spoken(text: str, start: float, step: float = 1.0) -> list[tuple[float, str]]:
    return [(start + i * step, word) for i, word in enumerate(text.split())]


ON_TOPIC = "iran will never have a nuclear weapon there would be no israel they want a deal"
FILLER = "the jobs report smashed all expectations and manufacturing is back again this year"


def test_windows_score_by_the_story_words():
    words = spoken(FILLER, 0) + spoken(ON_TOPIC, 100)
    scored = windows(words, WANTED)
    top = max(scored)
    assert 55 <= top[1] <= 100


# The same speech played twice is given once, and a window with none of the story's words is
# never given just to fill the count.
def test_best_skips_repeats_and_filler():
    words = spoken(ON_TOPIC, 0) + spoken(FILLER, 200) + spoken(ON_TOPIC, 400)
    picked = best(windows(words, WANTED), [], 6, words)
    assert len(picked) == 1


def test_best_keeps_the_window_around_a_found_quote():
    words = spoken(FILLER, 0) + spoken(ON_TOPIC, 300)
    picked = best(windows(words, WANTED), [50.0], 6, words)
    assert picked[0] == (40.0, 85.0)


def test_join_keeps_used_candidates_with_their_facts(tmp_path):
    screen = tmp_path / "screen"
    screen.mkdir()
    (screen / "task-1.md").write_text("task")
    (screen / "notes-1.md").write_text("## Y1\nuse: yes\nwhy: the quote\n\n## Y2\nuse: no\nwhy: off topic\n")
    (tmp_path / "gathered.md").write_text("# Gathered\n\n## Quotes\n\nQ1. \"x\"\n\n## YouTube\n\nY1. A title\n    The White House, 10:49\nY2. Other\n    Someone, 1:00\n")
    out = join(tmp_path).read_text()
    assert "## Y1\nY1" not in out and "A title\n    The White House, 10:49\nuse: yes" in out
    assert "## Y2" not in out and "Left out by screening: Y2" in out


def test_join_waits_for_every_note(tmp_path):
    (tmp_path / "screen").mkdir()
    (tmp_path / "screen" / "task-1.md").write_text("task")
    with pytest.raises(CutError, match="notes missing for task-1.md"):
        join(tmp_path)
