"""
file: bitpulse_api/panel/routes.py
importable: build

build returns the /panel-api routes. Only these routes are reachable from the internet. They never
accept a device key, and the device routes never accept this cookie.

description: Exposes the panel login over HTTP and attaches the panel actions.
"""

# NOTE: Every wrong login answer gets the same reply, so a caller can not tell which part failed.
# The one exception is the step after a correct password, which has to ask for the second factor.

import hmac
import sqlite3
from typing import Annotated, Any, Callable, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from .. import store as main_store
from ..config import Settings
from . import accounts, actions, passkeys, sessions

# --- Request Bodies ---

class PasswordBody(BaseModel):
    password: str


class CredentialBody(BaseModel):
    credential: dict[str, Any]


class CodeBody(BaseModel):
    code: str


class EnrolStartBody(BaseModel):
    token: str


class EnrolFinishBody(BaseModel):
    token: str
    credential: dict[str, Any]
    name: str


class ActionBody(BaseModel):
    action: str
    target: str


class ActionAnswerBody(ActionBody):
    credential: Optional[dict[str, Any]] = None
    code: Optional[str] = None

# --- Constants ---

LOGIN_PURPOSE = "login"

# --- Helpers ---

def _set_cookie(response: Response, token: str) -> None:
    response.set_cookie(sessions.COOKIE, token, httponly=True, secure=True, samesite="strict", path="/")


def _refused() -> HTTPException:
    return HTTPException(401, "invalid login")

# --- Routes ---

def build(settings: Settings, get_conn: Callable) -> APIRouter:
    """Builds the panel routes.

    Args:
        settings: Holds the panel address.
        get_conn: Dependency that gives each request its connection.

    Returns:
        The routes, every one of them under /panel-api.
    """

    # The browser sets this header and a page on another site can not change it.
    def check_origin(request: Request) -> None:
        if request.method not in ("GET", "HEAD") and request.headers.get("origin") != settings.panel_origin:
            raise HTTPException(403, "wrong origin")

    Conn = Annotated[sqlite3.Connection, Depends(get_conn)]
    router = APIRouter(prefix="/panel-api", dependencies=[Depends(check_origin)])

    def any_session(request: Request, conn: Conn) -> Optional[sessions.Current]:
        return sessions.load(conn, request.cookies.get(sessions.COOKIE))

    AnySession = Annotated[Optional[sessions.Current], Depends(any_session)]

    def pending_session(conn: Conn, current: AnySession) -> sessions.Current:
        if current is None or current.full:
            raise _refused()
        if accounts.is_locked(conn):
            raise HTTPException(429, "too many attempts")
        return current

    Pending = Annotated[sessions.Current, Depends(pending_session)]

    def full_session(request: Request, current: AnySession) -> sessions.Current:
        if current is None or not current.full:
            raise HTTPException(401, "not signed in")
        if request.method not in ("GET", "HEAD"):
            sent = request.headers.get("x-csrf-token", "")
            if not hmac.compare_digest(sent.encode(), current.csrf.encode()):
                raise HTTPException(403, "wrong token")
        return current

    Full = Annotated[sessions.Current, Depends(full_session)]

    def finish_login(response: Response, conn: Conn, pending: sessions.Current, method: str) -> dict[str, str]:
        token, current = sessions.promote(conn, pending)
        with conn:
            main_store.add_audit(conn, "panel", "login.ok", method)
        _set_cookie(response, token)
        return {"csrf": current.csrf}

    # --- Login ---

    @router.get("/auth/me")
    def me(current: AnySession) -> dict[str, Any]:
        if current is None or not current.full:
            return {"signed_in": False}
        return {"signed_in": True, "csrf": current.csrf}

    @router.post("/auth/password")
    def password(body: PasswordBody, response: Response, conn: Conn) -> dict[str, Any]:
        if accounts.is_locked(conn):
            raise HTTPException(429, "too many attempts")
        try:
            matched = accounts.check_password(conn, body.password)
        except accounts.Busy:
            raise HTTPException(429, "too many attempts") from None
        if not matched:
            accounts.record_failure(conn)
            raise _refused()
        token = sessions.start_pending(conn)
        _set_cookie(response, token)
        current = sessions.load(conn, token)
        return {"options": passkeys.ask(conn, settings, current, LOGIN_PURPOSE)}

    @router.post("/auth/passkey")
    def passkey(body: CredentialBody, response: Response, conn: Conn, pending: Pending) -> dict[str, str]:
        if not passkeys.verify(conn, settings, pending, LOGIN_PURPOSE, body.credential):
            accounts.record_failure(conn)
            raise _refused()
        return finish_login(response, conn, pending, "passkey")

    @router.post("/auth/backup-code")
    def backup_code(body: CodeBody, response: Response, conn: Conn, pending: Pending) -> dict[str, str]:
        if not accounts.spend_backup_code(conn, body.code):
            accounts.record_failure(conn)
            raise _refused()
        return finish_login(response, conn, pending, "backup code")

    @router.post("/auth/logout", status_code=204)
    def logout(response: Response, conn: Conn, current: Full) -> None:
        sessions.end(conn, current)
        response.delete_cookie(sessions.COOKIE, path="/", secure=True, httponly=True, samesite="strict")

    # --- First Passkey ---

    @router.post("/auth/enrol/options")
    def enrol_options(body: EnrolStartBody, conn: Conn) -> dict[str, Any]:
        options = passkeys.enrol_options(conn, settings, body.token)
        if options is None:
            raise _refused()
        return {"options": options}

    @router.post("/auth/enrol/finish", status_code=204)
    def enrol_finish(body: EnrolFinishBody, conn: Conn) -> None:
        if not passkeys.enrol_finish(conn, settings, body.token, body.credential, body.name):
            raise _refused()

    # --- Second Factor For One Action ---

    @router.post("/auth/action/options")
    def action_options(body: ActionBody, conn: Conn, current: Full) -> dict[str, Any]:
        purpose = sessions.purpose_of(body.action, body.target)
        return {"options": passkeys.ask(conn, settings, current, purpose)}

    @router.post("/auth/action/answer", status_code=204)
    def action_answer(body: ActionAnswerBody, conn: Conn, current: Full) -> None:
        if accounts.is_locked(conn):
            raise HTTPException(429, "too many attempts")
        purpose = sessions.purpose_of(body.action, body.target)
        passed = False
        if body.credential is not None:
            passed = passkeys.verify(conn, settings, current, purpose, body.credential)
        elif body.code is not None:
            passed = accounts.spend_backup_code(conn, body.code)
        if not passed:
            accounts.record_failure(conn)
            raise _refused()
        sessions.grant_action(conn, current, body.action, body.target)

    actions.attach(router, settings, Conn, Full)

    return router
