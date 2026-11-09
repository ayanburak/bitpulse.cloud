"""
file: bitpulse_api/__main__.py
importable: main

Commands run on the server:

    bitpulse-api serve
    bitpulse-api key-create laptop
    bitpulse-api key-revoke laptop
    bitpulse-api import /path/to/stories --skip 2026-10-13-example
    bitpulse-api rebuild --no-switch
    bitpulse-api admin-init
    bitpulse-api admin-init --reset
    bitpulse-api admin-unlock

description: Starts the API and runs the server side management commands.
"""

import argparse
import getpass
import sys
from pathlib import Path

import uvicorn

from . import keys, service
from .app import create_app
from .config import PORT, Settings
from .db import connect
from .importer import import_stories
from .panel import accounts

# --- Commands ---

def _serve(settings: Settings, _: argparse.Namespace) -> None:
    uvicorn.run(create_app(settings), host="127.0.0.1", port=PORT, access_log=False, server_header=False)


def _key_create(settings: Settings, args: argparse.Namespace) -> None:
    print(keys.create_key(connect(settings.db), args.name))


def _key_revoke(settings: Settings, args: argparse.Namespace) -> None:
    conn = connect(settings.db)
    with conn:
        found = service.store.revoke_key(conn, args.name)
        if found:
            service.store.add_audit(conn, "server", "key.revoke", args.name)
    print("revoked" if found else "no such active key")


def _import(settings: Settings, args: argparse.Namespace) -> None:
    settings.prepare()
    names = import_stories(connect(settings.db), settings, Path(args.root), set(args.skip))
    print(f"imported {len(names)} stories")


def _rebuild(settings: Settings, args: argparse.Namespace) -> None:
    print(f"job {service.request_rebuild(connect(settings.db), 'server', not args.no_switch)}")


# The password is typed on the server and never passes through an argument, which would show in the
# process list and the shell history.
def _admin_init(settings: Settings, args: argparse.Namespace) -> None:
    password = getpass.getpass("New panel password: ")
    if password != getpass.getpass("Again: "):
        sys.exit("error: the passwords differ")
    try:
        token, codes = accounts.init_admin(connect(settings.db), password, args.reset)
    except accounts.InvalidAdmin as error:
        sys.exit(f"error: {error}")
    print(f"Register the first passkey within {accounts.ENROL_MINUTES} minutes:")
    print(f"{settings.panel_origin}/#enrol={token}")
    print("Backup codes, write them on paper. They are not shown again:")
    print("\n".join(codes))


def _admin_unlock(settings: Settings, _: argparse.Namespace) -> None:
    accounts.unlock(connect(settings.db))
    print("unlocked")

# --- Entry ---

def main() -> None:
    """Runs the command given on the command line."""
    parser = argparse.ArgumentParser(prog="bitpulse-api")
    commands = parser.add_subparsers(required=True)

    commands.add_parser("serve").set_defaults(run=_serve)

    create = commands.add_parser("key-create")
    create.add_argument("name")
    create.set_defaults(run=_key_create)

    revoke = commands.add_parser("key-revoke")
    revoke.add_argument("name")
    revoke.set_defaults(run=_key_revoke)

    load = commands.add_parser("import")
    load.add_argument("root")
    load.add_argument("--skip", nargs="*", default=[])
    load.set_defaults(run=_import)

    rebuild = commands.add_parser("rebuild")
    rebuild.add_argument("--no-switch", action="store_true")
    rebuild.set_defaults(run=_rebuild)

    init = commands.add_parser("admin-init")
    init.add_argument("--reset", action="store_true")
    init.set_defaults(run=_admin_init)

    commands.add_parser("admin-unlock").set_defaults(run=_admin_unlock)

    args = parser.parse_args()
    args.run(Settings.from_env(), args)


if __name__ == "__main__":
    main()
