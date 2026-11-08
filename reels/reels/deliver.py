"""
file: reels/deliver.py
importable: deliver, recent, clean

Puts a finished reel where the editor posts from, next to the story's other social files, with
its caption, and notes its structure and music so the next reel can be made different. The edit
file is kept in records/cuts, the story's raw material is thrown away by clean once the editor
has approved the reel.

description: Hands a rendered reel over to the site's social files and records what it used.
"""

# NOTE: The caption is the Instagram caption of the story's post, from npm run social, with its
# image credit line replaced by the credits of the footage and the music. The story's facts and
# wording stay the ones that were checked for the post.

import csv
import re
import shutil
from datetime import datetime
from pathlib import Path

import yaml

from reels.config import MUSIC, ROOT, SITE
from reels.cut import Cut
from reels.fields import CutError

SOCIAL = SITE / "social-posts"
HISTORY = ROOT / "records" / "history.csv"
CUTS = ROOT / "records" / "cuts"
TRACKS = MUSIC / "tracks.yaml"


def music_credit(name: str) -> str:
    if TRACKS.exists():
        track = (yaml.safe_load(TRACKS.read_text()) or {}).get(name) or {}
        if track.get("credit"):
            return track["credit"]
    return f'"{Path(name).stem}"'


def deliver(cut: Cut, edit: Path) -> Path:
    """Copies the reel and writes its caption into the story's social folder.

    Raises:
        CutError: The reel is not rendered, the post was never made, or the edit has no credits.
    """
    reel = cut.work / "reel.mp4"
    folder = SOCIAL / cut.story
    caption = folder / "caption.txt"
    if not reel.exists():
        raise CutError("no reel.mp4, run reels render first")
    if not caption.exists():
        raise CutError(f"no {caption}, the post is made by npm run social in the site first")
    if not cut.credits:
        raise CutError("credits: missing, name the owners of the footage")
    credits = f"Video: {', '.join(cut.credits)}." + (f" Music: {music_credit(cut.music.path.name)}." if cut.music else "")
    text = re.sub(r"(?m)^Images?: .*?\.(?= Every claim)", credits, caption.read_text())
    if credits not in text:
        text = text.rstrip("\n") + f"\n\n{credits}\n"
    shutil.copy(reel, folder / "reel.mp4")
    (folder / "reel.txt").write_text(text)
    CUTS.mkdir(parents=True, exist_ok=True)
    shutil.copy(edit, CUTS / f"{cut.story}.yaml")
    remember(cut)
    return folder / "reel.mp4"


def remember(cut: Cut) -> None:
    HISTORY.parent.mkdir(exist_ok=True)
    new = not HISTORY.exists()
    with HISTORY.open("a", newline="") as handle:
        writer = csv.writer(handle)
        if new:
            writer.writerow(["day", "story", "blocks", "music"])
        writer.writerow([datetime.now().strftime("%Y-%m-%d"), cut.story, " ".join(block.kind for block in cut.blocks),
                         cut.music.path.name if cut.music else "no music"])


def clean(story: str, work: Path) -> int:
    """Deletes a story's work folder once its reel is delivered and returns the bytes freed.

    Raises:
        CutError: The reel was not delivered yet.
    """
    if not (SOCIAL / story / "reel.mp4").exists() or not (CUTS / f"{story}.yaml").exists():
        raise CutError(f"{story}: the reel is not delivered yet, nothing is deleted")
    freed = sum(path.stat().st_size for path in work.rglob("*") if path.is_file())
    shutil.rmtree(work)
    return freed


def recent(count: int = 5) -> str:
    """Returns the last reels' structures and music as lines, newest first."""
    if not HISTORY.exists():
        return "no reels yet"
    rows = list(csv.DictReader(HISTORY.open()))[-count:]
    return "\n".join(f"{row['day']} {row['story']}: {row['blocks']} | {row['music']}" for row in reversed(rows))
