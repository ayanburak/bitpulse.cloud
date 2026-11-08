"""
file: reels/media.py
importable: MediaError, run, shot, black, frame_pipe, concat, finish, duration, size, loudness, sheet

Every call to ffmpeg and ffprobe goes through here. The pieces of a reel are all encoded the same
way, H.264 at 30 frames a second in yuv420p, so concat can join them without encoding again.

description: Cuts shots, writes black frames, joins pieces and measures the finished reel.
"""

# NOTE: Shots are cut by a frame count, never by a length in seconds. The first reel had a lip
# sync drift of a tenth of a second because seconds were rounded differently in every piece.
#
# XXX: The final encode caps the bit rate. Without the cap the grain made a 37 second reel
# 254 MB, Instagram would recompress it anyway and the upload would take minutes. For the same
# reason the preset is medium, slow took 22 seconds longer for a file 1 percent smaller.

import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import IO, Iterator

from reels.config import FPS, HEIGHT, MARK, MARK_SCALE, WIDTH
from reels.fields import Crop
from reels.style import LOOKS, MARK_X, MARK_Y

# --- Constants ---

# The pieces are kept at a high quality, the reel is only compressed once, at the end.
PIECE = ["-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-r", str(FPS)]
FINAL = ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "14M", "-bufsize", "28M", "-profile:v", "high",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart"]

# --- Errors ---


class MediaError(Exception):
    """Raised when ffmpeg or ffprobe fails. The message holds the first lines of its error."""


# ffmpeg names the cause in its first lines, the last ones only say that nothing was written.
def run(args: list[str]) -> str:
    """Runs ffmpeg or ffprobe and returns what it printed.

    Raises:
        MediaError: The program could not start or ended with an error.
    """
    try:
        result = subprocess.run(args, capture_output=True, text=True)
    except FileNotFoundError as error:
        raise MediaError(f"{args[0]} is not installed: {error}") from None
    if result.returncode != 0:
        raise MediaError(f"{args[0]} failed: {' '.join(result.stderr.strip().splitlines()[:4])}")
    return result.stdout + result.stderr


# --- Pieces ---


# The push grows the picture a little every frame from the centre. It is done after the scale to
# full size, so the steps of the crop are one pixel of the final frame and do not shake. The
# punch is a quick push in over the first quarter second, the same snap a still opens with.
def shot(source: Path, start: float, frames: int, crop: Crop, look: str, push: float, out: Path,
         shade: Path | None = None, punch: float = 0) -> None:
    """Cuts frames frames of source from start, crops them to 9:16 and scales them to the frame.

    Args:
        source: The video file.
        start: Second of the source the shot starts at.
        frames: Number of frames to keep.
        crop: The 9:16 window of the source to keep.
        look: A key of LOOKS.
        push: How much the picture grows per second, 0.024 is a slow push in.
        out: The piece to write.
        shade: A transparent picture laid over the shot, the darkening under narration.
        punch: How much the picture grows in the quick push in at the start, 0 for none.
    """
    chain = [f"fps={FPS}", crop.filter(), f"scale={WIDTH}:{HEIGHT}:flags=lanczos"]
    if push or punch:
        grow = f"(1+{push}*t)*(1+{punch}*(1-pow(1-min(t/0.25,1),4)))"
        chain += [f"scale=w='trunc({WIDTH}*{grow}/2)*2':h=-2:eval=frame:flags=lanczos", f"crop={WIDTH}:{HEIGHT}"]
    chain += [LOOKS[look]]
    if shade is None:
        picture = ["-vf", ",".join(chain + ["format=yuv420p"])]
    else:
        picture = ["-loop", "1", "-i", str(shade), "-filter_complex",
                   f"[0:v]{','.join(chain)}[v];[v][1:v]overlay=0:0,format=yuv420p"]
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-i", str(source), *picture,
         "-frames:v", str(frames), "-an", *PIECE, str(out)])


def black(frames: int, out: Path) -> None:
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=black:s={WIDTH}x{HEIGHT}:r={FPS}",
         "-frames:v", str(frames), *PIECE, str(out)])


# A piece drawn frame by frame in Python is written straight into ffmpeg, no frame touches the disk.
@contextmanager
def frame_pipe(out: Path, filters: str = "format=yuv420p") -> Iterator[IO[bytes]]:
    """Opens an ffmpeg process that encodes raw RGB frames written to it into a piece.

    Args:
        out: The piece to write.
        filters: ffmpeg filters applied before the encode.

    Yields:
        The input of the process. Each write is one frame of WIDTH by HEIGHT rgb24 bytes.

    Raises:
        MediaError: ffmpeg ended with an error.
    """
    process = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS),
         "-i", "-", "-vf", filters, *PIECE, str(out)],
        stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.stdin is not None
    try:
        yield process.stdin
    finally:
        process.stdin.close()
        error = process.stderr.read().decode() if process.stderr else ""
        if process.wait() != 0:
            raise MediaError(f"ffmpeg failed: {error.strip()[:300]}")


# --- Reel ---


def concat(pieces: list[Path], out: Path) -> None:
    listing = out.with_suffix(".txt")
    listing.write_text("".join(f"file '{piece}'\n" for piece in pieces))
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(out)])


def finish(picture: Path, text: Path, sound: Path, hidden: list[tuple[float, float]], out: Path) -> None:
    """Lays the text layer and the logo over the picture, adds the mixed sound and makes the final file.

    Args:
        picture: The joined picture pieces.
        text: The transparent text layer.
        sound: The mixed sound track.
        hidden: Stretches in seconds where the logo is not shown, the closing card has its own.
        out: The reel to write.
    """
    shown = "1" if not hidden else "not(" + "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in hidden) + ")"
    graph = (f"[3]scale=iw/{MARK_SCALE}:-1:flags=lanczos[m];[0][1]overlay=0:0:shortest=1[t];"
             f"[t][m]overlay={MARK_X}:{MARK_Y}:shortest=1:enable='{shown}',format=yuv420p[v]")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(picture), "-i", str(text), "-i", str(sound), "-loop", "1", "-i", str(MARK),
         "-filter_complex", graph, "-map", "[v]", "-map", "2:a", *FINAL, "-shortest", str(out)])


# --- Measuring ---


def size(path: Path) -> tuple[int, int]:
    width, height = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                         "-of", "csv=p=0", str(path)]).strip().split(",")[:2]
    return int(width), int(height)


def duration(path: Path) -> float:
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]).strip())


# ebur128 prints its summary at the end, the integrated loudness is the line that starts with I:.
def loudness(path: Path) -> float:
    output = run(["ffmpeg", "-nostats", "-i", str(path), "-af", "ebur128=framelog=quiet", "-f", "null", "-"])
    lines = [line for line in output.splitlines() if line.strip().startswith("I:")]
    return float(lines[-1].split()[1])


# Two frames a second, small enough to look at in one image, with the time on every frame.
def sheet(path: Path, out: Path, columns: int = 13) -> None:
    frames = int(duration(path) * 2) + 1
    rows = -(-frames // columns)
    run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-vf",
         f"fps=2,scale=150:-1,drawtext=text='%{{pts\\:hms}}':x=3:y=3:fontsize=11:fontcolor=yellow:box=1:boxcolor=black,"
         f"tile={columns}x{rows}", "-frames:v", "1", str(out)])
