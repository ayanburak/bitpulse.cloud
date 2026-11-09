"""
file: tests/conftest.py
importable: nothing, pytest loads it

description: Shared fixtures for the API tests.
"""

import base64
import hashlib
import io
import json
import os

import cbor2
import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from PIL import Image

from bitpulse_api.app import create_app
from bitpulse_api.config import Settings
from bitpulse_api.db import connect
from bitpulse_api.keys import create_key
from bitpulse_api.panel import accounts, store


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


# --- Panel ---

ORIGIN = "https://panel.test"
PASSWORD = "a long enough password"


def b64(raw):
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


# Plays the part of a phone or security key, with the same bytes a real one would send.
class Authenticator:
    def __init__(self, origin=ORIGIN):
        self.key = ec.generate_private_key(ec.SECP256R1())
        self.id = os.urandom(16)
        self.count = 0
        self.origin = origin
        self.rp_hash = hashlib.sha256(b"panel.test").digest()

    def _client_data(self, kind, challenge):
        return json.dumps({"type": kind, "challenge": challenge, "origin": self.origin, "crossOrigin": False}).encode()

    def register(self, options):
        numbers = self.key.public_key().public_numbers()
        cose = cbor2.dumps({1: 2, 3: -7, -1: 1, -2: numbers.x.to_bytes(32, "big"), -3: numbers.y.to_bytes(32, "big")})
        body = self.rp_hash + bytes([0x45]) + (0).to_bytes(4, "big") + bytes(16) + len(self.id).to_bytes(2, "big")
        attestation = cbor2.dumps({"fmt": "none", "attStmt": {}, "authData": body + self.id + cose})
        return {
            "id": b64(self.id),
            "rawId": b64(self.id),
            "type": "public-key",
            "response": {
                "clientDataJSON": b64(self._client_data("webauthn.create", options["challenge"])),
                "attestationObject": b64(attestation),
            },
        }

    def answer(self, options, verified=True):
        self.count += 1
        flags = 0x05 if verified else 0x01
        data = self.rp_hash + bytes([flags]) + self.count.to_bytes(4, "big")
        client = self._client_data("webauthn.get", options["challenge"])
        signature = self.key.sign(data + hashlib.sha256(client).digest(), ec.ECDSA(hashes.SHA256()))
        return {
            "id": b64(self.id),
            "rawId": b64(self.id),
            "type": "public-key",
            "response": {
                "clientDataJSON": b64(client),
                "authenticatorData": b64(data),
                "signature": b64(signature),
            },
        }


@pytest.fixture
def panel_settings(tmp_path):
    result = Settings(data=tmp_path / "data", spool=tmp_path / "spool", panel_origin=ORIGIN)
    result.prepare()
    return result


@pytest.fixture
def db(panel_settings):
    connection = connect(panel_settings.db)
    yield connection
    connection.close()


def browser_for(panel_settings):
    return TestClient(create_app(panel_settings), base_url="https://testserver", headers={"Origin": ORIGIN})


@pytest.fixture
def browser(panel_settings):
    return browser_for(panel_settings)


# Moves the clock of everything that expires.
@pytest.fixture
def clock(monkeypatch):
    moment = {"now": 2_000_000_000}
    monkeypatch.setattr(store, "now", lambda: moment["now"])
    return moment


@pytest.fixture
def account(db, browser):
    token, codes = accounts.init_admin(db, PASSWORD)
    key = Authenticator()
    options = browser.post("/panel-api/auth/enrol/options", json={"token": token}).json()["options"]
    finished = browser.post(
        "/panel-api/auth/enrol/finish", json={"token": token, "credential": key.register(options), "name": "phone"}
    )
    assert finished.status_code == 204
    return key, codes, token


def password(browser, password=PASSWORD):
    return browser.post("/panel-api/auth/password", json={"password": password})


def sign_in(browser, key):
    options = password(browser).json()["options"]
    response = browser.post("/panel-api/auth/passkey", json={"credential": key.answer(options)})
    assert response.status_code == 200
    return response.json()["csrf"]


def action(browser, key, csrf, action_name="publish", target="story"):
    headers = {"X-CSRF-Token": csrf}
    body = {"action": action_name, "target": target}
    options = browser.post("/panel-api/auth/action/options", json=body, headers=headers).json()["options"]
    return browser.post(
        "/panel-api/auth/action/answer", json={**body, "credential": key.answer(options)}, headers=headers
    )


def signed_in(browser):
    return browser.get("/panel-api/auth/me").json()["signed_in"]
