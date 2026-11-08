"""
file: reels/mix.py
importable: Music, mix, music_file

Builds the whole sound of a reel: every stretch of speech at its place, the music under it and the
sounds of the library on top, brought to -14 LUFS at the end.

description: Mixes speech, music and sound effects into the sound track of a reel.
"""

# NOTE: The music level follows the speech by itself. Wherever someone speaks it drops to
# MUSIC_UNDER_VOICE, between the voices it rises to MUSIC_HIGH. Stretches of speech closer than
# DUCK_JOIN are joined, so the music does not swell up for a breath between two sentences.
#
# NOTE: The loudness is set in two passes, the mix is measured first and then brought to the
# target in one straight gain. A single pass of loudnorm guesses as it goes and left the first
# reel at -15.1 instead of -14, and its own two pass mode left it at -14.5.
#
# XXX: The model that writes the edit file can not hear. The level of the music and of every
# sound is only right once the editor has listened to the reel.

import json
from dataclasses import dataclass
from pathlib import Path

from reels.config import MUSIC, SOUNDS
from reels.events import Sound, Voice
from reels.fields import CutError
from reels.media import run
from reels.style import LOUDNESS, MUSIC_FADE_IN, MUSIC_FADE_OUT, MUSIC_HIGH, MUSIC_UNDER_VOICE, VOICE_GAIN

# --- Constants ---

DUCK_DOWN = 0.35
DUCK_UP = 0.3
DUCK_AFTER = 0.2
DUCK_JOIN = 0.7
RATE = 48000
TARGET = -14.0

# -1.5 dBFS as a level, the highest a sample may reach after the gain.
CEILING = 0.841

# --- Music ---


@dataclass(frozen=True)
class Music:
    path: Path
    start: float


# The stretches where someone speaks, joined when the gap between them is short.
def spoken(voices: list[Voice]) -> list[tuple[float, float]]:
    spans: list[list[float]] = []
    for voice in sorted((voice for voice in voices if voice.duck), key=lambda item: item.at):
        end = voice.at + voice.source_to - voice.source_from
        if spans and voice.at - spans[-1][1] < DUCK_JOIN:
            spans[-1][1] = max(spans[-1][1], end)
        else:
            spans.append([voice.at, end])
    return [(start, end) for start, end in spans]


# The music is fully down when a voice begins and back up a moment after it ends. ffmpeg
# evaluates this for every block of samples, max picks the stretch the time falls in.
def level(voices: list[Voice]) -> str:
    dips = [f"clip((t-{start - DUCK_DOWN:.3f})/{DUCK_DOWN},0,1)*clip(({end + DUCK_AFTER:.3f}-t)/{DUCK_UP},0,1)"
            for start, end in spoken(voices)]
    if not dips:
        return str(MUSIC_HIGH)
    deepest = dips[0]
    for dip in dips[1:]:
        deepest = f"max({deepest},{dip})"
    return f"{MUSIC_HIGH}-{MUSIC_HIGH - MUSIC_UNDER_VOICE:.3f}*{deepest}"


# --- Mix ---


def sound_file(name: str) -> Path:
    path = SOUNDS / f"{name}.wav"
    if not path.exists():
        raise CutError(f"sound {name}: no file {path.name} in the library")
    return path


def mix(voices: list[Voice], sounds: list[Sound], music: Music | None, length: float, out: Path) -> None:
    """Writes the sound track of a reel.

    Args:
        voices: Speech with times in seconds from the start of the reel.
        sounds: Library sounds with their times.
        music: The track and the second it starts from, None for a reel without music.
        length: Length of the reel in seconds.
        out: The .wav file to write.

    Raises:
        CutError: A sound name has no file in the library, or there is nothing to hear at all.
        MediaError: ffmpeg ended with an error.
    """
    inputs: list[Path] = []

    def index(path: Path) -> int:
        if path not in inputs:
            inputs.append(path)
        return inputs.index(path)

    graph: list[str] = []
    labels: list[str] = []
    for number, voice in enumerate(voices):
        span = voice.source_to - voice.source_from
        delay = round(voice.at * 1000)
        graph.append(
            f"[{index(voice.path)}:a]atrim={voice.source_from}:{voice.source_to},asetpts=PTS-STARTPTS,"
            f"aformat=sample_rates={RATE}:channel_layouts=mono,afade=t=in:d={voice.fade_in},"
            f"afade=t=out:st={span - voice.fade_out:.3f}:d={voice.fade_out},volume={voice.gain},"
            f"adelay={delay}:all=1[v{number}]")
        labels.append(f"[v{number}]")
    if voices:
        graph.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0,"
                     f"aformat=channel_layouts=stereo,volume={VOICE_GAIN}[voice]")

    if music is not None:
        graph.append(
            f"[{index(music.path)}:a]atrim={music.start}:{music.start + length},asetpts=PTS-STARTPTS,"
            f"aformat=sample_rates={RATE}:channel_layouts=stereo,volume='{level(voices)}':eval=frame,"
            f"afade=t=in:d={MUSIC_FADE_IN},afade=t=out:st={length - MUSIC_FADE_OUT:.3f}:d={MUSIC_FADE_OUT}[music]")

    effects: list[str] = []
    for number, sound in enumerate(sounds):
        graph.append(f"[{index(sound_file(sound.name))}:a]aformat=sample_rates={RATE}:channel_layouts=stereo,"
                     f"volume={sound.gain},adelay={round(sound.at * 1000)}:all=1[s{number}]")
        effects.append(f"[s{number}]")

    parts = (["[voice]"] if voices else []) + (["[music]"] if music is not None else []) + effects
    if not parts:
        raise CutError("the reel has no music, no voice and no sound, there is nothing to hear")
    # Without music nothing else lasts the whole reel, the end is padded with silence.
    graph.append(f"{''.join(parts)}amix=inputs={len(parts)}:normalize=0:duration=longest,apad,atrim=0:{length:.3f}[out]")

    args = ["ffmpeg", "-v", "error", "-y"]
    for path in inputs:
        args += ["-i", str(path)]
    raw = out.with_name(f"{out.stem}-raw.wav")
    run([*args, "-filter_complex", ";".join(graph), "-map", "[out]", "-ar", str(RATE), "-c:a", "pcm_f32le", str(raw)])
    normalize(raw, out)
    raw.unlink()


# loudnorm only measures here. Its own second pass gives up the straight gain whenever the peaks
# would pass the limit, and with a boom in the mix they always do. The gain is applied here and
# the few peaks above -1.5 dBFS are caught by a limiter. The limiter takes a little loudness
# with them, so the result is measured once more and the gain corrected by what is missing.
def normalize(raw: Path, out: Path) -> None:
    gain = TARGET - measure(raw)
    for _ in range(2):
        run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", f"volume={gain:.2f}dB,alimiter=limit={CEILING}:level=false",
             "-ar", str(RATE), str(out)])
        gain += TARGET - measure(out)


def measure(path: Path) -> float:
    output = run(["ffmpeg", "-nostats", "-i", str(path), "-af", f"loudnorm={LOUDNESS}:print_format=json", "-f", "null", "-"])
    return float(json.loads(output[output.rindex("{"):output.rindex("}") + 1])["input_i"])

def music_file(name: str) -> Path:
    path = MUSIC / name
    if not path.exists():
        raise CutError(f"music: no file {name} in the library")
    return path
