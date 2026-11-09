"""
file: tests/test_db.py
importable: nothing, pytest loads it

description: Tests that the database migrations keep existing data and can run more than once.
"""

import sqlite3
import threading

import pytest

from bitpulse_api import db


# A database from before versioning has the first set of tables and a version of zero.
def _old_database(path):
    conn = sqlite3.connect(path)
    conn.executescript(db.BASE)
    conn.execute("INSERT INTO stories (handle, created_at) VALUES ('sample', '2026-01-01 09:00')")
    conn.execute(
        "INSERT INTO jobs (kind, handle, moment, status, release) "
        "VALUES ('publish', 'sample', '2026-01-01 09:00', 'succeeded', 'release-1')"
    )
    conn.commit()
    assert conn.execute("PRAGMA user_version").fetchone()[0] == 0
    conn.close()


def test_old_database_keeps_its_rows(tmp_path):
    path = tmp_path / "old.db"
    _old_database(path)
    conn = db.connect(path)
    row = conn.execute("SELECT * FROM jobs").fetchone()
    assert (row["handle"], row["release"]) == ("sample", "release-1")
    assert conn.execute("PRAGMA user_version").fetchone()[0] == len(db.MIGRATIONS)
    conn.close()


def test_new_ids_continue_after_the_copied_jobs(tmp_path):
    path = tmp_path / "old.db"
    _old_database(path)
    conn = db.connect(path)
    with conn:
        conn.execute("INSERT INTO jobs (kind, moment, status) VALUES ('rebuild', 'now', 'queued')")
    assert [row["id"] for row in conn.execute("SELECT id FROM jobs ORDER BY id")] == [1, 2]
    conn.close()


def test_withdraw_is_a_job_kind_and_others_are_refused(conn):
    with conn:
        conn.execute("INSERT INTO jobs (kind, moment, status) VALUES ('withdraw', 'now', 'queued')")
    with pytest.raises(sqlite3.IntegrityError):
        with conn:
            conn.execute("INSERT INTO jobs (kind, moment, status) VALUES ('other', 'now', 'queued')")


def test_recorded_history_still_can_not_be_changed(conn):
    with conn:
        conn.execute("INSERT INTO audit_log (at, actor, action, target) VALUES ('now', 'a', 'b', 'c')")
    with pytest.raises(sqlite3.IntegrityError):
        with conn:
            conn.execute("DELETE FROM audit_log")


def test_failed_migration_changes_nothing(tmp_path, monkeypatch):
    path = tmp_path / "old.db"
    _old_database(path)
    monkeypatch.setattr(db, "MIGRATIONS", (*db.MIGRATIONS, "CREATE TABLE half (id);\nBROKEN STATEMENT;\n"))
    with pytest.raises(sqlite3.Error):
        db.connect(path)
    monkeypatch.undo()
    conn = sqlite3.connect(path)
    assert conn.execute("PRAGMA user_version").fetchone()[0] == 0
    assert conn.execute("SELECT name FROM sqlite_master WHERE name = 'half'").fetchone() is None
    conn.close()


# After a code release is undone the older code meets a database that is ahead of it.
def test_newer_database_is_left_alone(tmp_path):
    path = tmp_path / "new.db"
    db.connect(path).close()
    conn = sqlite3.connect(path)
    conn.execute(f"PRAGMA user_version = {len(db.MIGRATIONS) + 5}")
    conn.close()
    conn = db.connect(path)
    assert conn.execute("PRAGMA user_version").fetchone()[0] == len(db.MIGRATIONS) + 5
    conn.close()


def test_two_processes_can_migrate_together(tmp_path):
    path = tmp_path / "old.db"
    _old_database(path)
    errors = []

    def open_it():
        try:
            db.connect(path).close()
        except sqlite3.Error as error:
            errors.append(error)

    threads = [threading.Thread(target=open_it) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
