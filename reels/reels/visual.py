"""
file: reels/visual.py
importable: Visual, Still, Clip, Box, IMAGES, read_visual

A picture that fills the frame for a while, under a card's narration or under someone's voice.
A still is a real photograph a camera moves over: it opens on its focus, keeps pushing in slowly
and travels to another part of the photograph when to is given. A clip is a stretch of a video.

    show: {source: c6, focus: [610, 220, 1180, 900], to: [700, 300, 1000, 640]}
    show: {source: boot, from: 41.2, crop: "405:720:438:0"}

focus and to are left, top, right and bottom in pixels of the photograph, without focus the
whole photograph is framed. Whether a source is a still or a clip is told by its file type.

A visual is rendered either plain or shaded. A shaded visual sits under narration: its subject
is placed in the upper part of the frame and the lower part is darkened for the text. A snapped
visual opens with a quick push in, the moment a card line brings it in.

description: Draws real photographs with a moving camera and cuts video clips to fill the frame.
"""

# NOTE: A photograph always covers the whole frame, the camera never shows past its edges. When a
# focus asks for more than that allows, the view is moved back inside the photograph and the
# focus ends up off centre instead of a black border showing.
#
# NOTE: Commons photographs are often 5000 pixels wide. They are scaled down once to what the
# closest view needs, every frame is then cut from that smaller copy.
#
# NOTE: The snap is the only fast move, its frames are the average of three moments a third of a
# frame apart. The slow push afterwards needs no motion blur.
#
# NOTE: The copy of the photograph is made at the closest view's size, so a frame is cut at almost
# one to one and bilinear sampling looks as good as bicubic at a third of the time. The frames
# are drawn by one process per core, started fresh for the same reason as in the document block:
# the render runs blocks in threads and forking a process with threads can hang.

import math
import multiprocessing
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from reels.config import FPS, HEIGHT, WIDTH
from reels.fields import Crop, CutError, centre, crop, number
from reels.media import MediaError, frame_pipe, shot, size
from reels.style import LOOKS

# --- Constants ---

IMAGES = {".jpg", ".jpeg", ".png", ".webp"}
FIELDS = {"source", "focus", "to", "from", "crop", "look", "push"}

# The focus fills this much of the frame's width, or of the height left for it.
FILL = 0.9
# Where the middle of the focus sits, in frame pixels from the top. A shaded visual keeps its
# subject above the narration in the lower third.
PLAIN_Y = 960
SHADED_Y = 700
SHADED_HEIGHT = 1100

# The snap starts this much wider and closes in over SNAP seconds. A still keeps this much room
# above the scale that just covers the frame, so a snap is possible on every photograph.
SNAP = 0.25
SNAP_WIDER = 0.9
ROOM = 1.12
PUSH = 0.03

# The shade is the full picture down to SHADE_FROM, then darkens to SHADE_DEPTH at SHADE_TO.
SHADE_FROM = 980
SHADE_TO = 1560
SHADE_DEPTH = 0.3

Box = tuple[float, float, float, float]


# --- Visuals ---


@dataclass(frozen=True)
class Still:
    source: Path
    focus: Box | None
    to: Box | None

    def render(self, frames: int, out: Path, shaded: bool, snapped: bool) -> None:
        Camera(self, shaded, snapped, frames / FPS).write(frames, out)


@dataclass(frozen=True)
class Clip:
    source: Path
    start: float
    crop: Crop
    look: str
    push: float

    def render(self, frames: int, out: Path, shaded: bool, snapped: bool) -> None:
        shot(self.source, self.start, frames, self.crop, self.look, self.push, out,
             shade=shade_image(out) if shaded else None, punch=1 - SNAP_WIDER if snapped else 0)


Visual = Still | Clip


def read_visual(raw: dict[str, Any], where: str, sources: dict[str, Path], look: str) -> Visual:
    """Reads a still or a clip from fields the caller has already checked by name.

    Args:
        raw: The fields, a source and either focus and to or from, crop, look and push.
        where: Where the visual sits in the edit file, used in errors.
        sources: The story's sources by name.
        look: The look a clip gets when it names none.

    Raises:
        CutError: The source is unknown, a field does not fit its kind or a box is outside the photograph.
    """
    name = raw.get("source")
    if name not in sources:
        raise CutError(f"{where}: unknown source {name}, the sources are {', '.join(sources)}")
    path = sources[name]
    if path.suffix.lower() in IMAGES:
        wrong = {"from", "crop", "look", "push"} & raw.keys()
        if wrong:
            raise CutError(f"{where}: {', '.join(sorted(wrong))} is for a video, {name} is a photograph, give focus and to")
        try:
            with Image.open(path) as image:
                width, height = image.size
        except OSError:
            raise CutError(f"{where}: could not open the photograph {path.name}") from None
        return Still(path, read_box(raw, "focus", where, width, height), read_box(raw, "to", where, width, height))
    wrong = {"focus", "to"} & raw.keys()
    if wrong:
        raise CutError(f"{where}: {', '.join(sorted(wrong))} is for a photograph, {name} is a video, give from and crop")
    look = raw.get("look", look)
    if look not in LOOKS:
        raise CutError(f"{where}: unknown look {look}, the looks are {', '.join(LOOKS)}")
    if "crop" in raw:
        window = crop(raw["crop"], where)
    else:
        try:
            window = centre(*size(path))
        except MediaError:
            raise CutError(f"{where}: could not read the size of {path.name} for a centre crop, give crop") from None
    return Clip(path, number(raw, "from", where, 0, 1e6), window, look, number(raw, "push", where, 0, 0.2, 0))


def read_box(raw: dict[str, Any], key: str, where: str, width: int, height: int) -> Box | None:
    box = raw.get(key)
    if box is None:
        return None
    if not isinstance(box, list) or len(box) != 4 or not all(isinstance(v, (int, float)) for v in box):
        raise CutError(f"{where}: {key} must be [left, top, right, bottom] in pixels of the photograph")
    left, top, right, bottom = (float(v) for v in box)
    if not (0 <= left < right <= width and 0 <= top < bottom <= height):
        raise CutError(f"{where}: {key} {box} is not inside the {width}x{height} photograph")
    return left, top, right, bottom


# --- Shade ---


def shade_curve() -> np.ndarray:
    y = np.arange(HEIGHT, dtype=np.float32)
    depth = np.clip((y - SHADE_FROM) / (SHADE_TO - SHADE_FROM), 0, 1)
    return (1 - (1 - SHADE_DEPTH) * depth * depth * (3 - 2 * depth))[:, None, None]


# The same shade for a clip, as a black picture whose transparency follows the curve. ffmpeg
# lays it over the clip, each piece writes its own copy next to itself.
def shade_image(out: Path) -> Path:
    alpha = ((1 - shade_curve()[:, :, 0]) * 255).astype(np.uint8)
    picture = np.zeros((HEIGHT, WIDTH, 4), np.uint8)
    picture[..., 3] = np.repeat(alpha, WIDTH, axis=1)
    path = out.with_suffix(".shade.png")
    Image.fromarray(picture, "RGBA").save(path)
    return path


# --- Camera ---


def ease(x: float) -> float:
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def snap(x: float) -> float:
    return 1 - (1 - x) ** 4


class Camera:
    """Draws the frames of one still.

    A view is a scale and the photograph pixel that sits at the anchor, the frame point the
    focus is placed on.
    """

    def __init__(self, still: Still, shaded: bool, snapped: bool, length: float) -> None:
        image = Image.open(still.source).convert("RGB")
        self.still, self.shaded = still, shaded
        self.anchor = SHADED_Y if shaded else PLAIN_Y
        self.room = SHADED_HEIGHT if shaded else HEIGHT
        self.cover = max(WIDTH / image.width, HEIGHT / image.height) * ROOM
        self.size = image.size
        self.first = self.frame_box(still.focus or (0, 0, image.width, image.height))
        self.last = self.frame_box(still.to) if still.to else (self.first[0] * (1 + PUSH * length), *self.first[1:])
        self.snapped = snapped
        self.length = length
        self.shade = shade_curve() if shaded else None
        # The closest view decides how small the photograph can be made before drawing.
        self.k = min(1.0, max(self.first[0], self.last[0]))
        self.image = image.resize((round(image.width * self.k), round(image.height * self.k)), Image.LANCZOS) if self.k < 1 else image

    # The view that fits a box, the box's middle on the anchor.
    def frame_box(self, box: Box) -> tuple[float, float, float]:
        left, top, right, bottom = box
        scale = max(self.cover, min(WIDTH * FILL / (right - left), self.room * FILL / (bottom - top)))
        return scale, (left + right) / 2, (top + bottom) / 2

    def view(self, t: float) -> tuple[float, float, float]:
        u = ease(min(1.0, t / self.length)) if self.length > 0 else 1.0
        a, b = self.first, self.last
        scale = math.exp(math.log(a[0]) + (math.log(b[0]) - math.log(a[0])) * u)
        x, y = a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u
        if self.snapped and t < SNAP:
            scale *= SNAP_WIDER + (1 - SNAP_WIDER) * snap(t / SNAP)
        return self.inside(max(scale, self.cover / ROOM), x, y)

    # The view moved back inside the photograph, so no frame shows past its edges.
    def inside(self, scale: float, x: float, y: float) -> tuple[float, float, float]:
        width, height = self.size
        x = min(max(x, WIDTH / 2 / scale), width - WIDTH / 2 / scale)
        y = min(max(y, self.anchor / scale), height - (HEIGHT - self.anchor) / scale)
        return scale, x, y

    def draw(self, t: float) -> np.ndarray:
        scale, x, y = self.view(t)
        s = scale / self.k
        x, y = x * self.k, y * self.k
        drawn = self.image.transform((WIDTH, HEIGHT), Image.AFFINE, (1 / s, 0, x - WIDTH / 2 / s, 0, 1 / s, y - self.anchor / s),
                                     resample=Image.BILINEAR)
        return np.asarray(drawn, dtype=np.float32)

    def frame(self, index: int) -> bytes:
        t = index / FPS
        if self.snapped and t < SNAP + 0.05:
            picture = sum(self.draw(max(0.0, t + d)) for d in (-1 / 90, 0, 1 / 90)) / 3
        else:
            picture = self.draw(t)
        if self.shade is not None:
            picture = picture * self.shade
        return picture.clip(0, 255).astype(np.uint8).tobytes()

    def write(self, frames: int, out: Path) -> None:
        context = multiprocessing.get_context("spawn")
        with context.Pool(initializer=start_worker, initargs=(self.still, self.shaded, self.snapped, self.length)) as pool, \
                frame_pipe(out, "noise=alls=5:allf=t,format=yuv420p") as pipe:
            for frame in pool.imap(draw_frame, range(frames), chunksize=4):
                pipe.write(frame)


# --- Workers ---

# Each worker process opens the photograph once and keeps it for every frame it draws.
worker: Camera | None = None


def start_worker(still: Still, shaded: bool, snapped: bool, length: float) -> None:
    global worker
    worker = Camera(still, shaded, snapped, length)


def draw_frame(index: int) -> bytes:
    assert worker is not None
    return worker.frame(index)
