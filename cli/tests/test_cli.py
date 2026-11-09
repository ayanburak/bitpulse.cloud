"""
file: tests/test_cli.py
importable: nothing, pytest loads it

description: Checks the command against a small stand-in for the API.
"""

import base64
import hashlib
import stat
from datetime import datetime, timezone

import pytest

from bitpulse_cli import client as client_module
from bitpulse_cli.__main__ import (
    candidate_rows,
    days_left,
    handle_of,
    link_skills,
    list_rows,
    number_of,
    publish,
    pull_all,
    push_draft,
    save_brief,
    upload_social,
)
from bitpulse_cli.client import ApiError, SSH_HOST, write_key


# Records calls and answers like the API, so the tests stay about what the command decides.
class FakeApi:
    def __init__(self, status="succeeded", known_image=False):
        self.status = status
        self.known_image = known_image
        self.uploads = 0
        self.drafts = []

    def get_bytes(self, path):
        if self.known_image or self.uploads:
            return b"server image"
        raise ApiError(404, "image not found")

    def post_bytes(self, path, data):
        self.uploads += 1
        return {"sha": "uploaded"}

    def send_json(self, method, path, body):
        if path.endswith("/draft"):
            self.drafts.append((path, body))
            return {"version": 1}
        if path.endswith("/social"):
            self.social = (path, body)
            return {"files": sorted(body["files"])}
        return {"job": 7}

    def get(self, path):
        if path == "/candidates/493/brief":
            return {"text": "The brief"}
        if path.startswith("/jobs/"):
            return {"status": self.status, "error": "boom", "release": "r", "duration_ms": 1}
        if path == "/stories":
            return [{"handle": "done", "key": "2026-02-03-done"}, {"handle": "open", "key": None}]
        return {"key": "2026-02-03-done", "en": "EN", "tr": "TR", "social": "S", "image": hashlib.sha256(b"img").hexdigest()}


@pytest.fixture
def folder(tmp_path):
    path = tmp_path / "2026-01-01-done"
    path.mkdir()
    (path / "en.md").write_text("en")
    (path / "tr.md").write_text("tr")
    (path / "image.jpg").write_bytes(b"img")
    return path


def test_handle_drops_the_date(tmp_path):
    assert handle_of(tmp_path / "2026-01-01-some-story") == "some-story"
    assert handle_of(tmp_path / "some-story") == "some-story"


def test_draft_uploads_a_new_image(folder):
    api = FakeApi()
    push_draft(api, folder)
    assert api.uploads == 1
    assert api.drafts[0][0] == "/stories/done/draft"
    assert api.drafts[0][1]["image"] == "uploaded" and api.drafts[0][1]["social"] == ""


def test_draft_does_not_send_an_image_the_server_has(folder):
    api = FakeApi(known_image=True)
    push_draft(api, folder)
    assert api.uploads == 0
    assert api.drafts[0][1]["image"] == hashlib.sha256(b"img").hexdigest()


def test_publish_moves_the_folder_to_its_final_key(folder):
    result = publish(FakeApi(), folder)
    assert result["folder"].endswith("2026-02-03-done")
    assert not folder.exists()
    assert (folder.parent / "2026-02-03-done" / "en.md").read_text() == "EN"


def test_failed_publish_keeps_the_working_folder(folder):
    with pytest.raises(ApiError, match="boom"):
        publish(FakeApi(status="failed"), folder)
    assert folder.exists()


def test_pull_all_skips_stories_never_published(tmp_path):
    assert pull_all(FakeApi(known_image=True), tmp_path) == 1
    assert (tmp_path / "2026-02-03-done").is_dir()
    assert not (tmp_path / "open").exists()


def test_pull_writes_no_social_file_for_a_story_without_social_text(tmp_path):
    api = FakeApi(known_image=True)
    story = api.get("/stories/done") | {"social": ""}
    api.get = lambda path: [{"handle": "done", "key": "2026-02-03-done"}] if path == "/stories" else story
    pull_all(api, tmp_path)
    assert not (tmp_path / "2026-02-03-done" / "social.yaml").exists()


def test_list_marks_unpublished_stories():
    rows = list_rows([
        {"published_at": "2026-02-03 09:00", "handle": "done", "latest": 3},
        {"published_at": None, "handle": "open", "latest": 1},
    ])
    assert "done  v3" in rows[0] and rows[1].startswith("not published")


def test_days_left():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert days_left("2026-01-11 00:00", now) == 10
    assert days_left("2025-12-30 00:00", now) < 0


def test_key_file_is_private(tmp_path, monkeypatch):
    path = tmp_path / "config" / "key"
    monkeypatch.setattr(client_module, "KEY_FILE", path)
    write_key("  secret\n")
    assert path.read_text() == "secret\n"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700


def test_tunnel_does_not_use_the_root_account():
    assert SSH_HOST != "vps"


def test_a_draft_can_name_its_radar_event(folder):
    api = FakeApi(known_image=True)
    push_draft(api, folder, 493)
    assert api.drafts[0][1]["candidate"] == 493


def test_a_plain_draft_sends_no_event(folder):
    api = FakeApi(known_image=True)
    push_draft(api, folder)
    assert "candidate" not in api.drafts[0][1]


def test_publish_passes_the_event_on(folder):
    api = FakeApi(known_image=True)
    publish(api, folder, 493)
    assert api.drafts[0][1]["candidate"] == 493


def test_event_numbers():
    assert number_of("R-0493") == 493 and number_of("r-12") == 12 and number_of("7") == 7
    with pytest.raises(ValueError):
        number_of("story")


def test_a_brief_is_saved_under_its_number(tmp_path):
    path = save_brief(FakeApi(), 493, tmp_path / "briefs")
    assert path.name == "R-0493.md" and path.read_text() == "The brief"


def test_candidates_show_whether_the_brief_is_ready():
    rows = candidate_rows([{"number": 7, "has_brief": 1, "title": "A"}, {"number": 8, "has_brief": 0, "title": "B"}])
    assert rows[0].startswith("R-0007  brief ready") and "no brief" in rows[1]


def test_only_finished_social_files_are_uploaded(tmp_path):
    post = tmp_path / "2026-11-09-a-story"
    (post / "images").mkdir(parents=True)
    (post / "x.txt").write_bytes(b"post")
    (post / "page-1.png").write_bytes(b"png")
    (post / "reel.mp4").write_bytes(b"not this one")
    api = FakeApi()
    assert upload_social(api, post) == ["page-1.png", "x.txt"]
    assert api.social[0] == "/stories/a-story/social"
    assert base64.b64decode(api.social[1]["files"]["x.txt"]) == b"post"


def repository(tmp_path):
    (tmp_path / "workflows" / "haber").mkdir(parents=True)
    (tmp_path / "workflows" / "haber" / "SKILL.md").write_text("skill")
    (tmp_path / "workflows" / "notes").mkdir()
    return tmp_path


def test_skills_are_linked_and_linking_twice_is_fine(tmp_path):
    root = repository(tmp_path)
    assert link_skills(root) == ["haber"] and link_skills(root) == ["haber"]
    assert (root / ".claude" / "skills" / "haber" / "SKILL.md").read_text() == "skill"
    assert not (root / ".claude" / "skills" / "notes").exists()


def test_linking_never_replaces_a_real_folder(tmp_path):
    root = repository(tmp_path)
    kept = root / ".claude" / "skills" / "haber"
    kept.mkdir(parents=True)
    (kept / "mine.md").write_text("mine")
    with pytest.raises(OSError, match="already exists"):
        link_skills(root)
    assert (kept / "mine.md").read_text() == "mine"
