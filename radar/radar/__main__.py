"""
file: radar/__main__.py
importable: main, run as radar <command> or python -m radar <command>

    radar listen          read every feed once, report big events at once
    radar rank            run one ranking round and send its picks
    radar rank --dry-run  print this round's shortlist without the model or Telegram
    radar replay 2026-11-08 --db copy.db   run the rounds of a past day without Telegram
    radar poll            wait for Do and Skip presses and pasted links, runs as a service
    radar clips           list the links saved from the bot
    radar show 142        print every story of cluster R-0142 with its link
    radar brief R-0142    download the stories of a cluster into a brief and print it
    radar check en.md brief.md   list numbers and quotes of a story missing from its brief
    radar sources         print the state of every feed
    radar chat-id         list the chats that wrote to the bot, used once during setup

On the server, listen runs every few minutes, rank every hour inside the editor's hours,
and poll runs all the time.

description: Command line entry of the radar.
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from html import escape

from radar import brief as briefing
from radar import check as checking
from radar import listen as listening
from radar import rank as ranking
from radar import replay as replaying
from radar import telegram
from radar.store import connect


def regions(path: str) -> dict[str, str]:
    return {source.name: source.region for source in listening.load_sources(path)}

# --- Hours ---

# The editor's waking hours in UTC, written as 06-22. Big events outside them wait for the
# morning round, which ranks everything that came in during the night.
def awake(now: datetime) -> bool:
    start, end = (int(part) for part in os.environ.get("RADAR_HOURS", "06-22").split("-"))
    return start <= now.hour < end


# --- Commands ---

def cmd_listen(args) -> None:
    db = connect()
    count, big = listening.listen(db, listening.load_sources(args.sources))
    print(f"{count} new stories, {len(big)} big events", flush=True)
    now = datetime.now(timezone.utc)
    # Without Telegram, as on a development machine, big events are only printed.
    if "TELEGRAM_TOKEN" not in os.environ:
        for cluster in big:
            print(f"big event R-{cluster['id']:04d} {cluster['title']}")
        return
    if not awake(now):
        return
    for cluster in big:
        telegram.send_cluster(db, cluster, label="BIG EVENT")
        db.execute("update clusters set alerted = ? where id = ?", (now.isoformat(timespec="seconds"), cluster["id"]))
        db.commit()


# A failed round only shows in the journal otherwise, and an empty chat looks the same as a
# quiet hour. Running out of API credit is the likely cause, so the editor gets one line.
def cmd_rank(args) -> None:
    try:
        chosen = ranking.rank(connect(), telegram.send_cluster, dry_run=args.dry_run, regions=regions(args.sources))
    except Exception as error:
        if "TELEGRAM_TOKEN" in os.environ and not args.dry_run:
            telegram.send(f"Ranking failed: {escape(f'{type(error).__name__}: {error}'[:300])}")
        raise
    for cluster, reason in chosen:
        print(f"R-{cluster['id']:04d} {cluster['title']}\n  {reason}")


def cmd_replay(args) -> None:
    print("Sent by the current ranking:")
    for row in replaying.sent_that_day(args.db, args.day):
        print(f"  {row['sent'][11:16]} R-{row['id']:04d} {row['sources']}s {row['title']}")
    print("\nWould be sent:")
    for moment, cluster, reason in replaying.replay(args.db, args.day, regions(args.sources)):
        print(f"  {moment[11:16]} R-{cluster['id']:04d} {cluster['sources']}s {cluster['title']}\n        {reason}")


def cmd_poll(args) -> None:
    telegram.poll(connect())


def cmd_clips(args) -> None:
    for row in connect().execute("select id, title, first_seen from clusters where clip = 1 order by id desc"):
        print(f"R-{row['id']:04d}  {row['first_seen'][:16]}  {row['title']}")


def cmd_show(args) -> None:
    db = connect()
    number = number_of(args.cluster)
    cluster = db.execute("select * from clusters where id = ?", (number,)).fetchone()
    if not cluster:
        sys.exit(f"No cluster R-{number:04d}")
    print(f"R-{number:04d} {cluster['title']}")
    print(f"first seen {cluster['first_seen']}, {cluster['sources']} sources, decision {cluster['decision'] or 'none'}\n")
    for item in db.execute("select * from items where cluster = ? order by published", (number,)):
        print(f"{item['published'] or 'no date'}  {item['source']}\n  {item['title']}\n  {item['url']}")
        if item["summary"]:
            print(f"  {item['summary'][:300]}")
        print()


def number_of(text: str) -> int:
    return int(text.upper().removeprefix("R-"))


def cmd_brief(args) -> None:
    path = briefing.build_brief(connect(), number_of(args.cluster))
    print(path.read_text(encoding="utf-8"))


def cmd_check(args) -> None:
    missing = checking.check_files(args.story, args.brief)
    print("\n".join(missing) if missing else "Every number and quote was found in the brief.")


def cmd_sources(args) -> None:
    db = connect()
    for row in db.execute("select * from feeds order by name"):
        print(f"{'FAIL' if row['error'] else 'ok  '}  {row['name']}  checked {row['checked']}  {row['error'] or ''}")


def cmd_chat_id(args) -> None:
    for chat, name in telegram.chat_ids():
        print(chat, name)


# --- Entry ---

def main() -> None:
    parser = argparse.ArgumentParser(prog="radar")
    parser.add_argument("--sources", default="sources.toml")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("listen").set_defaults(run=cmd_listen)
    rank = sub.add_parser("rank")
    rank.add_argument("--dry-run", action="store_true")
    rank.set_defaults(run=cmd_rank)
    day = sub.add_parser("replay")
    day.add_argument("day")
    day.add_argument("--db", required=True)
    day.set_defaults(run=cmd_replay)
    sub.add_parser("poll").set_defaults(run=cmd_poll)
    sub.add_parser("clips").set_defaults(run=cmd_clips)
    show = sub.add_parser("show")
    show.add_argument("cluster")
    show.set_defaults(run=cmd_show)
    brief = sub.add_parser("brief")
    brief.add_argument("cluster")
    brief.set_defaults(run=cmd_brief)
    check = sub.add_parser("check")
    check.add_argument("story")
    check.add_argument("brief")
    check.set_defaults(run=cmd_check)
    sub.add_parser("sources").set_defaults(run=cmd_sources)
    sub.add_parser("chat-id").set_defaults(run=cmd_chat_id)
    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
