"""
file: bitpulse_api/panel/instagram.py
importable: attach

attach adds the Instagram routes of the panel to its router. They only read what the insights
service stored, so a session is enough.

description: Shows Instagram posts, their counts over time, the daily account numbers and the audience to the panel.
"""

from typing import Annotated, Any, Literal, Optional

from fastapi import APIRouter, Path, Query
from fastapi.responses import FileResponse

from .. import service as main_service
from ..config import Settings
from ..instagram import store, thumbs
from ..instagram.routes import POST_ID

# --- Constants ---

PAGE = 30
DAYS = 30

# --- Routes ---

def attach(router: APIRouter, settings: Settings, Conn: Any, Full: Any) -> None:
    """Adds the Instagram routes to a router.

    Args:
        router: Router of the panel.
        settings: Folder paths.
        Conn: Dependency type that gives a connection.
        Full: Dependency type that requires a signed in session.
    """

    # One row more than asked is read, which tells whether another page exists without counting.
    @router.get("/instagram")
    def posts(
        conn: Conn, _: Full, kind: Optional[Literal["reel", "image", "carousel"]] = None, offset: int = Query(0, ge=0)
    ) -> dict[str, Any]:
        rows = store.posts_page(conn, kind, PAGE + 1, offset)
        return {"rows": rows[:PAGE], "more": len(rows) > PAGE, "days": store.days(conn, DAYS), "audience": store.audience(conn)}

    # Every reading of one post, oldest first, which is what the chart of the post draws.
    @router.get("/instagram/{post_id}/history")
    def history(post_id: Annotated[str, Path(pattern=POST_ID)], conn: Conn, _: Full) -> list[dict[str, Any]]:
        if store.post(conn, post_id) is None:
            raise main_service.NotFound(f"no post {post_id}")
        return store.history(conn, post_id)

    # The id has to be a stored one with a picture, and only then does it become part of a file path.
    @router.get("/instagram/{post_id}/thumb")
    def thumb(post_id: Annotated[str, Path(pattern=POST_ID)], conn: Conn, _: Full) -> FileResponse:
        row = store.post(conn, post_id)
        if row is None or not row["thumb"]:
            raise main_service.NotFound(f"no picture for post {post_id}")
        return FileResponse(thumbs.path_of(settings.thumbs, post_id), media_type="image/jpeg")
