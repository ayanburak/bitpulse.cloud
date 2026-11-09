"""
file: tests/test_importer.py
importable: nothing, pytest loads it

description: Checks the one time import of published stories.
"""

import pytest

from bitpulse_api import store
from bitpulse_api.importer import import_stories
from conftest import story_file


def make(root, key, jpeg, en=None, tr=None):
    folder = root / key
    folder.mkdir(parents=True)
    (folder / "en.md").write_text(en or story_file(f"{key[11:]}-en"))
    (folder / "tr.md").write_text(tr or story_file(f"{key[11:]}-tr"))
    (folder / "image.jpg").write_bytes(jpeg)
    (folder / "social.yaml").write_text("x: post\n")


def test_keeps_moment_and_image_bytes(tmp_path, settings, conn, jpeg):
    make(tmp_path / "s", "2026-01-01-kept", jpeg)
    assert import_stories(conn, settings, tmp_path / "s", set()) == ["2026-01-01-kept"]
    assert store.story(conn, "kept")["published_at"] == "2026-01-01 09:00"
    record = store.live_versions(conn)[0]
    assert (settings.images / f"{record['image']}.jpg").read_bytes() == jpeg
    assert record["content"]["social"] == "x: post\n"


def test_leaves_out_skipped_stories_and_links_to_them(tmp_path, settings, conn, jpeg):
    root = tmp_path / "s"
    make(root, "2026-01-01-gone", jpeg)
    linked = story_file("kept-en").replace("Body text.", "See [the chips](/en/stories/gone-en/) here.")
    make(root, "2026-01-02-kept", jpeg, en=linked)
    import_stories(conn, settings, root, {"2026-01-01-gone"})
    assert store.story(conn, "gone") is None
    assert "See the chips here." in store.live_versions(conn)[0]["content"]["en"]["body"]


def test_refuses_a_database_that_already_has_stories(tmp_path, settings, conn, jpeg):
    make(tmp_path / "s", "2026-01-01-kept", jpeg)
    import_stories(conn, settings, tmp_path / "s", set())
    with pytest.raises(ValueError):
        import_stories(conn, settings, tmp_path / "s", set())


def test_refuses_a_skip_name_that_does_not_exist(tmp_path, settings, conn, jpeg):
    make(tmp_path / "s", "2026-01-01-kept", jpeg)
    with pytest.raises(ValueError):
        import_stories(conn, settings, tmp_path / "s", {"2026-01-01-typo"})
