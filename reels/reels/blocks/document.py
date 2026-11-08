"""
file: reels/blocks/document.py
importable: Document

A real document, a poster or a page, shown whole and then gone through one part at a time. For
every step the camera snaps in with a click, the part comes into focus while everything around it
blurs and darkens, and the picture slowly pushes in. A step with words then blurs the whole
document and shows our narration over it while the camera goes back to the full page.

    document:
      source: poster
      steps:
        - focus: [390, 8, 1128, 128]
          zoom: 1.10
          hold: 1.3
          say: It wants to know who works on Iran's program.
        - focus: [8, 920, 240, 982]
          hold: 2.4

focus is the part to show, as left, top, right and bottom in pixels of the source image. via is
the point the camera stops at on its way in, as scale, x and y, and zoom the scale it ends at.
Both are worked out from focus when they are left out.

description: A block that walks through a document part by part with focus, blur and narration.
"""

# NOTE: The document is never cut out of its background and its colours are never changed. The
# viewer has to see that it is a real page, that is what made the editor like this block.
#
# NOTE: The narration only comes before a focus is left, never on both sides of it, otherwise
# the block gets too long. The last step has no narration, the next block follows it.
#
# NOTE: Every frame is the average of three moments a third of a frame apart. That is the
# motion blur that keeps a fast snap from looking like a jump. A frame takes about half a second,
# so the frames are drawn by one process per core. The processes are started fresh, not forked,
# because the render runs blocks in threads and forking a process with threads can hang.

import math
import multiprocessing
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from reels.blocks.base import Block, Sources, frames_of, seconds
from reels.config import HEIGHT, WIDTH
from reels.events import Sound, Text
from reels.fields import CutError, number, record
from reels.media import frame_pipe
from reels.style import NOTE
from reels.text import wrap

# --- Timing ---

INTRO = 0.8
SNAP = 0.3
STILL = 0.2
BACK = 2.4
REST = 0.6
PUSH = 0.033

# --- Look ---

# The document is centred a little above the middle of the frame, clear of the bottom of the
# screen where Instagram draws.
CENTRE_Y = 900
FOCUS_PAD = 14
FOCUS_RADIUS = 18
FEATHER = 14
DARKEN = 0.42
FIT = 0.85
MOST_ZOOM = 2.4
NOTE_LINES = 3

STEP_FIELDS = {"focus", "via", "zoom", "pause", "hold", "say"}

# --- Plan ---


@dataclass(frozen=True)
class Step:
    focus: tuple[float, float, float, float]
    via: tuple[float, float, float]
    zoom: float
    pause: float
    hold: float
    say: str | None


# A camera position is a scale and the source pixel that sits at the centre of the view.
View = tuple[float, float, float]


@dataclass(frozen=True)
class Key:
    t: float
    view: View
    snap: bool = False


# Everything that happens in the block, in seconds from its start, worked out once from the steps.
@dataclass(frozen=True)
class Plan:
    length: float
    keys: tuple[Key, ...]
    focus: tuple[tuple[float, float, tuple[float, float, float, float]], ...]
    blur: tuple[tuple[float, float], ...]
    notes: tuple[tuple[float, float, str], ...]
    sounds: tuple[Sound, ...]


def plan(steps: tuple[Step, ...], full: View) -> Plan:
    keys = [Key(0, (full[0] * 0.977, full[1], full[2])), Key(INTRO, full)]
    focus, blur, notes, sounds = [], [], [], []
    t = INTRO
    for index, step in enumerate(steps):
        last = index == len(steps) - 1
        centre = ((step.focus[0] + step.focus[2]) / 2, (step.focus[1] + step.focus[3]) / 2)
        sounds.append(Sound("click", t))
        keys += [Key(t + SNAP, step.via, True), Key(t + SNAP + step.pause, step.via)]
        sounds.append(Sound("click", t + SNAP + step.pause))
        arrive = t + 2 * SNAP + step.pause
        leave = arrive + step.hold
        keys.append(Key(arrive, (step.zoom, *centre), True))
        pushed = leave if last else leave - STILL
        closer = (step.zoom * (1 + PUSH * (pushed - arrive)), *centre)
        keys.append(Key(pushed, closer))
        focus.append((arrive, math.inf if last else leave, step.focus))
        if last:
            t = leave
            break
        keys.append(Key(leave, closer))
        back = leave + BACK
        keys += [Key(back, full), Key(back + REST, full)]
        if step.say:
            blur.append((leave - 0.05, back + 0.15))
            notes.append((leave + 0.12, back + 0.1, step.say))
            sounds += [Sound("soft", leave - 0.1), Sound("soft", back - 0.05)]
        t = back + REST
    return Plan(t, tuple(keys), tuple(focus), tuple(blur), tuple(notes), tuple(sounds))


# --- Camera ---


def snap(x: float) -> float:
    return 1 - (1 - x) ** 4


def smooth(x: float) -> float:
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


# The scale moves on a log curve, so a zoom from 1 to 2 feels as fast as one from 2 to 4.
def camera(keys: tuple[Key, ...], t: float) -> View:
    for a, b in zip(keys, keys[1:]):
        if a.t <= t <= b.t:
            u = (t - a.t) / (b.t - a.t) if b.t > a.t else 1
            u = snap(u) if b.snap else smooth(u)
            scale = math.exp(math.log(a.view[0]) + (math.log(b.view[0]) - math.log(a.view[0])) * u)
            return scale, a.view[1] + (b.view[1] - a.view[1]) * u, a.view[2] + (b.view[2] - a.view[2]) * u
    return keys[-1].view


def ramp(t: float, a: float, b: float) -> float:
    return min(1.0, max(0.0, (t - a) / (b - a)))


# --- Block ---


@dataclass(frozen=True)
class Document(Block):
    kind = "document"
    source: Path
    steps: tuple[Step, ...]

    @classmethod
    def parse(cls, data: Any, where: str, sources: Sources) -> "Document":
        data = record(data, where, {"source", "steps"})
        name = data.get("source")
        if name not in sources:
            raise CutError(f"{where}: unknown source {name}, the sources are {', '.join(sources)}")
        try:
            with Image.open(sources[name]) as image:
                width, height = image.size
        except OSError:
            raise CutError(f"{where}: source {name} is not an image") from None
        raw_steps = data.get("steps")
        if not isinstance(raw_steps, list) or not raw_steps:
            raise CutError(f"{where}: missing steps")
        steps = tuple(cls.read_step(item, f"{where}, step {position}", width, height)
                      for position, item in enumerate(raw_steps, 1))
        return cls(sources[name], steps)

    @staticmethod
    def read_step(item: Any, where: str, width: int, height: int) -> Step:
        raw = record(item, where, STEP_FIELDS)
        box = raw.get("focus")
        if not isinstance(box, list) or len(box) != 4 or not all(isinstance(v, (int, float)) for v in box):
            raise CutError(f"{where}: focus must be [left, top, right, bottom] in pixels of the image")
        left, top, right, bottom = (float(v) for v in box)
        if not (0 <= left < right <= width and 0 <= top < bottom <= height):
            raise CutError(f"{where}: focus {box} is not inside the {width}x{height} image")
        fit = min(MOST_ZOOM, WIDTH * FIT / (right - left + 2 * FOCUS_PAD))
        zoom = number(raw, "zoom", where, 0.3, MOST_ZOOM, round(fit, 2))
        centre = ((left + right) / 2, (top + bottom) / 2)
        via = raw.get("via", [round(min(1.0, zoom * 0.9), 2), (width / 2 + centre[0]) / 2, (height / 2 + centre[1]) / 2])
        if not isinstance(via, list) or len(via) != 3 or not all(isinstance(v, (int, float)) for v in via):
            raise CutError(f"{where}: via must be [scale, x, y]")
        say = raw.get("say")
        if say is not None and (not isinstance(say, str) or len(wrap(say, NOTE)) > NOTE_LINES):
            raise CutError(f"{where}: say must be a text of at most {NOTE_LINES} lines on screen")
        return Step((left, top, right, bottom), tuple(float(v) for v in via), zoom,
                    number(raw, "pause", where, 0, 1, 0.1), number(raw, "hold", where, 0.6, 6), say)

    def plan(self) -> Plan:
        with Image.open(self.source) as image:
            width, height = image.size
        return plan(self.steps, (WIDTH / width, width / 2, height / 2))

    def frames(self) -> int:
        return frames_of(self.plan().length)

    def texts(self, start: int) -> list[Text]:
        begin = seconds(start)
        return [Text(begin + a, begin + b, words, NOTE) for a, b, words in self.plan().notes]

    def sounds(self, start: int) -> list[Sound]:
        begin = seconds(start)
        return [Sound(sound.name, begin + sound.at, sound.gain) for sound in self.plan().sounds]

    def render(self, start: int, prefix: Path) -> list[Path]:
        out = prefix.with_name(f"{prefix.name}-document.mp4")
        Walk(self.source, self.plan()).write(self.frames(), out)
        return [out]


# --- Drawing ---


class Walk:
    """Draws the frames of one document block."""

    def __init__(self, source: Path, plan: Plan) -> None:
        self.source = source
        self.page = Image.open(source).convert("RGBA")
        # A view smaller than the page is drawn from a half size copy, scaling down a large
        # image straight to a third of its size leaves jagged letters.
        self.half = self.page.resize((self.page.width // 2, self.page.height // 2), Image.LANCZOS)
        self.plan = plan
        cover = self.page.convert("RGB")
        cover = cover.resize((int(cover.width * HEIGHT / cover.height), HEIGHT)).crop((0, 0, WIDTH, HEIGHT))
        self.back = ImageEnhance.Brightness(cover.filter(ImageFilter.GaussianBlur(40))).enhance(0.22)

    def view(self, scale: float, x: float, y: float) -> np.ndarray:
        page, s = (self.half, scale * 2) if scale < 0.75 else (self.page, scale)
        if page is self.half:
            x, y = x / 2, y / 2
        drawn = page.transform((WIDTH, HEIGHT), Image.AFFINE, (1 / s, 0, x - WIDTH / 2 / s, 0, 1 / s, y - CENTRE_Y / s),
                               resample=Image.BICUBIC)
        frame = self.back.copy()
        frame.paste(drawn, (0, 0), drawn)
        return np.asarray(frame, dtype=np.float32)

    def focus(self, t: float):
        for a, b, box in self.plan.focus:
            if a - 0.05 <= t < b + 0.4:
                return box, ramp(t, a - 0.05, a + 0.2)
        return None, 0.0

    def blur(self, t: float) -> float:
        return max([min(ramp(t, a, a + 0.3), 1 - ramp(t, b - 0.05, b + 0.35)) for a, b in self.plan.blur], default=0.0)

    def frame(self, index: int) -> np.ndarray:
        t = seconds(index)
        sharp = sum(self.view(*camera(self.plan.keys, max(0.0, t + d))) for d in (-1 / 90, 0, 1 / 90)) / 3
        box, strength = self.focus(t)
        whole = self.blur(t)
        if strength > 0 or whole > 0:
            small = Image.fromarray(sharp.clip(0, 255).astype(np.uint8)).resize((WIDTH // 4, HEIGHT // 4), Image.BILINEAR)
            soft = np.asarray(small.filter(ImageFilter.GaussianBlur(5)).resize((WIDTH, HEIGHT), Image.BILINEAR), dtype=np.float32)
            outside = np.zeros((HEIGHT, WIDTH), np.float32)
            if box is not None and strength > 0:
                outside = self.mask(box, *camera(self.plan.keys, t)) * strength
            weight = np.maximum(outside, whole)[..., None]
            sharp = (sharp * (1 - weight) + soft * weight) * (1 - DARKEN * weight)
        if index < 4:
            sharp = sharp * (0.5 + 0.5 * index / 4)
        return sharp

    # 1 outside the focus box and 0 inside, with soft edges, in frame pixels.
    def mask(self, box, scale: float, x: float, y: float) -> np.ndarray:
        left, top, right, bottom = box
        corners = (WIDTH / 2 + (left - FOCUS_PAD - x) * scale, CENTRE_Y + (top - FOCUS_PAD - y) * scale,
                   WIDTH / 2 + (right + FOCUS_PAD - x) * scale, CENTRE_Y + (bottom + FOCUS_PAD - y) * scale)
        mask = Image.new("L", (WIDTH, HEIGHT), 255)
        ImageDraw.Draw(mask).rounded_rectangle(corners, radius=FOCUS_RADIUS, fill=0)
        return np.asarray(mask.filter(ImageFilter.GaussianBlur(FEATHER)), dtype=np.float32) / 255

    def write(self, frames: int, out: Path) -> None:
        context = multiprocessing.get_context("spawn")
        with context.Pool(initializer=start_worker, initargs=(self.source, self.plan)) as pool, \
                frame_pipe(out, "noise=alls=6:allf=t,format=yuv420p") as pipe:
            for frame in pool.imap(draw_frame, range(frames), chunksize=4):
                pipe.write(frame)


# --- Workers ---

# Each worker process opens the document once and keeps it for every frame it draws.
worker: Walk | None = None


def start_worker(source: Path, plan: Plan) -> None:
    global worker
    worker = Walk(source, plan)


def draw_frame(index: int) -> bytes:
    assert worker is not None
    return worker.frame(index).clip(0, 255).astype(np.uint8).tobytes()
