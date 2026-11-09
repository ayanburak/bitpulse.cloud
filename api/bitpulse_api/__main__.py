"""
file: bitpulse_api/__main__.py
importable: main

Commands run on the server:

    bitpulse-api serve
    bitpulse-api key-create laptop
    bitpulse-api key-revoke laptop
    bitpulse-api import /path/to/stories --skip 2026-10-13-example
    bitpulse-api rebuild --no-switch

description: Starts the API and runs the server side management commands.
"""

import argparse
from pathlib import Path

import uvicorn

from . import keys, service
from .app import create_app
from .config import PORT, Settings
from .db import connect
from .importer import import_stories

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

    args = parser.parse_args()
    args.run(Settings.from_env(), args)


if __name__ == "__main__":
    main()
