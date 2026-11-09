"""
file: deploy/backup.py
importable: nothing, the backup timer runs this file as root

Writes one encrypted archive per day to /var/backups/bitpulse and keeps the last fourteen. The
server only holds the public half of the age key, so nothing on it can open its own backups.

description: Makes the encrypted daily backup of the story database, images and radar database.
"""

# NOTE: Python is used for the database copies because the sqlite3 command is not installed on the
# server, and the backup call in the standard library gives a correct copy of a database in use.

import sqlite3
import subprocess
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# --- Constants ---

API_DB = Path("/var/lib/bitpulse/api/bitpulse.db")
RADAR_DB = Path("/var/lib/bitpulse/radar/radar.db")
IMAGES = Path("/var/lib/bitpulse/api/images")
OUTPUT = Path("/var/backups/bitpulse")
RECIPIENT = Path("/etc/bitpulse/backup.pub")
KEEP = 14

# --- Backup ---

# A copy that fails its own integrity check stops the run, an old good backup beats a new bad one.
def copy_database(source: Path, target: Path) -> None:
    origin = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    copy = sqlite3.connect(target)
    try:
        origin.backup(copy)
        result = copy.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        origin.close()
        copy.close()
    if result != "ok":
        raise RuntimeError(f"integrity check failed for {source}: {result}")


def main() -> None:
    OUTPUT.mkdir(mode=0o700, parents=True, exist_ok=True)
    name = datetime.now(timezone.utc).strftime("bitpulse-%Y-%m-%d.tar.age")
    with tempfile.TemporaryDirectory() as work:
        folder = Path(work)
        copy_database(API_DB, folder / "bitpulse.db")
        copy_database(RADAR_DB, folder / "radar.db")
        archive = folder / "backup.tar"
        with tarfile.open(archive, "w") as tar:
            tar.add(folder / "bitpulse.db", arcname="bitpulse.db")
            tar.add(folder / "radar.db", arcname="radar.db")
            tar.add(IMAGES, arcname="images")
        partial = OUTPUT / f".{name}.part"
        subprocess.run(["age", "-R", str(RECIPIENT), "-o", str(partial), str(archive)], check=True)
        partial.replace(OUTPUT / name)
    for old in sorted(OUTPUT.glob("bitpulse-*.tar.age"))[:-KEEP]:
        old.unlink()
    print(f"backup written: {name}")


if __name__ == "__main__":
    main()
