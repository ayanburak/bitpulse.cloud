"""
file: radar/api.py
importable: ApiError, enabled, save_events, decide, work, put_brief, seen, finish_link

Talks to the Bitpulse API on the same server. The key comes from RADAR_API_KEY. Without it, as on a
development machine, enabled says so and the rest of the radar runs without the API.

description: Sends radar events to the API and asks what the panel wants done.
"""

# NOTE: Only the standard library is used, the server runs this on Python 3.10 and a new package
# there would be one more thing to keep up to date.

import json
import os
import urllib.error
import urllib.request

# --- Constants ---

DEFAULT_URL = "http://127.0.0.1:8010"
TIMEOUT = 30
BATCH = 500

# --- Errors ---

class ApiError(Exception):
    """Raised when the API refuses a call or can not be reached."""

# --- Calls ---

def enabled() -> bool:
    return bool(os.environ.get("RADAR_API_KEY"))


def _call(method: str, path: str, body: dict | None = None) -> dict | None:
    if not enabled():
        raise ApiError("RADAR_API_KEY is not set")
    base = os.environ.get("RADAR_API_URL", DEFAULT_URL).rstrip("/")
    headers = {"Authorization": f"Bearer {os.environ['RADAR_API_KEY']}", "Content-Type": "application/json"}
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(base + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            answer = response.read()
    except urllib.error.HTTPError as error:
        raise ApiError(f"API answered {error.code} to {path}: {error.read().decode('utf-8', 'replace')[:300]}") from None
    except OSError as error:
        raise ApiError(f"API can not be reached: {error}") from None
    return json.loads(answer) if answer else None


def save_events(events: list[dict]) -> None:
    """
    Stores events on the API in groups it accepts.

    Args:
        events: Events in the form radar.sync builds.

    Raises:
        ApiError: When a group is refused or the API is down.
    """
    for start in range(0, len(events), BATCH):
        _call("PUT", "/radar/events", {"events": events[start:start + BATCH]})


def decide(number: int, decision: str) -> None:
    _call("POST", f"/radar/events/{number}/decision", {"decision": decision})


def work() -> dict:
    """
    Asks what is waiting for the radar.

    Returns:
        Lists under briefs, decisions and links.
    """
    return _call("GET", "/radar/work")


def put_brief(number: int, text: str | None = None, error: str | None = None) -> None:
    _call("PUT", f"/radar/events/{number}/brief", {"text": text, "error": error})


def seen(number: int) -> None:
    _call("POST", f"/radar/events/{number}/seen")


def finish_link(link: int, number: int | None = None, error: str | None = None) -> None:
    _call("POST", f"/radar/links/{link}", {"number": number, "error": error})
