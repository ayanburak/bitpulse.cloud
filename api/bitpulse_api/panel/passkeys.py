"""
file: bitpulse_api/panel/passkeys.py
importable: enrol_options, enrol_finish, add_options, add_finish, ask, verify

enrol_options and enrol_finish register the first passkey with the one time token from the server
command. ask and verify run the challenge and answer used at login and before dangerous actions.

description: Registers passkeys and checks the answers they give.
"""

# NOTE: User verification is required everywhere, so the phone or key must also ask for its own PIN
# or fingerprint. A stolen key alone does not get anyone through.

import json
import sqlite3
from typing import Any, Optional

from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.exceptions import WebAuthnException
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from .. import store as main_store
from ..config import Settings
from . import accounts, sessions, store

# --- Constants ---

SITE_NAME = "Bitpulse"
USER_NAME = "editor"
CHALLENGE_SECONDS = 5 * 60
ADD_PURPOSE = "passkey.add"

# --- Enrolment ---

# Registering the same device twice is refused by the browser when it sees the existing ids.
def _registration(conn: sqlite3.Connection, settings: Settings) -> Any:
    return generate_registration_options(
        rp_id=settings.panel_host,
        rp_name=SITE_NAME,
        user_name=USER_NAME,
        user_id=bytes(store.admin(conn)["user_id"]),
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        exclude_credentials=[
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(row["id"])) for row in store.passkeys(conn)
        ],
    )


def _store_new(conn: sqlite3.Connection, settings: Settings, challenge: bytes, credential: dict[str, Any], name: str) -> bool:
    try:
        verified = verify_registration_response(
            credential=credential,
            expected_challenge=challenge,
            expected_rp_id=settings.panel_host,
            expected_origin=settings.panel_origin,
            require_user_verification=True,
        )
    except WebAuthnException:
        return False
    with conn:
        store.add_passkey(
            conn,
            bytes_to_base64url(verified.credential_id),
            verified.credential_public_key,
            verified.sign_count,
            name[:60],
            main_store.minute(),
        )
        main_store.add_audit(conn, "panel", "passkey.add", name[:60])
    return True


def enrol_options(conn: sqlite3.Connection, settings: Settings, token: str) -> Optional[dict[str, Any]]:
    """Starts the registration of the first passkey.

    Args:
        conn: Open connection.
        settings: Holds the panel address.
        token: One time token from the server command.

    Returns:
        Options for the browser, or None for a wrong or expired token.
    """
    digest = accounts.digest(token)
    if store.enrolment(conn, digest) is None:
        return None
    options = _registration(conn, settings)
    with conn:
        store.set_enrolment_challenge(conn, digest, options.challenge)
    return json.loads(options_to_json(options))


# The token ends with the first success. Further passkeys need a signed in session and a touch of
# an existing one.
def enrol_finish(conn: sqlite3.Connection, settings: Settings, token: str, credential: dict[str, Any], name: str) -> bool:
    """Finishes the registration of the first passkey.

    Args:
        conn: Open connection.
        settings: Holds the panel address.
        token: One time token from the server command.
        credential: Answer from the browser.
        name: Label for the passkey.

    Returns:
        True when the passkey was stored.
    """
    digest = accounts.digest(token)
    row = store.enrolment(conn, digest)
    if row is None or row["challenge"] is None:
        return False
    if not _store_new(conn, settings, bytes(row["challenge"]), credential, name):
        return False
    with conn:
        store.drop_enrolment(conn, digest)
    return True


def add_options(conn: sqlite3.Connection, settings: Settings, current: sessions.Current) -> dict[str, Any]:
    """Starts the registration of one more passkey.

    Args:
        conn: Open connection.
        settings: Holds the panel address.
        current: Signed in session.

    Returns:
        Options for the browser.
    """
    options = _registration(conn, settings)
    with conn:
        store.put_challenge(conn, current.digest, ADD_PURPOSE, options.challenge, store.now() + CHALLENGE_SECONDS)
    return json.loads(options_to_json(options))


def add_finish(
    conn: sqlite3.Connection, settings: Settings, current: sessions.Current, credential: dict[str, Any], name: str
) -> bool:
    """Finishes the registration of one more passkey.

    Args:
        conn: Open connection.
        settings: Holds the panel address.
        current: Signed in session.
        credential: Answer from the browser.
        name: Label for the passkey.

    Returns:
        True when the passkey was stored.
    """
    with conn:
        challenge = store.take_challenge(conn, current.digest, ADD_PURPOSE)
    return challenge is not None and _store_new(conn, settings, challenge, credential, name)

# --- Challenge and Answer ---

def ask(conn: sqlite3.Connection, settings: Settings, current: sessions.Current, purpose: str) -> dict[str, Any]:
    """Creates a challenge for the stored passkeys.

    Args:
        conn: Open connection.
        settings: Holds the panel address.
        current: Session the challenge belongs to.
        purpose: What the answer will be good for.

    Returns:
        Options for the browser.
    """
    options = generate_authentication_options(
        rp_id=settings.panel_host,
        allow_credentials=[
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(row["id"])) for row in store.passkeys(conn)
        ],
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    with conn:
        store.put_challenge(conn, current.digest, purpose, options.challenge, store.now() + CHALLENGE_SECONDS)
    return json.loads(options_to_json(options))


# The answer names its own passkey, so the id is only used to look one up among the stored ones.
def verify(
    conn: sqlite3.Connection, settings: Settings, current: sessions.Current, purpose: str, credential: dict[str, Any]
) -> bool:
    """Checks the answer to a challenge.

    Args:
        conn: Open connection.
        settings: Holds the panel address.
        current: Session the challenge belongs to.
        purpose: Must match the one the challenge was made for.
        credential: Answer from the browser.

    Returns:
        True when the answer is right. The challenge can not be used again either way.
    """
    with conn:
        challenge = store.take_challenge(conn, current.digest, purpose)
    row = store.passkey(conn, str(credential.get("id", "")))
    if challenge is None or row is None:
        return False
    try:
        verified = verify_authentication_response(
            credential=credential,
            expected_challenge=challenge,
            expected_rp_id=settings.panel_host,
            expected_origin=settings.panel_origin,
            credential_public_key=bytes(row["public_key"]),
            credential_current_sign_count=row["sign_count"],
            require_user_verification=True,
        )
    except WebAuthnException:
        return False
    with conn:
        store.mark_passkey_used(conn, row["id"], verified.new_sign_count, main_store.minute())
    return True
