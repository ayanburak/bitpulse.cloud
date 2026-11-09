"""
file: tests/test_cli.py
importable: nothing, pytest loads it

description: Checks the command against a small stand-in for the API.
"""

import hashlib

import pytest

from bitpulse_cli.__main__ import handle_of, publish, pull_all, push_draft
from bitpulse_cli.client import ApiError


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
        return {"job": 7}

    def get(self, path):
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
