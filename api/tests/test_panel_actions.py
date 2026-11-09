"""
file: tests/test_panel_actions.py
importable: nothing, pytest loads it

description: Tests the panel routes for stories, publishing, access and the audit log.
"""

import json

import pytest

from bitpulse_api import jobs, store as main_store
from bitpulse_api.keys import actor_for
from bitpulse_api.panel import store
from conftest import Authenticator, action, b64, browser_for, sign_in


def fields(title="A Sample Story", slug="sample-story", category="world"):
    return {
        "slug": slug,
        "title": title,
        "summary": "A summary.",
        "category": category,
        "kind": "news",
        "sources": [{"name": "A source", "url": "https://example.com/a"}],
        "image": {
            "file": "image.jpg",
            "alt": "Alt text",
            "credit": "Someone",
            "license": "CC0",
            "licenseUrl": "https://example.com/license",
            "source": "https://example.com/image",
        },
        "body": "Body text.\n",
    }


@pytest.fixture
def session(browser, account):
    key = account[0]
    csrf = sign_in(browser, key)
    browser.headers["X-CSRF-Token"] = csrf
    return key, csrf


@pytest.fixture
def image_sha(browser, session, jpeg):
    response = browser.post("/panel-api/images", content=jpeg)
    assert response.status_code == 200
    return response.json()["sha"]


@pytest.fixture
def draft(browser, session, image_sha):
    response = browser.put(
        "/panel-api/stories/sample/draft",
        json={"en": fields(), "tr": fields("Örnek haber", "ornek-haber"), "image": image_sha},
    )
    assert response.status_code == 200
    return "sample"


# Plays the worker: reads the queue the way the service does and reports success.
def finish_job(db, settings, ok=True):
    jobs.tick(db, settings)
    active = main_store.dispatched(db)
    assert active is not None
    stories = sorted(path.name for path in (settings.jobs / str(active["id"]) / "stories").iterdir())
    result = {"ok": ok, "release": f"release-{active['id']}", "ms": 5, "error": None if ok else "broken"}
    (settings.results / f"{active['id']}.json").write_text(json.dumps(result), encoding="utf-8")
    jobs.tick(db, settings)
    return stories


def confirmed(browser, session, name, target):
    key, csrf = session
    assert action(browser, key, csrf, action_name=name, target=target).status_code == 204


def publish(browser, session, db, settings, handle="sample"):
    confirmed(browser, session, "publish", handle)
    assert browser.post(f"/panel-api/stories/{handle}/publish").status_code == 202
    return finish_job(db, settings)


# --- Drafts ---

def test_routes_need_a_session(panel_settings):
    anonymous = browser_for(panel_settings)
    for path in ("/panel-api/stories", "/panel-api/audit", "/panel-api/keys", "/panel-api/status", "/panel-api/account"):
        assert anonymous.get(path).status_code == 401


def test_saving_a_draft_needs_csrf(browser, session, image_sha):
    del browser.headers["X-CSRF-Token"]
    response = browser.put("/panel-api/stories/sample/draft", json={"en": fields(), "tr": fields(), "image": image_sha})
    assert response.status_code == 403


def test_draft_appears_with_its_state(browser, draft):
    row = browser.get("/panel-api/stories").json()[0]
    assert (row["handle"], row["title"], row["state"], row["latest"]) == ("sample", "A Sample Story", "draft", 1)


def test_draft_fields_come_back_whole(browser, draft):
    body = browser.get("/panel-api/stories/sample").json()
    assert body["content"]["tr"]["title"] == "Örnek haber"
    assert [item["number"] for item in body["versions"]] == [1]


def test_invalid_fields_name_the_problem(browser, session, image_sha):
    bad = fields()
    bad["sources"] = []
    response = browser.put("/panel-api/stories/sample/draft", json={"en": bad, "tr": fields(), "image": image_sha})
    assert response.status_code == 422
    assert "sources" in response.json()["detail"]


def test_languages_must_agree(browser, session, image_sha):
    response = browser.put(
        "/panel-api/stories/sample/draft",
        json={"en": fields(), "tr": fields(category="science"), "image": image_sha},
    )
    assert response.status_code == 422


def test_bad_handle_is_refused(browser, session, image_sha):
    response = browser.put("/panel-api/stories/Bad%20Name/draft", json={"en": fields(), "tr": fields(), "image": image_sha})
    assert response.status_code == 422


def test_panel_fields_become_a_valid_file(db, browser, draft):
    from bitpulse_api import content

    record = main_store.latest_version(db, "sample")
    text = content.to_markdown(record["content"]["en"], "2026-01-01 09:00")
    fields_back, body, _, _ = content.parse_file(text, "en.md")
    assert (fields_back["title"], body) == ("A Sample Story", "Body text.\n")


# --- Publishing ---

def test_publish_needs_a_fresh_confirmation(browser, draft):
    assert browser.post("/panel-api/stories/sample/publish").status_code == 403


def test_confirmation_for_another_story_does_not_count(browser, session, draft):
    confirmed(browser, session, "publish", "another")
    assert browser.post("/panel-api/stories/sample/publish").status_code == 403


def test_one_confirmation_is_one_publish(db, panel_settings, browser, session, draft):
    publish(browser, session, db, panel_settings)
    assert browser.post("/panel-api/stories/sample/publish").status_code == 403


def test_publish_goes_live(db, panel_settings, browser, session, draft):
    publish(browser, session, db, panel_settings)
    row = browser.get("/panel-api/stories").json()[0]
    assert row["state"] == "live"
    status = browser.get("/panel-api/status").json()
    assert status["active"] is None and status["last"]["release"].startswith("release-")


def test_new_draft_shows_as_changed(db, panel_settings, browser, session, draft, image_sha):
    publish(browser, session, db, panel_settings)
    browser.put("/panel-api/stories/sample/draft", json={"en": fields("Second"), "tr": fields(), "image": image_sha})
    assert browser.get("/panel-api/stories").json()[0]["state"] == "changed"


def test_audit_names_the_panel(db, panel_settings, browser, session, draft):
    publish(browser, session, db, panel_settings)
    actions = {(row["actor"], row["action"]) for row in browser.get("/panel-api/audit").json()}
    assert ("panel", "publish.request") in actions and ("worker", "publish.done") in actions


# --- Undo ---

def test_undo_brings_back_the_previous_content(db, panel_settings, browser, session, draft, image_sha):
    publish(browser, session, db, panel_settings)
    browser.put("/panel-api/stories/sample/draft", json={"en": fields("Bad"), "tr": fields(), "image": image_sha})
    publish(browser, session, db, panel_settings)
    confirmed(browser, session, "undo", "sample")
    assert browser.post("/panel-api/stories/sample/undo").status_code == 202
    finish_job(db, panel_settings)
    live = main_store.live_versions(db)[0]
    assert live["content"]["en"]["title"] == "A Sample Story"


# A rebuild after undo is what the plain release switch got wrong.
def test_rebuild_after_undo_keeps_the_good_content(db, panel_settings, browser, session, draft, image_sha):
    publish(browser, session, db, panel_settings)
    browser.put("/panel-api/stories/sample/draft", json={"en": fields("Bad"), "tr": fields(), "image": image_sha})
    publish(browser, session, db, panel_settings)
    confirmed(browser, session, "undo", "sample")
    browser.post("/panel-api/stories/sample/undo")
    finish_job(db, panel_settings)
    from bitpulse_api import service

    service.request_rebuild(db, "test")
    jobs.tick(db, panel_settings)
    folder = next(iter((panel_settings.jobs).iterdir()))
    text = next(folder.glob("stories/*/en.md")).read_text(encoding="utf-8")
    assert "A Sample Story" in text and "Bad" not in text


def test_undo_without_an_earlier_version_is_refused(db, panel_settings, browser, session, draft):
    publish(browser, session, db, panel_settings)
    confirmed(browser, session, "undo", "sample")
    assert browser.post("/panel-api/stories/sample/undo").status_code == 409


def test_undo_needs_confirmation(db, panel_settings, browser, session, draft):
    publish(browser, session, db, panel_settings)
    assert browser.post("/panel-api/stories/sample/undo").status_code == 403


# --- Withdraw ---

def test_withdraw_takes_the_story_off_the_build(db, panel_settings, browser, session, draft):
    publish(browser, session, db, panel_settings)
    confirmed(browser, session, "withdraw", "sample")
    assert browser.post("/panel-api/stories/sample/withdraw").status_code == 202
    assert finish_job(db, panel_settings) == []
    assert browser.get("/panel-api/stories").json()[0]["state"] == "withdrawn"


def test_failed_withdraw_leaves_the_story_live(db, panel_settings, browser, session, draft):
    publish(browser, session, db, panel_settings)
    confirmed(browser, session, "withdraw", "sample")
    browser.post("/panel-api/stories/sample/withdraw")
    finish_job(db, panel_settings, ok=False)
    assert browser.get("/panel-api/stories").json()[0]["state"] == "live"


def test_withdrawn_story_keeps_its_versions_and_date(db, panel_settings, browser, session, draft):
    publish(browser, session, db, panel_settings)
    published = main_store.story(db, "sample")["published_at"]
    confirmed(browser, session, "withdraw", "sample")
    browser.post("/panel-api/stories/sample/withdraw")
    finish_job(db, panel_settings)
    assert main_store.story(db, "sample")["published_at"] == published
    assert len(browser.get("/panel-api/stories/sample").json()["versions"]) == 2


def test_withdrawn_story_can_come_back(db, panel_settings, browser, session, draft):
    publish(browser, session, db, panel_settings)
    confirmed(browser, session, "withdraw", "sample")
    browser.post("/panel-api/stories/sample/withdraw")
    finish_job(db, panel_settings)
    publish(browser, session, db, panel_settings)
    assert browser.get("/panel-api/stories").json()[0]["state"] == "live"


# The device copy of the stories must not bring a withdrawn one back into a local build.
def test_withdrawn_story_has_no_key_for_devices(db, panel_settings, browser, session, draft):
    from bitpulse_api import service

    publish(browser, session, db, panel_settings)
    assert service.list_stories(db)[0]["key"] is not None
    confirmed(browser, session, "withdraw", "sample")
    browser.post("/panel-api/stories/sample/withdraw")
    finish_job(db, panel_settings)
    assert service.list_stories(db)[0]["key"] is None
    assert service.read_story(db, "sample")["key"] is None


def test_withdraw_of_a_draft_is_refused(browser, session, draft):
    confirmed(browser, session, "withdraw", "sample")
    assert browser.post("/panel-api/stories/sample/withdraw").status_code == 409


# --- Device Keys ---

def test_key_is_created_once_and_works(db, browser, session):
    confirmed(browser, session, "key.create", "phone")
    response = browser.post("/panel-api/keys", json={"name": "phone"})
    assert response.status_code == 201
    assert actor_for(db, response.json()["key"]) == "phone"
    listed = browser.get("/panel-api/keys").json()[0]
    assert "digest" not in listed and "key" not in listed


def test_key_needs_confirmation(browser, session):
    assert browser.post("/panel-api/keys", json={"name": "phone"}).status_code == 403


def test_bad_key_name_is_refused(browser, session):
    assert browser.post("/panel-api/keys", json={"name": "Bad Name"}).status_code == 422


def test_taken_key_name_is_refused(browser, session):
    confirmed(browser, session, "key.create", "phone")
    browser.post("/panel-api/keys", json={"name": "phone"})
    confirmed(browser, session, "key.create", "phone")
    assert browser.post("/panel-api/keys", json={"name": "phone"}).status_code == 409


def test_revoked_key_stops_working(db, browser, session):
    confirmed(browser, session, "key.create", "phone")
    token = browser.post("/panel-api/keys", json={"name": "phone"}).json()["key"]
    confirmed(browser, session, "key.revoke", "phone")
    assert browser.delete("/panel-api/keys/phone").status_code == 204
    assert actor_for(db, token) is None


# --- Passkeys ---

def add_passkey(browser, session, name="key"):
    confirmed(browser, session, "passkey.add", "panel")
    options = browser.post("/panel-api/account/passkeys/options").json()["options"]
    new = Authenticator()
    response = browser.post("/panel-api/account/passkeys", json={"credential": new.register(options), "name": name})
    return new, response


def test_second_passkey_can_sign_in(panel_settings, browser, session):
    new, response = add_passkey(browser, session)
    assert response.status_code == 204
    other = browser_for(panel_settings)
    sign_in(other, new)


def test_adding_a_passkey_needs_confirmation(browser, session):
    options = browser.post("/panel-api/account/passkeys/options").json()["options"]
    answer = Authenticator().register(options)
    assert browser.post("/panel-api/account/passkeys", json={"credential": answer, "name": "x"}).status_code == 403


def test_last_passkey_can_not_be_removed(db, browser, session):
    key_id = store.passkeys(db)[0]["id"]
    confirmed(browser, session, "passkey.remove", key_id)
    assert browser.delete(f"/panel-api/account/passkeys/{key_id}").status_code == 409


def test_passkey_can_be_removed_when_another_exists(db, browser, session):
    new, _ = add_passkey(browser, session)
    assert store.passkey(db, b64(new.id)) is not None
    confirmed(browser, session, "passkey.remove", b64(new.id))
    assert browser.delete(f"/panel-api/account/passkeys/{b64(new.id)}").status_code == 204
    assert store.passkey(db, b64(new.id)) is None


def test_account_shows_counts_and_no_secrets(browser, session):
    body = browser.get("/panel-api/account").json()
    assert body["backup_codes"] == 10
    assert set(body["passkeys"][0]) == {"id", "name", "created_at", "used_at"}


# --- Audit Paging ---

def test_audit_pages_by_id(db, browser, session):
    with db:
        for number in range(5):
            main_store.add_audit(db, "test", "x", str(number))
    first = browser.get("/panel-api/audit", params={"limit": 2}).json()
    second = browser.get("/panel-api/audit", params={"limit": 2, "before": first[-1]["id"]}).json()
    assert [row["target"] for row in first + second] == ["4", "3", "2", "1"]


def test_device_routes_have_no_way_to_withdraw(db, panel_settings):
    from fastapi.testclient import TestClient

    from bitpulse_api.app import create_app
    from bitpulse_api.keys import create_key

    token = create_key(db, "device")
    device = TestClient(create_app(panel_settings), headers={"Authorization": f"Bearer {token}"})
    for path in ("/stories/x/withdraw", "/stories/x/undo", "/keys"):
        assert device.post(path).status_code in (404, 405)
