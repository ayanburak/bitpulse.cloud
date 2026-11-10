"""
file: bitpulse_api/app.py
importable: create_app

create_app builds the HTTP application for the given folders. Every route except health and the
panel routes needs a key: a device key for the story routes and a radar key for the radar routes.
The panel routes use a browser session and live under /panel-api.

description: Exposes stories, images and publishing jobs over HTTP.
"""

# NOTE: The automatic API docs are off. Nothing needs them, and each extra page is more surface.

import sqlite3
import threading
from contextlib import asynccontextmanager
from typing import Annotated, Any, AsyncIterator, Iterator, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from . import images, jobs, keys, service, social, store
from .config import Settings
from .content import InvalidDraft
from .db import connect
from .panel import routes as panel_routes
from .radar import routes as radar_routes
from .radar import service as radar_service

# --- Request Bodies ---

class DraftBody(BaseModel):
    en: str
    tr: str
    social: str = ""
    image: str
    candidate: Optional[int] = None


class RebuildBody(BaseModel):
    go_live: bool = True

# --- Application ---

def create_app(settings: Settings) -> FastAPI:
    """Builds the API application.

    Args:
        settings: Folder paths.

    Returns:
        The application. The job loop runs only while it is served.
    """
    settings.prepare()

    # The job loop lives and dies with the server process, there is no separate service to forget.
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        stop = threading.Event()
        thread = threading.Thread(target=jobs.run, args=(settings, stop), daemon=True)
        thread.start()
        yield
        stop.set()
        thread.join(5)

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)

    def get_conn() -> Iterator[sqlite3.Connection]:
        conn = connect(settings.db)
        try:
            yield conn
        finally:
            conn.close()

    Conn = Annotated[sqlite3.Connection, Depends(get_conn)]

    # The same answer for a missing, expired, revoked and wrong scope key, a caller learns nothing
    # about which.
    def _key_owner(request: Request, conn: sqlite3.Connection, scope: str) -> str:
        kind, _, token = request.headers.get("authorization", "").partition(" ")
        actor = keys.actor_for(conn, token, scope) if kind.lower() == "bearer" and token else None
        if actor is None:
            raise HTTPException(401, "invalid key")
        return actor

    def get_actor(request: Request, conn: Conn) -> str:
        return _key_owner(request, conn, keys.DEVICE)

    def get_radar(request: Request, conn: Conn) -> str:
        return _key_owner(request, conn, keys.RADAR)

    Actor = Annotated[str, Depends(get_actor)]

    @app.exception_handler(InvalidDraft)
    async def _invalid_draft(_: Request, error: InvalidDraft) -> JSONResponse:
        return JSONResponse({"detail": str(error)}, status_code=422)

    @app.exception_handler(images.InvalidImage)
    async def _invalid_image(_: Request, error: images.InvalidImage) -> JSONResponse:
        return JSONResponse({"detail": str(error)}, status_code=422)

    @app.exception_handler(social.InvalidSocial)
    async def _invalid_social(_: Request, error: social.InvalidSocial) -> JSONResponse:
        return JSONResponse({"detail": str(error)}, status_code=422)

    @app.exception_handler(service.NotFound)
    async def _not_found(_: Request, error: service.NotFound) -> JSONResponse:
        return JSONResponse({"detail": str(error)}, status_code=404)

    @app.exception_handler(service.Conflict)
    async def _conflict(_: Request, error: service.Conflict) -> JSONResponse:
        return JSONResponse({"detail": str(error)}, status_code=409)

    # --- Routes ---

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    # The body is read in pieces and cut off at the limit, a huge upload can not fill the memory.
    @app.post("/images")
    async def upload_image(request: Request, conn: Conn, actor: Actor) -> dict[str, Any]:
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > images.MAX_UPLOAD:
                raise HTTPException(413, "image is too large")
        sha, width, height = await run_in_threadpool(images.accept_upload, settings.images, bytes(raw))
        with conn:
            store.add_image(conn, sha, width, height)
            store.add_audit(conn, actor, "image.upload", sha)
        return {"sha": sha, "width": width, "height": height}

    # The hash comes from the address, so only a plain hash may ever become part of a file path.
    @app.get("/images/{sha}")
    def get_image(sha: str, conn: Conn, _: Actor) -> FileResponse:
        if not store.has_image(conn, sha):
            raise service.NotFound(f"image not found: {sha}")
        return FileResponse(settings.images / f"{sha}.jpg", media_type="image/jpeg")

    @app.get("/stories")
    def list_stories(conn: Conn, _: Actor) -> list[dict[str, Any]]:
        return service.list_stories(conn)

    @app.get("/stories/{handle}")
    def read_story(handle: str, conn: Conn, _: Actor) -> dict[str, Any]:
        return service.read_story(conn, handle)

    @app.get("/stories/{handle}/versions")
    def story_versions(handle: str, conn: Conn, _: Actor) -> list[dict[str, Any]]:
        if store.story(conn, handle) is None:
            raise service.NotFound(f"story not found: {handle}")
        return [dict(row) for row in store.versions_of(conn, handle)]

    @app.get("/whoami")
    def whoami(conn: Conn, actor: Actor) -> dict[str, Any]:
        return dict(store.key_by_name(conn, actor))

    @app.put("/stories/{handle}/draft")
    def save_draft(handle: str, body: DraftBody, conn: Conn, actor: Actor) -> dict[str, int]:
        if body.candidate is not None:
            radar_service.require(conn, body.candidate)
        version = service.save_draft(conn, handle, body.en, body.tr, body.social, body.image, actor)
        if body.candidate is not None:
            radar_service.link_story(conn, body.candidate, handle, actor)
        return {"version": version}

    # The whole set arrives in one body, and it is cut off at the limit like an image upload.
    @app.put("/stories/{handle}/social")
    async def upload_social(handle: str, request: Request, conn: Conn, actor: Actor) -> dict[str, list[str]]:
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > social.MAX_UPLOAD:
                raise HTTPException(413, "upload is too large")
        files = social.decode(bytes(raw))
        return {"files": await run_in_threadpool(social.accept, conn, settings, handle, files, actor)}

    # A clip goes to Instagram only, so it is uploaded under its own name and never touches a story.
    @app.put("/clips/{handle}")
    async def upload_clip(handle: str, request: Request, conn: Conn, actor: Actor) -> dict[str, list[str]]:
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > social.MAX_CLIP_UPLOAD:
                raise HTTPException(413, "upload is too large")
        title, files = social.decode_clip(bytes(raw))
        return {"files": await run_in_threadpool(social.accept_clip, conn, settings, handle, title, files, actor)}

    @app.post("/stories/{handle}/publish", status_code=202)
    def publish(handle: str, conn: Conn, actor: Actor) -> dict[str, int]:
        return {"job": service.request_publish(conn, handle, actor)}

    @app.post("/rebuild", status_code=202)
    def rebuild(body: RebuildBody, conn: Conn, actor: Actor) -> dict[str, int]:
        return {"job": service.request_rebuild(conn, actor, body.go_live)}

    @app.get("/jobs/{job_id}")
    def read_job(job_id: int, conn: Conn, _: Actor) -> dict[str, Any]:
        row = store.job(conn, job_id)
        if row is None:
            raise service.NotFound(f"job not found: {job_id}")
        return {key: row[key] for key in ("id", "kind", "handle", "status", "release", "error", "duration_ms")}

    app.include_router(radar_routes.build(get_conn, get_actor, get_radar))
    app.include_router(panel_routes.build(settings, get_conn))

    return app
