"""
file: reels/blocks/card.py
importable: Card, Closing

A card is a few lines of our own narration, the moment the reel turns from what was said to what
it means. Each line appears on its own second and all of them leave together just before the card
ends. The closing card is the same for every reel.

    card:
      seconds: 1.73
      lines: ["The same day,", "the US put this out."]
      reveal: [0.18, 0.78]
      sounds: [{name: boom, at: 0, gain: 1.1}]

A line may bring a real picture with it, a photograph or a video clip that fills the frame from
the moment the line appears until the next picture. The lines then sit in the lower third and
the picture changes with a quick push in and a click:

    card:
      seconds: 4
      lines:
        - {text: "Lionel Messi", show: {source: c6, focus: [610, 220, 1180, 900]}}
        - "is the first"
        - {text: "to win the Golden Boot", show: {source: boot, from: 41.2}}

Once a card shows pictures its first line must bring one, so the card never opens on black.
clicks: false leaves the clicks out. A card without pictures is a black screen.

description: Narration cards, black or over real pictures, and the fixed closing card of every reel.
"""

# NOTE: A card line is never wrapped. A line that is too wide is an error, since a wrapped line
# would push the lines under it out of their places. The writer splits the sentence instead.
#
# NOTE: A picture runs from its line's reveal to the next picture's, the first one from the
# card's first frame. The frame counts are worked out from the reveals once, so the pieces add
# up to the card's length exactly.

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from reels.blocks.base import Block, Sources, frames_of, read_sounds, seconds
from reels.events import Sound, Text
from reels.fields import CutError, number, record
from reels.media import black
from reels.style import BRAND, CARD, CARD_OVER, CARD_STEP, CLOSING_LINE, TAGLINE
from reels.text import wrap
from reels.visual import FIELDS, Visual, read_visual

# --- Constants ---

MOST_LINES = 4
FIRST_REVEAL = 0.2
NEXT_REVEAL = 0.5
LEAVE_EARLY = 0.05
CLOSING_FRAMES = 75
CLICK_GAIN = 0.8
SHORTEST_PICTURE = 6

# --- Card ---


@dataclass(frozen=True)
class Card(Block):
    kind = "card"
    length: int
    lines: tuple[str, ...]
    reveal: tuple[float, ...]
    effects: tuple[Sound, ...]
    # Each picture with the frame it starts at, from the card's first frame.
    pictures: tuple[tuple[int, Visual], ...] = ()
    clicks: bool = True

    @classmethod
    def parse(cls, data: Any, where: str, sources: Sources) -> "Card":
        data = record(data, where, {"seconds", "lines", "reveal", "sounds", "clicks"})
        length = number(data, "seconds", where, 0.5, 10)
        items = data.get("lines")
        if not isinstance(items, list) or not 1 <= len(items) <= MOST_LINES:
            raise CutError(f"{where}: lines must be a list of 1 to {MOST_LINES} lines")
        lines, shows = [], []
        for position, item in enumerate(items, 1):
            at = f"{where}, line {position}"
            if isinstance(item, dict):
                raw = record(item, at, {"text", "show"})
                item = raw.get("text")
                if "show" in raw:
                    shows.append((position - 1, read_visual(record(raw["show"], f"{at}, show", FIELDS), f"{at}, show", sources, "speech")))
            if not isinstance(item, str) or not item.strip():
                raise CutError(f"{at}: a line is its text, or {{text: ..., show: {{...}}}}")
            if len(wrap(item, CARD)) > 1:
                raise CutError(f"{at}: the line {item!r} is wider than the screen, split it into two lines")
            lines.append(item.strip())
        reveal = data.get("reveal", [FIRST_REVEAL + NEXT_REVEAL * index for index in range(len(lines))])
        if not isinstance(reveal, list) or len(reveal) != len(lines):
            raise CutError(f"{where}: reveal needs one second for every line")
        times = tuple(number({"reveal": value}, "reveal", where, 0, length - 0.3) for value in reveal)
        frames = frames_of(length)
        pictures = cls.place(shows, times, frames, where)
        clicks = data.get("clicks", True)
        if not isinstance(clicks, bool):
            raise CutError(f"{where}: clicks is true or false")
        return cls(frames, tuple(lines), times, read_sounds(data.get("sounds"), where, length), pictures, clicks)

    @staticmethod
    def place(shows: list[tuple[int, Visual]], reveal: tuple[float, ...], frames: int, where: str) -> tuple[tuple[int, Visual], ...]:
        if not shows:
            return ()
        if shows[0][0] != 0:
            raise CutError(f"{where}: the first line must show a picture too, a card with pictures never opens on black")
        starts = [0] + [frames_of(reveal[index]) for index, _ in shows[1:]]
        for a, b in zip(starts, starts[1:] + [frames]):
            if b - a < SHORTEST_PICTURE:
                raise CutError(f"{where}: a picture would show for {b - a} frames, give its line a later reveal or leave the picture out")
        return tuple((start, visual) for start, (_, visual) in zip(starts, shows))

    def frames(self) -> int:
        return self.length

    def render(self, start: int, prefix: Path) -> list[Path]:
        if not self.pictures:
            out = prefix.with_name(f"{prefix.name}-card.mp4")
            black(self.length, out)
            return [out]
        pieces = []
        ends = [first for first, _ in self.pictures[1:]] + [self.length]
        for position, ((first, visual), last) in enumerate(zip(self.pictures, ends), 1):
            out = prefix.with_name(f"{prefix.name}-picture{position}.mp4")
            visual.render(last - first, out, shaded=True, snapped=True)
            pieces.append(out)
        return pieces

    # The lines are stacked around the middle of their place, each one step apart, the centre of
    # a black card or the lower third over a picture.
    def texts(self, start: int) -> list[Text]:
        begin, end = seconds(start), self.end(start) - LEAVE_EARLY
        style = CARD_OVER if self.pictures else CARD
        middle = (len(self.lines) - 1) / 2
        return [Text(begin + reveal, end, line, style, round(style.y + (index - middle) * CARD_STEP))
                for index, (line, reveal) in enumerate(zip(self.lines, self.reveal))]

    # A picture after the first comes in with a click, the first one rides on the cut into the card.
    def sounds(self, start: int) -> list[Sound]:
        own = [Sound(sound.name, seconds(start) + sound.at, sound.gain) for sound in self.effects]
        if self.clicks:
            own += [Sound("click", seconds(start + first), CLICK_GAIN) for first, _ in self.pictures[1:]]
        return own


# --- Closing ---


# The closing card takes no fields, it is the same on every reel.
@dataclass(frozen=True)
class Closing(Block):
    kind = "closing"
    branded = False

    @classmethod
    def parse(cls, data: Any, where: str, sources: Sources) -> "Closing":
        record(data, where, set())
        return cls()

    def frames(self) -> int:
        return CLOSING_FRAMES

    def render(self, start: int, prefix: Path) -> list[Path]:
        out = prefix.with_name(f"{prefix.name}-closing.mp4")
        black(CLOSING_FRAMES, out)
        return [out]

    def texts(self, start: int) -> list[Text]:
        begin, end = seconds(start), self.end(start)
        return [Text(begin + 0.15, end, "", BRAND), Text(begin + 0.55, end, CLOSING_LINE, TAGLINE)]
