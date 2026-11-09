"""
file: tests/test_social.py
importable: nothing, pytest loads it

description: Checks the upload, the storage and the panel screen of the finished social files.
"""

import base64
import io

import pytest
from PIL import Image

from bitpulse_api import jobs, social, store
from conftest import browser_for, sign_in, story_file

VIDEO = b"\x00\x00\x00\x18ftypisom" + b"\x00" * 64


def png(size=(1080, 1350)):
    output = io.BytesIO()
    Image.new("RGB", size, (20, 30, 40)).save(output, "PNG")
    return output.getvalue()


def files(**changes):
    result = {"x.txt": b"A post", "caption.txt": "Caption ü".encode(), "post.mp4": VIDEO, "page-1.png": png()}
    return {**result, **changes}


def body(content):
    return {"files": {name: base64.b64encode(data).decode() for name, data in content.items()}}


def make_story(client, jpeg, handle="sample"):
    sha = client.post("/images", content=jpeg).json()["sha"]
    assert client.put(f"/stories/{handle}/draft", json={"en": story_file(), "tr": story_file("ornek"), "image": sha}).status_code == 200


# --- Upload ---

def test_upload_stores_the_set(client, settings, jpeg):
    make_story(client, jpeg)
    response = client.put("/stories/sample/social", json=body(files()))
    assert response.status_code == 200
    assert response.json()["files"] == ["caption.txt", "page-1.png", "post.mp4", "x.txt"]
    assert (settings.social / "sample" / "x.txt").read_bytes() == b"A post"


def test_upload_for_a_missing_story_is_refused(client):
    assert client.put("/stories/nobody/social", json=body(files())).status_code == 404


def test_upload_needs_a_device_key(settings):
    from fastapi.testclient import TestClient
    from bitpulse_api.app import create_app

    assert TestClient(create_app(settings)).put("/stories/sample/social", json=body(files())).status_code == 401


@pytest.mark.parametrize(
    "changes,message",
    [
        ({"page-1.png": b"not an image"}, "page-1.png"),
        ({"post.mp4": b"not a video at all"}, "post.mp4"),
        ({"x.txt": b"\xff\xfe\xff"}, "x.txt"),
        ({"x.txt": b"x" * (social.MAX_TEXT + 1)}, "x.txt"),
        ({"../evil.txt": b"x"}, "unknown file"),
        ({"page-21.png": png()}, "unknown file"),
        ({"page-1.exe": b"x"}, "unknown file"),
        ({"page-1.png": png((4000, 4000))}, "too many pixels"),
    ],
)
def test_bad_files_are_refused_and_nothing_is_stored(client, settings, jpeg, changes, message):
    make_story(client, jpeg)
    response = client.put("/stories/sample/social", json=body(files(**changes)))
    assert response.status_code == 422 and message in response.json()["detail"]
    assert not (settings.social / "sample").exists()


def test_a_missing_file_is_refused(client, jpeg):
    make_story(client, jpeg)
    content = files()
    del content["post.mp4"]
    assert "post.mp4" in client.put("/stories/sample/social", json=body(content)).json()["detail"]


def test_a_broken_body_is_refused(client, jpeg):
    make_story(client, jpeg)
    assert client.put("/stories/sample/social", content=b"nonsense").status_code == 422
    assert client.put("/stories/sample/social", json={"files": {"x.txt": "%%%"}}).status_code == 422


def test_a_page_is_drawn_again(client, settings, jpeg):
    make_story(client, jpeg)
    marked = png() + b"trailing bytes"
    client.put("/stories/sample/social", json=body(files(**{"page-1.png": marked})))
    assert b"trailing bytes" not in (settings.social / "sample" / "page-1.png").read_bytes()


def test_a_new_upload_replaces_the_whole_set(client, settings, jpeg):
    make_story(client, jpeg)
    client.put("/stories/sample/social", json=body(files(**{"page-2.png": png()})))
    client.put("/stories/sample/social", json=body(files()))
    assert not (settings.social / "sample" / "page-2.png").exists()
    assert [path.name for path in settings.social.iterdir()] == ["sample"]


# --- Panel ---

@pytest.fixture
def panel(browser, account):
    browser.headers["X-CSRF-Token"] = sign_in(browser, account[0])
    return browser


@pytest.fixture
def uploaded(panel_settings, db, jpeg):
    from bitpulse_api import images

    sha, width, height = images.accept_upload(panel_settings.images, jpeg)
    with db:
        store.add_image(db, sha, width, height)
        store.ensure_story(db, "sample")
    social.accept(db, panel_settings, "sample", files(), "laptop")
    return "sample"


def test_the_panel_lists_a_post_with_its_text(panel, uploaded):
    row = panel.get("/panel-api/social").json()["rows"][0]
    assert (row["x"], row["caption"], row["pages"]) == ("A post", "Caption ü", ["page-1.png"])


def test_files_are_served_as_downloads(panel, uploaded):
    response = panel.get("/panel-api/social/sample/post.mp4")
    assert response.status_code == 200 and response.headers["content-type"] == "video/mp4"
    assert response.headers["content-disposition"].startswith("attachment")
    assert panel.get("/panel-api/social/sample/page-1.png").headers["content-type"] == "image/png"


@pytest.mark.parametrize("handle,name", [("sample", "secret.db"), ("..", "bitpulse.db"), ("nobody", "x.txt")])
def test_only_stored_files_can_be_read(panel, uploaded, handle, name):
    assert panel.get(f"/panel-api/social/{handle}/{name}").status_code in (404, 405)


def test_marking_as_shared_moves_it_between_the_filters(panel, uploaded):
    assert panel.post("/panel-api/social/sample/shared", json={"shared": True}).status_code == 204
    assert panel.get("/panel-api/social", params={"shared": "false"}).json()["rows"] == []
    assert panel.get("/panel-api/social", params={"shared": "true"}).json()["rows"][0]["shared_at"]
    panel.post("/panel-api/social/sample/shared", json={"shared": False})
    assert panel.get("/panel-api/social", params={"shared": "false"}).json()["rows"][0]["handle"] == "sample"


def test_a_new_upload_keeps_the_shared_mark(panel, panel_settings, db, uploaded):
    panel.post("/panel-api/social/sample/shared", json={"shared": True})
    social.accept(db, panel_settings, "sample", files(), "laptop")
    assert store.social_post(db, "sample")["shared_at"]


def test_a_month_old_post_is_removed(panel_settings, db, uploaded):
    with db:
        db.execute("UPDATE social_posts SET uploaded_at = '2020-01-01 09:00'")
    jobs.prune_old(db, panel_settings)
    assert store.social_post(db, "sample") is None
    assert not (panel_settings.social / "sample").exists()


def test_every_file_is_refused_without_a_session(panel_settings):
    assert browser_for(panel_settings).get("/panel-api/social/sample/x.txt").status_code == 401
