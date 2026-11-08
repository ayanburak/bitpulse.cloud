"""
file: reels/events.py
importable: Text, Voice, Sound

What a block leaves on the timeline besides its picture. Every time here is in seconds from the
start of the reel, the block has already added its own start.

description: Describes the text, speech and sound events that blocks place on the reel.
"""

from dataclasses import dataclass
from pathlib import Path

from reels.style import TextStyle


# y overrides the style's position, a card uses it to stack its lines.
@dataclass(frozen=True)
class Text:
    start: float
    end: float
    words: str
    style: TextStyle
    y: int | None = None


# A stretch of a source's own sound, cut from source_from to source_to and played at at. The
# music drops under it when duck is true, as it does under speech. A crowd under a montage is
# laid on top of the music instead.
@dataclass(frozen=True)
class Voice:
    path: Path
    source_from: float
    source_to: float
    at: float
    fade_in: float
    fade_out: float
    gain: float
    duck: bool = True


# A sound from the library, named by its file name without .wav.
@dataclass(frozen=True)
class Sound:
    name: str
    at: float
    gain: float = 1.0
