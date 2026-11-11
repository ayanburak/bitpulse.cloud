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
from radar import api, brief, clip, sync
from radar import rank as ranking
from radar import telegram
from radar.rank import Score, Scores, choose, shortlist
from radar.replay import replay
from radar.store import connect, meta, set_meta

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


def score(cluster: int, value: int = 8, category: str = "world", duplicate: int | None = None, in_scope: bool = True) -> Score:
    return Score(id=cluster, in_scope=in_scope, impact=value, tension=value, visual=value, category=category, duplicate_of=duplicate)


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


def test_two_events_per_category_and_best_first():
    chosen = choose([score(1, 7, "sports"), score(2, 9, "sports"), score(3, 8, "sports"), score(4, 8, "world")], limit=4)
    assert [item.id for item in chosen] == [2, 3, 4]


def four_events(db) -> list[int]:
    titles = ["Giant pandas debut at Atlanta zoo", "Tesla ends Cybertruck production", "Volcano erupts near Reykjavik harbor", "Parliament dissolved after budget vote"]
    return [add_item(db, Source(name, "", ""), entry(title, f"https://{name}.com/1"), NOW) for name, title in zip("WSTU", titles)]


def test_the_long_request_carries_its_own_timeout(tmp_path):
    db = connect(str(tmp_path / "r.db"))
    cluster = four_events(db)[0]
    asked = []

    class Model:
        messages = SimpleNamespace(parse=lambda **kwargs: asked.append(kwargs) or SimpleNamespace(
            stop_reason="end_turn", parsed_output=Scores(events=[score(cluster, 4)]), usage=SimpleNamespace(input_tokens=1, output_tokens=1)))

    ranking.rank(db, collect([]), now=NOW, client=Model())
    assert asked[0]["timeout"] == ranking.REQUEST_SECONDS


def test_an_event_is_scored_once_even_when_it_grows(tmp_path):
    db = connect(str(tmp_path / "r.db"))
    cluster = add_item(db, Source("A", "", ""), entry("Giant pandas debut at Atlanta zoo", "https://a.com/1"), NOW)
    ranking.rank(db, collect([]), now=NOW, client=fake_model(score(cluster, value=4)))
    add_item(db, Source("B", "", ""), entry("China giant pandas debut in Atlanta zoo", "https://b.com/2"), NOW)
    assert shortlist(db, NOW) == []


def test_an_event_the_model_left_out_is_not_asked_again(tmp_path):
    db = connect(str(tmp_path / "r.db"))
    one = add_item(db, Source("A", "", ""), entry("Giant pandas debut at Atlanta zoo", "https://a.com/1"), NOW)
    ranking.rank(db, collect([]), now=NOW, client=fake_model())
    assert shortlist(db, NOW) == [] and ranking.reserve(db, set(), NOW) == []


def test_an_event_outside_the_covered_countries_is_never_sent(tmp_path):
    db = connect(str(tmp_path / "r.db"))
    cluster = add_item(db, Source("A", "", ""), entry("Giant pandas debut at Atlanta zoo", "https://a.com/1"), NOW)
    sent = []
    ranking.rank(db, collect(sent), now=NOW, client=fake_model(score(cluster, value=10, in_scope=False)))
    assert sent == [] and db.execute("select importance from clusters").fetchone()[0] == 0


def test_a_big_round_goes_in_parts_that_see_each_other(tmp_path, monkeypatch):
    monkeypatch.setattr(ranking, "PART_EVENTS", 2)
    db = connect(str(tmp_path / "r.db"))
    ids = four_events(db)
    asked = []

    def parse(**kwargs):
        content = kwargs["messages"][0]["content"]
        asked.append(content)
        listed = [number for number in ids if f"[{number}] " in content.split("Events to score:")[1]]
        return SimpleNamespace(stop_reason="end_turn", parsed_output=Scores(events=[score(number, 4) for number in listed]),
                               usage=SimpleNamespace(input_tokens=1, output_tokens=1))

    ranking.rank(db, collect([]), now=NOW, client=SimpleNamespace(messages=SimpleNamespace(parse=parse)))
    assert len(asked) == 2 and "Giant pandas" in asked[1].split("Events to score:")[0]


def test_a_part_stays_below_the_budget_but_never_comes_out_empty():
    assert ranking.take(["x" * 60, "x" * 60, "x" * 60], 0, 130) == 2
    assert ranking.take(["x" * 200], 0, 130) == 1


def test_a_busy_day_keeps_only_the_newest_titles(tmp_path, monkeypatch):
    monkeypatch.setattr(ranking, "KNOWN_CHARACTERS", 60)
    db = connect(str(tmp_path / "r.db"))
    ids = four_events(db)
    db.execute("update clusters set scored_at = ?", (NOW.isoformat(timespec="seconds"),))
    assert [row["id"] for row in ranking.seen_today(db, NOW)] == ids[-1:]


def test_live_blogs_never_reach_the_model(tmp_path):
    db = connect(str(tmp_path / "r.db"))
    add_item(db, Source("A", "", ""), entry("Live: Piastri starts tenth in Brazil", "https://a.com/1"), NOW)
    assert shortlist(db, NOW) == []


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


# --- Reserve ---

def two_world_events(db) -> tuple[int, int]:
    first = add_item(db, Source("A", "", ""), entry("Giant pandas debut at Atlanta zoo", "https://a.com/1"), NOW)
    second = add_item(db, Source("B", "", ""), entry("Tesla ends Cybertruck production line", "https://b.com/2"), NOW)
    return first, second


def no_model() -> SimpleNamespace:
    def refuse(**_):
        raise AssertionError("the model must not be called")
    return SimpleNamespace(messages=SimpleNamespace(parse=refuse))


def test_an_event_that_lost_its_place_waits_and_costs_no_second_call(tmp_path, monkeypatch):
    monkeypatch.setattr(ranking, "CATEGORY_CAP", 1)
    db = connect(str(tmp_path / "r.db"))
    first, second = two_world_events(db)
    sent = []
    ranking.rank(db, collect(sent), now=NOW, client=fake_model(score(first, 9), score(second, 8)))
    assert sent == [first]
    ranking.rank(db, collect(sent), now=NOW + timedelta(hours=1), client=no_model())
    assert sent == [first, second]


def test_an_event_below_the_bar_never_waits(tmp_path):
    db = connect(str(tmp_path / "r.db"))
    first, second = two_world_events(db)
    ranking.rank(db, collect([]), now=NOW, client=fake_model(score(first, 9), score(second, 4)))
    assert ranking.reserve(db, {first}, NOW) == []


def test_the_reserve_goes_stale(tmp_path, monkeypatch):
    monkeypatch.setattr(ranking, "CATEGORY_CAP", 1)
    db = connect(str(tmp_path / "r.db"))
    first, second = two_world_events(db)
    ranking.rank(db, collect([]), now=NOW, client=fake_model(score(first, 9), score(second, 8)))
    assert ranking.reserve(db, set(), NOW + timedelta(hours=13)) == []


def test_a_new_event_can_merge_into_a_waiting_one(tmp_path, monkeypatch):
    monkeypatch.setattr(ranking, "CATEGORY_CAP", 1)
    db = connect(str(tmp_path / "r.db"))
    first, second = two_world_events(db)
    ranking.rank(db, collect([]), now=NOW, client=fake_model(score(first, 9), score(second, 8)))
    later = NOW + timedelta(hours=1)
    third = add_item(db, Source("C", "", ""), entry("Electric pickup assembly halted by carmaker", "https://c.com/3"), later)
    asked = []
    answer = Scores(events=[score(third, 7, duplicate=second)])

    class Model:
        messages = SimpleNamespace(parse=lambda **kwargs: asked.append(kwargs["messages"][0]["content"]) or SimpleNamespace(
            stop_reason="end_turn", parsed_output=answer, usage=SimpleNamespace(input_tokens=1, output_tokens=1)))

    ranking.rank(db, collect([]), now=later, client=Model())
    assert "Tesla ends Cybertruck" in asked[0]
    assert db.execute("select merged_into from clusters where id = ?", (third,)).fetchone()[0] == second


def test_the_model_reads_more_of_each_summary(tmp_path):
    db = connect(str(tmp_path / "r.db"))
    long = {**entry("Giant pandas debut at Atlanta zoo", "https://a.com/1"), "summary": "x" * 400}
    add_item(db, Source("A", "", ""), long, NOW)
    row = db.execute("select * from clusters").fetchone()
    assert "x" * 400 in ranking.describe(db, row, {})


# --- API ---

class FakeApi:
    def __init__(self):
        self.calls = []
        self.broken = False
        self.waiting = {"briefs": [], "decisions": [], "links": []}

    def __call__(self, method, path, body=None):
        if self.broken:
            raise api.ApiError("down")
        self.calls.append((method, path, body))
        return self.waiting if path == "/radar/work" else None

    def events(self):
        return [item for method, path, body in self.calls if path == "/radar/events" for item in body["events"]]


@pytest.fixture
def fake_api(monkeypatch):
    fake = FakeApi()
    monkeypatch.setenv("RADAR_API_KEY", "key")
    monkeypatch.setattr(api, "_call", fake)
    return fake


@pytest.fixture
def telegram_calls(monkeypatch):
    calls = []
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "7")
    monkeypatch.setattr(telegram, "call", lambda method, **params: calls.append((method, params)) or {"message_id": 55})
    return calls


def press(number=1, choice="do", chat=7):
    return {"callback_query": {"id": "q", "data": f"{choice}:{number}", "message": {"message_id": 5, "chat": {"id": chat}}}}


def one_event(db) -> int:
    return add_item(db, Source("A", "", ""), entry("Giant pandas debut at Atlanta zoo", "https://a.com/1"), NOW)


def test_a_press_goes_to_the_api_and_the_button_changes(tmp_path, fake_api, telegram_calls):
    db = connect(str(tmp_path / "r.db"))
    number = one_event(db)
    telegram.handle(db, press(number))
    assert ("POST", f"/radar/events/{number}/decision", {"decision": "do"}) in fake_api.calls
    assert [method for method, _ in telegram_calls] == ["answerCallbackQuery", "editMessageReplyMarkup"]
    assert db.execute("select decision from clusters").fetchone()[0] is None


def test_a_press_is_refused_while_the_api_is_down(tmp_path, fake_api, telegram_calls):
    db = connect(str(tmp_path / "r.db"))
    number = one_event(db)
    fake_api.broken = True
    telegram.handle(db, press(number))
    assert [method for method, _ in telegram_calls] == ["answerCallbackQuery"]
    assert "press again" in telegram_calls[0][1]["text"]


def test_a_press_from_another_chat_reaches_nothing(tmp_path, fake_api, telegram_calls):
    db = connect(str(tmp_path / "r.db"))
    telegram.handle(db, press(one_event(db), chat=9))
    assert fake_api.calls == [] and telegram_calls == []


def test_a_sent_post_remembers_its_message_and_reaches_the_api(tmp_path, fake_api, telegram_calls):
    db = connect(str(tmp_path / "r.db"))
    number = one_event(db)
    telegram.send_cluster(db, db.execute("select * from clusters").fetchone(), "A reason")
    assert db.execute("select message_id from clusters where id = ?", (number,)).fetchone()[0] == 55
    assert fake_api.events()[0]["stage"] == "sent"


def test_a_stopped_api_does_not_stop_a_post(tmp_path, fake_api, telegram_calls):
    db = connect(str(tmp_path / "r.db"))
    one_event(db)
    fake_api.broken = True
    telegram.send_cluster(db, db.execute("select * from clusters").fetchone())
    assert telegram_calls[0][0] == "sendMessage"


# --- Stages ---

def row_with(db, **columns):
    number = one_event(db)
    for name, value in columns.items():
        db.execute(f"update clusters set {name} = ? where id = ?", (value, number))
    return db.execute("select * from clusters where id = ?", (number,)).fetchone()


SCORED = {"importance": 8, "shareable": 8, "visual": 8, "category": "world", "reason": "Why", "scored_at": NOW.isoformat()}


@pytest.mark.parametrize(
    "columns,stage",
    [
        ({}, "unseen"),
        (SCORED, "reserve"),
        ({**SCORED, "importance": 2, "shareable": 2, "visual": 2}, "below"),
        ({"sent": "2026-11-07T12:30:00+00:00"}, "sent"),
        ({"merged_into": 9, "sent": "2026-11-07T12:30:00+00:00"}, "merged"),
        ({"title": "Live: a final"}, "noise"),
        ({"clip": 1, "sent": NOW.isoformat(timespec="seconds"), "first_seen": NOW.isoformat(timespec="seconds")}, "sent"),
        ({"sent": NOW.isoformat(timespec="seconds"), "first_seen": NOW.isoformat(timespec="seconds")}, None),
    ],
)
def test_stages(tmp_path, columns, stage):
    db = connect(str(tmp_path / "r.db"))
    assert sync.stage_of(row_with(db, **columns)) == stage


# --- Sending Events ---

def test_the_first_round_sends_only_what_comes_after_it(tmp_path, fake_api):
    db = connect(str(tmp_path / "r.db"))
    one_event(db)
    assert sync.sync(db) == 0
    db.execute("update clusters set last_seen = ?", ("2999-01-01T00:00:00+00:00",))
    assert sync.sync(db) == 1


def test_a_failed_round_is_sent_again(tmp_path, fake_api):
    db = connect(str(tmp_path / "r.db"))
    number = one_event(db)
    sync.sync(db)
    db.execute("update clusters set last_seen = ?", ("2999-01-01T00:00:00+00:00",))
    fake_api.broken = True
    with pytest.raises(api.ApiError):
        sync.sync(db)
    fake_api.broken = False
    assert sync.sync(db) == 1 and fake_api.events()[0]["number"] == number


def test_a_bad_link_and_long_text_do_not_block_a_round(tmp_path, fake_api):
    db = connect(str(tmp_path / "r.db"))
    number = one_event(db)
    db.execute("update items set title = ? where cluster = ?", ("t" * 900, number))
    db.execute("insert into items(url, source, title, summary, image, published, seen, cluster) values('javascript:alert(1)', 'B', 'T', '', 0, null, 's', ?)", (number,))
    row = db.execute("select * from clusters").fetchone()
    event = sync.payload(db, row, "unseen")
    assert [link["url"] for link in event["links"]] == ["https://a.com/1"]
    assert len(event["links"][0]["title"]) == 400


def test_a_stored_score_goes_across(tmp_path):
    db = connect(str(tmp_path / "r.db"))
    event = sync.payload(db, row_with(db, **SCORED), "reserve")
    assert (event["score"], event["importance"], event["reason"], event["category"]) == (8.0, 8, "Why", "world")


def test_history_copies_only_what_reached_the_editor(tmp_path, fake_api, monkeypatch):
    monkeypatch.setenv("RADAR_DB", str(tmp_path / "r.db"))
    db = connect()
    reached = row_with(db, sent="2026-11-07T12:30:00+00:00", decision="do")["id"]
    add_item(db, Source("B", "", ""), entry("Tesla ends Cybertruck production line", "https://b.com/2"), NOW)
    brief.brief_path(reached).write_text("Old brief")
    assert sync.sync_history(db) == 1
    assert fake_api.events()[0]["decision"] == "do"
    assert ("PUT", f"/radar/events/{reached}/brief", {"text": "Old brief", "error": None}) in fake_api.calls


def test_a_lost_connection_warns_once_a_day(tmp_path, fake_api, monkeypatch):
    from radar.__main__ import send_events

    db = connect(str(tmp_path / "r.db"))
    said = []
    monkeypatch.setenv("TELEGRAM_TOKEN", "t")
    monkeypatch.setattr(telegram, "send", said.append)
    one_event(db)
    set_meta(db, "api_synced_at", "2000-01-01T00:00:00+00:00")
    fake_api.broken = True
    send_events(db)
    send_events(db)
    assert len(said) == 1


# --- Panel Requests ---

def test_a_panel_decision_updates_the_post_and_leaves_the_running(tmp_path, fake_api, telegram_calls):
    db = connect(str(tmp_path / "r.db"))
    number = row_with(db, message_id=12)["id"]
    fake_api.waiting["decisions"] = [{"number": number, "decision": "skip"}]
    telegram.run_work(db)
    assert telegram_calls[0][1]["reply_markup"]["inline_keyboard"][0][0]["text"] == "Skip ✓"
    assert ("POST", f"/radar/events/{number}/seen", None) in fake_api.calls
    assert db.execute("select sent from clusters").fetchone()[0] and shortlist(db, NOW) == []


def test_an_event_that_never_had_a_post_is_just_acknowledged(tmp_path, fake_api, telegram_calls):
    db = connect(str(tmp_path / "r.db"))
    number = one_event(db)
    fake_api.waiting["decisions"] = [{"number": number, "decision": "do"}]
    telegram.run_work(db)
    assert telegram_calls == [] and ("POST", f"/radar/events/{number}/seen", None) in fake_api.calls


def test_a_brief_goes_to_the_api_and_a_panel_request_stays_quiet(tmp_path, fake_api, telegram_calls, monkeypatch):
    monkeypatch.setenv("RADAR_DB", str(tmp_path / "r.db"))
    db = connect()
    number = one_event(db)
    monkeypatch.setattr(telegram, "build_brief", lambda db, n: brief.brief_path(n).write_text("Text") and brief.brief_path(n))
    fake_api.waiting["briefs"] = [{"number": number, "decided_by": "panel"}]
    telegram.run_work(db)
    assert ("PUT", f"/radar/events/{number}/brief", {"text": "Text", "error": None}) in fake_api.calls
    assert telegram_calls == []


def test_a_failed_brief_is_reported_to_the_api(tmp_path, fake_api, telegram_calls):
    db = connect(str(tmp_path / "r.db"))
    fake_api.waiting["briefs"] = [{"number": 404, "decided_by": "telegram"}]
    telegram.run_work(db)
    method, path, body = fake_api.calls[-1]
    assert (method, path) == ("PUT", "/radar/events/404/brief") and "LookupError" in body["error"]
    assert "failed" in telegram_calls[0][1]["text"]


def test_a_link_from_the_panel_becomes_a_chosen_event(tmp_path, fake_api, telegram_calls, monkeypatch):
    monkeypatch.setenv("RADAR_DB", str(tmp_path / "r.db"))
    db = connect()
    monkeypatch.setattr(clip, "title_of", lambda url: ("Pandas debut at the zoo", "Text"))
    monkeypatch.setattr(clip, "build_brief", lambda db, n: brief.brief_path(n).write_text("Brief"))
    fake_api.waiting["links"] = [{"id": 3, "url": "https://a.com/1"}]
    telegram.run_work(db)
    assert fake_api.events()[0]["decision"] == "do" and fake_api.events()[0]["clip"] is True
    assert ("POST", "/radar/links/3", {"number": 1, "error": None}) in fake_api.calls


def test_one_failing_item_does_not_stop_the_others(tmp_path, fake_api, telegram_calls, monkeypatch):
    db = connect(str(tmp_path / "r.db"))
    number = one_event(db)
    done = []

    def broken(db, number, choice):
        raise RuntimeError("no")

    monkeypatch.setattr(telegram, "reflect", broken)
    monkeypatch.setattr(telegram, "make_brief", lambda db, n, by: done.append(n))
    fake_api.waiting.update(decisions=[{"number": number, "decision": "do"}], briefs=[{"number": number, "decided_by": "panel"}])
    telegram.run_work(db)
    assert done == [number]


def test_without_a_key_the_poll_does_no_panel_work(tmp_path, monkeypatch):
    monkeypatch.delenv("RADAR_API_KEY", raising=False)
    telegram.run_work(connect(str(tmp_path / "r.db")))


def test_a_follow_up_merges_into_a_story_sent_days_ago(tmp_path):
    db = connect(str(tmp_path / "r.db"))
    first = add_item(db, Source("A", "", ""), entry("House opens impeachment of defence secretary", "https://a.com/1"), NOW)
    ranking.rank(db, collect([]), now=NOW, client=fake_model(score(first)))
    later = NOW + timedelta(days=2)
    second = add_item(db, Source("B", "", ""), entry("Pentagon chief faces floor vote", "https://b.com/2", hours_ago=-47), later)
    sent = []
    ranking.rank(db, collect(sent), now=later, client=fake_model(score(second, duplicate=first)))
    assert sent == []
    assert db.execute("select merged_into from clusters where id = ?", (second,)).fetchone()[0] == first
