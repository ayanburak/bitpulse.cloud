"""
file: tests/test_mix.py
importable: nothing, pytest loads this file

description: Checks where the music drops under speech.
"""

from pathlib import Path

from reels.events import Voice
from reels.mix import level, spoken
from reels.style import MUSIC_HIGH


def voice(at: float, length: float) -> Voice:
    return Voice(Path("v.mp4"), 10, 10 + length, at, 0.04, 0.06, 1)


# The three Kennedy quotes follow each other with no gap and count as one stretch, the Palm
# Beach quote comes after the document and is its own.
def test_close_voices_are_one_stretch():
    spans = spoken([voice(0, 4.87), voice(4.867, 2.3), voice(7.167, 4.7), voice(26.9, 3.11)])
    assert [(round(a, 2), round(b, 2)) for a, b in spans] == [(0, 11.87), (26.9, 30.01)]


def test_music_stays_high_without_speech():
    assert level([]) == str(MUSIC_HIGH)
    assert level([voice(0, 2), voice(10, 2)]).count("max(") == 1
