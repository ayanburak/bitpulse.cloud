"""
file: tests/test_cut.py
importable: nothing, pytest loads this file

description: Checks that a whole edit file is read and that its mistakes name their place.
"""

from pathlib import Path

import pytest

import reels.cut
import reels.mix
from reels.cut import load
from reels.fields import CutError

EDIT = """story: test-story
music: {file: calm.mp3, from: 3}
sources:
  clip: src/clip.mp4
blocks:
  - card: {seconds: 2, lines: [One line.]}
  - closing: {}
"""


@pytest.fixture
def folders(tmp_path, monkeypatch):
    work = tmp_path / "work"
    (work / "test-story" / "src").mkdir(parents=True)
    (work / "test-story" / "src" / "clip.mp4").touch()
    music = tmp_path / "music"
    music.mkdir()
    (music / "calm.mp3").touch()
    monkeypatch.setattr(reels.cut, "WORK", work)
    monkeypatch.setattr(reels.mix, "MUSIC", music)
    return tmp_path


def write(folder: Path, text: str) -> Path:
    path = folder / "cut.yaml"
    path.write_text(text)
    return path


def test_a_whole_edit_is_read(folders):
    cut = load(write(folders, EDIT))
    assert cut.story == "test-story"
    assert cut.music.start == 3
    assert [block.kind for block in cut.blocks] == ["card", "closing"]
    assert [block.branded for block in cut.blocks] == [True, False]


@pytest.mark.parametrize("change, message", [
    (("calm.mp3", "loud.mp3"), "no file loud.mp3"),
    (("src/clip.mp4", "src/gone.mp4"), "sources, clip: no file"),
    (("test-story", "other-story"), "no work folder"),
    (("  - closing: {}", "  - closing: {extra: 1}"), "blocks 2, closing: unknown field extra"),
])
def test_mistakes_name_their_place(folders, change, message):
    with pytest.raises(CutError, match=message):
        load(write(folders, EDIT.replace(*change)))
