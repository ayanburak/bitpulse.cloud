"""
file: bitpulse_api/panel/actions.py
importable: attach

attach adds the working routes of the panel to its router. Saving a draft needs a session. Anything
that changes the live site or the access to the system also needs a fresh second factor for that
exact action and target.

description: Exposes stories, publishing, access and the audit log to the panel.
"""

# NOTE: Withdrawing a story, undoing a publish and managing keys exist only here. The device routes
# have no such paths, so a device key can publish but can never remove anything or make new keys.

import json
import re
import sqlite3
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .. import images, keys, service, store as main_store
from ..config import Settings
from . import passkeys, sessions, store

# --- Constants ---

ACTOR = "panel"
KEY_NAME = re.compile(r"^[a-z0-9-]{1,40}$")
AUDIT_PAGE_MAX = 200

# --- Request Bodies ---

class DraftFields(BaseModel):
    en: dict[str, Any]
    tr: dict[str, Any]
    social: str = ""
    image: str


class KeyBody(BaseModel):
    name: str


class PasskeyBody(BaseModel):
    credential: dict[str, Any]
    name: str

# --- Helpers ---

# The grant is spent even when the action then fails, one touch is never good for a second try.
def _confirmed(conn: sqlite3.Connection, current: sessions.Current, action: str, target: str) -> None:
    if not sessions.take_action(conn, current, action, target):
        raise HTTPException(403, "confirmation required")


def _state(row: sqlite3.Row) -> str:
    if row["live_version"] is None:
        return "withdrawn" if row["published_at"] else "draft"
    return "changed" if row["latest"] > row["live_number"] else "live"


def _job(row: Optional[sqlite3.Row]) -> Optional[dict[str, Any]]:
    if row is None:
        return None
    fields = ("id", "kind", "handle", "status", "release", "error", "duration_ms", "finished_at")
    return {key: row[key] for key in fields}

# --- Routes ---

def attach(router: APIRouter, settings: Settings, Conn: Any, Full: Any) -> None:
    """Adds the panel actions to a router.

    Args:
        router: Router of the panel.
        settings: Folder paths and the panel address.
        Conn: Dependency type that gives a connection.
        Full: Dependency type that requires a signed in session.
    """

    # --- Stories ---

    @router.get("/stories")
    def stories(conn: Conn, _: Full) -> list[dict[str, Any]]:
        result = []
        for row in main_store.story_rows(conn):
            content = json.loads(row["content"])["en"]
            result.append(
                {
                    "handle": row["handle"],
                    "title": content["title"],
                    "category": content["category"],
                    "state": _state(row),
                    "latest": row["latest"],
                    "live": row["live_number"],
                    "published_at": row["published_at"],
                    "saved_at": row["saved_at"],
                }
            )
        return result

    def _versions(conn: sqlite3.Connection, handle: str) -> list[dict[str, Any]]:
        return [dict(row) for row in main_store.versions_of(conn, handle)]

    @router.get("/stories/{handle}")
    def story(handle: str, conn: Conn, _: Full) -> dict[str, Any]:
        row = main_store.story(conn, handle)
        latest = main_store.latest_version(conn, handle)
        if row is None or latest is None:
            raise service.NotFound(f"story not found: {handle}")
        return {
            "handle": handle,
            "published_at": row["published_at"],
            "live_version": row["live_version"],
            "number": latest["number"],
            "content": latest["content"],
            "image": latest["image"],
            "versions": _versions(conn, handle),
        }

    @router.get("/stories/{handle}/versions/{number}")
    def version(handle: str, number: int, conn: Conn, _: Full) -> dict[str, Any]:
        record = main_store.version_by_number(conn, handle, number)
        if record is None:
            raise service.NotFound(f"version not found: {handle} {number}")
        return {"number": record["number"], "content": record["content"], "image": record["image"]}

    @router.put("/stories/{handle}/draft")
    def save(handle: str, body: DraftFields, conn: Conn, _: Full) -> dict[str, int]:
        return {"version": service.save_fields(conn, handle, body.en, body.tr, body.social, body.image, ACTOR)}

    # --- Live Site ---

    @router.post("/stories/{handle}/publish", status_code=202)
    def publish(handle: str, conn: Conn, current: Full) -> dict[str, int]:
        _confirmed(conn, current, "publish", handle)
        return {"job": service.request_publish(conn, handle, ACTOR)}

    @router.post("/stories/{handle}/undo", status_code=202)
    def undo(handle: str, conn: Conn, current: Full) -> dict[str, int]:
        _confirmed(conn, current, "undo", handle)
        return {"job": service.request_undo(conn, handle, ACTOR)}

    @router.post("/stories/{handle}/withdraw", status_code=202)
    def withdraw(handle: str, conn: Conn, current: Full) -> dict[str, int]:
        _confirmed(conn, current, "withdraw", handle)
        return {"job": service.request_withdraw(conn, handle, ACTOR)}

    @router.get("/jobs/{job_id}")
    def job(job_id: int, conn: Conn, _: Full) -> dict[str, Any]:
        row = main_store.job(conn, job_id)
        if row is None:
            raise service.NotFound(f"job not found: {job_id}")
        return _job(row)

    @router.get("/status")
    def status(conn: Conn, _: Full) -> dict[str, Any]:
        return {"active": _job(main_store.active_job(conn)), "last": _job(main_store.last_finished_job(conn))}

    # --- Images ---

    # The body is read in pieces and cut off at the limit, a huge upload can not fill the memory.
    @router.post("/images")
    async def upload(request: Request, conn: Conn, _: Full) -> dict[str, Any]:
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > images.MAX_UPLOAD:
                raise HTTPException(413, "image is too large")
        sha, width, height = await run_in_threadpool(images.accept_upload, settings.images, bytes(raw))
        with conn:
            main_store.add_image(conn, sha, width, height)
            main_store.add_audit(conn, ACTOR, "image.upload", sha)
        return {"sha": sha, "width": width, "height": height}

    # The hash comes from the address, so only a stored hash may ever become part of a file path.
    @router.get("/images/{sha}")
    def image(sha: str, conn: Conn, _: Full) -> FileResponse:
        if not main_store.has_image(conn, sha):
            raise service.NotFound(f"image not found: {sha}")
        return FileResponse(settings.images / f"{sha}.jpg", media_type="image/jpeg")

    # --- Audit ---

    @router.get("/audit")
    def audit(conn: Conn, _: Full, before: Optional[int] = None, limit: int = Query(100, ge=1, le=AUDIT_PAGE_MAX)) -> list[dict[str, Any]]:
        return [dict(row) for row in main_store.audit_page(conn, before, limit)]

    # --- Device Keys ---

    @router.get("/keys")
    def device_keys(conn: Conn, _: Full) -> list[dict[str, Any]]:
        return [dict(row) for row in main_store.keys(conn)]

    # A name stays taken after its key is revoked, so the audit log never has two devices under one name.
    @router.post("/keys", status_code=201)
    def create_key(body: KeyBody, conn: Conn, current: Full) -> dict[str, str]:
        if not KEY_NAME.match(body.name):
            raise HTTPException(422, "use lower case letters, digits and dashes")
        _confirmed(conn, current, "key.create", body.name)
        try:
            return {"key": keys.create_key(conn, body.name, actor=ACTOR)}
        except sqlite3.IntegrityError:
            raise service.Conflict("that name is already used") from None

    @router.delete("/keys/{name}", status_code=204)
    def revoke_key(name: str, conn: Conn, current: Full) -> None:
        _confirmed(conn, current, "key.revoke", name)
        with conn:
            found = main_store.revoke_key(conn, name)
            if found:
                main_store.add_audit(conn, ACTOR, "key.revoke", name)
        if not found:
            raise service.NotFound(f"no active key: {name}")

    # --- Passkeys ---

    @router.get("/account")
    def account(conn: Conn, _: Full) -> dict[str, Any]:
        rows = [
            {"id": row["id"], "name": row["name"], "created_at": row["created_at"], "used_at": row["used_at"]}
            for row in store.passkeys(conn)
        ]
        return {"passkeys": rows, "backup_codes": store.unused_backup_codes(conn)}

    @router.post("/account/passkeys/options")
    def passkey_options(conn: Conn, current: Full) -> dict[str, Any]:
        return {"options": passkeys.add_options(conn, settings, current)}

    @router.post("/account/passkeys", status_code=204)
    def passkey_add(body: PasskeyBody, conn: Conn, current: Full) -> None:
        _confirmed(conn, current, "passkey.add", "panel")
        if not passkeys.add_finish(conn, settings, current, body.credential, body.name):
            raise HTTPException(422, "the passkey was not accepted")

    # The last passkey stays, removing it would leave only paper codes to sign in with.
    @router.delete("/account/passkeys/{key_id}", status_code=204)
    def passkey_remove(key_id: str, conn: Conn, current: Full) -> None:
        _confirmed(conn, current, "passkey.remove", key_id)
        if store.passkey(conn, key_id) is None:
            raise service.NotFound("passkey not found")
        if len(store.passkeys(conn)) == 1:
            raise service.Conflict("the last passkey can not be removed")
        with conn:
            store.remove_passkey(conn, key_id)
            main_store.add_audit(conn, ACTOR, "passkey.remove", key_id)
