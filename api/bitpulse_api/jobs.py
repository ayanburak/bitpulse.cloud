"""
file: bitpulse_api/jobs.py
importable: tick, run

tick does one round of the job loop: it collects a finished result, then starts the next queued
job if nothing is running. run repeats tick until the service stops.

description: Passes publishing jobs to the render worker and records their results.
"""

# NOTE: The worker never opens the database. It receives a folder with the stories to build, and
# answers with one result file. This is what keeps the database out of reach of the page builder.
#
# NOTE: Only one job is out at a time, and its folder is written when it starts rather than when it
# is requested. A folder written earlier would miss a story that was still being published, and
# building from it would remove that story from the site.

import json
import logging
import shutil
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from . import content as story_text
from . import notify, store
from .config import Settings
from .db import connect
from .service import story_key

log = logging.getLogger(__name__)

# --- Constants ---

TICK_SECONDS = 1.0
# The worker service is stopped by systemd after five minutes, so a job silent for longer is dead.
TIMEOUT = timedelta(minutes=10)

# --- Snapshot ---

def _write_story(root: Path, images: Path, key: str, published: str, record: dict[str, Any]) -> None:
    folder = root / key
    folder.mkdir()
    for lang in ("en", "tr"):
        (folder / f"{lang}.md").write_text(story_text.to_markdown(record["content"][lang], published), encoding="utf-8")
    shutil.copyfile(images / f"{record['image']}.jpg", folder / "image.jpg")


# The folder is finished under a hidden name and renamed, and the queue entry is written last.
# The worker can only ever see a complete job.
def _dispatch(conn: sqlite3.Connection, settings: Settings, job: sqlite3.Row) -> None:
    job_id = job["id"]
    records = {record["handle"]: record for record in store.live_versions(conn)}
    paths: list[str] = []
    if job["kind"] == "publish":
        story = store.story(conn, job["handle"])
        candidate = store.version(conn, job["version"])
        published = story["published_at"] or job["moment"]
        records[job["handle"]] = {**candidate, "published_at": published}
        paths = [f"/{lang}/stories/{candidate['content'][lang]['slug']}/" for lang in ("en", "tr")]
    elif job["kind"] == "withdraw":
        records.pop(job["handle"], None)

    partial = settings.jobs / f".{job_id}"
    shutil.rmtree(partial, ignore_errors=True)
    (partial / "stories").mkdir(parents=True)
    for handle, record in records.items():
        key = story_key(handle, record["published_at"])
        _write_story(partial / "stories", settings.images, key, record["published_at"], record)
    (partial / "job.json").write_text(
        json.dumps({"id": job_id, "paths": paths, "goLive": bool(job["go_live"])}), encoding="utf-8"
    )
    partial.rename(settings.jobs / str(job_id))

    with conn:
        store.mark_dispatched(conn, job_id)
    entry = settings.queue / f".{job_id}"
    entry.write_text("", encoding="utf-8")
    entry.rename(settings.queue / str(job_id))

# --- Results ---

def _clean(settings: Settings, job_id: int) -> None:
    shutil.rmtree(settings.jobs / str(job_id), ignore_errors=True)
    (settings.queue / str(job_id)).unlink(missing_ok=True)
    (settings.results / f"{job_id}.json").unlink(missing_ok=True)


# The story only becomes live here, in the same transaction that records the result.
def _finish(conn: sqlite3.Connection, settings: Settings, job: sqlite3.Row, result: dict[str, Any]) -> None:
    job_id = job["id"]
    ok = bool(result.get("ok"))
    release, error, ms = result.get("release"), result.get("error"), result.get("ms")
    with conn:
        store.finish_job(conn, job_id, ok, release, error, ms)
        if ok and job["kind"] == "publish":
            story = store.story(conn, job["handle"])
            store.set_live(conn, job["handle"], job["version"], story["published_at"] or job["moment"])
        elif ok and job["kind"] == "withdraw":
            store.clear_live(conn, job["handle"])
        target = job["handle"] or f"job {job_id}"
        store.add_audit(conn, "worker", "publish.done" if ok else "publish.failed", target, release or str(error))
    _clean(settings, job_id)


def _is_stale(job: sqlite3.Row) -> bool:
    return datetime.now(timezone.utc) - datetime.fromisoformat(job["dispatched_at"]) > TIMEOUT

# --- Loop ---

def tick(conn: sqlite3.Connection, settings: Settings) -> None:
    """Runs one round of the job loop.

    Args:
        conn: Open connection.
        settings: Folder paths.
    """
    active = store.dispatched(conn)
    if active is not None:
        path = settings.results / f"{active['id']}.json"
        if path.exists():
            _finish(conn, settings, active, json.loads(path.read_text(encoding="utf-8")))
        elif _is_stale(active):
            _finish(conn, settings, active, {"ok": False, "error": "worker did not answer"})
        else:
            return
    queued = store.next_queued(conn)
    if queued is not None:
        _dispatch(conn, settings, queued)


# A failing round is logged and the loop goes on, one bad job must not stop every later publish.
def run(settings: Settings, stop: threading.Event) -> None:
    """Repeats tick until stop is set.

    Args:
        settings: Folder paths.
        stop: Set by the service when it shuts down.
    """
    conn = connect(settings.db)
    try:
        while not stop.is_set():
            for step in (tick, notify.relay):
                try:
                    step(conn, settings)
                except Exception:
                    log.exception("job loop round failed")
            stop.wait(TICK_SECONDS)
    finally:
        conn.close()
