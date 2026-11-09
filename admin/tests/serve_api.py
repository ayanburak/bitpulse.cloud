"""
file: tests/serve_api.py
importable: nothing, the browser tests start this file

Starts the real API with an empty database in the given folder, with a stand-in for the render
worker. It writes the one time registration token and a cover image into that folder.

description: Runs the API for the browser tests of the admin panel.
"""

import sys
import threading
import time
from pathlib import Path

import uvicorn
from PIL import Image

from bitpulse_api.app import create_app
from bitpulse_api.config import Settings
from bitpulse_api.db import connect
from bitpulse_api.panel import accounts

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


def main() -> None:
    root, origin, port = Path(sys.argv[1]), sys.argv[2], int(sys.argv[3])
    settings = Settings(data=root / "data", spool=root / "spool", panel_origin=origin)
    settings.prepare()
    token, codes = accounts.init_admin(connect(settings.db), PASSWORD)
    (root / "enrol.txt").write_text(token, encoding="utf-8")
    (root / "code.txt").write_text(codes[0], encoding="utf-8")
    Image.new("RGB", (1400, 900), (40, 90, 140)).save(root / "cover.jpg", "JPEG")
    threading.Thread(target=fake_worker, args=(settings,), daemon=True).start()
    uvicorn.run(create_app(settings), host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
