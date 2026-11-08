"""
file: tests/test_blocks.py
importable: nothing, pytest loads this file

The numbers here come from the first approved reel, the Iran reward story of 7 November 2026.
The engine has to place everything where the hand made version placed it.

description: Checks how blocks work out their length, shots, texts, voices and sounds.
"""

import math
from pathlib import Path

import pytest
from PIL import Image

from reels.blocks import read_block
from reels.fields import CutError

SOURCES = {"kennedy": Path("kennedy.mp4"), "b2": Path("b2.webm")}

OPENING = {"speech": {
    "voice": {"source": "kennedy", "from": 47.18, "to": 52.05},
    "shots": [{"source": "b2", "from": 0.3, "frames": 74, "crop": "405:720:438:0", "push": 0.024},
              {"source": "b2", "from": 8.15, "crop": "405:720:690:0"}],
    "lines": [[47.28, 49.61, "If we didn't go in with those beautiful"]],
}}


def test_speech_lasts_as_long_as_its_voice_and_the_last_shot_fills_the_rest():
    block = read_block(OPENING, "blocks 1", SOURCES)
    assert block.frames() == 146
    assert [shot.frames for shot in block.shots] == [74, 72]
    assert [shot.visual.look for shot in block.shots] == ["archive", "archive"]


def test_speech_places_its_lines_and_voice_from_its_start():
    block = read_block(OPENING, "blocks 1", SOURCES)
    line = block.texts(146)[0]
    assert (round(line.start, 3), round(line.end, 3)) == (round(146 / 30 + 0.1, 3), round(146 / 30 + 2.43, 3))
    assert block.voices(146)[0].at == pytest.approx(146 / 30)


# The Palm Beach quote starts half a second under the document before it, so its lips are cut
# from half a second into the voice.
def test_a_prelap_moves_the_voice_back_and_the_sync_shot_forward():
    block = read_block({"speech": {
        "voice": {"source": "kennedy", "from": 54.67, "to": 57.78, "prelap": 0.5},
        "shots": [{"sync": True, "crop": "608:1080:690:0"}],
        "lines": [[54.70, 55.82, "We're dealing with them now."]],
    }}, "blocks 6", SOURCES)
    assert block.frames() == 78
    assert block.shots[0].visual.start == pytest.approx(55.17)
    assert block.shots[0].visual.look == "speech"
    assert block.voices(822)[0].at == pytest.approx(26.9)
    assert block.texts(822)[0].start == pytest.approx(26.93)


# The Messi goal runs straight into a montage with lines, so its speech asks for the shade too.
def test_speech_is_plain_unless_it_asks_for_the_shade():
    assert read_block(OPENING, "blocks 1", SOURCES).shade is False
    assert read_block({"speech": {**OPENING["speech"], "shade": True}}, "blocks 1", SOURCES).shade is True
    with pytest.raises(CutError, match="shade is true or false"):
        read_block({"speech": {**OPENING["speech"], "shade": "yes"}}, "blocks 1", SOURCES)


@pytest.mark.parametrize("shots, message", [
    ([{"source": "b2", "from": 0, "crop": "405:720:0:0"}, {"source": "b2", "from": 0, "crop": "405:720:0:0"}], "missing frames"),
    ([{"source": "b2", "from": 0, "frames": 500, "crop": "405:720:0:0"}], "between 1 and 146"),
    ([{"sync": True, "source": "b2", "crop": "405:720:0:0"}], "takes its source"),
    ([{"source": "nowhere", "from": 0, "crop": "405:720:0:0"}], "unknown source nowhere"),
])
def test_speech_refuses_shots_that_do_not_fit(shots, message):
    data = {"speech": {**OPENING["speech"], "shots": shots}}
    with pytest.raises(CutError, match=message):
        read_block(data, "blocks 1", SOURCES)


def test_card_stacks_its_lines_around_the_middle():
    two = read_block({"card": {"seconds": 1.73, "lines": ["The same day,", "the US put this out."], "reveal": [0.18, 0.78]}}, "b", {})
    assert two.frames() == 52
    assert [text.y for text in two.texts(356)] == [905, 1011]
    three = read_block({"card": {"seconds": 4.4, "lines": ["one", "two", "three"]}}, "b", {})
    assert [text.y for text in three.texts(0)] == [852, 958, 1064]
    assert [round(text.start, 2) for text in three.texts(0)] == [0.2, 0.7, 1.2]


def test_card_refuses_a_line_wider_than_the_screen():
    with pytest.raises(CutError, match="wider than the screen"):
        read_block({"card": {"seconds": 2, "lines": ["Washington has not said what would earn the full amount"]}}, "b", {})


def test_unknown_block_names_the_known_ones():
    with pytest.raises(CutError, match="the blocks are speech, card, montage, document, closing"):
        read_block({"map": {}}, "blocks 2", {})


# --- Document ---

STEPS = [
    {"via": [0.95, 1024, 150], "focus": [390, 8, 1128, 128], "zoom": 1.10, "pause": 0.2, "hold": 1.3, "say": "One."},
    {"via": [1.0, 520, 450], "focus": [52, 334, 668, 392], "zoom": 1.55, "hold": 1.1, "say": "Two."},
    {"via": [1.0, 470, 860], "focus": [8, 920, 240, 982], "zoom": 1.95, "hold": 2.4},
]


@pytest.fixture
def poster(tmp_path):
    path = tmp_path / "poster.png"
    Image.new("RGB", (2048, 1200)).save(path)
    return {"poster": path}


def test_document_keeps_the_timing_of_the_first_reel(poster):
    block = read_block({"document": {"source": "poster", "steps": STEPS}}, "blocks 5", poster)
    timing = block.plan()
    assert block.frames() == 414
    clicks = [round(sound.at, 2) for sound in timing.sounds if sound.name == "click"]
    softs = [round(sound.at, 2) for sound in timing.sounds if sound.name == "soft"]
    assert clicks == [0.8, 1.3, 5.9, 6.3, 10.7, 11.1]
    assert softs == [2.8, 5.25, 7.6, 10.05]
    assert [(round(a, 2), round(b, 2)) for a, b, _ in timing.notes] == [(3.02, 5.4), (7.82, 10.2)]
    assert [(round(a, 2), b if math.isinf(b) else round(b, 2)) for a, b, _ in timing.focus] == [(1.6, 2.9), (6.6, 7.7), (11.4, math.inf)]


def test_document_works_out_zoom_and_via_when_left_out(poster):
    block = read_block({"document": {"source": "poster", "steps": [{"focus": [52, 334, 668, 392], "hold": 2}]}}, "b", poster)
    step = block.steps[0]
    assert 1 < step.zoom <= 2.4
    assert len(step.via) == 3


def test_document_refuses_a_focus_outside_the_image(poster):
    with pytest.raises(CutError, match="not inside the 2048x1200 image"):
        read_block({"document": {"source": "poster", "steps": [{"focus": [0, 0, 3000, 50], "hold": 1}]}}, "b", poster)
