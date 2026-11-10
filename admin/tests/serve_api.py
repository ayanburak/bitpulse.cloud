"""
file: tests/serve_api.py
importable: nothing, the browser tests start this file

Starts the real API with an empty database in the given folder, with a stand-in for the render
worker. It writes the one time registration token and a cover image into that folder, and fills in
radar events and two Instagram posts, one with a picture, for the pages that show them.

description: Runs the API for the browser tests of the admin panel.
"""

import io
import json
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from PIL import Image

from bitpulse_api.app import create_app
from bitpulse_api.config import Settings
from bitpulse_api.db import connect
from bitpulse_api.panel import accounts
from bitpulse_api import images, store
from bitpulse_api.instagram import store as instagram_store
from bitpulse_api.instagram import thumbs
from bitpulse_api.radar import store as radar_store

PASSWORD = "a long enough password"


# Answers every job at once, the browser tests are about the panel and not about building pages.
def fake_worker(settings: Settings) -> None:
    while True:
        for entry in settings.queue.iterdir():
            if not entry.name.startswith("."):
                result = settings.results / f"{entry.name}.json"
                if not result.exists():
                    result.write_text('{"ok": true, "release": "release-test", "ms": 7}', encoding="utf-8")
        time.sleep(0.2)


# The title and the link are what the open web could send, the page must show them as plain text.
def event(number: int, stage: str, score: float, title: str) -> dict:
    return {
        "number": number, "title": title, "summary": "A short summary.", "first_seen": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "last_seen": datetime.now(timezone.utc).isoformat(timespec="seconds"), "sources": 2, "stage": stage, "score": score,
        "importance": None if score < 0 else 6, "shareable": None if score < 0 else 6, "visual": None if score < 0 else 6,
        "category": "world", "reason": "A reason to look at it.", "merged_into": None, "clip": 0, "decision": None, "decided_by": None,
        "links": json.dumps([{"source": "Outlet", "title": "The article", "url": "https://example.com/a"}]),
    }


def seed(conn, settings: Settings) -> None:
    rows = [event(1, "sent", 7.5, "A candidate sent to Telegram")]
    rows.append(event(2, "reserve", 7.0, '<img src=x id="injected-title"> Waiting for a place'))
    rows += [event(number, "below", 5.0, f"Left out event {number}") for number in range(3, 123)]
    rows.append(event(123, "unseen", -1, "Never read by the model"))
    picture = io.BytesIO()
    Image.new("RGB", (1080, 1920), (20, 30, 40)).save(picture, "JPEG")
    reel = {
        "id": "1790001", "kind": "reel", "posted_at": "2026-11-05T14:02:11+0000",
        "permalink": "https://www.instagram.com/reel/1790001/", "caption": '<img src=x id="injected-caption"> A sample reel',
        "counts": {"views": 1520, "reach": 1100, "likes": 40, "comments": 3, "saves": 9, "shares": 12, "watch_ms": 4300},
    }
    image = {
        "id": "1790002", "kind": "image", "posted_at": "2026-11-04T09:00:00+0000",
        "permalink": "https://www.instagram.com/p/1790002/", "caption": "A sample image",
        "counts": {"views": 300, "likes": 5},
    }
    with conn:
        radar_store.save_events(conn, rows)
        for hour, views in ((6, 210), (7, 640), (8, 1100), (9, 1520)):
            reel["counts"]["views"] = views
            instagram_store.save_posts(conn, [reel], f"2026-11-11 0{hour}:00")
        instagram_store.save_posts(conn, [image], "2026-11-11 09:00")
        instagram_store.save_days(conn, [
            {"day": "2026-11-11", "followers": 410},
            {"day": "2026-11-10", "profile_views": 33, "link_taps": 4, "reach": 3255, "reach_followers": 2, "reach_others": 3253},
        ])
        thumbs.accept(settings.thumbs, "1790001", picture.getvalue())
        instagram_store.set_thumb(conn, "1790001")


def main() -> None:
    root, origin, port = Path(sys.argv[1]), sys.argv[2], int(sys.argv[3])
    settings = Settings(data=root / "data", spool=root / "spool", panel_origin=origin)
    settings.prepare()
    token, codes = accounts.init_admin(connect(settings.db), PASSWORD)
    (root / "enrol.txt").write_text(token, encoding="utf-8")
    (root / "code.txt").write_text(codes[0], encoding="utf-8")
    Image.new("RGB", (1400, 900), (40, 90, 140)).save(root / "cover.jpg", "JPEG")
    seed(connect(settings.db), settings)
    threading.Thread(target=fake_worker, args=(settings,), daemon=True).start()
    uvicorn.run(create_app(settings), host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
