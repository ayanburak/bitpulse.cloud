"""
file: bitpulse_api/config.py
importable: Settings, PORT

Settings.from_env reads the two folders the API works in. Defaults match the server layout, tests
pass their own folders.

description: Holds the paths the API reads and writes.
"""

import os
from dataclasses import dataclass
from pathlib import Path

# --- Constants ---

# The API only listens inside the server, and this port is free next to the other services there.
PORT = 8010

# --- Settings ---

# Paths are derived from two roots, so a test can move everything by changing two values.
@dataclass(frozen=True)
class Settings:
    """Folders used by the API.

    Args:
        data: Holds the database and the image files. Only the API can read it.
        spool: Holds the job folders shared with the render worker.
    """

    data: Path
    spool: Path

    @property
    def db(self) -> Path:
        return self.data / "bitpulse.db"

    @property
    def images(self) -> Path:
        return self.data / "images"

    @property
    def jobs(self) -> Path:
        return self.spool / "jobs"

    @property
    def queue(self) -> Path:
        return self.spool / "queue"

    @property
    def results(self) -> Path:
        return self.spool / "results"

    # The server creates these folders with their real owners during setup. On a laptop or in a
    # test nothing has made them yet, so they are created here and existing ones are left alone.
    def prepare(self) -> None:
        """Creates every working folder that does not exist yet."""
        for path in (self.data, self.images, self.jobs, self.queue, self.results):
            path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> "Settings":
        """Builds the settings from BITPULSE_DATA and BITPULSE_SPOOL.

        Returns:
            Settings pointing at the given folders or at the server defaults.
        """
        return cls(
            data=Path(os.environ.get("BITPULSE_DATA", "/var/lib/bitpulse/api")),
            spool=Path(os.environ.get("BITPULSE_SPOOL", "/var/lib/bitpulse/spool")),
        )
