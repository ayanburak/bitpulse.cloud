"""
file: tests/test_radar_routes.py
importable: nothing, pytest loads it

description: Checks the radar events, their key scope, the panel list and the link to a story.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from bitpulse_api import store as main_store
from bitpulse_api.app import create_app
from bitpulse_api.keys import RADAR, create_key
from bitpulse_api.panel.actions import KeyBody
from bitpulse_api.radar import store
from conftest import browser_for, sign_in, story_file

FIRST_SEEN = "2026-11-09T10:00:00+00:00"


def event(number=1, stage="sent", score=7.5, **extra):
    return {
        "number": number,
        "title": f"Event number {number}",
        "first_seen": FIRST_SEEN,
        "last_seen": FIRST_SEEN,
        "sources": 2,
        "stage": stage,
        "score": score,
        "links": [{"source": "Outlet", "title": "A title", "url": "https://example.com/a"}],
        **extra,
    }


@pytest.fixture
def radar(settings, conn):
    token = create_key(conn, "radar-test", scope=RADAR)
    return TestClient(create_app(settings), headers={"Authorization": f"Bearer {token}"})


def push(radar, *events):
    response = radar.put("/radar/events", json={"events": list(events)})
    assert response.status_code == 204


# --- Key Scope ---

def test_a_radar_key_opens_only_the_radar_routes(radar, jpeg):
    assert radar.get("/stories").status_code == 401
    assert radar.get("/candidates").status_code == 401
    assert radar.post("/stories/sample/publish").status_code == 401
    assert radar.post("/images", content=jpeg).status_code == 401
    assert radar.post("/rebuild", json={}).status_code == 401
    assert radar.get("/radar/work").status_code == 200


def test_a_device_key_can_not_write_radar_events(client):
    assert client.put("/radar/events", json={"events": [event()]}).status_code == 401
    assert client.get("/radar/work").status_code == 401
    assert client.get("/candidates").status_code == 200


# --- Input From The Web ---

@pytest.mark.parametrize(
    "bad",
    [
        {"links": [{"source": "A", "title": "T", "url": "javascript:alert(1)"}]},
        {"links": [{"source": "A", "title": "T", "url": "file:///etc/passwd"}]},
        {"title": "x" * 401},
        {"reason": "x" * 501},
        {"first_seen": "yesterday"},
        {"stage": "invented"},
        {"impact": 11},
        {"links": [{"source": "A", "title": "T", "url": "https://a.example"}] * 9},
    ],
)
def test_bad_events_are_refused(radar, bad):
    assert radar.put("/radar/events", json={"events": [{**event(), **bad}]}).status_code == 422


def test_a_brief_has_a_size_limit(radar):
    push(radar, event())
    assert radar.put("/radar/events/1/brief", json={"text": "x" * 400_001}).status_code == 422


# --- Decisions ---

def test_a_new_report_keeps_the_decision_and_the_brief(radar, conn):
    push(radar, event())
    radar.post("/radar/events/1/decision", json={"decision": "do"})
    radar.put("/radar/events/1/brief", json={"text": "Brief text"})
    push(radar, {**event(), "title": "A better title"})
    row = store.event(conn, 1)
    assert (row["title"], row["decision"], row["has_brief"]) == ("A better title", "do", 1)


def test_old_answers_move_once_and_never_overwrite(radar, conn):
    push(radar, event(decision="skip"))
    assert store.event(conn, 1)["decided_by"] == "history"
    radar.post("/radar/events/1/decision", json={"decision": "do"})
    push(radar, event(decision="skip"))
    assert store.event(conn, 1)["decision"] == "do"


def test_a_press_in_telegram_asks_for_a_brief_and_not_for_an_update(radar):
    push(radar, event())
    radar.post("/radar/events/1/decision", json={"decision": "do"})
    work = radar.get("/radar/work").json()
    assert [item["number"] for item in work["briefs"]] == [1]
    assert work["decisions"] == []


def test_a_brief_or_a_failure_ends_the_request(radar):
    push(radar, event(1), event(2))
    radar.post("/radar/events/1/decision", json={"decision": "do"})
    radar.post("/radar/events/2/decision", json={"decision": "do"})
    radar.put("/radar/events/1/brief", json={"text": "Ready"})
    radar.put("/radar/events/2/brief", json={"error": "blocked"})
    assert radar.get("/radar/work").json()["briefs"] == []


def test_a_decision_on_an_unknown_event_is_refused(radar):
    assert radar.post("/radar/events/99/decision", json={"decision": "do"}).status_code == 404


def test_only_do_events_without_a_story_are_offered_to_a_session(radar, client):
    push(radar, event(1), event(2), event(3))
    radar.post("/radar/events/1/decision", json={"decision": "do"})
    radar.post("/radar/events/2/decision", json={"decision": "skip"})
    radar.put("/radar/events/1/brief", json={"text": "The brief"})
    assert [row["number"] for row in client.get("/candidates").json()] == [1]
    assert client.get("/candidates/1/brief").json()["text"] == "The brief"
    assert client.get("/candidates/2/brief").status_code == 404


# --- Stories ---

def draft_body(client, jpeg, candidate):
    sha = client.post("/images", content=jpeg).json()["sha"]
    return {"en": story_file(), "tr": story_file("ornek-haber"), "social": "x: hi\n", "image": sha, "candidate": candidate}


def test_a_draft_ties_the_story_to_its_event(radar, client, conn, jpeg):
    push(radar, event())
    radar.post("/radar/events/1/decision", json={"decision": "do"})
    assert client.put("/stories/sample/draft", json=draft_body(client, jpeg, 1)).status_code == 200
    assert store.event(conn, 1)["handle"] == "sample"
    assert store.event(conn, 1)["status"] == "draft"
    assert client.get("/candidates").json() == []


def test_a_draft_for_an_unknown_event_saves_nothing(client, conn, jpeg):
    assert client.put("/stories/sample/draft", json=draft_body(client, jpeg, 99)).status_code == 404
    assert main_store.story(conn, "sample") is None


# --- Cleaning ---

def test_only_old_events_nobody_acted_on_are_removed(radar, conn):
    old = "2026-01-01T10:00:00+00:00"
    push(
        radar,
        {**event(1, "below"), "first_seen": old},
        {**event(2, "sent"), "first_seen": old},
        {**event(3, "below"), "first_seen": old, "decision": "do"},
        event(4, "below"),
    )
    with conn:
        store.prune(conn, "2026-06-01T00:00:00+00:00")
    remaining = [row[0] for row in conn.execute("SELECT number FROM radar_events ORDER BY number")]
    assert remaining == [2, 3, 4]


# --- Panel ---

@pytest.fixture
def panel(browser, account):
    browser.headers["X-CSRF-Token"] = sign_in(browser, account[0])
    return browser


@pytest.fixture
def feed(panel_settings, db):
    token = create_key(db, "radar-test", scope=RADAR)
    return TestClient(create_app(panel_settings), headers={"Authorization": f"Bearer {token}"})


def listed(panel, **query):
    response = panel.get("/panel-api/radar/events", params=query)
    assert response.status_code == 200
    return response.json()


def test_the_panel_routes_need_a_session(panel_settings):
    stranger = browser_for(panel_settings)
    assert stranger.get("/panel-api/radar/events").status_code == 401
    assert stranger.get("/panel-api/instagram").status_code == 401
    assert stranger.post("/panel-api/radar/links", json={"url": "https://a.example"}).status_code == 401


def test_a_change_from_the_panel_needs_the_token(panel, feed):
    push(feed, event())
    del panel.headers["X-CSRF-Token"]
    assert panel.post("/panel-api/radar/events/1/decision", json={"decision": "do"}).status_code == 403


def test_eliminated_events_are_kept_apart_and_counted(panel, feed):
    push(feed, event(1, "sent"), event(2, "below", 5.0), event(3, "reserve", 7.0), event(4, "unseen", -1))
    page = listed(panel, group="eliminated")
    assert [row["number"] for row in page["rows"]] == [3, 2, 4]
    assert page["rows"][2]["score"] is None
    assert page["counts"] == {"below": 1, "reserve": 1, "unseen": 1}
    assert [row["number"] for row in listed(panel, group="candidates")["rows"]] == [1]


def test_one_stage_is_shown_and_the_counts_stay_complete(panel, feed):
    push(feed, event(2, "below", 5.0), event(3, "reserve", 7.0))
    page = listed(panel, group="eliminated", stage="below")
    assert [row["number"] for row in page["rows"]] == [2]
    assert page["counts"] == {"below": 1, "reserve": 1}


def test_the_scored_view_leaves_out_what_the_model_never_read(panel, feed):
    push(feed, event(2, "below", 5.0), event(3, "reserve", 7.0), event(4, "unseen", -1))
    assert [row["number"] for row in listed(panel, group="eliminated", stage="scored")["rows"]] == [3, 2]


def test_pages_cover_every_row_once(panel, feed):
    push(feed, *[event(number, "below", number % 4 + 1.0) for number in range(1, 124)])
    seen, cursor = [], None
    while True:
        query = {"group": "eliminated", "limit": 50}
        page = listed(panel, **({**query, "cursor": cursor} if cursor else query))
        seen += [row["number"] for row in page["rows"]]
        cursor = page["next"]
        if cursor is None:
            break
    assert len(seen) == 123 and len(set(seen)) == 123


def test_candidates_are_paged_too(panel, feed):
    push(feed, *[event(number) for number in range(1, 6)])
    first = listed(panel, limit=2)
    assert [row["number"] for row in first["rows"]] == [5, 4]
    assert [row["number"] for row in listed(panel, limit=2, cursor=first["next"])["rows"]] == [3, 2]


def test_a_bad_cursor_is_refused(panel):
    assert panel.get("/panel-api/radar/events", params={"cursor": "x;drop"}).status_code == 422


def test_filters_narrow_the_list(panel, feed):
    push(
        feed,
        {**event(1, "below"), "category": "world", "sources": 1, "title": "Flood in the north"},
        {**event(2, "below"), "category": "sports", "sources": 5, "title": "Final in the south"},
        {**event(3, "below"), "first_seen": "2026-11-08T10:00:00+00:00", "title": "100% sure"},
    )
    assert [r["number"] for r in listed(panel, group="eliminated", category="sports")["rows"]] == [2]
    assert [r["number"] for r in listed(panel, group="eliminated", min_sources=3)["rows"]] == [2]
    assert [r["number"] for r in listed(panel, group="eliminated", text="flood")["rows"]] == [1]
    assert [r["number"] for r in listed(panel, group="eliminated", day="2026-11-08")["rows"]] == [3]
    assert [r["number"] for r in listed(panel, group="eliminated", text="0%")["rows"]] == [3]
    assert listed(panel, group="eliminated", text="%%%")["rows"] == []


def test_recent_keeps_the_last_day(panel, feed):
    now = datetime.now(timezone.utc)
    fresh = (now - timedelta(hours=2)).isoformat(timespec="seconds")
    stale = (now - timedelta(hours=30)).isoformat(timespec="seconds")
    push(feed, {**event(1, "below"), "first_seen": fresh}, {**event(2, "below"), "first_seen": stale})
    assert [r["number"] for r in listed(panel, group="eliminated", recent="true")["rows"]] == [1]


def test_do_on_an_eliminated_event_makes_it_a_candidate(panel, feed):
    push(feed, event(1, "unseen", -1))
    assert panel.post("/panel-api/radar/events/1/decision", json={"decision": "do"}).status_code == 204
    assert listed(panel, group="eliminated")["rows"] == []
    assert listed(panel, group="candidates")["rows"][0]["status"] == "do"
    work = feed.get("/radar/work").json()
    assert [item["number"] for item in work["briefs"]] == [1]
    assert [item["number"] for item in work["decisions"]] == [1]
    feed.post("/radar/events/1/seen")
    assert feed.get("/radar/work").json()["decisions"] == []


def test_a_failed_brief_can_be_asked_again(panel, feed):
    push(feed, event())
    panel.post("/panel-api/radar/events/1/decision", json={"decision": "do"})
    feed.put("/radar/events/1/brief", json={"error": "blocked"})
    assert panel.get("/panel-api/radar/events/1").json()["brief_error"] == "blocked"
    assert feed.get("/radar/work").json()["briefs"] == []
    panel.post("/panel-api/radar/events/1/retry-brief")
    assert [item["number"] for item in feed.get("/radar/work").json()["briefs"]] == [1]


def test_the_detail_holds_links_and_the_brief_is_separate(panel, feed):
    push(feed, event())
    feed.put("/radar/events/1/brief", json={"text": "Long text"})
    detail = panel.get("/panel-api/radar/events/1").json()
    assert detail["links"][0]["url"] == "https://example.com/a" and detail["has_brief"] is True and "brief" not in detail
    assert panel.get("/panel-api/radar/events/1/brief").json()["text"] == "Long text"


def test_a_decision_is_in_the_audit_log_and_sends_no_notice(panel, feed, db):
    from bitpulse_api.notify import NOTIFIED

    push(feed, event())
    panel.post("/panel-api/radar/events/1/decision", json={"decision": "skip"})
    row = db.execute("SELECT * FROM audit_log WHERE action = 'candidate.decision'").fetchone()
    assert (row["actor"], row["target"], row["detail"]) == ("panel", "R-0001", "skip, panel")
    assert "candidate.decision" not in NOTIFIED


def test_a_link_waits_for_the_radar(panel, feed):
    assert panel.post("/panel-api/radar/links", json={"url": "ftp://a.example"}).status_code == 422
    assert panel.post("/panel-api/radar/links", json={"url": "https://"}).status_code == 422
    link = panel.post("/panel-api/radar/links", json={"url": "https://a.example/news"}).json()["id"]
    assert feed.get("/radar/work").json()["links"] == [{"id": link, "url": "https://a.example/news"}]
    feed.post(f"/radar/links/{link}", json={"number": 7})
    assert feed.get("/radar/work").json()["links"] == []
    assert panel.get("/panel-api/radar/links").json()[0]["state"] == "done"
    assert feed.post(f"/radar/links/{link}", json={"number": 7}).status_code == 404


# --- Keys In The Panel ---

def test_the_panel_can_not_make_a_radar_key():
    assert "scope" not in KeyBody.model_fields
