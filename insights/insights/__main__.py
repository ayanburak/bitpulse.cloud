"""
file: insights/__main__.py
importable: main, run as insights <command> or python -m insights <command>

    insights run              read the posts that are due and the last two days of the account
    insights run --days 28    the same, with four weeks of account numbers, used for the first round
    insights check            print what Meta answers for the account, one post and each metric

The settings come from the environment: INSIGHTS_META_TOKEN, INSIGHTS_ACCOUNT, INSIGHTS_API_KEY and
optionally INSIGHTS_API_URL and INSIGHTS_GRAPH_VERSION. On the server they are in
/etc/bitpulse/insights/env and a timer runs insights run every hour.

description: Command line entry of the insights service.
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

from . import http
from . import round as rounds
from .api import DEFAULT_URL, Api
from .meta import METRICS, REEL_METRICS, VERSION, Meta, kind_of

# --- Commands ---

def _meta() -> Meta:
    return Meta(os.environ["INSIGHTS_META_TOKEN"], os.environ["INSIGHTS_ACCOUNT"], os.environ.get("INSIGHTS_GRAPH_VERSION", VERSION))


# Each metric is asked alone, so the output shows exactly which names Meta still knows.
def check(meta: Meta) -> None:
    profile = meta.profile()
    print(f"account: {profile.get('username')}, {profile.get('followers_count')} followers, {profile.get('media_count')} posts")
    newest = next(meta.posts(), None)
    if newest is None:
        print("no posts")
        return
    print(f"newest post: {newest['id']}, {kind_of(newest)}, {newest['timestamp']}")
    print(f"picture: {'yes' if newest.get('thumbnail_url') or newest.get('media_url') else 'no'}")
    wanted = {**METRICS, **(REEL_METRICS if kind_of(newest) == "reel" else {})}
    for name in wanted:
        try:
            print(f"  {name}: {meta.metrics(newest['id'], {name: name}) or 'refused'}")
        except http.HttpError as error:
            print(f"  {name}: {error}")
    midnight = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    start = midnight - timedelta(days=1)
    try:
        print(f"yesterday: {meta.day(int(start.timestamp()), int(midnight.timestamp())) or 'refused'}")
    except http.HttpError as error:
        print(f"yesterday: {error}")
    try:
        rows = meta.audience()
        print(f"audience: {len(rows)} rows" if rows else "audience: none, Meta gives it above one hundred followers")
    except http.HttpError as error:
        print(f"audience: {error}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="insights")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("run").add_argument("--days", type=int, default=2, choices=range(1, 29), metavar="1-28")
    commands.add_parser("check")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    missing = [name for name in ("INSIGHTS_META_TOKEN", "INSIGHTS_ACCOUNT") if not os.environ.get(name)]
    if args.command == "run" and not os.environ.get("INSIGHTS_API_KEY"):
        missing.append("INSIGHTS_API_KEY")
    if missing:
        sys.exit(f"missing settings: {', '.join(missing)}")

    try:
        if args.command == "check":
            check(_meta())
        else:
            api = Api(os.environ["INSIGHTS_API_KEY"], os.environ.get("INSIGHTS_API_URL", DEFAULT_URL))
            result = rounds.run(_meta(), api, args.days)
            print(f"read {result['posts']} posts, sent {result['pictures']} pictures, {result['failed']} failed")
    except http.HttpError as error:
        sys.exit(str(error))


if __name__ == "__main__":
    main()
