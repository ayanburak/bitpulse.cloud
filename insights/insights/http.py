"""
file: insights/http.py
importable: HttpError, get_json, send_json, send_bytes, download

Small wrappers around urllib with a timeout and a size limit. Every failure becomes HttpError with
the status and the start of the answer, so the caller has one error to catch.

description: Makes the HTTP calls of the insights service.
"""

# NOTE: Only the standard library is used, the server runs this on Python 3.10 and a new package
# there would be one more thing to keep up to date.

import json
import urllib.error
import urllib.request
from urllib.parse import urlsplit
from typing import Any, Optional

# --- Constants ---

TIMEOUT = 30
MAX_ANSWER = 5 * 1024 * 1024

# --- Errors ---

class HttpError(Exception):
    """Raised when a call fails or its answer can not be used.

    Args:
        message: What went wrong.
        status: HTTP status, or None when no answer came.
    """

    def __init__(self, message: str, status: Optional[int] = None):
        super().__init__(message)
        self.status = status

# --- Calls ---

# A read stops one byte past the limit, which is enough to know the answer was too long.
def _open(request: urllib.request.Request) -> tuple[bytes, str]:
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            body = response.read(MAX_ANSWER + 1)
            final = response.geturl()
    except urllib.error.HTTPError as error:
        detail = error.read(2000).decode("utf-8", "replace")
        raise HttpError(f"{request.full_url.split('?')[0]} answered {error.code}: {detail[:300]}", error.code) from None
    except OSError as error:
        raise HttpError(f"{request.full_url.split('?')[0]} can not be reached: {error}") from None
    if len(body) > MAX_ANSWER:
        raise HttpError(f"{request.full_url.split('?')[0]} answered more than {MAX_ANSWER} bytes")
    return body, final


def get_json(url: str, headers: Optional[dict[str, str]] = None) -> Any:
    body, _ = _open(urllib.request.Request(url, headers=headers or {}))
    return json.loads(body) if body else None


def send_json(method: str, url: str, data: Any, headers: dict[str, str]) -> Any:
    request = urllib.request.Request(
        url, data=json.dumps(data).encode(), method=method, headers={**headers, "Content-Type": "application/json"}
    )
    body, _ = _open(request)
    return json.loads(body) if body else None


def send_bytes(method: str, url: str, data: bytes, headers: dict[str, str]) -> None:
    _open(urllib.request.Request(url, data=data, method=method, headers=headers))


# The address comes from Instagram, so it is only trusted for its own picture servers, before and
# after any redirect.
def download(url: str, hosts: tuple[str, ...]) -> bytes:
    """Downloads a picture from one of the given hosts.

    Args:
        url: Address of the picture.
        hosts: Host name endings that are allowed.

    Returns:
        The bytes of the answer.

    Raises:
        HttpError: If the address or the place it leads to is not allowed, or the call fails.
    """
    if not _allowed(url, hosts):
        raise HttpError(f"picture address is not on an allowed host: {url[:80]}")
    body, final = _open(urllib.request.Request(url))
    if not _allowed(final, hosts):
        raise HttpError(f"picture address led to another host: {final[:80]}")
    return body


def _allowed(url: str, hosts: tuple[str, ...]) -> bool:
    parts = urlsplit(url)
    host = parts.hostname or ""
    return parts.scheme == "https" and any(host == item or host.endswith("." + item) for item in hosts)
