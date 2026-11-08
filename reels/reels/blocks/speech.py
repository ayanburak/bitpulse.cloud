"""
file: reels/blocks/speech.py
importable: Speech

Someone speaks, and one or more shots play under the voice. A shot is either the speaker's own
picture, sync, cut from the same second as the voice so the lips match, or other footage laid
under the words, for example a bomber while the speaker says B-2. The block is as long as the
voice, minus a prelap, the part of the voice that already starts under the block before it.

The voice is named by its words, and the engine cuts it in the quiet around them:

    speech:
      voice: {source: kennedy, words: "If we didn't go in ... a year ago"}
      shots:
        - {source: b2, from: 0.3, until: "B-2", crop: "405:720:438:0", push: 0.024}
        - {sync: true, crop: "484:860:688:0"}
      lines: ["If we didn't go in with those beautiful", "B-2 bombers a little more than a year ago,"]

A shot with until ends where that word begins. A shot from a photograph takes focus and to
instead of from and crop, the camera moves over it the way it does under a card. The lines are what the screen shows, spelled
right even where the transcript misheard, and each is timed to the words it matches. Without
lines the words themselves are shown, one sentence at a time.

A voice can also be given in seconds of its source, from and to, and lines as [from, to, words]
in the same seconds. The edit of the first reel is written that way.

shade: true darkens the lower part of every shot the way a montage with lines does. It is meant
for a voice that runs straight into a montage with lines, the darkening is then already there
when our text comes in instead of dropping in with it. A shaded photograph also moves its
subject up, as it does under a card.

description: A block where a voice plays over the speaker or over footage tied to the words.
"""

# NOTE: Only the last shot may leave out its length, it takes what is left of the block. A shot
# without crop is cut from the middle of its source, which suits a speaker at a podium.

#
# NOTE: tail keeps a moment of sound after the last word, applause or a room going quiet. It is
# added after the cut, so it may hold the start of the next sentence. The editor listens to it.

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from reels.blocks.base import Block, Sources, frames_of, seconds
from reels.events import Text, Voice
from reels.fields import CutError, centre, crop, number, record, text
from reels.media import MediaError, size
from reels.style import LOOKS, QUOTE
from reels.text import wrap
from reels.transcript import Transcript
from reels.visual import FIELDS, Clip, Visual, read_visual

# --- Fields ---

VOICE_FIELDS = {"source", "words", "near", "from", "to", "tail", "prelap", "fade_in", "fade_out", "gain"}
SHOT_FIELDS = FIELDS | {"frames", "until", "sync"}
LONGEST = 600.0

# A screen line shows a little after its last word and gives way just before the next line.
LINE_AFTER = 0.15
LINE_GAP = 0.04

# A gap shorter than this between two lines would make the text blink, the first line stays up.
LINE_HOLD = 0.7
LINE_ROWS = 2


@dataclass(frozen=True)
class Shot:
    visual: Visual
    frames: int


@dataclass(frozen=True)
class Line:
    start: float
    end: float
    words: str


# The words of a voice in its transcript, when the voice was given by its words.
@dataclass(frozen=True)
class Spoken:
    transcript: Transcript
    first: int
    last: int


def source(sources: Sources, name: Any, where: str) -> Path:
    if name not in sources:
        raise CutError(f"{where}: unknown source {name}, the sources are {', '.join(sources)}")
    return sources[name]


# --- Block ---


@dataclass(frozen=True)
class Speech(Block):
    kind = "speech"
    voice: Voice
    prelap: float
    shots: tuple[Shot, ...]
    lines: tuple[Line, ...]
    shade: bool = False

    @classmethod
    def parse(cls, data: Any, where: str, sources: Sources) -> "Speech":
        data = record(data, where, {"voice", "shots", "lines", "shade"})
        shade = data.get("shade", False)
        if not isinstance(shade, bool):
            raise CutError(f"{where}: shade is true or false")
        at = f"{where}, voice"
        raw = record(data.get("voice"), at, VOICE_FIELDS)
        path = source(sources, raw.get("source"), at)
        spoken, start, end = cls.read_span(raw, at, path, sources)
        end += number(raw, "tail", at, 0, 3, 0)
        prelap = number(raw, "prelap", at, 0, (end - start) / 2, 0)
        voice = Voice(path, start, end, 0, number(raw, "fade_in", at, 0, 1, 0.04),
                      number(raw, "fade_out", at, 0, 2, 0.06), number(raw, "gain", at, 0.1, 4, 1))
        total = frames_of(end - start - prelap)
        shots = cls.read_shots(data.get("shots"), where, sources, voice, prelap, total, spoken)
        lines = cls.read_lines(data.get("lines"), where, voice, spoken, raw.get("words"))
        if spoken:
            sources.note(where, spoken.transcript)
        return cls(voice, prelap, shots, lines, shade)

    # Either words, cut in the quiet around them, or from and to in seconds.
    @staticmethod
    def read_span(raw: dict, at: str, path: Path, sources: Sources) -> tuple[Spoken | None, float, float]:
        if "words" in raw:
            if "from" in raw or "to" in raw:
                raise CutError(f"{at}: give either words or from and to, not both")
            transcript = sources.transcript(path)
            near = number(raw, "near", at, 0, 1e6) if "near" in raw else None
            first, last = transcript.find(text(raw, "words", at), near)
            return Spoken(transcript, first, last), transcript.cut_before(first), transcript.cut_after(last)
        start = number(raw, "from", at, 0, 1e6)
        return None, start, number(raw, "to", at, start + 0.5, start + LONGEST)

    # Shots are laid one after the other from the block's first frame. A sync shot works out its
    # own start, the voice second that plays at its first frame.
    @staticmethod
    def read_shots(value: Any, where: str, sources: Sources, voice: Voice, prelap: float, total: int,
                   spoken: Spoken | None) -> tuple[Shot, ...]:
        if not isinstance(value, list) or not value:
            raise CutError(f"{where}: missing shots")
        shots: list[Shot] = []
        used = 0
        for position, item in enumerate(value, 1):
            at = f"{where}, shot {position}"
            raw = record(item, at, SHOT_FIELDS)
            last = position == len(value)
            length = Speech.shot_length(raw, at, voice, prelap, total, used, spoken, last)
            if length <= 0 or used + length > total:
                raise CutError(f"{at}: the shots run past the voice, the block has {total} frames")
            if raw.get("sync"):
                visual = Speech.sync_clip(raw, at, voice, voice.source_from + prelap + seconds(used))
            else:
                visual = read_visual({key: raw[key] for key in FIELDS & raw.keys()}, at, sources, "archive")
            shots.append(Shot(visual, length))
            used += length
        if used != total:
            raise CutError(f"{where}: the shots fill {used} of the block's {total} frames")
        return tuple(shots)

    # A sync shot is the speaker's own video from the second the voice is at.
    @staticmethod
    def sync_clip(raw: dict, at: str, voice: Voice, start: float) -> Clip:
        if {"source", "from", "focus", "to"} & raw.keys():
            raise CutError(f"{at}: a sync shot takes its source and start from the voice")
        look = raw.get("look", "speech")
        if look not in LOOKS:
            raise CutError(f"{at}: unknown look {look}, the looks are {', '.join(LOOKS)}")
        if "crop" in raw:
            window = crop(raw["crop"], at)
        else:
            try:
                window = centre(*size(voice.path))
            except MediaError:
                raise CutError(f"{at}: could not read the size of {voice.path.name} for a centre crop, give crop") from None
        return Clip(voice.path, start, window, look, number(raw, "push", at, 0, 0.2, 0))

    # until puts the cut on the start of a word, so the picture changes as the word is heard.
    @staticmethod
    def shot_length(raw: dict, at: str, voice: Voice, prelap: float, total: int, used: int,
                    spoken: Spoken | None, last: bool) -> int:
        if "frames" in raw and "until" in raw:
            raise CutError(f"{at}: give either frames or until, not both")
        if "frames" in raw:
            return int(number(raw, "frames", at, 1, total))
        if "until" in raw:
            if spoken is None:
                raise CutError(f"{at}: until needs a voice given by its words")
            word, _ = spoken.transcript.align(spoken.first, spoken.last, text(raw, "until", at))
            return frames_of(spoken.transcript.cut_before(word) - voice.source_from - prelap) - used
        if not last:
            raise CutError(f"{at}: missing frames or until, only the last shot may leave them out")
        return total - used

    @staticmethod
    def read_lines(value: Any, where: str, voice: Voice, spoken: Spoken | None, words: Any) -> tuple[Line, ...]:
        if value is None:
            if spoken is None or "..." in words:
                raise CutError(f"{where}: missing lines, they can only be left out when the words are given whole")
            value = [part for part in re.split(r"(?<=[.?!])\s+", words.strip()) if part]
        if not isinstance(value, list):
            raise CutError(f"{where}: lines must be a list")
        lines: list[Line] = []
        for position, item in enumerate(value, 1):
            at = f"{where}, line {position}"
            if isinstance(item, str):
                if spoken is None:
                    raise CutError(f"{at}: a line without times needs a voice given by its words")
                first, last = spoken.transcript.align(spoken.first, spoken.last, item)
                start = max(voice.source_from, spoken.transcript.words[first].start)
                end = min(voice.source_to, spoken.transcript.words[last].end + LINE_AFTER)
                line = Line(start, end, item.strip())
            elif isinstance(item, list) and len(item) == 3:
                raw = {"from": item[0], "to": item[1], "words": item[2]}
                start = number(raw, "from", at, voice.source_from, voice.source_to)
                line = Line(start, number(raw, "to", at, start + 0.2, voice.source_to), text(raw, "words", at))
            else:
                raise CutError(f"{at}: a line is its words, or [from, to, words]")
            if len(wrap(line.words, QUOTE)) > LINE_ROWS:
                raise CutError(f"{at}: {line.words!r} takes more than {LINE_ROWS} rows on screen, split it")
            lines.append(line)
        return tuple(Speech.join(line, after) for line, after in zip(lines, lines[1:] + [None]))

    # A line never overlaps the next one, whatever the transcript's times say, and stays up until
    # the next one when the gap between them is short.
    @staticmethod
    def join(line: Line, after: Line | None) -> Line:
        if after is None:
            return line
        end = after.start - LINE_GAP if after.start - line.end < LINE_HOLD else line.end
        return Line(line.start, min(end, after.start - LINE_GAP), line.words)

    def frames(self) -> int:
        return sum(item.frames for item in self.shots)

    def render(self, start: int, prefix: Path) -> list[Path]:
        pieces = []
        for position, item in enumerate(self.shots, 1):
            out = prefix.with_name(f"{prefix.name}-shot{position}.mp4")
            item.visual.render(item.frames, out, shaded=self.shade, snapped=False)
            pieces.append(out)
        return pieces

    # The voice starts prelap seconds before the block, so every voice second maps to the reel
    # by the same offset.
    def offset(self, start: int) -> float:
        return seconds(start) - self.prelap - self.voice.source_from

    def texts(self, start: int) -> list[Text]:
        offset = self.offset(start)
        return [Text(line.start + offset, line.end + offset, line.words, QUOTE) for line in self.lines]

    def voices(self, start: int) -> list[Voice]:
        return [Voice(self.voice.path, self.voice.source_from, self.voice.source_to, seconds(start) - self.prelap,
                      self.voice.fade_in, self.voice.fade_out, self.voice.gain)]
