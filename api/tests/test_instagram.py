"""
file: tests/test_instagram.py
importable: nothing, pytest loads it

description: Tests the insights service routes, the stored pictures and the Instagram routes of the panel.
"""

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from bitpulse_api import db as schema
from bitpulse_api import store as main_store
from bitpulse_api.app import create_app
from bitpulse_api.db import connect
from bitpulse_api.instagram import store, thumbs
from bitpulse_api.keys import INSIGHTS, RADAR, actor_for, create_key
from conftest import sign_in

# --- Helpers ---

def post(post_id="1790001", kind="reel", views=120, **extra):
    return {
        "id": post_id,
        "kind": kind,
        "posted_at": "2026-11-05T14:02:11+0000",
        "permalink": f"https://www.instagram.com/reel/{post_id}/",
        "caption": "Digital sales were 60.7% of Nintendo's game software sales.",
        "counts": {"views": views, "reach": 90, "likes": 7, "comments": 1, "saves": 2, "shares": 3, "watch_ms": 4100},
        **extra,
    }


def picture(width=1080, height=1920, kind="JPEG"):
    output = io.BytesIO()
    Image.new("RGB", (width, height), (200, 40, 40)).save(output, kind, exif=b"Exif\x00\x00secret")
    return output.getvalue()


def client_with(settings, conn, scope):
    token = create_key(conn, f"key-{scope}", scope=scope)
    return TestClient(create_app(settings), headers={"Authorization": f"Bearer {token}"})


@pytest.fixture
def service(settings, conn):
    return client_with(settings, conn, INSIGHTS)


@pytest.fixture
def minute(monkeypatch):
    moment = {"now": "2026-11-11 09:00"}
    monkeypatch.setattr(main_store, "minute", lambda: moment["now"])
    return moment

# --- Keys ---

def test_only_an_insights_key_opens_the_service_routes(settings, conn, client):
    radar = client_with(settings, conn, RADAR)
    for caller in (client, radar, TestClient(create_app(settings))):
        assert caller.put("/insights/posts", json={"posts": [post()]}).status_code == 401
        assert caller.get("/insights/fetched").status_code == 401


def test_an_insights_key_opens_no_story_route(service):
    assert service.get("/stories").status_code == 401
    assert service.get("/candidates").status_code == 401


def test_an_older_database_keeps_its_keys_and_accepts_the_new_scope(settings, monkeypatch):
    full = schema.MIGRATIONS
    monkeypatch.setattr(schema, "MIGRATIONS", full[:-1])
    old = connect(settings.db)
    radar_token = create_key(old, "radar-old", scope=RADAR)
    old.execute("INSERT INTO stories (handle, created_at) VALUES ('sample', '2026-11-01 09:00')")
    old.execute("INSERT INTO social_posts (handle, uploaded_at) VALUES ('sample', '2026-11-01 09:00')")
    old.commit()
    old.close()

    monkeypatch.setattr(schema, "MIGRATIONS", full)
    new = connect(settings.db)
    assert actor_for(new, radar_token, RADAR) == "radar-old"
    assert actor_for(new, create_key(new, "insights-new", scope=INSIGHTS), INSIGHTS) == "insights-new"
    assert new.execute("SELECT name FROM sqlite_master WHERE name = 'social_posts'").fetchone() is None
    new.close()

# --- Posts ---

def test_each_fetch_adds_a_counts_row_and_keeps_one_post(service, conn, minute):
    assert service.put("/insights/posts", json={"posts": [post(views=100)]}).status_code == 200
    minute["now"] = "2026-11-11 10:00"
    service.put("/insights/posts", json={"posts": [post(views=180, caption="Edited on Instagram")]})

    assert conn.execute("SELECT COUNT(*) FROM instagram_posts").fetchone()[0] == 1
    assert conn.execute("SELECT caption FROM instagram_posts").fetchone()[0] == "Edited on Instagram"
    views = [row[0] for row in conn.execute("SELECT views FROM instagram_counts ORDER BY at")]
    assert views == [100, 180]
    assert service.get("/insights/fetched").json() == {"posts": {"1790001": "2026-11-11 10:00"}}


def test_a_count_instagram_does_not_give_stays_empty(service, conn, minute):
    image = post("1790002", kind="image")
    image["counts"] = {"views": 50, "likes": 4}
    service.put("/insights/posts", json={"posts": [image]})
    row = conn.execute("SELECT * FROM instagram_counts WHERE post = '1790002'").fetchone()
    assert (row["views"], row["likes"], row["watch_ms"], row["shares"]) == (50, 4, None, None)


@pytest.mark.parametrize("changes", [
    {"id": "../etc"},
    {"id": "17 9"},
    {"kind": "story"},
    {"permalink": "javascript:alert(1)"},
    {"permalink": "https://instagram.com.evil.example/reel/1/"},
    {"permalink": "http://www.instagram.com/reel/1/"},
    {"caption": "x" * 2201},
    {"posted_at": "yesterday"},
])
def test_a_bad_post_is_refused_before_anything_is_stored(service, conn, changes):
    assert service.put("/insights/posts", json={"posts": [post(**changes)]}).status_code == 422
    assert conn.execute("SELECT COUNT(*) FROM instagram_posts").fetchone()[0] == 0


def test_a_negative_count_is_refused(service):
    bad = post()
    bad["counts"]["views"] = -1
    assert service.put("/insights/posts", json={"posts": [bad]}).status_code == 422

# --- Pictures ---

def test_the_answer_names_posts_without_a_picture_until_one_arrives(service, settings, minute):
    assert service.put("/insights/posts", json={"posts": [post()]}).json() == {"thumbs": ["1790001"]}
    assert service.put("/insights/posts/1790001/thumb", content=picture()).status_code == 204
    assert service.put("/insights/posts", json={"posts": [post()]}).json() == {"thumbs": []}

    with Image.open(settings.thumbs / "1790001.jpg") as stored:
        assert stored.format == "JPEG"
        assert stored.width == 360
        assert "exif" not in stored.info


def test_a_picture_needs_a_known_post_and_a_real_image(service, settings, minute):
    assert service.put("/insights/posts/1790001/thumb", content=picture()).status_code == 404
    service.put("/insights/posts", json={"posts": [post()]})
    assert service.put("/insights/posts/1790001/thumb", content=b"<svg onload=alert(1)>").status_code == 422
    assert service.put("/insights/posts/1790001/thumb", content=picture(kind="GIF")).status_code == 422
    assert not list(settings.thumbs.iterdir())


def test_a_huge_picture_is_cut_off(service, minute):
    service.put("/insights/posts", json={"posts": [post()]})
    assert service.put("/insights/posts/1790001/thumb", content=b"0" * (5 * 1024 * 1024 + 1)).status_code == 413

# --- Days ---

def test_a_day_sent_again_keeps_the_numbers_it_did_not_bring(service, conn):
    service.put("/insights/days", json={"days": [{"day": "2026-11-10", "followers": 410, "profile_views": 33}]})
    service.put("/insights/days", json={"days": [{"day": "2026-11-10", "link_taps": 5}]})
    row = conn.execute("SELECT * FROM instagram_days").fetchone()
    assert (row["followers"], row["profile_views"], row["link_taps"]) == (410, 33, 5)

# --- Panel ---

def test_the_panel_lists_posts_with_their_latest_counts(panel_settings, db, browser, account, monkeypatch):
    monkeypatch.setattr(main_store, "minute", lambda: "2026-11-11 09:00")
    with db:
        store.save_posts(db, [post(views=100), post("1790002", kind="image", posted_at="2026-11-06T08:00:00+0000")], "2026-11-11 09:00")
        store.save_posts(db, [post(views=150)], "2026-11-11 10:00")
        store.save_days(db, [{"day": "2026-11-10", "followers": 410}])
    sign_in(browser, account[0])

    page = browser.get("/panel-api/instagram").json()
    assert [row["id"] for row in page["rows"]] == ["1790002", "1790001"]
    latest = {row["id"]: row["counts"] for row in page["rows"]}["1790001"]
    assert (latest["views"], latest["at"]) == (150, "2026-11-11 10:00")
    assert page["days"][0]["followers"] == 410
    assert [row["id"] for row in browser.get("/panel-api/instagram?kind=reel").json()["rows"]] == ["1790001"]


def test_the_panel_serves_a_stored_picture_only(panel_settings, db, browser, account):
    with db:
        store.save_posts(db, [post()], "2026-11-11 09:00")
    sign_in(browser, account[0])
    assert browser.get("/panel-api/instagram/1790001/thumb").status_code == 404
    assert browser.get("/panel-api/instagram/..%2Fbitpulse.db/thumb").status_code in (404, 422)

    thumbs.accept(panel_settings.thumbs, "1790001", picture())
    with db:
        store.set_thumb(db, "1790001")
    response = browser.get("/panel-api/instagram/1790001/thumb")
    assert (response.status_code, response.headers["content-type"]) == (200, "image/jpeg")
