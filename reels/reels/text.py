"""
file: reels/text.py
importable: render_layer

Draws every text event of a reel on a clear background and writes it as one transparent video
the length of the reel. The picture pieces never carry text, so a text change only redraws this
layer.

description: Renders the text events of a reel into a transparent video layer.
"""

# NOTE: Each text is drawn once into its own image and only moved and faded per frame. Drawing
# the letters again on every frame took most of the time in the first version. Most frames show
# the same texts in the same place as the frame before, those are written again as they are.
#
# NOTE: qtrle is used because it keeps the alpha channel and ffmpeg overlays it directly. The
# file is large but lives only in the build folder.

import subprocess
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from reels.config import FPS, HEIGHT, WIDTH
from reels.events import Text
from reels.media import MediaError
from reels.style import TextStyle

# --- Fonts ---


@lru_cache(maxsize=None)
def font(style: TextStyle) -> ImageFont.FreeTypeFont:
    face = ImageFont.truetype(str(style.font), style.size)
    if style.axes:
        face.set_variation_by_axes(list(style.axes))
    elif style.instance:
        face.set_variation_by_name(style.instance)
    return face


def color(value: str) -> tuple[int, int, int, int]:
    value = value.lstrip("#")
    if len(value) == 6:
        value += "ff"
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4, 6))


# --- Drawing ---


# Words are added to a line until the next one would pass max_width.
def wrap(words: str, style: TextStyle) -> list[str]:
    face = font(style)
    lines: list[str] = []
    for word in words.split():
        if lines and face.getlength(f"{lines[-1]} {word}") <= style.max_width:
            lines[-1] += f" {word}"
        else:
            lines.append(word)
    return lines


# The box is drawn per line, so a short last line gets a short box, the way subtitles look.
def draw(event: Text) -> Image.Image:
    style = event.style
    face = font(style)
    lines = wrap(event.words, style)
    step = int(style.size * style.line_height)
    top = (event.y if event.y is not None else style.y) - step * len(lines) / 2
    image = Image.new("RGBA", (WIDTH, HEIGHT))
    canvas = ImageDraw.Draw(image)
    for index, line in enumerate(lines):
        width = face.getlength(line)
        x = style.x if style.align == "left" else WIDTH / 2 - width / 2
        y = top + index * step
        if style.box:
            left, _, right, _ = canvas.textbbox((x, y), line, font=face)
            canvas.rounded_rectangle((left - style.pad, y + style.size * 0.02 - style.pad * 0.55,
                                      right + style.pad, y + style.size * 1.08 + style.pad * 0.55),
                                     radius=6, fill=color(style.box))
        canvas.text((x, y), line, font=face, fill=color(style.color))
    if style.logo:
        logo = Image.open(style.logo.path).convert("RGBA")
        logo = logo.resize((style.logo.width, round(logo.height * style.logo.width / logo.width)), Image.LANCZOS)
        image.alpha_composite(logo, (style.logo.x, style.logo.y))
    return image


# Fades in while it rises a few pixels with an ease out, fades out in place.
def placement(event: Text, t: float) -> tuple[float, int]:
    style = event.style
    rise = min(1.0, (t - event.start) / style.fade_in)
    fall = min(1.0, (event.end - t) / style.fade_out)
    eased = 1 - (1 - rise) ** 3
    return min(rise, fall), int((1 - eased) * style.rise)


# --- Layer ---


def render_layer(events: list[Text], frames: int, out: Path) -> None:
    """Writes the text events as a transparent video of frames frames.

    Args:
        events: Text events with times in seconds from the start of the reel.
        frames: Length of the reel in frames.
        out: The .mov file to write.

    Raises:
        MediaError: ffmpeg ended with an error.
    """
    images = [np.asarray(draw(event), dtype=np.float32) for event in events]
    blank = np.zeros((HEIGHT, WIDTH, 4), np.uint8).tobytes()
    process = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS),
         "-i", "-", "-c:v", "qtrle", str(out)], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.stdin is not None
    previous: tuple = ()
    written = blank
    for index in range(frames):
        t = index / FPS
        shown = [(event, image) for event, image in zip(events, images) if event.start <= t < event.end]
        if not shown:
            process.stdin.write(blank)
            continue
        state = tuple((id(event), *placement(event, t)) for event, _ in shown)
        if state == previous:
            process.stdin.write(written)
            continue
        previous = state
        # The colours are summed premultiplied by their alpha and divided back at the end, which
        # is the only way two half transparent texts over each other keep their real colour.
        paint = np.zeros((HEIGHT, WIDTH, 3), np.float32)
        cover = np.zeros((HEIGHT, WIDTH, 1), np.float32)
        for event, image in shown:
            alpha, drop = placement(event, t)
            layer = np.roll(image, drop, axis=0) if drop else image
            a = layer[..., 3:4] / 255 * alpha
            paint = layer[..., :3] * a + paint * (1 - a)
            cover = a + cover * (1 - a)
        rgb = np.divide(paint, cover, out=np.zeros_like(paint), where=cover > 0)
        frame = np.concatenate([rgb, cover * 255], axis=2)
        written = frame.clip(0, 255).astype(np.uint8).tobytes()
        process.stdin.write(written)
    process.stdin.close()
    error = process.stderr.read().decode() if process.stderr else ""
    if process.wait() != 0:
        raise MediaError(f"ffmpeg failed on the text layer: {error.strip()[:300]}")
