"""
file: bitpulse_api/radar/routes.py
importable: build, EventIn, DecisionBody

build returns the routes the radar service and the devices use. The radar writes under /radar and
only with a radar key. A device reads candidates and briefs under /candidates with a device key.

description: Exposes radar events to the radar service and to the devices.
"""

# NOTE: Everything arriving here was read from the open web, so length and link checks run before
# anything is stored, even though the sender is our own service.

import json
import sqlite3
from typing import Annotated, Any, Callable, Literal, Optional
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field, field_validator

from .. import service as main_service
from .. import store as main_store
from . import service, store

# --- Constants ---

WORK_BATCH = 3
MOMENT = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}"
CANDIDATE_LIMIT = 200

# --- Request Bodies ---

class Link(BaseModel):
    source: str = Field(max_length=120)
    title: str = Field(max_length=400)
    url: str = Field(max_length=2000)

    # A link is shown on a page, and a javascript address there would run inside the panel.
    @field_validator("url")
    @classmethod
    def _web_only(cls, value: str) -> str:
        if urlsplit(value).scheme not in ("http", "https"):
            raise ValueError("only web addresses are allowed")
        return value


class EventIn(BaseModel):
    number: int = Field(gt=0)
    title: str = Field(max_length=400)
    summary: str = Field(default="", max_length=500)
    first_seen: str = Field(pattern=MOMENT, max_length=32)
    last_seen: str = Field(pattern=MOMENT, max_length=32)
    sources: int = Field(ge=0)
    stage: Literal["sent", "reserve", "below", "unseen", "noise", "merged"]
    score: float = Field(default=-1, ge=-1, le=10)
    impact: Optional[int] = Field(default=None, ge=0, le=10)
    tension: Optional[int] = Field(default=None, ge=0, le=10)
    visual: Optional[int] = Field(default=None, ge=0, le=10)
    category: Optional[str] = Field(default=None, max_length=20)
    reason: str = Field(default="", max_length=500)
    merged_into: Optional[int] = None
    clip: bool = False
    links: list[Link] = Field(max_length=8)
    decision: Optional[Literal["do", "skip"]] = None


class EventsBody(BaseModel):
    events: list[EventIn] = Field(max_length=500)


class DecisionBody(BaseModel):
    decision: Literal["do", "skip"]


class BriefBody(BaseModel):
    text: Optional[str] = Field(default=None, max_length=400_000)
    error: Optional[str] = Field(default=None, max_length=500)


class LinkDoneBody(BaseModel):
    number: Optional[int] = None
    error: Optional[str] = Field(default=None, max_length=500)

# --- Routes ---

def build(get_conn: Callable, get_actor: Callable, get_radar: Callable) -> APIRouter:
    """Builds the routes of the radar service and of the devices.

    Args:
        get_conn: Dependency that gives each request its connection.
        get_actor: Dependency that needs a device key.
        get_radar: Dependency that needs a radar key.

    Returns:
        The routes.
    """
    router = APIRouter()
    Conn = Annotated[sqlite3.Connection, Depends(get_conn)]
    Actor = Annotated[str, Depends(get_actor)]
    Radar = Annotated[str, Depends(get_radar)]

    # --- Radar Service ---

    @router.put("/radar/events", status_code=204)
    def save_events(body: EventsBody, conn: Conn, _: Radar) -> None:
        rows = []
        for item in body.events:
            data = item.model_dump()
            data["links"] = json.dumps(data["links"], ensure_ascii=False)
            data["clip"] = int(data["clip"])
            data["decided_by"] = "history" if data["decision"] else None
            rows.append(data)
        with conn:
            store.save_events(conn, rows)

    @router.get("/radar/work")
    def work(conn: Conn, _: Radar) -> dict[str, Any]:
        return {
            "briefs": [dict(row) for row in store.wanted_briefs(conn, WORK_BATCH)],
            "decisions": [dict(row) for row in store.unseen_decisions(conn, WORK_BATCH)],
            "links": [dict(row) for row in store.waiting_links(conn, WORK_BATCH)],
        }

    @router.post("/radar/events/{number}/decision", status_code=204)
    def decide(number: int, body: DecisionBody, conn: Conn, actor: Radar) -> None:
        service.decide(conn, number, body.decision, actor, "telegram", True)

    @router.post("/radar/events/{number}/seen", status_code=204)
    def seen(number: int, conn: Conn, _: Radar) -> None:
        with conn:
            store.mark_seen(conn, number)

    @router.put("/radar/events/{number}/brief", status_code=204)
    def put_brief(number: int, body: BriefBody, conn: Conn, _: Radar) -> None:
        service.require(conn, number)
        with conn:
            store.set_brief(conn, number, body.text, body.error, main_store.minute())

    @router.post("/radar/links/{link}", status_code=204)
    def finish_link(link: int, body: LinkDoneBody, conn: Conn, _: Radar) -> None:
        with conn:
            if not store.finish_link(conn, link, body.number, body.error):
                raise main_service.NotFound(f"no waiting link: {link}")

    # --- Devices ---

    @router.get("/candidates")
    def candidates(conn: Conn, _: Actor, limit: int = Query(50, ge=1, le=CANDIDATE_LIMIT)) -> list[dict[str, Any]]:
        return [dict(row) for row in store.candidates(conn, limit)]

    @router.get("/candidates/{number}/brief")
    def read_brief(number: int, conn: Conn, _: Actor) -> dict[str, Any]:
        row = store.brief(conn, number)
        if row is None:
            raise main_service.NotFound(f"no brief for {service.label(number)}")
        return {"number": number, "text": row["brief"], "written_at": row["brief_at"]}

    return router
