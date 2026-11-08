"""
file: reels/blocks/montage.py
importable: Montage

Pictures under the music with nobody speaking, a goal, a crowd, a stadium at night. Each shot
is a video clip or a photograph with its own length, and the cuts do not wait for any text. A
montage may carry a few lines of narration like a card, the pictures are then shaded and the
lines sit in the lower third.

    montage:
      shots:
        - {source: boot, from: 41.2, seconds: 1.4, sound: 0.7}
        - {source: c4, focus: [750, 275, 2950, 4575], to: [750, 3750, 2750, 4600], seconds: 2.2, snap: true}
      lines: ["26 goals", "in 31 appearances."]
      reveal: [0.3, 0.9]

sound plays the clip's own sound at that gain, on top of the music, which keeps its level.
snap opens a shot with the quick push in of a card's pictures, without it the cut is plain.

description: A block of real pictures under the music, cut by their own lengths.
"""

# NOTE: The lines are timed from the montage's first frame and stay until just before its end,
# the same way as on a card. They never move with the cuts.
#
# NOTE: A clip's sound starts a little before its picture and ends a little after, with fades as
# long as that overlap, so two clips' sounds cross instead of meeting in a hard cut. The Messi
# reel without music changed stadium every five seconds and sounded broken at every cut.
#
# XXX: The model can not hear what a commentator says in a clip. When the clip's source has a
# transcript, a cut through a word and commentary under on screen lines are warned about. The
# Messi reel cut "And it is Lionel Messi" in the middle and ran "what a disaster" under "he set
# up two goals".

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from reels.blocks.base import Block, Sources, frames_of, read_sounds, seconds
from reels.events import Sound, Text, Voice
from reels.fields import CutError, number, record
from reels.style import CARD, CARD_OVER, CARD_STEP
from reels.text import wrap
from reels.visual import FIELDS, Clip, Visual, read_visual

MOST_SHOTS = 12
MOST_LINES = 4
SHORTEST = 0.3
LEAVE_EARLY = 0.05
# Half of the crossing of two clips' sounds, each reaches this far past its picture.
CROSS = 0.25


@dataclass(frozen=True)
class Shot:
    visual: Visual
    frames: int
    snap: bool
    sound: float


@dataclass(frozen=True)
class Montage(Block):
    kind = "montage"
    shots: tuple[Shot, ...]
    lines: tuple[str, ...]
    reveal: tuple[float, ...]
    effects: tuple[Sound, ...]

    @classmethod
    def parse(cls, data: Any, where: str, sources: Sources) -> "Montage":
        data = record(data, where, {"shots", "lines", "reveal", "sounds"})
        items = data.get("shots")
        if not isinstance(items, list) or not 1 <= len(items) <= MOST_SHOTS:
            raise CutError(f"{where}: shots must be a list of 1 to {MOST_SHOTS} shots")
        shots = []
        for position, item in enumerate(items, 1):
            at = f"{where}, shot {position}"
            raw = record(item, at, FIELDS | {"seconds", "snap", "sound"})
            visual = read_visual({key: raw[key] for key in FIELDS & raw.keys()}, at, sources, "speech")
            snap = raw.get("snap", False)
            if not isinstance(snap, bool):
                raise CutError(f"{at}: snap is true or false")
            sound = number(raw, "sound", at, 0, 4, 0)
            if sound and not isinstance(visual, Clip):
                raise CutError(f"{at}: sound is for a video clip, a photograph has none")
            shots.append(Shot(visual, frames_of(number(raw, "seconds", at, SHORTEST, 10)), snap, sound))
        length = seconds(sum(shot.frames for shot in shots))
        cls.listen(shots, bool(data.get("lines")), where, sources)
        lines = data.get("lines", [])
        if not isinstance(lines, list) or len(lines) > MOST_LINES or not all(isinstance(line, str) and line.strip() for line in lines):
            raise CutError(f"{where}: lines must be a list of at most {MOST_LINES} texts")
        for line in lines:
            if len(wrap(line, CARD)) > 1:
                raise CutError(f"{where}: the line {line!r} is wider than the screen, split it into two lines")
        reveal = data.get("reveal", [0.3 + 0.5 * index for index in range(len(lines))])
        if not isinstance(reveal, list) or len(reveal) != len(lines):
            raise CutError(f"{where}: reveal needs one second for every line")
        times = tuple(number({"reveal": value}, "reveal", where, 0, length - 0.3) for value in reveal)
        return cls(tuple(shots), tuple(line.strip() for line in lines), times, read_sounds(data.get("sounds"), where, length))

    # What the commentators say in the clips, read from their sources' transcripts.
    @staticmethod
    def listen(shots: list[Shot], lines: bool, where: str, sources: Sources) -> None:
        for position, shot in enumerate(shots, 1):
            clip = shot.visual
            if not shot.sound or not isinstance(clip, Clip):
                continue
            if not (sources.work / "transcripts" / f"{clip.source.stem}.json").exists():
                continue
            begin, end = clip.start, clip.start + seconds(shot.frames)
            words = sources.transcript(clip.source).words
            for edge in (begin, end):
                cut = [word.text.strip() for word in words if word.start < edge < word.end]
                if cut:
                    sources.warnings.append(f"{where}, shot {position}: the cut at {edge:.1f} s of {clip.source.name} goes "
                                            f"through the word {cut[0]!r}, move it to a pause")
            heard = [word.text.strip() for word in words if begin < word.start and word.end < end]
            if lines and heard:
                sources.warnings.append(f"{where}, shot {position}: commentary under the lines, "
                                        f"\"{' '.join(heard)}\", pick a moment without it or lower its sound")

    def frames(self) -> int:
        return sum(shot.frames for shot in self.shots)

    def render(self, start: int, prefix: Path) -> list[Path]:
        pieces = []
        for position, shot in enumerate(self.shots, 1):
            out = prefix.with_name(f"{prefix.name}-montage{position}.mp4")
            shot.visual.render(shot.frames, out, shaded=bool(self.lines), snapped=shot.snap)
            pieces.append(out)
        return pieces

    def texts(self, start: int) -> list[Text]:
        begin, end = seconds(start), self.end(start) - LEAVE_EARLY
        middle = (len(self.lines) - 1) / 2
        return [Text(begin + reveal, end, line, CARD_OVER, round(CARD_OVER.y + (index - middle) * CARD_STEP))
                for index, (line, reveal) in enumerate(zip(self.lines, self.reveal))]

    # A clip's own sound reaches CROSS past both ends of its picture and fades over that much, so
    # it crosses the sound before and after. It can not reach back past the reel's or the source's start.
    def voices(self, start: int) -> list[Voice]:
        found, frame = [], start
        for shot in self.shots:
            if shot.sound and isinstance(shot.visual, Clip):
                span = seconds(shot.frames)
                early = min(CROSS, seconds(frame), shot.visual.start)
                found.append(Voice(shot.visual.source, shot.visual.start - early, shot.visual.start + span + CROSS,
                                   seconds(frame) - early, 2 * early or 0.05, 2 * CROSS, shot.sound, duck=False))
            frame += shot.frames
        return found

    def sounds(self, start: int) -> list[Sound]:
        return [Sound(sound.name, seconds(start) + sound.at, sound.gain) for sound in self.effects]
