"""
file: reels/render.py
importable: Result, render

Turns a checked edit into the finished reel. The blocks are laid end to end on the frame grid,
each one cuts or draws its picture, and the text layer and the sound are made for the whole reel
at once. The reel, reel.mp4, and a sheet of its frames, sheet.png, go into the story's work folder.

description: Renders an edit into the finished reel and a sheet of its frames.
"""

# NOTE: The build folder is removed after a good render and kept after a failed one, so the
# pieces that were made can be looked at.
#
# NOTE: A prelap starts a voice under the block before, and its first line with it. Over footage
# that is wanted, the Iran reel does it. Over a card the line would hang under the card's own
# narration, the Messi reel had one at 27 seconds, so after a card a line waits for its block.
#
# TODO: Every render cuts every piece again. Keeping pieces whose block did not change would
# make a render after a small fix much faster.

import shutil
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from pathlib import Path

from reels.blocks.base import seconds
from reels.cut import Cut
from reels.events import Sound, Text, Voice
from reels.fields import CutError
from reels.media import concat, duration, finish, loudness, sheet
from reels.mix import mix
from reels.text import render_layer


@dataclass(frozen=True)
class Result:
    reel: Path
    sheet: Path
    seconds: float
    loudness: float


def render(cut: Cut) -> Result:
    """Renders the reel of an edit.

    Args:
        cut: A checked edit from load().

    Returns:
        Where the reel and its frame sheet were written, its length and its loudness.

    Raises:
        CutError: A block's speech would start before the reel does, or a sound is missing.
        MediaError: ffmpeg failed on a piece.
    """
    starts, frame = [], 0
    for block in cut.blocks:
        starts.append(frame)
        frame += block.frames()
    total = frame

    texts: list[Text] = []
    voices: list[Voice] = []
    sounds: list[Sound] = []
    for index, (block, start) in enumerate(zip(cut.blocks, starts)):
        own = block.texts(start)
        if index and cut.blocks[index - 1].kind == "card":
            own = [replace(text, start=max(text.start, seconds(start))) for text in own]
        texts += own
        voices += block.voices(start)
        sounds += block.sounds(start)
    early = [voice for voice in voices if voice.at < 0]
    if early:
        raise CutError("blocks 1: the first block's voice starts before the reel, its prelap must be 0")

    build = cut.work / "build"
    shutil.rmtree(build, ignore_errors=True)
    build.mkdir()

    # The pieces and the text layer do not depend on each other. Most of the work happens in
    # ffmpeg processes and numpy, so threads are enough to keep several cores busy.
    with ThreadPoolExecutor() as pool:
        jobs = [pool.submit(block.render, start, build / f"{position:02d}")
                for position, (block, start) in enumerate(zip(cut.blocks, starts), 1)]
        layer = pool.submit(render_layer, texts, total, build / "text.mov")
        sound = pool.submit(mix, voices, sounds, cut.music, seconds(total), build / "sound.wav")
        pieces = [piece for job in jobs for piece in job.result()]
        layer.result()
        sound.result()

    concat(pieces, build / "picture.mp4")
    reel = cut.work / "reel.mp4"
    hidden = [(seconds(start), block.end(start)) for block, start in zip(cut.blocks, starts) if not block.branded]
    finish(build / "picture.mp4", build / "text.mov", build / "sound.wav", hidden, reel)
    frames = cut.work / "sheet.png"
    sheet(reel, frames)
    shutil.rmtree(build)
    return Result(reel, frames, duration(reel), loudness(reel))
