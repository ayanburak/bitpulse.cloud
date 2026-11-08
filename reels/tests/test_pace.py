"""
file: tests/test_pace.py
importable: nothing, pytest loads this file

description: Checks the black screen share of an edit and its warnings.
"""

from pathlib import Path

from PIL import Image

from reels.blocks import read_block
from reels.pace import gaps, measure


def test_a_black_opening_and_too_many_black_cards_are_warned(tmp_path):
    photo = tmp_path / "p.jpg"
    Image.new("RGB", (1200, 2000)).save(photo)
    sources = {"p": photo}
    black = read_block({"card": {"seconds": 3, "lines": ["A"]}}, "blocks 1", sources)
    shown = read_block({"card": {"seconds": 3, "lines": [{"text": "B", "show": {"source": "p"}}]}}, "blocks 2", sources)
    closing = read_block({"closing": {}}, "blocks 3", sources)
    pace = measure((black, shown, closing))
    assert (pace.length, pace.black, pace.first_black) == (6, 3, 0)
    assert [warning.split(",")[0] for warning in pace.warnings()] == ["black card at 0.0 s", "black cards take 3.0 s"]
    assert measure((shown, black, shown, shown, closing)).warnings() == []


def test_a_reel_without_music_is_warned_about_its_silences():
    assert gaps([(0.0, 2.0), (2.3, 5.0), (6.0, 8.0)], 9.0) == ((5.0, 6.0), (8.0, 9.0))
    assert gaps([], 3.0) == ((0.0, 3.0),)
