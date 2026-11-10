"""
file: bitpulse_api/config.py
importable: Settings, PORT

Settings.from_env reads the two folders the API works in and the address of the panel. Defaults
match the server layout, tests pass their own values.

description: Holds the paths the API reads and writes and the address of the panel.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

# --- Constants ---

# The API only listens inside the server, and this port is free next to the other services there.
PORT = 8010
PANEL_ORIGIN = "https://admin.bitpulse.cloud"

# --- Settings ---

# Paths are derived from two roots, so a test can move everything by changing two values.
@dataclass(frozen=True)
class Settings:
    """Folders used by the API.

    Args:
        data: Holds the database and the image files. Only the API can read it.
        spool: Holds the job folders shared with the render worker.
        panel_origin: The one address the panel is served from. Passkeys are bound to it.
    """

    data: Path
    spool: Path
    panel_origin: str = PANEL_ORIGIN

    @property
    def panel_host(self) -> str:
        return str(urlsplit(self.panel_origin).hostname)

    @property
    def db(self) -> Path:
        return self.data / "bitpulse.db"

    @property
    def images(self) -> Path:
        return self.data / "images"

    @property
    def social(self) -> Path:
        return self.data / "social"

    # Clips are posts without a story. Their own folder keeps a clip name from ever meeting a story name.
    @property
    def clips(self) -> Path:
        return self.data / "clips"

    @property
    def jobs(self) -> Path:
        return self.spool / "jobs"

    # A sibling of the spool, so a test that moves the spool moves this too.
    @property
    def notify(self) -> Path:
        return self.spool.parent / "notify"

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
        for path in (self.data, self.images, self.social, self.clips, self.jobs, self.queue, self.results, self.notify):
            path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> "Settings":
        """Builds the settings from BITPULSE_DATA, BITPULSE_SPOOL and BITPULSE_PANEL_ORIGIN.

        Returns:
            Settings pointing at the given folders or at the server defaults.
        """
        return cls(
            data=Path(os.environ.get("BITPULSE_DATA", "/var/lib/bitpulse/api")),
            spool=Path(os.environ.get("BITPULSE_SPOOL", "/var/lib/bitpulse/spool")),
            panel_origin=os.environ.get("BITPULSE_PANEL_ORIGIN", PANEL_ORIGIN),
        )
