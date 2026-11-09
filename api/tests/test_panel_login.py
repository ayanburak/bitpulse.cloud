"""
file: tests/test_panel_login.py
importable: nothing, pytest loads it

description: Tests the panel login with a software passkey, and the ways around it.
"""

import os

import pytest
from fastapi.testclient import TestClient

from bitpulse_api.app import create_app
from bitpulse_api.keys import create_key
from bitpulse_api.panel import accounts, sessions, store
from conftest import ORIGIN, PASSWORD, action, b64, browser_for, password, sign_in, signed_in

# --- Account ---

def test_short_password_is_refused(db):
    with pytest.raises(accounts.InvalidAdmin):
        accounts.init_admin(db, "short")


def test_second_account_needs_reset(db, account):
    with pytest.raises(accounts.InvalidAdmin):
        accounts.init_admin(db, PASSWORD)


def test_enrol_token_works_once(browser, account):
    key, _, token = account
    assert browser.post("/panel-api/auth/enrol/options", json={"token": token}).status_code == 401


def test_enrol_token_expires(db, browser, clock):
    token, _ = accounts.init_admin(db, PASSWORD)
    clock["now"] += accounts.ENROL_MINUTES * 60 + 1
    assert browser.post("/panel-api/auth/enrol/options", json={"token": token}).status_code == 401


def test_password_is_not_stored_plainly(db, account):
    assert PASSWORD not in store.admin(db)["password"]
    assert store.admin(db)["password"].startswith("$argon2id$")


def test_reset_ends_sessions_and_old_passkeys(db, browser, account):
    key, _, _ = account
    sign_in(browser, key)
    accounts.init_admin(db, PASSWORD, reset=True)
    assert not signed_in(browser)
    assert store.passkeys(db) == []


# --- Login ---

def test_password_and_passkey_sign_in(browser, account):
    sign_in(browser, account[0])
    assert signed_in(browser)


def test_cookie_has_every_protection(browser, account):
    cookie = password(browser).headers["set-cookie"]
    assert cookie.startswith("__Host-bitpulse=")
    for part in ("HttpOnly", "Secure", "SameSite=strict", "Path=/"):
        assert part.lower() in cookie.lower()
    assert "domain" not in cookie.lower()


def test_password_alone_is_not_enough(browser, account):
    password(browser)
    assert not signed_in(browser)
    assert browser.post("/panel-api/auth/logout", headers={"X-CSRF-Token": "x"}).status_code == 401


def test_wrong_password(browser, account):
    assert password(browser, "not the right password").status_code == 401


def test_passkey_without_password_is_refused(browser, account):
    key = account[0]
    fake = key.answer({"challenge": b64(os.urandom(32))})
    assert browser.post("/panel-api/auth/passkey", json={"credential": fake}).status_code == 401


def test_challenge_works_once(browser, account):
    key = account[0]
    options = password(browser).json()["options"]
    answer = key.answer(options)
    bad = {**answer, "response": {**answer["response"], "signature": b64(b"wrong")}}
    assert browser.post("/panel-api/auth/passkey", json={"credential": bad}).status_code == 401
    assert browser.post("/panel-api/auth/passkey", json={"credential": answer}).status_code == 401


def test_passkey_of_another_origin_is_refused(browser, account):
    key = account[0]
    options = password(browser).json()["options"]
    key.origin = "https://fake-panel.test"
    assert browser.post("/panel-api/auth/passkey", json={"credential": key.answer(options)}).status_code == 401


def test_passkey_must_verify_its_user(browser, account):
    key = account[0]
    options = password(browser).json()["options"]
    answer = key.answer(options, verified=False)
    assert browser.post("/panel-api/auth/passkey", json={"credential": answer}).status_code == 401


def test_cookie_value_changes_after_second_factor(browser, account):
    password(browser)
    before = browser.cookies.get(sessions.COOKIE)
    browser.cookies.clear()
    key = account[0]
    options = password(browser).json()["options"]
    browser.post("/panel-api/auth/passkey", json={"credential": key.answer(options)})
    assert browser.cookies.get(sessions.COOKIE) != before


def test_new_login_ends_the_old_one(panel_settings, browser, account):
    key = account[0]
    sign_in(browser, key)
    other = browser_for(panel_settings)
    sign_in(other, key)
    assert signed_in(other)
    assert not signed_in(browser)


# --- Backup Codes ---

def test_backup_code_signs_in_once(panel_settings, browser, account):
    _, codes, _ = account
    password(browser)
    assert browser.post("/panel-api/auth/backup-code", json={"code": codes[0].lower()}).status_code == 200
    other = browser_for(panel_settings)
    password(other)
    assert other.post("/panel-api/auth/backup-code", json={"code": codes[0]}).status_code == 401


# --- Session Limits ---

def test_idle_limit(browser, account, clock):
    sign_in(browser, account[0])
    clock["now"] += sessions.IDLE_SECONDS + 1
    assert not signed_in(browser)


def test_activity_keeps_a_session_until_the_full_limit(browser, account, clock):
    sign_in(browser, account[0])
    for _ in range(25):
        clock["now"] += sessions.IDLE_SECONDS - 60
        if clock["now"] - 2_000_000_000 > sessions.FULL_SECONDS:
            break
        assert signed_in(browser)
    assert not signed_in(browser)


def test_session_cookie_survives_closing_the_browser(browser, account):
    key = account[0]
    options = password(browser).json()["options"]
    response = browser.post("/panel-api/auth/passkey", json={"credential": key.answer(options)})
    assert f"Max-Age={sessions.FULL_SECONDS}" in response.headers["set-cookie"]


def test_pending_session_runs_out(browser, account, clock):
    key = account[0]
    options = password(browser).json()["options"]
    clock["now"] += sessions.PENDING_SECONDS + 1
    assert browser.post("/panel-api/auth/passkey", json={"credential": key.answer(options)}).status_code == 401


# --- Forged Requests ---

def test_wrong_origin_is_refused(panel_settings, account):
    other = TestClient(create_app(panel_settings), base_url="https://testserver", headers={"Origin": "https://evil.test"})
    assert other.post("/panel-api/auth/password", json={"password": PASSWORD}).status_code == 403


def test_missing_origin_is_refused(panel_settings, account):
    other = TestClient(create_app(panel_settings), base_url="https://testserver")
    assert other.post("/panel-api/auth/password", json={"password": PASSWORD}).status_code == 403


def test_wrong_csrf_is_refused(browser, account):
    sign_in(browser, account[0])
    assert browser.post("/panel-api/auth/logout", headers={"X-CSRF-Token": "wrong"}).status_code == 403
    assert signed_in(browser)


def test_logout(browser, account):
    csrf = sign_in(browser, account[0])
    assert browser.post("/panel-api/auth/logout", headers={"X-CSRF-Token": csrf}).status_code == 204
    assert not signed_in(browser)


# --- Lock ---

def test_lock_closes_even_the_right_password(browser, account):
    for _ in range(accounts.MAX_FAILURES):
        password(browser, "not the right password")
    assert password(browser).status_code == 429


def test_lock_opens_after_its_time(browser, account, clock):
    for _ in range(accounts.MAX_FAILURES):
        password(browser, "not the right password")
    clock["now"] += accounts.LOCK_SECONDS + 1
    assert password(browser).status_code == 200


def test_admin_unlock(db, browser, account):
    for _ in range(accounts.MAX_FAILURES):
        password(browser, "not the right password")
    accounts.unlock(db)
    assert password(browser).status_code == 200


def test_correct_password_does_not_clear_the_count(db, browser, account):
    for _ in range(accounts.MAX_FAILURES - 1):
        password(browser, "not the right password")
    password(browser)
    assert store.lock_state(db)["failures"] == accounts.MAX_FAILURES - 1


def test_lock_is_written_once_to_the_audit_log(db, browser, account):
    for _ in range(accounts.MAX_FAILURES):
        password(browser, "not the right password")
    assert db.execute("SELECT COUNT(*) FROM audit_log WHERE action = 'login.locked'").fetchone()[0] == 1


def test_too_many_password_checks_at_once_are_refused(browser, account, monkeypatch):
    for _ in range(2):
        assert accounts._hashing.acquire(blocking=False)
    try:
        assert password(browser).status_code == 429
    finally:
        accounts._hashing.release()
        accounts._hashing.release()


# --- Second Factor For One Action ---

def _current(db, browser):
    return sessions.load(db, browser.cookies.get(sessions.COOKIE))


def test_action_grant_is_for_one_use(db, browser, account):
    key = account[0]
    csrf = sign_in(browser, key)
    assert action(browser, key, csrf).status_code == 204
    current = _current(db, browser)
    assert sessions.take_action(db, current, "publish", "story")
    assert not sessions.take_action(db, current, "publish", "story")


def test_action_grant_is_for_one_target(db, browser, account):
    key = account[0]
    csrf = sign_in(browser, key)
    action(browser, key, csrf, target="story")
    assert not sessions.take_action(db, _current(db, browser), "publish", "another")


def test_action_grant_is_for_one_action(db, browser, account):
    key = account[0]
    csrf = sign_in(browser, key)
    action(browser, key, csrf, action_name="publish")
    assert not sessions.take_action(db, _current(db, browser), "withdraw", "story")


def test_action_grant_runs_out(db, browser, account, clock):
    key = account[0]
    csrf = sign_in(browser, key)
    action(browser, key, csrf)
    clock["now"] += sessions.GRANT_SECONDS + 1
    assert not sessions.take_action(db, _current(db, browser), "publish", "story")


def test_answer_for_another_action_is_refused(browser, account):
    key = account[0]
    csrf = sign_in(browser, key)
    headers = {"X-CSRF-Token": csrf}
    body = {"action": "publish", "target": "story"}
    options = browser.post("/panel-api/auth/action/options", json=body, headers=headers).json()["options"]
    answer = {"action": "withdraw", "target": "story", "credential": key.answer(options)}
    assert browser.post("/panel-api/auth/action/answer", json=answer, headers=headers).status_code == 401


def test_action_needs_a_full_session(browser, account):
    password(browser)
    body = {"action": "publish", "target": "story"}
    assert browser.post("/panel-api/auth/action/options", json=body, headers={"X-CSRF-Token": "x"}).status_code == 401


# --- Separation From Device Keys ---

def test_cookie_does_not_open_device_routes(browser, account):
    sign_in(browser, account[0])
    assert browser.get("/stories").status_code == 401


def test_device_key_does_not_open_panel_routes(db, panel_settings, account):
    token = create_key(db, "device")
    other = TestClient(
        create_app(panel_settings),
        base_url="https://testserver",
        headers={"Origin": ORIGIN, "Authorization": f"Bearer {token}"},
    )
    assert other.get("/panel-api/auth/me").json() == {"signed_in": False}
    assert other.post("/panel-api/auth/action/options", json={"action": "a", "target": "b"}).status_code == 401
