"""
file: bitpulse_cli/client.py
importable: Api, ApiError, tunnel, read_key, write_key

Api makes the HTTP calls. tunnel opens the private route to the server for as long as a command
runs.

description: Talks to the Bitpulse API through an SSH tunnel.
"""

# NOTE: Only the standard library is used, so the command installs anywhere without extra packages.
#
# NOTE: The device routes of the API are never on the internet. The tunnel uses an SSH account that
# has no shell and can reach only the API port, and the device key is still checked on the server.

import json
import os
import socket
import subprocess
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional

# --- Constants ---

REMOTE_PORT = 8010
KEY_FILE = Path.home() / ".config" / "bitpulse" / "key"
TUNNEL_WAIT_SECONDS = 15
SSH_HOST = "bitpulse-tunnel"

# --- Errors ---

class ApiError(Exception):
    """Raised when the API refuses a call or can not be reached.

    Args:
        status: HTTP status, or zero when no answer came.
        message: Text to show the user.
    """

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status

# --- Client ---

class Api:
    """Calls the API with a device key.

    Args:
        base: Address of the API.
        key: Device key.
    """

    def __init__(self, base: str, key: str) -> None:
        self.base = base.rstrip("/")
        self.key = key

    # FastAPI puts its explanation in a detail field, which is what the user needs to see.
    def _send(self, method: str, path: str, data: Optional[bytes], kind: Optional[str]) -> bytes:
        headers = {"Authorization": f"Bearer {self.key}"}
        if kind:
            headers["Content-Type"] = kind
        request = urllib.request.Request(self.base + path, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", "replace")
            try:
                detail = json.loads(body)["detail"]
            except (ValueError, KeyError, TypeError):
                detail = body
            raise ApiError(error.code, str(detail)) from None
        except OSError as error:
            raise ApiError(0, f"API can not be reached: {error}") from None

    def get(self, path: str) -> Any:
        return json.loads(self._send("GET", path, None, None))

    def get_bytes(self, path: str) -> bytes:
        return self._send("GET", path, None, None)

    def send_json(self, method: str, path: str, body: dict[str, Any]) -> Any:
        return json.loads(self._send(method, path, json.dumps(body).encode(), "application/json"))

    def post_bytes(self, path: str, data: bytes) -> Any:
        return json.loads(self._send("POST", path, data, "application/octet-stream"))

# --- Setup ---

def read_key() -> str:
    """Returns the device key.

    Returns:
        BITPULSE_KEY if set, otherwise the content of the key file.

    Raises:
        ApiError: If there is no key on this device.
    """
    if os.environ.get("BITPULSE_KEY"):
        return os.environ["BITPULSE_KEY"]
    if not KEY_FILE.exists():
        raise ApiError(0, f"no device key at {KEY_FILE}")
    return KEY_FILE.read_text(encoding="utf-8").strip()


# The folder and the file are private from the moment they exist.
def write_key(key: str) -> Path:
    """Stores the device key for this user.

    Args:
        key: Key text.

    Returns:
        Path of the key file.
    """
    KEY_FILE.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = os.open(KEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
        output.write(key.strip() + "\n")
    os.chmod(KEY_FILE, 0o600)
    return KEY_FILE


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _wait_until_open(port: int, process: subprocess.Popen) -> None:
    deadline = time.monotonic() + TUNNEL_WAIT_SECONDS
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise ApiError(0, "SSH tunnel could not be opened")
        with socket.socket() as probe:
            if probe.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.2)
    raise ApiError(0, "SSH tunnel timed out")


# BITPULSE_API skips the tunnel, which tests and a local API use.
@contextmanager
def tunnel() -> Iterator[str]:
    """Opens the route to the API while the block runs.

    Yields:
        Address of the API.

    Raises:
        ApiError: If the tunnel can not be opened.
    """
    if os.environ.get("BITPULSE_API"):
        yield os.environ["BITPULSE_API"]
        return
    port = _free_port()
    host = os.environ.get("BITPULSE_SSH", SSH_HOST)
    forward = f"127.0.0.1:{port}:127.0.0.1:{REMOTE_PORT}"
    process = subprocess.Popen(
        ["ssh", "-N", "-o", "ExitOnForwardFailure=yes", "-o", "BatchMode=yes", "-L", forward, host],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_until_open(port, process)
        yield f"http://127.0.0.1:{port}"
    finally:
        process.terminate()
        process.wait(timeout=5)
