"""
file: reels/cut.py
importable: Cut, load

The edit file, cut.yaml, is the only thing the model writes for a reel. It names the story, the
music, the sources in the story's work folder and the blocks in the order they play.

    story: 2026-11-07-iran-nuclear-reward
    music: {file: Impact Prelude.mp3, from: 35.73}
    sources:
      b2: src/b2.webm
    credits: ["The White House", "US Air Force"]
    blocks:
      - card: {...}

A reel without music leaves music out, its sound is then only what the pictures and voices bring.

description: Reads and checks a whole edit file.
"""

from dataclasses import dataclass
from pathlib import Path

import yaml

from reels.blocks import Block, read_block
from reels.blocks.base import Sources
from reels.config import WORK
from reels.fields import CutError, number, record, text
from reels.mix import Music, music_file


@dataclass(frozen=True)
class Cut:
    story: str
    work: Path
    music: Music | None
    blocks: tuple[Block, ...]
    warnings: tuple[str, ...]
    credits: tuple[str, ...]


def load(path: Path) -> Cut:
    """Reads an edit file and checks every field of it.

    Args:
        path: The cut.yaml file.

    Returns:
        The checked edit, with every source resolved to a file in the story's work folder.

    Raises:
        CutError: The file can not be read or breaks a rule. The message names where.
    """
    try:
        data = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError) as error:
        raise CutError(f"{path.name}: {error}") from None
    data = record(data, path.name, {"story", "music", "sources", "credits", "blocks"})
    story = text(data, "story", path.name)
    work = WORK / story
    if not work.is_dir():
        raise CutError(f"story: no work folder {work}")

    music = None
    if "music" in data:
        raw = record(data["music"], "music", {"file", "from"})
        music = Music(music_file(text(raw, "file", "music")), number(raw, "from", "music", 0, 3600, 0))

    files = {}
    for name, value in record(data.get("sources"), "sources", set(data.get("sources") or {})).items():
        file = work / str(value)
        if not file.is_file():
            raise CutError(f"sources, {name}: no file {file}")
        files[str(name)] = file
    sources = Sources(files, work)

    blocks = data.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        raise CutError("blocks: missing")
    parsed = tuple(read_block(item, f"blocks {position}", sources) for position, item in enumerate(blocks, 1))
    credits = data.get("credits") or []
    if not isinstance(credits, list) or not all(isinstance(name, str) and name.strip() for name in credits):
        raise CutError("credits: a list of the owners of the footage, as they name themselves")
    return Cut(story, work, music, parsed, tuple(sources.warnings), tuple(name.strip() for name in credits))
