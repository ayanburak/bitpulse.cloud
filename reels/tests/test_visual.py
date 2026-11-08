"""
file: tests/test_visual.py
importable: nothing, pytest loads this file

description: Checks cards over real pictures, montages, photographs under a voice and the camera over a photograph.
"""

import json
from pathlib import Path

import pytest
from PIL import Image

from reels.blocks import read_block
from reels.blocks.base import Sources
from reels.config import HEIGHT, WIDTH
from reels.fields import CutError
from reels.mix import spoken
from reels.style import CARD_OVER
from reels.visual import Camera, Clip, Still


@pytest.fixture
def sources(tmp_path):
    photo = tmp_path / "messi.jpg"
    Image.new("RGB", (3333, 5000), "gray").save(photo)
    return {"messi": photo, "boot": Path("boot.mp4"), "kennedy": Path("kennedy.mp4")}


def card(lines, sources, **fields):
    return read_block({"card": {"seconds": 4, "lines": lines, **fields}}, "blocks 1", sources)


# Each picture runs from its line's reveal to the next picture, and the pieces fill the card.
def test_card_pictures_change_on_their_lines(sources):
    block = card([{"text": "Lionel Messi", "show": {"source": "messi", "focus": [800, 600, 2400, 2600]}},
                  "is the first",
                  {"text": "to win the Golden Boot", "show": {"source": "boot", "from": 41.2, "crop": "405:720:438:0"}}],
                 sources, reveal=[0.2, 0.8, 1.6])
    assert [start for start, _ in block.pictures] == [0, 48]
    assert isinstance(block.pictures[0][1], Still) and isinstance(block.pictures[1][1], Clip)
    assert [sound.at for sound in block.sounds(30)] == [pytest.approx(1 + 1.6)]
    assert {text.style for text in block.texts(0)} == {CARD_OVER}


def test_card_without_pictures_stays_black_and_quiet(sources):
    block = card(["No goal on the final day."], sources)
    assert block.pictures == () and block.sounds(0) == []
    assert block.texts(0)[0].y == 958


@pytest.mark.parametrize("lines, fields, message", [
    (["Lionel Messi", {"text": "the Golden Boot", "show": {"source": "messi"}}], {}, "first line must show"),
    ([{"text": "a", "show": {"source": "messi"}}, {"text": "b", "show": {"source": "messi"}}], {"reveal": [0.2, 0.1]},
     "for 3 frames"),
    ([{"text": "a", "show": {"source": "messi", "from": 3}}], {}, "from is for a video"),
    ([{"text": "a", "show": {"source": "boot", "focus": [0, 0, 10, 10]}}], {}, "focus is for a photograph"),
    ([{"text": "a", "show": {"source": "messi", "focus": [0, 0, 4000, 10]}}], {}, "not inside the 3333x5000"),
])
def test_card_refuses_pictures_that_do_not_fit(sources, lines, fields, message):
    with pytest.raises(CutError, match=message):
        card(lines, sources, **fields)


def test_speech_takes_a_photograph_as_a_shot(sources):
    block = read_block({"speech": {
        "voice": {"source": "kennedy", "from": 10, "to": 13},
        "shots": [{"source": "messi", "focus": [800, 600, 2400, 2600]}],
        "lines": [[10, 12.9, "Words."]],
    }}, "blocks 2", sources)
    assert isinstance(block.shots[0].visual, Still) and block.shots[0].frames == 90


# Every view of the camera stays inside the photograph, through the snap and on to the last frame.
def test_camera_never_shows_past_the_photograph(sources):
    still = Still(sources["messi"], (0, 0, 600, 600), (2700, 4300, 3333, 5000))
    camera = Camera(still, shaded=True, snapped=True, length=3)
    width, height = camera.size
    for t in (0, 0.05, 0.2, 1, 2, 3):
        scale, x, y = camera.view(t)
        assert scale * width >= WIDTH - 1 and scale * height >= HEIGHT - 1
        assert x - WIDTH / 2 / scale >= -0.5 and x + WIDTH / 2 / scale <= width + 0.5
        assert y - camera.anchor / scale >= -0.5 and y + (HEIGHT - camera.anchor) / scale <= height + 0.5
    assert camera.view(0)[0] < camera.view(0.3)[0]


# The shots play one after the other for their own lengths, a clip's sound plays where the clip does
# and the music does not drop under it.
def test_montage_cuts_by_lengths_and_places_clip_sound(sources, tmp_path):
    block = read_block({"montage": {"shots": [
        {"source": "boot", "from": 41.2, "crop": "405:720:438:0", "seconds": 1.4, "sound": 0.7},
        {"source": "messi", "focus": [800, 600, 2400, 2600], "seconds": 2.2, "snap": True},
        {"source": "boot", "from": 50, "crop": "405:720:438:0", "seconds": 1, "sound": 0.5},
    ]}}, "blocks 3", Sources(sources, tmp_path))
    assert [shot.frames for shot in block.shots] == [42, 66, 30] and block.frames() == 138
    voices = block.voices(30)
    # Each sound starts a quarter second before its picture, to cross the one before it.
    assert [(voice.source_from, voice.at, voice.gain) for voice in voices] == [
        (pytest.approx(40.95), pytest.approx(0.75), 0.7), (pytest.approx(49.75), pytest.approx(4.35), 0.5)]
    assert voices[0].source_to == pytest.approx(41.2 + 1.4 + 0.25)
    assert block.texts(30) == []
    assert spoken(voices) == []


def test_montage_lines_sit_in_the_lower_third(sources):
    block = read_block({"montage": {"shots": [{"source": "messi", "seconds": 3}], "lines": ["26 goals"]}}, "blocks 3", sources)
    assert block.texts(0)[0].style == CARD_OVER


def test_montage_refuses_sound_on_a_photograph(sources):
    with pytest.raises(CutError, match="sound is for a video clip"):
        read_block({"montage": {"shots": [{"source": "messi", "seconds": 2, "sound": 0.5}]}}, "blocks 3", sources)


# A clip whose source was transcribed is checked for a cut through a word and for commentary
# under the montage's lines.
def test_montage_warns_about_cut_words_and_commentary(sources, tmp_path):
    (tmp_path / "transcripts").mkdir()
    (tmp_path / "transcripts" / "boot.json").write_text(json.dumps({"quiet": -40, "levels": [], "words": [
        [10.2, 10.6, "And"], [10.6, 10.8, "it"], [10.8, 11.0, "is"], [11.0, 11.6, "Lionel"], [11.6, 12.3, "Messi!"]]}))
    found = Sources(sources, tmp_path)
    read_block({"montage": {"shots": [{"source": "boot", "from": 10.0, "crop": "405:720:438:0", "seconds": 1.8, "sound": 1}],
                            "lines": ["Golden Boot"]}}, "blocks 2", found)
    assert [warning.split(",")[2].split(" goes")[0].strip() for warning in found.warnings[:1]] == ["shot 1: the cut at 11.8 s of boot.mp4"]
    assert "'Lionel'" not in found.warnings[0] and "'Messi!'" in found.warnings[0]
    assert '"And it is Lionel"' in found.warnings[1]
