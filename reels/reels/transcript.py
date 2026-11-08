"""
file: reels/transcript.py
importable: Transcript, transcribe, load_transcript

A transcript is every word a source says with the second it starts and ends, plus the quiet
stretches of its sound. The edit file can then name a voice by its words, and the engine finds
where to cut it so no word is clipped.

    words = load_transcript(path)
    first, last = words.find("We're dealing with them now. ... very badly.")
    start, end = words.cut_before(first), words.cut_after(last)

description: Makes word timed transcripts and finds clean cut points in them.
"""

# NOTE: Whisper's word times are good enough to find a word, not to cut on. Its end of a word is
# often a little early, so a cut there would clip the last sound. The cut is placed by the sound
# itself: in a quiet stretch next to the word, found from the loudness in 10 ms steps.
#
# NOTE: The small model mishears names now and then, it wrote "The red will never" for "Iran will
# never". A phrase that is not found word for word is looked for by likeness, and the match is
# reported so the editor knows the transcript and the screen differ there.
#
# NOTE: What counts as quiet is worked out per source, from its own floor and its loud parts. A
# speech on an airfield never gets as quiet as one in a hall, a fixed threshold found no pause
# at all in the Palm Beach recording.
#
# XXX: The model is loaded from the work folder only, never fetched again. HF_HOME is pointed
# there before faster_whisper is imported, otherwise the download library opens its own folder
# in ~/.cache/huggingface.

import difflib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from reels.config import WORK
from reels.fields import CutError
from reels.media import MediaError

# --- Constants ---

MODELS = WORK / "models"
MODEL = "small.en"
RATE = 16000
STEP = 0.01
WINDOW = 0.02

# A pause this long is a clean cut. A shorter dip under the threshold is still taken, but the
# cut is reported as tight so the editor listens to it.
CLEAN_PAUSE = 0.12
SHORT_PAUSE = 0.03
QUIET_SHARE = 0.4

# A fast speaker leaves pauses that never reach the source's quiet, "happen. Iran" in the first
# reel dropped 15 dB for 50 ms. A dip this far under the loudest point near it counts as well.
LOCAL_DROP = 12

# How alike a phrase and a stretch of the transcript must be to count as the same words.
LIKENESS = 0.75

# Two words closer than this were said in one breath.
SAME_BREATH = 0.1

# How far from a word's time a cut may move. Whisper put the start of "if" in the first reel
# 0.4 s before it was spoken, so the search reaches half a second, never into the next word.
# MARGIN is the quiet kept next to the word.
REACH = 0.5
MARGIN = 0.05

# --- Transcript ---


@dataclass(frozen=True)
class Word:
    start: float
    end: float
    text: str


@dataclass
class Transcript:
    words: list[Word]
    levels: np.ndarray
    quiet: float
    warnings: list[str]

    def find(self, phrase: str, near: float | None = None) -> tuple[int, int]:
        """Finds a phrase and returns the index of its first and last word.

        The phrase may skip a middle part with "...", then it runs from the first part to the
        first match of the last part after it. Case and punctuation do not count.

        Args:
            phrase: The words as they are spoken.
            near: A second the phrase is close to, needed when it is said more than once.

        Raises:
            CutError: The phrase is not found, or found more than once without near.
        """
        parts = [tokens(part) for part in phrase.split("...")]
        if any(not part for part in parts):
            raise CutError(f"words {phrase!r}: an empty part around ...")
        keys = [key(word.text) for word in self.words]
        starts = self.places(keys, parts[0], 0, phrase)
        if near is not None:
            starts = sorted(starts, key=lambda i: abs(self.words[i[0]].start - near))[:1]
        if len(starts) > 1:
            places = ", ".join(f"{self.words[i].start:.1f}" for i, _ in starts)
            raise CutError(f"words {phrase!r}: said {len(starts)} times, at {places}, add near")
        first, last = starts[0]
        for part in parts[1:]:
            last = self.places(keys, part, last + 1, phrase)[0][1]
        return first, last

    # Every place the words are said, as first and last index, from index on. Word for word
    # matches come first. Without one the most alike stretch of the same length is taken.
    def places(self, keys: list[str], part: list[str], start: int, phrase: str) -> list[tuple[int, int]]:
        size = len(part)
        exact = [(i, i + size - 1) for i in range(start, len(keys) - size + 1) if keys[i:i + size] == part]
        if exact:
            return exact
        # A misheard name may take more or fewer words than the real one, Iran became The red.
        wanted = " ".join(part)
        scored = [(difflib.SequenceMatcher(None, " ".join(keys[i:i + width]), wanted).ratio(), i, width)
                  for width in range(max(1, size - 2), size + 3) for i in range(start, len(keys) - width + 1)]
        if not scored or max(scored)[0] < LIKENESS:
            raise CutError(f"words {phrase!r}: {wanted!r} is not in the transcript")
        score, i, width = max(scored)
        i, width = self.widen(keys, part, i, width, score)
        heard = " ".join(word.text for word in self.words[i:i + width])
        self.warnings.append(f"{wanted!r} matched {heard!r} in the transcript, {score:.0%} alike")
        return [(i, i + width - 1)]

    # The best stretch may leave out half of a misheard name: red will never instead of The red
    # will never. A name heard as two words is said in one breath, so where an edge word differs
    # from the phrase, the word right next to it in time is taken in as well.
    def widen(self, keys: list[str], part: list[str], i: int, width: int, score: float) -> tuple[int, int]:
        if keys[i] != part[0] and i > 0 and self.words[i].start - self.words[i - 1].end < SAME_BREATH:
            i, width = i - 1, width + 1
        end = i + width - 1
        if keys[end] != part[-1] and end + 1 < len(keys) and self.words[end + 1].start - self.words[end].end < SAME_BREATH:
            width += 1
        return i, width

    def align(self, first: int, last: int, line: str) -> tuple[int, int]:
        """Returns the first and last word of a screen line inside the words first to last.

        The line is matched by likeness, so it may spell a name the transcript got wrong.

        Raises:
            CutError: No stretch of the voice is alike enough to the line.
        """
        wanted = tokens(line)
        keys = [key(word.text) for word in self.words[first:last + 1]]
        best = (0.0, 0, 0)
        for size in range(max(1, len(wanted) - 2), len(wanted) + 3):
            for i in range(0, len(keys) - size + 1):
                score = difflib.SequenceMatcher(None, " ".join(keys[i:i + size]), " ".join(wanted)).ratio()
                best = max(best, (score, i, size))
        score, i, size = best
        if score < LIKENESS:
            raise CutError(f"line {line!r}: not spoken in this voice")
        return first + i, first + i + size - 1

    def cut_before(self, index: int) -> float:
        """Returns the second to start a cut at, in the quiet just before word index."""
        word = self.words[index]
        # Whisper's end of the word before may be late as well, by 0.15 s on "happen".
        earliest = max(self.words[index - 1].start, self.words[index - 1].end - REACH / 2) if index else 0.0
        low, high = max(earliest, word.start - REACH), min(word.end, word.start + REACH)
        pause = self.pause(low, high, last=True)
        if pause is None:
            raise CutError(f"no pause before {word.text!r} at {word.start:.2f}, start on another word")
        return max(0.0, pause[1] - MARGIN)

    def cut_after(self, index: int) -> float:
        """Returns the second to end a cut at, in the quiet just after word index."""
        word = self.words[index]
        if index + 1 < len(self.words):
            after = self.words[index + 1]
            high = min(after.end, after.start + REACH)
        else:
            high = word.end + REACH
        # Never before the word's end: a dip inside a word, between bad and ly, sounded like a
        # clean pause and cut the first reel to "very ba-".
        pause = self.pause(word.end, high, last=False)
        if pause is None:
            raise CutError(f"no pause after {word.text!r} at {word.end:.2f}, end on another word")
        return pause[0] + MARGIN

    # The first, or with last the latest, quiet run between low and high. A run of CLEAN_PAUSE
    # wins. Without one the quietest short dip is taken and a warning is kept.
    def pause(self, low: float, high: float, last: bool) -> tuple[float, float] | None:
        a, b = int(low / STEP), int(high / STEP) + 1
        if b <= a:
            return None
        quiet = self.levels[a:b] < max(self.quiet, float(self.levels[a:b].max()) - LOCAL_DROP)
        runs, start = [], None
        for i, flag in enumerate(list(quiet) + [False]):
            if flag and start is None:
                start = i
            elif not flag and start is not None:
                runs.append(((a + start) * STEP, (a + i) * STEP))
                start = None
        clean = [run for run in runs if run[1] - run[0] >= CLEAN_PAUSE]
        if clean:
            return clean[-1] if last else clean[0]
        short = [run for run in runs if run[1] - run[0] >= SHORT_PAUSE]
        if not short:
            return None
        run = min(short, key=lambda r: self.levels[int(r[0] / STEP):int(r[1] / STEP) + 1].mean())
        self.warnings.append(f"tight cut at {run[0]:.2f}, only {(run[1] - run[0]) * 1000:.0f} ms of quiet, listen to it")
        return run


# Words match without case and without anything but letters and digits, so B-2, b2 and "B2,"
# are the same word.
def key(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def tokens(phrase: str) -> list[str]:
    return [k for k in (key(part) for part in phrase.split()) if k]


# --- Making ---


def decode(path: Path) -> np.ndarray:
    result = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"],
                            capture_output=True)
    if result.returncode != 0:
        raise MediaError(f"ffmpeg could not read the sound of {path.name}: {result.stderr.decode().strip()[:200]}")
    return np.frombuffer(result.stdout, np.float32)


# Loudness in dB for every 10 ms, each over a 20 ms window.
def loudness_steps(audio: np.ndarray) -> np.ndarray:
    hop, width = int(STEP * RATE), int(WINDOW * RATE)
    count = max(0, (len(audio) - width) // hop)
    frames = np.lib.stride_tricks.sliding_window_view(audio, width)[::hop][:count]
    return 20 * np.log10(np.sqrt((frames ** 2).mean(axis=1)) + 1e-6)


def threshold(levels: np.ndarray) -> float:
    floor, loud = np.percentile(levels, 10), np.percentile(levels, 90)
    return float(floor + QUIET_SHARE * (loud - floor))


def transcribe(path: Path) -> Transcript:
    """Writes down every word a source says with its times.

    Args:
        path: A video or sound file.

    Raises:
        MediaError: ffmpeg could not read its sound.
    """
    os.environ["HF_HOME"] = str(MODELS / "hf")
    from faster_whisper import WhisperModel  # slow to import, only needed here

    audio = decode(path)
    model = WhisperModel(MODEL, device="cpu", compute_type="int8", download_root=str(MODELS), local_files_only=True)
    segments, _ = model.transcribe(audio, word_timestamps=True, vad_filter=True)
    words = [Word(round(w.start, 2), round(w.end, 2), w.word.strip()) for s in segments for w in s.words or []]
    levels = loudness_steps(audio)
    return Transcript(words, levels, threshold(levels), [])


# --- Files ---

# A transcript is saved twice: as JSON for the engine and as plain text, one sentence per line
# with its second, for a model or a person to read.


def save(transcript: Transcript, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"quiet": round(transcript.quiet, 2), "words": [[w.start, w.end, w.text] for w in transcript.words],
            "levels": [round(float(v), 1) for v in transcript.levels]}
    path.write_text(json.dumps(data, separators=(",", ":")))
    readable = path.with_suffix(".txt")
    readable.write_text(sentences(transcript.words))
    return readable


def sentences(words: list[Word]) -> str:
    lines, current = [], []
    for word in words:
        current.append(word)
        if word.text.endswith((".", "?", "!")):
            lines.append(f"[{current[0].start:7.2f}] {' '.join(w.text for w in current)}")
            current = []
    if current:
        lines.append(f"[{current[0].start:7.2f}] {' '.join(w.text for w in current)}")
    return "\n".join(lines) + "\n"


def load_transcript(path: Path) -> Transcript:
    """Reads a transcript saved by reels transcript.

    Raises:
        CutError: There is no transcript at path.
    """
    if not path.exists():
        raise CutError(f"no transcript {path.name}, run reels transcript first")
    data = json.loads(path.read_text())
    words = [Word(a, b, text) for a, b, text in data["words"]]
    return Transcript(words, np.array(data["levels"], np.float32), data["quiet"], [])
