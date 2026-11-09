"""
file: tests/test_api.py
importable: nothing, pytest loads it

description: Checks drafts, publishing jobs, keys, images and the protected tables.
"""

import io
import json
import sqlite3

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from bitpulse_api import jobs, store
from bitpulse_api.app import create_app
from bitpulse_api.content import InvalidDraft, parse_draft, stamp_updates, to_markdown
from bitpulse_api.keys import create_key
from conftest import story_file

UPDATE = """updates:
  - note: "A new detail"
"""


def draft(client, jpeg, handle="sample", en=None, tr=None):
    sha = client.post("/images", content=jpeg).json()["sha"]
    body = {"en": en or story_file(), "tr": tr or story_file("ornek-haber"), "social": "x: hi\n", "image": sha}
    return client.put(f"/stories/{handle}/draft", json=body)


# Stands in for the render worker: it answers the job that is waiting in the queue.
def answer(settings, conn, job_id, ok=True):
    jobs.tick(conn, settings)
    assert (settings.queue / str(job_id)).exists()
    result = {"id": job_id, "ok": ok, "release": "release-x" if ok else None, "error": None if ok else "boom", "ms": 5}
    (settings.results / f"{job_id}.json").write_text(json.dumps(result))
    jobs.tick(conn, settings)


# --- Keys ---

def test_rejects_requests_without_a_valid_key(settings):
    plain = TestClient(create_app(settings))
    assert plain.get("/stories").status_code == 401
    assert plain.get("/stories", headers={"Authorization": "Bearer nope"}).status_code == 401
    assert plain.get("/health").status_code == 200


def test_expired_and_revoked_keys_stop_working(settings, conn):
    plain = TestClient(create_app(settings))
    expired = create_key(conn, "old", days=-1)
    assert plain.get("/stories", headers={"Authorization": f"Bearer {expired}"}).status_code == 401
    live = create_key(conn, "phone")
    assert plain.get("/stories", headers={"Authorization": f"Bearer {live}"}).status_code == 200
    with conn:
        store.revoke_key(conn, "phone")
    assert plain.get("/stories", headers={"Authorization": f"Bearer {live}"}).status_code == 401


def test_stores_only_a_hash_of_the_key(conn):
    token = create_key(conn, "laptop")
    assert token not in str([tuple(row) for row in conn.execute("SELECT * FROM api_keys")])


# --- Drafts ---

def test_rejects_invalid_drafts(client, jpeg):
    assert draft(client, jpeg, en="no frontmatter").status_code == 422
    assert draft(client, jpeg, en=story_file("Bad Slug")).status_code == 422
    assert draft(client, jpeg, handle="Bad Name").status_code == 422
    different = story_file("ornek-haber").replace("category: world", "category: science")
    assert draft(client, jpeg, tr=different).status_code == 422


def test_rejects_a_draft_with_an_unknown_image(client):
    body = {"en": story_file(), "tr": story_file("ornek"), "image": "0" * 64}
    assert client.put("/stories/sample/draft", json=body).status_code == 404


def test_every_draft_is_a_new_version(client, jpeg):
    assert draft(client, jpeg).json() == {"version": 1}
    assert draft(client, jpeg).json() == {"version": 2}


def test_versions_and_audit_can_not_be_rewritten(client, jpeg, conn):
    draft(client, jpeg)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE story_versions SET content = ''")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM story_versions")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM audit_log")


# --- Images ---

def test_upload_drops_metadata_and_limits_width(client, settings):
    output = io.BytesIO()
    Image.new("RGB", (3000, 1500), "red").save(output, "PNG")
    answer_body = client.post("/images", content=output.getvalue()).json()
    assert (answer_body["width"], answer_body["height"]) == (2000, 1000)
    stored = Image.open(settings.images / f"{answer_body['sha']}.jpg")
    assert stored.format == "JPEG" and not stored.getexif()


def test_upload_refuses_what_is_not_a_cover_image(client):
    assert client.post("/images", content=b"<svg onload=alert(1)>").status_code == 422
    small = io.BytesIO()
    Image.new("RGB", (800, 600)).save(small, "JPEG")
    assert client.post("/images", content=small.getvalue()).status_code == 422


# --- Publishing ---

def test_server_sets_the_publishing_moment(client, jpeg, settings, conn, monkeypatch):
    draft(client, jpeg)
    monkeypatch.setattr(store, "minute", lambda: "2026-03-04 15:16")
    job_id = client.post("/stories/sample/publish").json()["job"]
    jobs.tick(conn, settings)
    text = (settings.jobs / str(job_id) / "stories" / "2026-03-04-sample" / "en.md").read_text()
    assert "date: '2026-03-04'" in text and "time: '15:16'" in text
    assert "2026-01-01" not in text


def test_story_is_live_only_after_the_worker_succeeds(client, jpeg, settings, conn):
    draft(client, jpeg)
    job_id = client.post("/stories/sample/publish").json()["job"]
    assert store.story(conn, "sample")["published_at"] is None
    answer(settings, conn, job_id, ok=False)
    assert client.get(f"/jobs/{job_id}").json()["status"] == "failed"
    assert store.story(conn, "sample")["published_at"] is None

    job_id = client.post("/stories/sample/publish").json()["job"]
    answer(settings, conn, job_id)
    assert client.get(f"/jobs/{job_id}").json()["status"] == "succeeded"
    assert store.story(conn, "sample")["published_at"] is not None
    assert not (settings.jobs / str(job_id)).exists()
    assert not (settings.results / f"{job_id}.json").exists()


def test_publishing_again_keeps_the_first_moment(client, jpeg, settings, conn, monkeypatch):
    draft(client, jpeg)
    monkeypatch.setattr(store, "minute", lambda: "2026-03-04 15:16")
    answer(settings, conn, client.post("/stories/sample/publish").json()["job"])
    draft(client, jpeg)
    monkeypatch.setattr(store, "minute", lambda: "2026-03-05 10:00")
    answer(settings, conn, client.post("/stories/sample/publish").json()["job"])
    assert store.story(conn, "sample")["published_at"] == "2026-03-04 15:16"


def test_second_job_waits_and_sees_the_first_story(client, jpeg, settings, conn):
    draft(client, jpeg, "first")
    draft(client, jpeg, "second", story_file("second-en"), story_file("second-tr"))
    first = client.post("/stories/first/publish").json()["job"]
    second = client.post("/stories/second/publish").json()["job"]
    jobs.tick(conn, settings)
    assert not (settings.jobs / str(second)).exists()
    answer(settings, conn, first)
    folders = [path.name for path in (settings.jobs / str(second) / "stories").iterdir()]
    assert any(name.endswith("-first") for name in folders) and any(name.endswith("-second") for name in folders)


def test_rebuild_can_stay_away_from_the_live_site(client, jpeg, settings, conn):
    draft(client, jpeg)
    answer(settings, conn, client.post("/stories/sample/publish").json()["job"])
    job_id = client.post("/rebuild", json={"go_live": False}).json()["job"]
    jobs.tick(conn, settings)
    assert json.loads((settings.jobs / str(job_id) / "job.json").read_text())["goLive"] is False


def test_read_story_returns_the_files(client, jpeg, settings, conn):
    draft(client, jpeg)
    answer(settings, conn, client.post("/stories/sample/publish").json()["job"])
    body = client.get("/stories/sample").json()
    assert body["key"].endswith("-sample") and "Body text." in body["en"] and body["social"] == "x: hi\n"


# --- Text ---

def test_markdown_round_trip_keeps_the_body_exactly():
    parsed = parse_draft(story_file(), story_file("ornek"))
    text = to_markdown(parsed["en"], "2026-02-03 04:05")
    assert text.endswith("---\n\nBody text.\n")
    assert parse_draft(text, text.replace("sample-story", "ornek"))["en"]["body"] == parsed["en"]["body"]


def test_new_updates_get_valid_increasing_times():
    parsed = parse_draft(story_file(extra=UPDATE + '  - note: "Another"\n'), story_file("ornek", UPDATE + '  - note: "Baska"\n'))
    stamped = stamp_updates(parsed, "2026-03-04 15:16", "2026-03-04 15:16")
    assert [u["time"] for u in stamped["en"]["updates"]] == ["2026-03-04 15:17", "2026-03-04 15:18"]
    assert [u["time"] for u in stamped["tr"]["updates"]] == ["2026-03-04 15:17", "2026-03-04 15:18"]


def test_unknown_fields_are_refused():
    with pytest.raises(InvalidDraft):
        parse_draft(story_file(extra="surprise: yes\n"), story_file("ornek"))
