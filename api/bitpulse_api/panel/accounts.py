"""
file: bitpulse_api/panel/accounts.py
importable: InvalidAdmin, Busy, digest, init_admin, check_password, is_locked, record_failure, unlock,
            spend_backup_code, ENROL_MINUTES

init_admin creates the single panel account on the server and is the only way to make one. There
is no sign up route. The rest answers the questions a login asks about that account.

description: Keeps the panel password, the backup codes and the login lock.
"""

# NOTE: The lock counts every wrong answer against the one account, so someone who keeps guessing can
# keep the real login closed too. nginx and fail2ban cut that traffic before it arrives, and
# admin-unlock opens the lock over SSH.
#
# NOTE: The backup codes are long and random, so a plain hash is enough for them, same as the device
# keys. Only the password needs Argon2.

import base64
import hashlib
import secrets
import sqlite3
import threading

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from .. import store as main_store
from . import store

# --- Constants ---

MIN_PASSWORD = 14
MAX_PASSWORD = 256
BACKUP_CODES = 10
ENROL_MINUTES = 15
MAX_FAILURES = 5
LOCK_SECONDS = 15 * 60

# One core and a 300 MB limit on the service. Each check takes 64 MB, so only two run at a time and
# a burst of requests can not push the service out of memory.
_hasher = PasswordHasher(time_cost=3, memory_cost=64 * 1024, parallelism=1)
_hashing = threading.BoundedSemaphore(2)

# --- Errors ---

class InvalidAdmin(Exception):
    """Raised when the account can not be created as asked."""


class Busy(Exception):
    """Raised when too many password checks are already running."""

# --- Helpers ---

def digest(text: str) -> str:
    """Returns the stored form of a long random secret."""
    return hashlib.sha256(text.encode()).hexdigest()


def _new_code() -> str:
    return base64.b32encode(secrets.token_bytes(10)).decode()

# --- Account ---

# A reset drops the passkeys, the codes and every session, so it also throws out anyone who got in.
def init_admin(conn: sqlite3.Connection, password: str, reset: bool = False) -> tuple[str, list[str]]:
    """Creates the panel account, or replaces it when reset is set.

    Args:
        conn: Open connection.
        password: New password.
        reset: Replaces an account that already exists.

    Returns:
        The one time token for registering a passkey, and the backup codes. Neither is kept.

    Raises:
        InvalidAdmin: If the password is too short or too long, or an account exists without reset.
    """
    if not MIN_PASSWORD <= len(password) <= MAX_PASSWORD:
        raise InvalidAdmin(f"the password must have {MIN_PASSWORD} to {MAX_PASSWORD} characters")
    if store.admin(conn) is not None and not reset:
        raise InvalidAdmin("the account already exists, use --reset to replace it")
    hashed = _hasher.hash(password)
    token = secrets.token_urlsafe(32)
    codes = [_new_code() for _ in range(BACKUP_CODES)]
    with conn:
        store.clear_account(conn)
        store.set_admin(conn, hashed, secrets.token_bytes(32), main_store.minute())
        store.add_backup_codes(conn, [digest(code) for code in codes])
        store.add_enrolment(conn, digest(token), store.now() + ENROL_MINUTES * 60)
        main_store.add_audit(conn, "server", "admin.reset" if reset else "admin.init", "panel")
    return token, codes


def check_password(conn: sqlite3.Connection, password: str) -> bool:
    """Checks a password against the account.

    Args:
        conn: Open connection.
        password: Password from the login form.

    Returns:
        True when it matches.

    Raises:
        Busy: If two checks are already running.
    """
    account = store.admin(conn)
    if account is None or len(password) > MAX_PASSWORD:
        return False
    if not _hashing.acquire(blocking=False):
        raise Busy
    try:
        return _hasher.verify(account["password"], password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
    finally:
        _hashing.release()

# --- Lock ---

def is_locked(conn: sqlite3.Connection) -> bool:
    return int(store.lock_state(conn)["until"]) > store.now()


# Only the moment of locking goes to the audit log, a guessing attack must not be able to fill it.
def record_failure(conn: sqlite3.Connection) -> None:
    """Counts one wrong answer and closes the login at the limit.

    Args:
        conn: Open connection.
    """
    with conn:
        if store.add_failure(conn) >= MAX_FAILURES:
            store.lock_until(conn, store.now() + LOCK_SECONDS)
            main_store.add_audit(conn, "panel", "login.locked", "panel")


def unlock(conn: sqlite3.Connection) -> None:
    """Opens the login lock."""
    with conn:
        store.clear_failures(conn)
        main_store.add_audit(conn, "server", "admin.unlock", "panel")

# --- Backup Codes ---

# Paper is read with mistakes, so case and spaces do not matter.
def spend_backup_code(conn: sqlite3.Connection, code: str) -> bool:
    """Spends a backup code.

    Args:
        conn: Open connection.
        code: Code as typed.

    Returns:
        True when the code was valid and unused. It can not be used again.
    """
    with conn:
        spent = store.use_backup_code(conn, digest(code.replace(" ", "").upper()), main_store.minute())
        if spent:
            main_store.add_audit(conn, "panel", "backup_code.used", "panel")
    return spent
