"""
file: tests/test_beats.py
importable: nothing, pytest loads this file

description: Checks the beat finder on a click track whose beat is known.
"""

import numpy as np
import pytest

from reels.beats import RATE, analyse


# Clicks at a tempo from a first second, every fourth one twice as loud, under a little noise.
def clicks(tempo: float = 120, first: float = 0.3, length: float = 20) -> np.ndarray:
    samples = np.random.default_rng(1).normal(0, 0.01, int(RATE * length)).astype(np.float32)
    tone = np.sin(np.arange(600) * 2 * np.pi * 900 / RATE) * np.exp(-np.arange(600) / 120)
    for n, at in enumerate(np.arange(first, length - 0.1, 60 / tempo)):
        start = int(at * RATE)
        samples[start:start + 600] += tone * (1.0 if n % 4 == 0 else 0.5)
    return samples


@pytest.mark.parametrize("tempo, first", [(120, 0.3), (96, 0.7), (140, 0.1)])
def test_beats_finds_the_tempo_the_first_beat_and_the_accents(tempo, first):
    found = analyse(clicks(tempo, first))
    step = 60 / tempo
    assert found.tempo == pytest.approx(tempo, abs=1)
    assert found.first == pytest.approx(first % step, abs=0.03)
    assert found.clear > 0.5
    assert all(abs((hit - first + step / 2) % step - step / 2) < 0.03 for hit in found.hits)
