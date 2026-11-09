"""
file: tests/test_notify.py
importable: nothing, pytest loads it

description: Tests that audit entries become notices and that notices are sent once and in order.
"""

import importlib.util
import json
from pathlib import Path

from bitpulse_api import notify, store

_spec = importlib.util.spec_from_file_location("notify_service", Path(__file__).parent.parent / "deploy" / "notify.py")
service = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(service)


def audit(conn, action, target="sample", detail=""):
    with conn:
        store.add_audit(conn, "panel", action, target, detail)


def notices(settings):
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(settings.notify.glob("*.json"))]


def test_important_entries_become_notices(conn, settings):
    audit(conn, "login.ok")
    notify.relay(conn, settings)
    assert [item["action"] for item in notices(settings)] == ["login.ok"]


def test_ordinary_entries_do_not(conn, settings):
    audit(conn, "draft.save")
    notify.relay(conn, settings)
    assert notices(settings) == []


def test_entry_is_relayed_once(conn, settings):
    audit(conn, "login.ok")
    notify.relay(conn, settings)
    (next(settings.notify.glob("*.json"))).unlink()
    notify.relay(conn, settings)
    assert notices(settings) == []


def test_history_before_the_relay_existed_is_not_sent(tmp_path, settings):
    import sqlite3

    from bitpulse_api import db

    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    for script in db.MIGRATIONS[:-1]:
        for statement in db._statements(script):
            old.execute(statement)
    old.execute(f"PRAGMA user_version = {len(db.MIGRATIONS) - 1}")
    old.execute("INSERT INTO audit_log (at, actor, action, target) VALUES ('now', 'a', 'login.ok', 'b')")
    old.commit()
    old.close()
    conn = db.connect(path)
    notify.relay(conn, settings)
    assert notices(settings) == []
    conn.close()


def test_no_half_written_file_is_visible(conn, settings):
    audit(conn, "login.ok")
    notify.relay(conn, settings)
    assert [path.name.startswith(".") for path in settings.notify.iterdir()] == [False]


def test_message_is_plain_and_cut(tmp_path):
    text = service.message({"action": "publish.failed", "target": "x", "actor": "worker", "at": "now", "detail": "e" * 500})
    assert text.startswith("Bitpulse: publish.failed")
    assert len(text.splitlines()[2]) == service.MAX_DETAIL


def _event(folder, name, action):
    (folder / name).write_text(json.dumps({"action": action, "target": "t", "actor": "a", "at": "n", "detail": ""}))


def test_sent_in_order_and_removed(tmp_path):
    _event(tmp_path, "000000000002.json", "second")
    _event(tmp_path, "000000000001.json", "first")
    sent = []
    assert service.drain(tmp_path, sent.append)
    assert [item.split("\n")[0] for item in sent] == ["Bitpulse: first", "Bitpulse: second"]
    assert list(tmp_path.iterdir()) == []


def test_failure_keeps_the_notice_and_stops(tmp_path):
    _event(tmp_path, "000000000001.json", "first")
    _event(tmp_path, "000000000002.json", "second")

    def fail(_):
        raise OSError("no network")

    assert not service.drain(tmp_path, fail)
    assert len(list(tmp_path.iterdir())) == 2


def test_failure_does_not_print_the_token(tmp_path, capsys):
    _event(tmp_path, "000000000001.json", "first")

    def fail(_):
        raise OSError("https://api.telegram.org/botSECRET/sendMessage")

    service.drain(tmp_path, fail)
    assert "SECRET" not in capsys.readouterr().err
