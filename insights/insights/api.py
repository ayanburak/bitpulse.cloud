"""
file: insights/api.py
importable: Api

Api talks to the Bitpulse API on the same server with an insights key, which opens only the
/insights routes.

description: Hands Instagram posts, their numbers and pictures to the Bitpulse API.
"""

from typing import Any

from . import http

# --- Constants ---

DEFAULT_URL = "http://127.0.0.1:8010"
BATCH = 100

# --- Client ---

class Api:
    """Client of the insights routes.

    Args:
        key: Insights key made on the server.
        url: Address of the API.
    """

    def __init__(self, key: str, url: str = DEFAULT_URL):
        self.base = url.rstrip("/") + "/insights"
        self.headers = {"Authorization": f"Bearer {key}"}

    # When each post was last read, and the last day an audience was stored for.
    def fetched(self) -> dict[str, Any]:
        return http.get_json(f"{self.base}/fetched", self.headers)

    # The API takes a limited number of posts per call, and answers which of them still need a picture.
    def save_posts(self, posts: list[dict[str, Any]]) -> list[str]:
        missing: list[str] = []
        for start in range(0, len(posts), BATCH):
            answer = http.send_json("PUT", f"{self.base}/posts", {"posts": posts[start:start + BATCH]}, self.headers)
            missing += answer["thumbs"]
        return missing

    def save_thumb(self, post_id: str, data: bytes) -> None:
        http.send_bytes("PUT", f"{self.base}/posts/{post_id}/thumb", data, self.headers)

    def save_days(self, days: list[dict[str, Any]]) -> None:
        http.send_json("PUT", f"{self.base}/days", {"days": days}, self.headers)

    def save_audience(self, day: str, rows: list[dict[str, Any]]) -> None:
        http.send_json("PUT", f"{self.base}/audience", {"day": day, "rows": rows}, self.headers)
