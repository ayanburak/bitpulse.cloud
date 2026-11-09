"""
file: tests/conftest.py
importable: nothing, pytest loads it

description: Shared fixtures for the API tests.
"""

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from bitpulse_api.app import create_app
from bitpulse_api.config import Settings
from bitpulse_api.db import connect
from bitpulse_api.keys import create_key


@pytest.fixture
def settings(tmp_path):
    result = Settings(data=tmp_path / "data", spool=tmp_path / "spool")
    result.prepare()
    return result


@pytest.fixture
def conn(settings):
    connection = connect(settings.db)
    yield connection
    connection.close()


# TestClient is used without its context manager, so the job loop does not run in the background
# and each test calls tick itself at the moment it wants.
@pytest.fixture
def client(settings, conn):
    token = create_key(conn, "test")
    return TestClient(create_app(settings), headers={"Authorization": f"Bearer {token}"})


@pytest.fixture
def jpeg():
    output = io.BytesIO()
    Image.new("RGB", (1400, 800), (40, 90, 140)).save(output, "JPEG", exif=b"Exif\x00\x00secret")
    return output.getvalue()


def story_file(slug="sample-story", extra=""):
    return f"""---
slug: {slug}
title: "A Sample Story"
summary: "A summary."
category: world
date: 2026-01-01
time: "09:00"
kind: news
sources:
  - name: "A source"
    url: https://example.com/a
image:
  file: image.jpg
  alt: "Alt text"
  credit: "Someone"
  license: "CC0"
  licenseUrl: https://example.com/license
  source: https://example.com/image
{extra}---

Body text.
"""
