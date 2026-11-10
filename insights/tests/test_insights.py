"""
file: tests/test_insights.py
importable: nothing, pytest loads it

description: Tests the insights service without Meta and without the API.
"""

from datetime import datetime, timezone

import pytest

from insights import http
from insights import round as rounds
from insights.meta import Meta, kind_of

NOW = datetime(2026, 11, 11, 9, 30, tzinfo=timezone.utc)

# --- Helpers ---

def post(post_id="1790001", timestamp="2026-11-10T14:02:11+0000", **extra):
    return {
        "id": post_id,
        "media_type": "VIDEO",
        "media_product_type": "REELS",
        "timestamp": timestamp,
        "permalink": f"https://www.instagram.com/reel/{post_id}/",
        "caption": "A caption",
        "thumbnail_url": f"https://scontent.cdninstagram.com/{post_id}.jpg",
        **extra,
    }


class FakeMeta:
    def __init__(self, posts, broken=()):
        self.items = posts
        self.broken = broken
        self.days = []

    def posts(self):
        yield from self.items

    def counts(self, item):
        if item["id"] in self.broken:
            raise http.HttpError("Meta failed", 500)
        return {"views": 10, "reach": 8}

    def profile(self):
        return {"followers_count": 410}

    def day(self, since, until):
        self.days.append((since, until))
        return {"profile_views": 3}


class FakeApi:
    def __init__(self, fetched=None, missing=None):
        self.known = fetched or {}
        self.missing = missing
        self.posts, self.thumbs, self.days = [], {}, []

    def fetched(self):
        return self.known

    def save_posts(self, rows):
        self.posts += rows
        return [row["id"] for row in rows] if self.missing is None else self.missing

    def save_thumb(self, post_id, data):
        self.thumbs[post_id] = data

    def save_days(self, days):
        self.days += days

# --- Which Posts ---

@pytest.mark.parametrize(("timestamp", "last", "expected"), [
    ("2026-11-10T14:02:11+0000", None, True),
    ("2026-11-10T14:02:11+0000", "2026-11-11 09:00", True),
    ("2026-10-01T14:02:11+0000", None, True),
    ("2026-10-01T14:02:11+0000", "2026-11-11 08:00", False),
    ("2026-10-01T14:02:11+0000", "2026-11-10 09:00", True),
])
def test_a_young_post_is_read_every_round_and_an_old_one_daily(timestamp, last, expected):
    assert rounds.due(post(timestamp=timestamp), last, NOW) is expected


@pytest.mark.parametrize(("item", "kind"), [
    ({"media_type": "VIDEO", "media_product_type": "REELS"}, "reel"),
    ({"media_type": "CAROUSEL_ALBUM", "media_product_type": "FEED"}, "carousel"),
    ({"media_type": "IMAGE", "media_product_type": "FEED"}, "image"),
])
def test_the_kind_follows_what_meta_reports(item, kind):
    assert kind_of(item) == kind

# --- Round ---

def test_a_round_sends_due_posts_and_only_the_missing_pictures(monkeypatch):
    monkeypatch.setattr(http, "download", lambda url, hosts: url.encode())
    old = post("1790002", timestamp="2026-10-01T10:00:00+0000")
    api = FakeApi(fetched={"1790002": "2026-11-11 08:00"}, missing=["1790001"])
    result = rounds.run(FakeMeta([post(), old]), api, days=2, now=NOW)

    assert [row["id"] for row in api.posts] == ["1790001"]
    assert api.posts[0]["kind"] == "reel"
    assert api.posts[0]["counts"] == {"views": 10, "reach": 8}
    assert api.thumbs == {"1790001": b"https://scontent.cdninstagram.com/1790001.jpg"}
    assert result == {"posts": 1, "pictures": 1, "failed": 0}


def test_one_failing_post_does_not_stop_the_others(monkeypatch):
    monkeypatch.setattr(http, "download", lambda url, hosts: b"")
    api = FakeApi(missing=[])
    result = rounds.run(FakeMeta([post(), post("1790002")], broken={"1790001"}), api, now=NOW)
    assert [row["id"] for row in api.posts] == ["1790002"]
    assert result["failed"] == 1


def test_a_picture_that_can_not_be_downloaded_is_skipped(monkeypatch):
    def refuse(url, hosts):
        raise http.HttpError("picture address is not on an allowed host")
    monkeypatch.setattr(http, "download", refuse)
    api = FakeApi()
    assert rounds.run(FakeMeta([post()]), api, now=NOW)["pictures"] == 0
    assert api.thumbs == {}


def test_the_days_are_today_followers_and_finished_past_days():
    meta = FakeMeta([])
    api = FakeApi()
    rounds.run(meta, api, days=2, now=NOW)
    assert api.days == [
        {"day": "2026-11-11", "followers": 410},
        {"day": "2026-11-10", "profile_views": 3},
        {"day": "2026-11-09", "profile_views": 3},
    ]
    assert meta.days[0] == (int(datetime(2026, 11, 10, tzinfo=timezone.utc).timestamp()), int(datetime(2026, 11, 11, tzinfo=timezone.utc).timestamp()))

# --- Meta ---

def test_a_refused_metric_is_left_out_and_the_rest_kept(monkeypatch):
    calls = []

    def answer(url, headers):
        assert headers == {"Authorization": "Bearer secret"}
        assert "secret" not in url
        metric = url.split("metric=")[1].split("&")[0]
        calls.append(metric)
        if "%2C" in metric or metric == "shares":
            raise http.HttpError("unsupported metric", 400)
        return {"data": [{"name": metric, "values": [{"value": 5}]}]}

    monkeypatch.setattr(http, "get_json", answer)
    counts = Meta("secret", "178414").counts(post())
    assert counts == {"views": 5, "reach": 5, "likes": 5, "comments": 5, "saves": 5, "watch_ms": 5}
    assert "shares" in calls


def test_a_failure_other_than_a_refused_metric_is_raised(monkeypatch):
    def answer(url, headers):
        raise http.HttpError("server error", 500)
    monkeypatch.setattr(http, "get_json", answer)
    with pytest.raises(http.HttpError):
        Meta("secret", "178414").counts(post())


def test_account_numbers_are_read_from_total_value(monkeypatch):
    monkeypatch.setattr(http, "get_json", lambda url, headers: {"data": [
        {"name": "profile_views", "total_value": {"value": 12}},
        {"name": "profile_links_taps", "total_value": {"value": 2}},
    ]})
    assert Meta("secret", "178414").day(0, 86400) == {"profile_views": 12, "link_taps": 2}


def test_posts_follow_pages_and_skip_stories(monkeypatch):
    pages = {
        "first": {"data": [post("1"), post("2", media_product_type="STORY")], "paging": {"next": "https://graph.facebook.com/next"}},
        "https://graph.facebook.com/next": {"data": [post("3")]},
    }
    monkeypatch.setattr(http, "get_json", lambda url, headers: pages.get(url) or pages["first"])
    assert [item["id"] for item in Meta("secret", "178414").posts()] == ["1", "3"]

# --- Pictures ---

@pytest.mark.parametrize(("url", "allowed"), [
    ("https://scontent-fra5-1.cdninstagram.com/v/a.jpg", True),
    ("https://scontent.xx.fbcdn.net/v/a.jpg", True),
    ("http://scontent.cdninstagram.com/a.jpg", False),
    ("https://cdninstagram.com.evil.example/a.jpg", False),
    ("https://evilcdninstagram.com/a.jpg", False),
    ("https://127.0.0.1/a.jpg", False),
])
def test_pictures_come_only_from_the_instagram_picture_servers(url, allowed):
    assert http._allowed(url, rounds.PICTURE_HOSTS) is allowed
