"""
file: tests/test_deliver.py
importable: nothing, pytest loads this file

description: Checks the reel's caption, its history and the cleaning of its raw material.
"""

from pathlib import Path

import pytest

import reels.deliver
from reels.blocks.card import Closing
from reels.cut import Cut
from reels.deliver import clean, deliver, recent
from reels.fields import CutError
from reels.mix import Music


@pytest.fixture
def story(tmp_path, monkeypatch):
    work = tmp_path / "work"
    work.mkdir()
    (work / "reel.mp4").write_bytes(b"reel")
    social = tmp_path / "social"
    (social / "s").mkdir(parents=True)
    (social / "s" / "caption.txt").write_text("The news.\n\nFull story and sources: link in bio.\n\nImage: AP Photo. Every claim is sourced in the full story.\n")
    monkeypatch.setattr(reels.deliver, "SOCIAL", social)
    monkeypatch.setattr(reels.deliver, "HISTORY", tmp_path / "history.csv")
    monkeypatch.setattr(reels.deliver, "TRACKS", tmp_path / "tracks.yaml")
    monkeypatch.setattr(reels.deliver, "CUTS", tmp_path / "cuts")
    (work / "cut.yaml").write_text("story: s\n")
    (tmp_path / "tracks.yaml").write_text('calm.mp3: {credit: "\\"Calm\\" by Someone, CC BY 4.0"}\n')
    return Cut("s", work, Music(Path("calm.mp3"), 0), (Closing(),), (), ("The White House",)), social


def test_deliver_swaps_the_image_credit_for_video_and_music(story):
    cut, social = story
    deliver(cut, cut.work / "cut.yaml")
    text = (social / "s" / "reel.txt").read_text()
    assert "Video: The White House. Music: \"Calm\" by Someone, CC BY 4.0. Every claim" in text
    assert "AP Photo" not in text
    assert (social / "s" / "reel.mp4").read_bytes() == b"reel"
    assert "s: closing | calm.mp3" in recent()


def test_deliver_needs_credits(story):
    cut, _ = story
    with pytest.raises(CutError, match="credits: missing"):
        deliver(Cut(cut.story, cut.work, cut.music, cut.blocks, (), ()), cut.work / "cut.yaml")


def test_clean_waits_for_delivery_and_keeps_the_edit(story, tmp_path):
    cut, social = story
    with pytest.raises(CutError, match="not delivered"):
        clean("s", cut.work)
    deliver(cut, cut.work / "cut.yaml")
    clean("s", cut.work)
    assert not cut.work.exists()
    assert (tmp_path / "cuts" / "s.yaml").exists()


def test_deliver_leaves_the_music_out_of_a_reel_without_music(story):
    cut, social = story
    deliver(Cut(cut.story, cut.work, None, cut.blocks, (), cut.credits), cut.work / "cut.yaml")
    assert "Video: The White House. Every claim" in (social / "s" / "reel.txt").read_text()
    assert "s: closing | no music" in recent()
