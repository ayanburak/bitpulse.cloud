"""
file: tests/test_transcript.py
importable: nothing, pytest loads this file

The transcript here is made up: a few words with their times and a loudness curve drawn by
hand, loud where a word is spoken and quiet between words. The traps of the first reel are
built into it, a dip inside "badly" and a misheard name.

description: Checks how phrases are found in a transcript and where cuts are placed.
"""

from pathlib import Path

import numpy as np
import pytest

from reels.blocks import read_block
from reels.blocks.base import Sources
from reels.fields import CutError
from reels.transcript import STEP, Transcript, Word

LOUD, QUIET = -15.0, -50.0

SPOKEN = [
    (1.0, 1.4, "We're"), (1.4, 1.8, "dealing"), (1.8, 2.0, "with"), (2.0, 2.2, "them"), (2.2, 2.6, "now."),
    (3.0, 3.2, "They"), (3.2, 3.5, "want"), (3.5, 3.9, "very"), (3.9, 4.4, "badly."),
    (5.0, 5.2, "The"), (5.2, 5.4, "red"), (5.4, 5.8, "will"), (5.8, 6.3, "never."),
    (7.0, 7.4, "now."),
]


def made_up() -> Transcript:
    levels = np.full(int(8 / STEP), QUIET, np.float32)
    for start, end, _ in SPOKEN:
        levels[int(start / STEP):int(end / STEP)] = LOUD
    # A 40 ms dip between bad and ly, the trap that clipped the first reel.
    levels[int(4.1 / STEP):int(4.14 / STEP)] = QUIET
    return Transcript([Word(a, b, w) for a, b, w in SPOKEN], levels, -30.0, [])


def test_a_phrase_is_found_without_case_or_punctuation():
    transcript = made_up()
    assert transcript.find("we're dealing with them now") == (0, 4)


def test_three_dots_skip_the_middle_of_a_phrase():
    assert made_up().find("We're dealing ... very badly.") == (0, 8)


def test_a_phrase_said_twice_needs_near():
    transcript = made_up()
    with pytest.raises(CutError, match="said 2 times"):
        transcript.find("now")
    assert transcript.find("now", near=7) == (13, 13)


def test_a_misheard_name_is_found_by_likeness_and_reported():
    transcript = made_up()
    assert transcript.find("Iran will never") == (9, 12)
    assert "The red will never." in transcript.warnings[0]


def test_an_end_cut_never_falls_inside_the_last_word():
    transcript = made_up()
    end = transcript.cut_after(8)
    assert end > 4.4
    assert end < 5.0


def test_a_start_cut_sits_in_the_quiet_before_the_word():
    transcript = made_up()
    start = transcript.cut_before(5)
    assert 2.6 < start < 3.0


def test_a_word_with_no_quiet_before_it_is_refused():
    transcript = made_up()
    transcript.levels[:] = LOUD
    with pytest.raises(CutError, match="no pause before"):
        transcript.cut_before(5)


# --- Speech by words ---


def sources() -> Sources:
    found = Sources({"palm": Path("palm.mp4")}, Path("."))
    found.loaded[Path("palm.mp4")] = made_up()
    return found


def test_speech_by_words_cuts_in_the_quiet_and_times_its_lines():
    found = sources()
    block = read_block({"speech": {
        "voice": {"source": "palm", "words": "We're dealing ... very badly."},
        "shots": [{"sync": True, "until": "They", "crop": "608:1080:690:0"}, {"sync": True, "crop": "608:1080:690:0"}],
        "lines": ["We're dealing with them now.", "They want very badly."],
    }}, "blocks 1", found)
    assert block.voice.source_from < 1.0 and 4.4 < block.voice.source_to < 5.0
    assert block.shots[1].visual.start == pytest.approx(block.voice.source_from + block.shots[0].frames / 30)
    first, second = block.lines
    assert first.start == pytest.approx(1.0) and second.start == pytest.approx(3.0)
    assert first.end <= second.start - 0.04


def test_lines_come_from_whole_words_but_not_from_skipped_ones():
    block = read_block({"speech": {"voice": {"source": "palm", "words": "They want very badly."},
                                   "shots": [{"sync": True, "crop": "608:1080:690:0"}]}}, "b", sources())
    assert [line.words for line in block.lines] == ["They want very badly."]
    with pytest.raises(CutError, match="missing lines"):
        read_block({"speech": {"voice": {"source": "palm", "words": "We're ... badly."},
                               "shots": [{"sync": True, "crop": "608:1080:690:0"}]}}, "b", sources())


def test_a_misheard_word_reaches_the_warnings_of_the_edit():
    found = sources()
    read_block({"speech": {"voice": {"source": "palm", "words": "Iran will never."},
                           "shots": [{"sync": True, "crop": "608:1080:690:0"}]}}, "blocks 4", found)
    assert found.warnings and found.warnings[0].startswith("blocks 4, speech:")
