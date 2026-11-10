"""
file: bitpulse_api/panel/radar.py
importable: attach

attach adds the radar and the social routes of the panel to its router. Nothing here changes the
site, so a session is enough and no second factor is asked.

description: Exposes radar events, links and social files to the panel.
"""

# NOTE: The list is cut into pages on the server. The radar reports thousands of events a day, and
# the browser must never have to hold them all.
#
# NOTE: The panel never opens a link itself. An added link waits in a table and the radar picks it
# up, because the API is not allowed to reach the internet.

import re
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Optional
from urllib.parse import urlsplit

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .. import service as main_service
from .. import social, store as main_store
from ..config import Settings
from ..radar import service, store
from ..radar.routes import DecisionBody

# --- Constants ---

ACTOR = "panel"
PAGE_MAX = 100
SOCIAL_PAGE = 30
RECENT_LINKS = 10
CURSOR = re.compile(r"^(-?\d+(?:\.\d+)?)_(\d+)$")
DAY = r"^\d{4}-\d{2}-\d{2}$"
TYPES = {".png": "image/png", ".mp4": "video/mp4", ".txt": "text/plain; charset=utf-8"}

# --- Request Bodies ---

class LinkBody(BaseModel):
    url: str = Field(max_length=2000)


class SharedBody(BaseModel):
    shared: bool

# --- Helpers ---

def _after(cursor: Optional[str]) -> Optional[tuple[float, int]]:
    if cursor is None:
        return None
    match = CURSOR.match(cursor)
    if match is None:
        raise HTTPException(422, "invalid cursor")
    return float(match.group(1)), int(match.group(2))


def _listed(row: sqlite3.Row) -> dict[str, Any]:
    return {**dict(row), "score": None if row["score"] < 0 else row["score"], "has_brief": bool(row["has_brief"])}

# --- Routes ---

def attach(router: APIRouter, settings: Settings, Conn: Any, Full: Any) -> None:
    """Adds the radar and social routes to a router.

    Args:
        router: Router of the panel.
        settings: Folder paths.
        Conn: Dependency type that gives a connection.
        Full: Dependency type that requires a signed in session.
    """

    # --- Radar ---

    # One row more than asked is read, which tells whether another page exists without counting.
    @router.get("/radar/events")
    def events(
        conn: Conn,
        _: Full,
        group: Literal["candidates", "eliminated"] = "candidates",
        stage: Optional[Literal["scored", "reserve", "below", "unseen", "noise", "merged"]] = None,
        status: Optional[Literal["new", "do", "skip", "draft", "published"]] = None,
        recent: bool = False,
        day: Optional[str] = Query(None, pattern=DAY),
        category: Optional[str] = Query(None, max_length=20),
        min_sources: int = Query(0, ge=0, le=100),
        text: Optional[str] = Query(None, max_length=100),
        cursor: Optional[str] = Query(None, max_length=40),
        limit: int = Query(50, ge=1, le=PAGE_MAX),
    ) -> dict[str, Any]:
        since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat(timespec="seconds") if recent and not day else None
        filters = store.Filters(group, stage, status, since, day, category or None, min_sources, text or None)
        rows = store.browse(conn, filters, _after(cursor), limit + 1)
        page = rows[:limit]
        following = f"{page[-1]['score']}_{page[-1]['number']}" if len(rows) > limit else None
        return {"rows": [_listed(row) for row in page], "next": following, "counts": store.counts(conn, filters)}

    @router.get("/radar/events/{number}")
    def event(number: int, conn: Conn, _: Full) -> dict[str, Any]:
        row = store.event(conn, number)
        if row is None:
            raise main_service.NotFound(f"no such event: {service.label(number)}")
        return {**row, "score": None if row["score"] < 0 else row["score"], "has_brief": bool(row["has_brief"])}

    @router.get("/radar/events/{number}/brief")
    def brief(number: int, conn: Conn, _: Full) -> dict[str, Any]:
        row = store.brief(conn, number)
        if row is None:
            raise main_service.NotFound(f"no brief for {service.label(number)}")
        return {"text": row["brief"], "written_at": row["brief_at"]}

    @router.post("/radar/events/{number}/decision", status_code=204)
    def decide(number: int, body: DecisionBody, conn: Conn, _: Full) -> None:
        service.decide(conn, number, body.decision, ACTOR, "panel", False)

    @router.post("/radar/events/{number}/retry-brief", status_code=204)
    def retry(number: int, conn: Conn, _: Full) -> None:
        service.require(conn, number)
        with conn:
            store.retry_brief(conn, number)

    @router.get("/radar/links")
    def links(conn: Conn, _: Full) -> list[dict[str, Any]]:
        return [dict(row) for row in store.recent_links(conn, RECENT_LINKS)]

    @router.post("/radar/links", status_code=201)
    def add_link(body: LinkBody, conn: Conn, _: Full) -> dict[str, int]:
        parts = urlsplit(body.url.strip())
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise HTTPException(422, "give a web address")
        with conn:
            link = store.add_link(conn, body.url.strip(), main_store.minute())
            main_store.add_audit(conn, ACTOR, "radar.link", f"link {link}", body.url.strip()[:200])
        return {"id": link}

    # --- Social ---

    @router.get("/social")
    def posts(conn: Conn, _: Full, shared: Optional[bool] = None, offset: int = Query(0, ge=0)) -> dict[str, Any]:
        rows = main_store.social_rows(conn, shared, SOCIAL_PAGE + 1, offset)
        result = []
        for row in rows[:SOCIAL_PAGE]:
            handle = row["handle"]
            if row["kind"] == "clip":
                post = {"title": row["title"], "x": "", "pages": ["page-1.png"],
                        "caption": social.clip_path(settings, handle, "caption.txt").read_text(encoding="utf-8")}
            else:
                post = {
                    "title": main_store.latest_version(conn, handle)["content"]["en"]["title"],
                    "x": social.read_text(settings, handle, "x.txt"),
                    "caption": social.read_text(settings, handle, "caption.txt"),
                    "pages": social.pages(settings, handle),
                }
            result.append({"handle": handle, "kind": row["kind"], "uploaded_at": row["uploaded_at"], "shared_at": row["shared_at"], **post})
        return {"rows": result, "more": len(rows) > SOCIAL_PAGE}

    # The handle has to be a stored one, and only then does it become part of a file path.
    @router.get("/social/{handle}/{name}")
    def social_file(handle: str, name: str, conn: Conn, _: Full) -> FileResponse:
        if main_store.social_post(conn, handle) is None:
            raise main_service.NotFound(f"no social files for {handle}")
        path = social.path_of(settings, handle, name)
        return FileResponse(path, media_type=TYPES[path.suffix], filename=f"{handle}-{name}")

    # The handle has to be a stored one, and only then does it become part of a file path.
    @router.get("/clips/{handle}/{name}")
    def clip_file(handle: str, name: str, conn: Conn, _: Full) -> FileResponse:
        if main_store.clip(conn, handle) is None:
            raise main_service.NotFound(f"no clip named {handle}")
        path = social.clip_path(settings, handle, name)
        return FileResponse(path, media_type=TYPES[path.suffix], filename=f"{handle}-{name}")

    @router.post("/clips/{handle}/shared", status_code=204)
    def clip_shared(handle: str, body: SharedBody, conn: Conn, _: Full) -> None:
        if main_store.clip(conn, handle) is None:
            raise main_service.NotFound(f"no clip named {handle}")
        with conn:
            main_store.set_clip_shared(conn, handle, body.shared)
            main_store.add_audit(conn, ACTOR, "clip.shared", handle, "shared" if body.shared else "not shared")

    @router.post("/social/{handle}/shared", status_code=204)
    def shared(handle: str, body: SharedBody, conn: Conn, _: Full) -> None:
        if main_store.social_post(conn, handle) is None:
            raise main_service.NotFound(f"no social files for {handle}")
        with conn:
            main_store.set_social_shared(conn, handle, body.shared)
            main_store.add_audit(conn, ACTOR, "social.shared", handle, "shared" if body.shared else "not shared")
