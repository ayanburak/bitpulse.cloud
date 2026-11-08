"""
file: reels/config.py
importable: WIDTH, HEIGHT, FPS, ROOT, MUSIC, SOUNDS, MARK, MARK_SCALE, WORK, SERIF, SANS

Every reel is 1080 by 1920 pixels at 30 frames a second. The folders here are where the
library, the site fonts and the working files of a story live.

description: Holds the frame size and the folders every part of the engine reads from.
"""

# NOTE: The fonts are read from the site repository instead of being copied, so a reel always
# uses the same type as the site. A move of the site folder breaks this path on purpose, loudly.

from pathlib import Path

# --- Frame ---

WIDTH = 1080
HEIGHT = 1920
FPS = 30

# --- Folders ---

ROOT = Path(__file__).resolve().parent.parent
MUSIC = ROOT / "library" / "music"
SOUNDS = ROOT / "library" / "sfx"
# The logo is drawn by tools/brand.cjs at three times its size on the Instagram page.
MARK = Path(__file__).resolve().parent / "assets" / "brand.png"
MARK_SCALE = 3

# The raw material of a story is large and is thrown away once the reel is approved, so it
# stays out of the project, one folder per story.
WORK = Path.home() / ".cache" / "bitpulse-reels"

# The site lives next to this project in the same repository.
SITE = ROOT.parent / "site"
FONTS = SITE / "public" / "fonts"
SERIF = FONTS / "literata-latin.woff2"
SANS = FONTS / "archivo-latin.woff2"
