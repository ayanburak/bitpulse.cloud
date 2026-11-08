"""
file: tests/test_radar.py
importable: nothing, pytest loads this file

description: Checks address cleaning, clustering, ranking picks and the Telegram poll loop.
"""

import time
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from radar.listen import Source, add_item, clean_url, plain_title, tokens
from radar import brief, clip
from radar import rank as ranking
from radar import telegram
from radar.rank import Score, Scores, choose, shortlist
from radar.replay import replay
from radar.store import connect, meta

NOW = datetime(2026, 11, 7, 12, 0, tzinfo=timezone.utc)


def entry(title: str, link: str, hours_ago: float = 1) -> dict:
    stamp = (NOW - timedelta(hours=hours_ago)).timetuple()
    return {"title": title, "link": link, "summary": "Text", "published_parsed": time.struct_time(stamp)}


def test_clean_url_drops_tracking_and_fragment():
    assert clean_url("https://Example.com/a?utm_source=x&id=7#top") == "https://example.com/a?id=7"


def test_google_news_titles_lose_the_outlet():
    assert plain_title("Pandas debut at zoo - Reuters", "Google News") == "Pandas debut at zoo"
    assert plain_title("Pandas debut at zoo - Reuters", "BBC World") == "Pandas debut at zoo - Reuters"


def test_tokens_skip_short_and_common_words():
    assert tokens("The pandas of the Atlanta zoo") == {"pandas", "atlanta", "zoo"}


def test_same_event_from_two_outlets_shares_a_cluster(tmp_path):
    db = connect(str(tmp_path / "r.db"))
    first = add_item(db, Source("A", "", ""), entry("Giant pandas from China debut at Atlanta zoo", "https://a.com/1"), NOW)
    second = add_item(db, Source("B", "", ""), entry("China giant pandas make debut in Atlanta zoo", "https://b.com/2"), NOW)
    other = add_item(db, Source("C", "", ""), entry("Tesla ends Cybertruck production", "https://c.com/3"), NOW)
    assert first == second != other
    assert db.execute("select sources from clusters where id = ?", (first,)).fetchone()[0] == 2


def test_old_stories_never_reach_the_ranking(tmp_path):
    db = connect(str(tmp_path / "r.db"))
    assert add_item(db, Source("A", "", ""), entry("Old story about the Atlanta zoo pandas", "https://a.com/1", hours_ago=30), NOW) is None
    assert db.execute("select count(*) from clusters where sent is null").fetchone()[0] == 0


def score(cluster: int, value: int = 8, category: str = "world", duplicate: int | None = None) -> Score:
    return Score(id=cluster, importance=value, shareable=value, visual=value, category=category, duplicate_of=duplicate, reason="Why")


def fake_model(*events: Score) -> SimpleNamespace:
    answer = Scores(events=list(events))
    return SimpleNamespace(messages=SimpleNamespace(parse=lambda **_: SimpleNamespace(
        stop_reason="end_turn", parsed_output=answer, usage=SimpleNamespace(input_tokens=1, output_tokens=1))))


def collect(sent: list):
    def send(db, cluster, reason):
        db.execute("update clusters set sent = ? where id = ?", (NOW.isoformat(timespec="seconds"), cluster["id"]))
        sent.append(cluster["id"])
    return send


def test_scores_outside_the_round_are_dropped(tmp_path):
    db = connect(str(tmp_path / "r.db"))
    cluster = add_item(db, Source("A", "", ""), entry("Giant pandas debut at Atlanta zoo", "https://a.com/1"), NOW)
    sent = []
    ranking.rank(db, collect(sent), now=NOW, client=fake_model(score(cluster), score(999)))
    assert sent == [cluster]


def test_weak_rounds_send_nothing(tmp_path):
    db = connect(str(tmp_path / "r.db"))
    cluster = add_item(db, Source("A", "", ""), entry("Giant pandas debut at Atlanta zoo", "https://a.com/1"), NOW)
    sent = []
    ranking.rank(db, collect(sent), now=NOW, client=fake_model(score(cluster, value=4)))
    assert sent == []


def test_one_event_per_category_and_best_first():
    chosen = choose([score(1, 7, "sports"), score(2, 9, "sports"), score(3, 8, "world")], limit=3)
    assert [item.id for item in chosen] == [2, 3]


def test_an_event_is_scored_again_only_after_it_grows(tmp_path):
    db = connect(str(tmp_path / "r.db"))
    cluster = add_item(db, Source("A", "", ""), entry("Giant pandas debut at Atlanta zoo", "https://a.com/1"), NOW)
    ranking.rank(db, collect([]), now=NOW, client=fake_model(score(cluster, value=4)))
    assert shortlist(db, {}, NOW) == []
    add_item(db, Source("B", "", ""), entry("China giant pandas debut in Atlanta zoo", "https://b.com/2"), NOW)
    assert [row["id"] for row in shortlist(db, {}, NOW)] == [cluster]


def test_live_blogs_never_reach_the_model(tmp_path):
    db = connect(str(tmp_path / "r.db"))
    add_item(db, Source("A", "", ""), entry("Live: Piastri starts tenth in Brazil", "https://a.com/1"), NOW)
    assert shortlist(db, {}, NOW) == []


def test_duplicates_move_their_stories_to_the_surviving_event(tmp_path):
    db = connect(str(tmp_path / "r.db"))
    first = add_item(db, Source("A", "", ""), entry("Trains collide south of Cairo", "https://a.com/1"), NOW)
    second = add_item(db, Source("B", "", ""), entry("Egypt rail crash leaves several dead", "https://b.com/2"), NOW)
    sent = []
    ranking.rank(db, collect(sent), now=NOW, client=fake_model(score(first), score(second, duplicate=first)))
    assert sent == [first]
    assert db.execute("select sources from clusters where id = ?", (first,)).fetchone()[0] == 2
    assert db.execute("select merged_into from clusters where id = ?", (second,)).fetchone()[0] == first


def test_replay_never_writes_the_source_and_respects_time(tmp_path):
    path = str(tmp_path / "r.db")
    db = connect(path)
    add_item(db, Source("A", "", ""), entry("Giant pandas debut at Atlanta zoo", "https://a.com/1"), NOW)
    db.commit()
    db.close()
    picked = []

    class Model:
        messages = SimpleNamespace(parse=lambda **kwargs: picked.append(kwargs["messages"]) or SimpleNamespace(
            stop_reason="end_turn", parsed_output=Scores(events=[score(1)]), usage=SimpleNamespace(input_tokens=1, output_tokens=1)))

    results = replay("" + path, "2026-11-07", {}, start=11, end=13, client=Model())
    assert [moment[11:13] for moment, _, _ in results] == ["12"]
    assert connect(path).execute("select sent from clusters where id = 1").fetchone()[0] is None


def test_private_addresses_are_refused(monkeypatch):
    monkeypatch.setattr(brief.socket, "getaddrinfo", lambda *_: [(0, 0, 0, "", ("127.0.0.1", 0))])
    with pytest.raises(ValueError):
        brief.public_url("https://inside.example/admin")
    with pytest.raises(ValueError):
        brief.public_url("file:///etc/passwd")
    monkeypatch.setattr(brief.socket, "getaddrinfo", lambda *_: [(0, 0, 0, "", ("93.184.216.34", 0))])
    assert brief.public_url("https://example.com/a") == "https://example.com/a"


def test_share_links_lose_their_tracking():
    assert clip.normal("https://twitter.com/nasa/status/123?s=20&t=abc") == "https://x.com/nasa/status/123"
    assert clip.find_link("look at this https://a.com/b.") == "https://a.com/b"


def test_links_are_saved_only_from_the_editors_chat(tmp_path, monkeypatch):
    db = connect(str(tmp_path / "r.db"))
    said = []
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "7")
    monkeypatch.setattr(telegram, "send", said.append)
    monkeypatch.setattr(clip, "title_of", lambda url: ("Pandas debut at the zoo", "Text"))
    monkeypatch.setattr(clip, "build_brief", lambda db, number: None)

    telegram.handle(db, {"message": {"chat": {"id": 9}, "text": "https://a.com/1"}})
    assert db.execute("select count(*) from clusters").fetchone()[0] == 0

    telegram.handle(db, {"message": {"chat": {"id": 7}, "text": "https://a.com/1"}})
    telegram.handle(db, {"message": {"chat": {"id": 7}, "text": "https://a.com/1"}})
    row = db.execute("select * from clusters").fetchone()
    assert (row["clip"], row["decision"]) == (1, "do") and row["sent"]
    assert db.execute("select count(*) from clusters").fetchone()[0] == 1
    assert said[0].startswith("Saved") and said[1].startswith("Already saved")


def test_check_lists_only_what_the_brief_lacks():
    from radar.check import check_story
    brief = 'Zoo Atlanta said an estimated 1,800 pandas live in the wild. "They inspire curiosity in everyone," King said.'
    story = '---\ntitle: X\n---\nAbout 1,800 pandas live wild, and 52 reserves exist. King said "they inspire curiosity in everyone" in 2026.'
    assert check_story(story, brief) == ["number not in brief: 52"]
    assert check_story('"A quote nobody ever said at all"', brief) == ["quote not in brief: A quote nobody ever said at all"]


class Stop(Exception):
    pass


def test_a_failing_press_does_not_stop_the_poll(tmp_path, monkeypatch):
    db = connect(str(tmp_path / "r.db"))
    calls = iter([[{"update_id": 41}], Stop()])

    def fake_call(method, **params):
        result = next(calls)
        if isinstance(result, Exception):
            raise result
        return result

    def broken(db, update):
        raise RuntimeError("Telegram answerCallbackQuery failed: query is too old")

    monkeypatch.setattr(telegram, "call", fake_call)
    monkeypatch.setattr(telegram, "handle", broken)
    try:
        telegram.poll(db)
    except Stop:
        pass
    assert meta(db, "telegram_offset") == "42"
