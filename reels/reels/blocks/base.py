"""
file: reels/blocks/base.py
importable: Block, Sources, seconds, frames_of, read_sounds

A reel is a row of blocks. Every block knows how many frames it takes, draws or cuts its own
picture pieces and says which texts, speech and sounds it adds, all from the frame it starts at.
A new kind of block is a new subclass registered in reels/blocks/__init__.py, the rest of the
engine does not change.

description: Defines the abstract block every part of a reel is made from.
"""

# NOTE: Blocks get their start as a frame number. Seconds are worked out from it in one place,
# seconds(), so a block can never drift off the frame grid the pieces are cut on.

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, ClassVar

from reels.config import FPS
from reels.events import Sound, Text, Voice
from reels.fields import CutError, number, record, text
from reels.transcript import Transcript, load_transcript

# Source names as the edit file gives them, mapped to the files in the story's work folder. A
# block that names a voice by its words reads the source's transcript through here, and leaves
# the warnings of the match here for the command to print.
class Sources(dict[str, Path]):
    def __init__(self, files: dict[str, Path], work: Path) -> None:
        super().__init__(files)
        self.work = work
        self.warnings: list[str] = []
        self.loaded: dict[Path, Transcript] = {}

    def transcript(self, path: Path) -> Transcript:
        if path not in self.loaded:
            self.loaded[path] = load_transcript(self.work / "transcripts" / f"{path.stem}.json")
        return self.loaded[path]

    def note(self, where: str, transcript: Transcript) -> None:
        self.warnings += [f"{where}: {warning}" for warning in transcript.warnings]
        transcript.warnings.clear()


class Block(ABC):
    """One part of a reel, for example a quote over footage or a black card with narration.

    parse() reads the block from the edit file. The other methods are called with the frame
    the block starts at, once the length of every block before it is known.
    """

    kind: ClassVar[str]

    # The logo in the top left corner shows over every block that does not say otherwise.
    branded: ClassVar[bool] = True

    @classmethod
    @abstractmethod
    def parse(cls, data: Any, where: str, sources: Sources) -> "Block":
        """Reads and checks the block's fields.

        Args:
            data: The block's mapping from the edit file.
            where: Where the block sits in the file, used in errors.
            sources: The story's sources by name.

        Raises:
            CutError: A field breaks a rule.
        """

    @abstractmethod
    def frames(self) -> int:
        """Returns the length of the block in frames."""

    @abstractmethod
    def render(self, start: int, prefix: Path) -> list[Path]:
        """Writes the block's picture pieces and returns them in order.

        Args:
            start: The frame the block starts at.
            prefix: Path the piece names start with, the block adds its own ending.
        """

    def texts(self, start: int) -> list[Text]:
        return []

    def voices(self, start: int) -> list[Voice]:
        return []

    def sounds(self, start: int) -> list[Sound]:
        return []

    def end(self, start: int) -> float:
        return seconds(start + self.frames())


def seconds(frame: int) -> float:
    return frame / FPS


def frames_of(length: float) -> int:
    return round(length * FPS)


# Sounds a block asks for itself, with times from the block's start. Whether the name exists in
# the library is checked when the sound is mixed.
def read_sounds(value: Any, where: str, length: float) -> tuple[Sound, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise CutError(f"{where}: sounds must be a list")
    sounds = []
    for position, item in enumerate(value, 1):
        at = f"{where}, sound {position}"
        raw = record(item, at, {"name", "at", "gain"})
        sounds.append(Sound(text(raw, "name", at), number(raw, "at", at, 0, length), number(raw, "gain", at, 0, 4, 1)))
    return tuple(sounds)
