"""
file: reels/usage.py
importable: Usage, measure, record

Counts what a /reels session cost, from Claude Code's own transcripts: the main session and every
agent it started, model by model. The numbers are tokens, not a share of the plan's limit, so
the first reels are also measured with /usage and the two are compared by hand.

description: Measures the tokens of a reels session and keeps one line per reel.
"""

# NOTE: The editor has two Claude accounts, each with its own folder, ~/.claude and ~/.claude-2.
# A session is looked for in both, under the site's project folder.
#
# NOTE: A transcript writes one line per content block, and the blocks of one answer repeat the
# same usage. Each answer is counted once, by its message id.

import csv
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from reels.config import ROOT
from reels.fields import CutError

PROJECT = "-home-burak-dev-web-bitpulse-cloud"
ACCOUNTS = (Path.home() / ".claude", Path.home() / ".claude-2")
LOG = ROOT / "records" / "usage.csv"
FIELDS = ("input", "cache_write", "cache_read", "output")


@dataclass
class Usage:
    turns: int = 0
    tokens: dict[str, int] = field(default_factory=lambda: dict.fromkeys(FIELDS, 0))

    def add(self, usage: dict) -> None:
        self.turns += 1
        self.tokens["input"] += usage.get("input_tokens", 0) or 0
        self.tokens["cache_write"] += usage.get("cache_creation_input_tokens", 0) or 0
        self.tokens["cache_read"] += usage.get("cache_read_input_tokens", 0) or 0
        self.tokens["output"] += usage.get("output_tokens", 0) or 0


def session_file(session: str | None) -> Path:
    """Finds a session transcript by its id, or the newest one when session is None.

    Raises:
        CutError: No transcript is found.
    """
    folders = [account / "projects" / PROJECT for account in ACCOUNTS if (account / "projects" / PROJECT).is_dir()]
    files = [path for folder in folders for path in folder.glob("*.jsonl")]
    if session:
        files = [path for path in files if path.stem.startswith(session)]
    if not files:
        raise CutError(f"no session transcript {session or ''} under {', '.join(str(f) for f in folders)}")
    return max(files, key=lambda path: path.stat().st_mtime)


def count(path: Path, into: dict[str, Usage], prefix: str) -> None:
    seen: set[str] = set()
    for line in path.read_text().splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = entry.get("message") or {}
        if entry.get("type") != "assistant" or "usage" not in message or message.get("id") in seen:
            continue
        seen.add(message.get("id"))
        model = message.get("model") or "unknown"
        if model == "<synthetic>":
            continue
        into.setdefault(f"{prefix}{model}", Usage()).add(message["usage"])


def measure(session: str | None) -> tuple[Path, dict[str, Usage]]:
    """Counts the tokens of a session and of every agent it started, by model."""
    path = session_file(session)
    found: dict[str, Usage] = {}
    count(path, found, "main ")
    for agent in sorted((path.parent / path.stem / "subagents").glob("*.jsonl")):
        count(agent, found, "agents ")
    return path, found


def record(story: str, path: Path, found: dict[str, Usage]) -> Path:
    LOG.parent.mkdir(exist_ok=True)
    new = not LOG.exists()
    with LOG.open("a", newline="") as handle:
        writer = csv.writer(handle)
        if new:
            writer.writerow(["day", "story", "session", "who", "turns", *FIELDS])
        for who, usage in found.items():
            writer.writerow([datetime.now().strftime("%Y-%m-%d"), story, path.stem[:8], who, usage.turns,
                             *(usage.tokens[name] for name in FIELDS)])
    return LOG
