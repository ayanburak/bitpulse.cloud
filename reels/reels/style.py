"""
file: reels/style.py
importable: TextStyle, Logo, QUOTE, CARD, CARD_STEP, CARD_OVER, NOTE, BRAND, TAGLINE, CLOSING_LINE, LOOKS,
    MARK_X, MARK_Y, VOICE_GAIN, MUSIC_HIGH, MUSIC_UNDER_VOICE, MUSIC_FADE_IN, MUSIC_FADE_OUT, LOUDNESS

The parts of a reel that never change from one video to the next. Serif Literata is only ever
the words someone said, the narrow bold Archivo only ever our own narration. A block picks one
of the styles here and never sets a size, a color or a position itself.

description: Defines the fixed type, picture looks and sound levels shared by every reel.
"""

# NOTE: These values were settled with the editor on the first reel, the Iran reward story of
# 7 November 2026. Changing one changes every reel after it, which is the point of keeping them
# in one place.
#
# NOTE: Nothing important goes into the bottom 320 pixels or near the right edge, Instagram
# draws its buttons and the account name there. The quote line at y 1330 and the card centre at
# y 958 both keep clear of it.

from dataclasses import dataclass
from pathlib import Path

from reels.config import MARK, SANS, SERIF

# --- Text ---


# An image drawn with a text, scaled to width with its own proportions.
@dataclass(frozen=True)
class Logo:
    path: Path
    x: int
    y: int
    width: int


# A font is picked either by a named instance such as Medium or by its axis values, the narrow
# Archivo has no named instance for width 75. y is the centre of the text block, x only counts
# for left aligned text.
@dataclass(frozen=True)
class TextStyle:
    font: Path
    size: int
    y: int
    instance: str | None = None
    axes: tuple[float, ...] | None = None
    color: str = "#ffffff"
    box: str | None = None
    pad: int = 16
    line_height: float = 1.18
    max_width: int = 900
    fade_in: float = 0.18
    fade_out: float = 0.12
    rise: int = 14
    align: str = "center"
    x: int = 0
    logo: Logo | None = None


# What a person says, one sentence at a time, on a dark box a little below the middle.
QUOTE = TextStyle(font=SERIF, instance="Medium", size=60, y=1330, box="#0000008c", line_height=1.32)

# Our narration on a black card. Each line of a card is its own item, stacked around CARD.y.
CARD = TextStyle(font=SANS, axes=(720, 75), size=92, y=958, line_height=1.15, fade_in=0.3)
CARD_STEP = 106

# The same narration over a picture sits in the lower third, under the subject, where the picture
# is shaded. Four lines still end above the 320 pixels Instagram keeps for itself.
CARD_OVER = TextStyle(font=SANS, axes=(720, 75), size=92, y=1360, line_height=1.15, fade_in=0.3)

# Our narration over a blurred document, one item that wraps by itself.
NOTE = TextStyle(font=SANS, axes=(720, 75), size=92, y=960, line_height=1.15, fade_in=0.3)

# The closing card shows the corner logo about twice as large, centred. 555 pixels is the width
# at which its square is the 96 pixels of the first reel's closing card.
BRAND = TextStyle(font=SANS, size=72, y=930, fade_in=0.35, logo=Logo(MARK, (1080 - 555) // 2, 840, 555))
TAGLINE = TextStyle(font=SERIF, instance="Regular", size=44, y=1040, color="#ffffffc0", fade_in=0.35)
CLOSING_LINE = "The full story is linked in our bio."

# --- Logo ---

# The logo sits where it sits on the Instagram page, 72 pixels from the left and 64 from the top
# of the page. Instagram shows a reel in the feed cut to the 4:5 middle of the frame, which starts
# 285 pixels down, so there the logo lands exactly where it is on a post. MARK holds 20 pixels of
# clear space around the logo for its shadow, tools/brand.cjs draws it.
MARK_X = 72 - 20
MARK_Y = 285 + 64 - 20

# --- Picture ---

# ffmpeg filters laid over a shot after it is cut to the frame. archive suits old or night
# footage that gains from grain, speech keeps a face clean.
LOOKS = {
    "archive": "noise=alls=12:allf=t,eq=contrast=1.1:brightness=0.02",
    "speech": "unsharp=5:5:0.6,noise=alls=5:allf=t",
}

# --- Sound ---

# Speech is raised before the mix and the whole mix is then brought to -14 LUFS, the level
# Instagram plays at. Music sits high between voices and drops under them.
VOICE_GAIN = 1.6
MUSIC_HIGH = 0.85
MUSIC_UNDER_VOICE = 0.3
MUSIC_FADE_IN = 1.2
MUSIC_FADE_OUT = 1.5
LOUDNESS = "I=-14:TP=-1.5:LRA=11"
