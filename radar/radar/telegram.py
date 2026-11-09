"""
file: radar/telegram.py
importable: send, send_cluster, poll, chat_ids, run_work

Talks to the Telegram Bot API with plain HTTPS calls. send_cluster posts one candidate with Do
and Skip buttons. poll waits for button presses, which it records on the API, and for links the
editor pastes into the chat, which it saves as candidates. Between two waits it does what the
panel asked for.

The bot token comes from TELEGRAM_TOKEN and the editor's chat from TELEGRAM_CHAT_ID.

description: Sends candidates to the editor on Telegram and records the answers.
"""

# NOTE: Only the configured chat is trusted. Anyone can find a bot and press buttons on a
# forwarded message, so updates from any other chat are dropped without a reply.
#
# NOTE: A decision lives on the API alone. When the API can not be reached a press is refused and
# the buttons stay, a local note here would be a second answer that nobody could see.

import json
import os
import sqlite3
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html import escape

from radar import api, clip, sync
from radar.brief import build_brief
from radar.store import meta, set_meta

# --- Constants ---

API = "https://api.telegram.org/bot{token}/{method}"

# Telegram holds the request open this long, so it is also the longest a panel request waits.
LONG_POLL = 25
LINKS = 4


# --- Calls ---

def call(method: str, **params) -> dict:
    token = os.environ["TELEGRAM_TOKEN"]
    request = urllib.request.Request(
        API.format(token=token, method=method),
        data=json.dumps(params).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=LONG_POLL + 10) as response:
        body = json.load(response)
    if not body.get("ok"):
        raise RuntimeError(f"Telegram {method} failed: {body.get('description')}")
    return body["result"]


def send(text: str, buttons: list[list[dict]] | None = None) -> dict:
    params = {"chat_id": os.environ["TELEGRAM_CHAT_ID"], "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if buttons:
        params["reply_markup"] = {"inline_keyboard": buttons}
    return call("sendMessage", **params)


# --- Candidates ---

def send_cluster(db: sqlite3.Connection, cluster: sqlite3.Row, reason: str = "", label: str = "") -> None:
    """
    Posts one cluster with its links and the two buttons, then marks it as sent.

    Args:
        db: Open radar database.
        cluster: Row from the clusters table.
        reason: One line from the ranking on why this story is worth a look.
        label: Short tag in front of the title, such as BIG EVENT.
    """
    items = db.execute(
        "select source, url, image from items where cluster = ? order by image desc, published desc",
        (cluster["id"],),
    ).fetchall()
    head = f"<b>R-{cluster['id']:04d}</b> · {cluster['sources']} source{'s' if cluster['sources'] != 1 else ''}"
    if label:
        head = f"<b>{escape(label)}</b> · {head}"
    lines = [head, escape(cluster["title"])]
    if reason:
        lines.append(f"<i>{escape(reason)}</i>")
    lines += [f'<a href="{escape(item["url"])}">{escape(item["source"])}</a>' for item in items[:LINKS]]
    buttons = [[
        {"text": "Do", "callback_data": f"do:{cluster['id']}"},
        {"text": "Skip", "callback_data": f"skip:{cluster['id']}"},
    ]]
    message = send("\n".join(lines), buttons)
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    db.execute("update clusters set sent = coalesce(sent, ?), message_id = ? where id = ?", (stamp, message.get("message_id"), cluster["id"]))
    db.commit()
    if api.enabled():
        try:
            sync.push_one(db, cluster["id"])
        except api.ApiError as error:  # The next round sends it again.
            print(f"event R-{cluster['id']:04d} not sent to the API: {error}", flush=True)


def show_choice(message_id: int, choice: str) -> None:
    call("editMessageReplyMarkup", chat_id=os.environ["TELEGRAM_CHAT_ID"], message_id=message_id,
         reply_markup={"inline_keyboard": [[{"text": "Do ✓" if choice == "do" else "Skip ✓", "callback_data": "done"}]]})


# --- Answers ---

def handle_link(db: sqlite3.Connection, message: dict) -> None:
    if str(message.get("chat", {}).get("id")) != os.environ["TELEGRAM_CHAT_ID"]:
        return
    url = clip.find_link(message.get("text") or message.get("caption") or "")
    if not url:
        send("Send a link to save it as a candidate.")
        return
    try:
        number, title, new = clip.save(db, url)
    except Exception as error:  # A bad link must not stop the poll loop.
        send(f"Could not save the link: {escape(str(error)[:300])}")
        return
    if new and api.enabled():
        try:
            sync.register_clip(db, number)
        except api.ApiError as error:  # The next round sends the event, and the brief is asked for again.
            print(f"link R-{number:04d} not sent to the API: {error}", flush=True)
    state = "Saved" if new else "Already saved"
    send(f"{state} <b>R-{number:04d}</b>\n{escape(title)}\nBrief ready. On the computer: /haber R-{number:04d}")


def handle(db: sqlite3.Connection, update: dict) -> None:
    if update.get("message"):
        handle_link(db, update["message"])
        return
    query = update.get("callback_query")
    if not query:
        return
    message = query.get("message") or {}
    if str(message.get("chat", {}).get("id")) != os.environ["TELEGRAM_CHAT_ID"]:
        return
    choice, _, number = query.get("data", "").partition(":")
    if choice not in ("do", "skip") or not number.isdigit():
        return
    try:
        # The event may have missed an earlier round, and the decision needs a row to land on.
        sync.push_one(db, int(number))
        api.decide(int(number), choice)
    except api.ApiError as error:
        print(f"decision on R-{int(number):04d} not saved: {error}", flush=True)
        call("answerCallbackQuery", callback_query_id=query["id"], text="Could not save this, press again in a minute.")
        return
    note = f"Tell Claude: R-{int(number):04d}" if choice == "do" else "Skipped"
    call("answerCallbackQuery", callback_query_id=query["id"], text=note)
    # The buttons go away once answered, and the choice stays visible under the message.
    show_choice(message["message_id"], choice)


# --- Panel Requests ---

# A decision made in the panel takes the event out of the running, the radar must not offer it later.
# A post that is too old to change only loses its checkmark, the decision itself is already safe.
def reflect(db: sqlite3.Connection, number: int, choice: str) -> None:
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    db.execute("update clusters set sent = coalesce(sent, ?) where id = ?", (stamp, number))
    db.commit()
    row = db.execute("select message_id from clusters where id = ?", (number,)).fetchone()
    if row and row["message_id"]:
        try:
            show_choice(row["message_id"], choice)
        except (urllib.error.URLError, TimeoutError, RuntimeError) as error:
            print(f"post of R-{number:04d} not changed: {error}", flush=True)
    api.seen(number)


def make_brief(db: sqlite3.Connection, number: int, by: str) -> None:
    try:
        path = build_brief(db, number)
    except Exception as error:  # A brief that can not be written must not stop the poll loop.
        api.put_brief(number, error=f"{type(error).__name__}: {error}"[:500])
        if by == "telegram":
            send(f"Brief for R-{number:04d} failed: {escape(str(error))}")
        return
    api.put_brief(number, text=path.read_text(encoding="utf-8")[:400_000])
    if by == "telegram":
        send(f"Brief ready for R-{number:04d}.")


def take_link(db: sqlite3.Connection, link: int, url: str) -> None:
    try:
        number, _, new = clip.save(db, url)
    except Exception as error:  # A bad link must not stop the poll loop.
        api.finish_link(link, error=f"{type(error).__name__}: {error}"[:500])
        return
    if new:
        sync.register_clip(db, number)
    api.finish_link(link, number=number)


def run_work(db: sqlite3.Connection) -> None:
    """
    Does what the panel is waiting for: updates Telegram posts, opens added links, writes briefs.
    A failing item is left for the next round and does not stop the others.

    Args:
        db: Open radar database.
    """
    if not api.enabled():
        return
    try:
        work = api.work()
    except api.ApiError as error:
        print(f"work not read: {error}", flush=True)
        return
    steps = [(reflect, (db, item["number"], item["decision"])) for item in work["decisions"]]
    steps += [(take_link, (db, item["id"], item["url"])) for item in work["links"]]
    steps += [(make_brief, (db, item["number"], item["decided_by"])) for item in work["briefs"]]
    for step, args in steps:
        try:
            step(*args)
        except Exception as error:
            print(f"{step.__name__} failed: {type(error).__name__}: {error}", flush=True)


def poll(db: sqlite3.Connection) -> None:
    """
    Waits for button presses forever. Telegram holds each request open until something happens,
    so the loop costs almost nothing while the editor is away. Each pass also picks up what the
    panel asked for.
    """
    while True:
        offset = int(meta(db, "telegram_offset", "0"))
        try:
            updates = call("getUpdates", offset=offset, timeout=LONG_POLL, allowed_updates=["callback_query", "message"])
        except (urllib.error.URLError, TimeoutError, RuntimeError) as error:
            print(f"poll error: {error}", flush=True)
            time.sleep(10)
            continue
        for update in updates:
            # The offset has to move on even when one press fails. Otherwise the service dies,
            # systemd starts it again, Telegram hands over the same press and it dies again,
            # forever. An answer to a press that waited too long is the usual way to get here.
            try:
                handle(db, update)
            except Exception as error:
                print(f"update {update['update_id']} failed: {type(error).__name__}: {error}", flush=True)
            set_meta(db, "telegram_offset", str(update["update_id"] + 1))
        run_work(db)


# --- Setup ---

def chat_ids() -> list[tuple[int, str]]:
    """
    Lists the chats that wrote to the bot recently, which is how the editor's chat id is found
    once after the bot is created.
    """
    seen = {}
    for update in call("getUpdates", timeout=0):
        chat = (update.get("message") or {}).get("chat")
        if chat:
            seen[chat["id"]] = chat.get("username") or chat.get("first_name") or ""
    return list(seen.items())
