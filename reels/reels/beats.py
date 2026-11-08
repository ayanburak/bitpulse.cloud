"""
file: reels/beats.py
importable: Beats, analyse, beats

Finds the beat of a music track from the second a reel starts it, so the model that writes the
edit, which can not hear, can still put a picture change or a line on the music. The answer is
the tempo, where the first beat falls and the hits, the moments the music strikes hardest. Every
time is a second of the reel, not of the track.

    reels beats "Inspiring - The_Mountain.mp3" --from 12.7

description: Measures the tempo, the beat grid and the strongest hits of a music track.
"""

# NOTE: The beat is found from onsets, the moments new sound starts. Each short window of the
# track is turned into its frequencies and the onset strength is how much louder the frequencies
# got since the window before. A tempo is scored by how well the strength repeats after one, two,
# three and four of its beats, a real beat repeats at all of them while half or twice the tempo
# misses some. Tempos near 120 a minute, where a foot taps, are slightly preferred. The first
# beat is the offset at which a grid of that tempo lands on the most strength.
#
# NOTE: Checked against the incompetech catalog on 8 November 2026: Loopster, Miami Viceroy,
# Inspired, Jerry Five and Realizer came out within half a beat a minute of their listed tempo.
# Adding the Sun, listed at 90, came out at 120.
#
# XXX: Slow, soft tracks without drums give a weak beat. The tempo is then a guess and the
# command says so, the hits are still the music's real accents.

import math
import subprocess
from dataclasses import dataclass

import numpy as np

from reels.media import MediaError
from reels.mix import music_file

RATE = 22050
HOP = 256
WINDOW = 1024
SLOWEST = 60.0
FASTEST = 180.0
MOST_HITS = 16


@dataclass(frozen=True)
class Beats:
    tempo: float
    first: float
    clear: float
    hits: tuple[float, ...]

    @property
    def step(self) -> float:
        return 60 / self.tempo


def onsets(samples: np.ndarray) -> np.ndarray:
    frames = 1 + (len(samples) - WINDOW) // HOP
    if frames < 2:
        return np.zeros(0, np.float32)
    index = np.arange(WINDOW)[None, :] + HOP * np.arange(frames)[:, None]
    spectrum = np.log1p(np.abs(np.fft.rfft(samples[index] * np.hanning(WINDOW), axis=1)))
    flux = np.maximum(np.diff(spectrum, axis=0), 0).sum(axis=1)
    flux = np.concatenate([[0.0], flux])
    flux -= np.convolve(flux, np.ones(32) / 32, mode="same")
    return np.maximum(flux, 0) / (flux.max() or 1)


def analyse(samples: np.ndarray) -> Beats:
    """Finds the tempo, the first beat and the hits of a stretch of mono samples at RATE.

    Returns:
        The beat, with clear between 0 and 1, how well the strength repeats at that tempo.
    """
    strength = onsets(samples)
    second = RATE / HOP
    centred = strength - strength.mean()
    power = float((centred * centred).sum()) or 1.0

    # How well the strength repeats after lag frames, between whole frames by linear steps.
    def repeat(lag: float) -> float:
        whole, part = int(lag), lag - int(lag)
        if whole + 1 >= len(centred):
            return 0.0
        a = (centred[:-whole] * centred[whole:]).sum()
        b = (centred[:-(whole + 1)] * centred[whole + 1:]).sum()
        return float(a * (1 - part) + b * part) / power

    def score(tempo: float) -> float:
        step = 60 * second / tempo
        total = sum(max(repeat(k * step), 0.0) / k ** 0.5 for k in (1, 2, 3, 4) if k * step < len(centred) / 2)
        return total * math.exp(-0.5 * math.log2(tempo / 120) ** 2)

    # A coarse pass finds the tempo, a fine one around it keeps the grid from drifting off the
    # beat over the 45 seconds of a reel.
    tempo = max(np.arange(SLOWEST, FASTEST, 0.25), key=score)
    tempo = max(np.arange(tempo - 0.3, tempo + 0.3, 0.02), key=score)
    lag = 60 * second / tempo
    clear = max(repeat(lag), 0.0)
    grid = np.arange(0, len(strength), lag)
    offsets = [strength[np.minimum(np.round(grid + start).astype(int), len(strength) - 1)].sum() for start in range(int(lag) + 1)]
    first = int(np.argmax(offsets))
    peaks = [i for i in range(1, len(strength) - 1)
             if strength[i] >= strength[i - 1] and strength[i] > strength[i + 1] and strength[i] > 0.35]
    peaks.sort(key=lambda i: strength[i], reverse=True)
    hits: list[int] = []
    for i in peaks:
        if all(abs(i - j) > second * 0.4 for j in hits):
            hits.append(i)
        if len(hits) == MOST_HITS:
            break
    # A window's onset is heard at its middle.
    shift = WINDOW / 2 / RATE
    return Beats(round(60 * second / lag, 1), round(first / second + shift, 2), round(clear, 2),
                 tuple(round(i / second + shift, 2) for i in sorted(hits)))


def beats(name: str, start: float, length: float) -> Beats:
    """Reads length seconds of a library track from start and finds its beat.

    Raises:
        CutError: The track is not in the library.
        MediaError: ffmpeg could not read it.
    """
    result = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{length:.3f}", "-i", str(music_file(name)),
                             "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"], capture_output=True)
    if result.returncode != 0:
        raise MediaError(f"ffmpeg failed: {result.stderr.decode().strip()[:300]}")
    return analyse(np.frombuffer(result.stdout, np.float32))
