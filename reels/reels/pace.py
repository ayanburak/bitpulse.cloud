"""
file: reels/pace.py
importable: Pace, measure, gaps

How much of a reel shows real pictures and how much is black, read from its blocks before
anything is rendered. A viewer stays or scrolls on in the first seconds, so a black screen there
is warned about, and so is a reel where black narration cards take too much of the time. A reel
without music is also checked for silence, every stretch where no voice or clip sound plays.

description: Measures the black screen time and, without music, the silences of an edit and warns about them.
"""

# NOTE: These are warnings, not errors. Sometimes a story has no real picture for a sentence and
# a black card is the honest choice. The model reads the warning and decides, the editor sees it.
#
# NOTE: The closing card is left out of the share, it is black on every reel and is not narration,
# and out of the silence, a quiet end after the last picture is fine.

from dataclasses import dataclass

from reels.blocks.base import Block, seconds
from reels.blocks.card import Card

# A viewer decides in about this many seconds whether to keep watching.
OPENING = 3.0
# The most of a reel that black narration cards may take.
MOST_BLACK = 0.25
# A gap in the sound shorter than this passes for a breath.
LONGEST_QUIET = 0.5


@dataclass(frozen=True)
class Pace:
    length: float
    black: float
    first_black: float | None
    quiet: tuple[tuple[float, float], ...] = ()

    @property
    def share(self) -> float:
        return self.black / self.length if self.length else 0.0

    def warnings(self) -> list[str]:
        found = []
        if self.first_black is not None and self.first_black < OPENING:
            found.append(f"black card at {self.first_black:.1f} s, the first {OPENING:.0f} seconds should show a real picture")
        if self.share > MOST_BLACK:
            found.append(f"black cards take {self.black:.1f} s, {self.share:.0%} of the reel, give them pictures "
                         f"to bring it under {MOST_BLACK:.0%}")
        if self.quiet:
            found.append("no music and nothing to hear at " + ", ".join(f"{a:.1f}-{b:.1f} s" for a, b in self.quiet)
                         + ", give those pictures a clip with its own sound")
        return found


def measure(blocks: tuple[Block, ...], music: bool = True) -> Pace:
    frame, black, first, length = 0, 0, None, 0
    heard: list[tuple[float, float]] = []
    for block in blocks:
        frames = block.frames()
        heard += [(voice.at, voice.at + voice.source_to - voice.source_from) for voice in block.voices(frame)]
        if isinstance(block, Card) and not block.pictures:
            black += frames
            first = seconds(frame) if first is None else first
        if block.kind != "closing":
            length += frames
        frame += frames
    return Pace(seconds(length), seconds(black), first, () if music else gaps(heard, seconds(length)))


# The stretches up to end that no sound covers, longer than LONGEST_QUIET.
def gaps(heard: list[tuple[float, float]], end: float) -> tuple[tuple[float, float], ...]:
    found, reached = [], 0.0
    for start, stop in sorted(heard) + [(end, end)]:
        if start - reached > LONGEST_QUIET:
            found.append((round(reached, 2), round(min(start, end), 2)))
        reached = max(reached, stop)
    return tuple(found)
