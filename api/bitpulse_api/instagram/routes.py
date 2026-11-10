"""
file: bitpulse_api/instagram/routes.py
importable: build, POST_ID

build returns the routes the insights service writes to. Every route needs an insights key, which
opens nothing else. The service sends what Instagram reports and the API keeps it.

description: Receives Instagram posts, their counts, their pictures and the daily account numbers.
"""

# NOTE: The sender is our own service, but every text here was written on Instagram, so lengths and
# the link are checked before anything is stored. The permalink becomes a link in the panel.

import sqlite3
from typing import Annotated, Callable, Literal, Optional
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field, field_validator

from .. import store as main_store
from ..config import Settings
from . import store, thumbs

# --- Constants ---

POST_ID = r"^\d{1,30}$"
MOMENT = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}"
DAY = r"^\d{4}-\d{2}-\d{2}$"
HOSTS = ("instagram.com", "www.instagram.com")

# --- Request Bodies ---

Count = Optional[Annotated[int, Field(ge=0)]]


class Counts(BaseModel):
    views: Count = None
    reach: Count = None
    likes: Count = None
    comments: Count = None
    saves: Count = None
    shares: Count = None
    watch_ms: Count = None


class PostIn(BaseModel):
    id: str = Field(pattern=POST_ID)
    kind: Literal["reel", "image", "carousel"]
    posted_at: str = Field(pattern=MOMENT, max_length=32)
    permalink: str = Field(max_length=300)
    caption: str = Field(default="", max_length=2200)
    counts: Counts

    @field_validator("permalink")
    @classmethod
    def _instagram_only(cls, value: str) -> str:
        parts = urlsplit(value)
        if parts.scheme != "https" or parts.hostname not in HOSTS:
            raise ValueError("only Instagram addresses are allowed")
        return value


class PostsBody(BaseModel):
    posts: list[PostIn] = Field(max_length=200)


class DayIn(BaseModel):
    day: str = Field(pattern=DAY)
    followers: Count = None
    profile_views: Count = None
    link_taps: Count = None


class DaysBody(BaseModel):
    days: list[DayIn] = Field(max_length=100)

# --- Routes ---

def build(settings: Settings, get_conn: Callable, get_insights: Callable) -> APIRouter:
    """Builds the routes of the insights service.

    Args:
        settings: Folder paths.
        get_conn: Dependency that gives each request its connection.
        get_insights: Dependency that needs an insights key.

    Returns:
        The routes.
    """
    router = APIRouter(prefix="/insights")
    Conn = Annotated[sqlite3.Connection, Depends(get_conn)]
    Insights = Annotated[str, Depends(get_insights)]

    @router.get("/fetched")
    def fetched(conn: Conn, _: Insights) -> dict[str, dict[str, str]]:
        return {"posts": store.fetched(conn)}

    # The answer names the posts that still have no picture, so the service downloads only those.
    @router.put("/posts")
    def save_posts(body: PostsBody, conn: Conn, _: Insights) -> dict[str, list[str]]:
        rows = [item.model_dump() for item in body.posts]
        with conn:
            store.save_posts(conn, rows, main_store.minute())
        return {"thumbs": store.missing_thumbs(conn, [row["id"] for row in rows])}

    # The body is read in pieces and cut off at the limit, a huge upload can not fill the memory.
    @router.put("/posts/{post_id}/thumb", status_code=204)
    async def save_thumb(post_id: Annotated[str, Path(pattern=POST_ID)], request: Request, conn: Conn, _: Insights) -> None:
        if store.post(conn, post_id) is None:
            raise HTTPException(404, f"no post {post_id}")
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > thumbs.MAX_UPLOAD:
                raise HTTPException(413, "picture is too large")
        try:
            await run_in_threadpool(thumbs.accept, settings.thumbs, post_id, bytes(raw))
        except thumbs.InvalidThumb as error:
            raise HTTPException(422, str(error)) from None
        with conn:
            store.set_thumb(conn, post_id)

    @router.put("/days", status_code=204)
    def save_days(body: DaysBody, conn: Conn, _: Insights) -> None:
        with conn:
            store.save_days(conn, [item.model_dump() for item in body.days])

    return router
