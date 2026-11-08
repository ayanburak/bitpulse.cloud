"""
file: radar/telegram.py
importable: send, send_cluster, poll, chat_ids

Talks to the Telegram Bot API with plain HTTPS calls. send_cluster posts one candidate with Do
and Skip buttons. poll waits for button presses, which it stores on the cluster, and for links
the editor pastes into the chat, which it saves as candidates.

The bot token comes from TELEGRAM_TOKEN and the editor's chat from TELEGRAM_CHAT_ID.

description: Sends candidates to the editor on Telegram and records the answers.
"""

# NOTE: Only the configured chat is trusted. Anyone can find a bot and press buttons on a
# forwarded message, so updates from any other chat are dropped without a reply.

import json
import os
import sqlite3
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html import escape

from radar import clip
from radar.brief import build_brief
from radar.store import meta, set_meta

# --- Constants ---

API = "https://api.telegram.org/bot{token}/{method}"
LONG_POLL = 50
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
    send("\n".join(lines), buttons)
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    db.execute("update clusters set sent = coalesce(sent, ?) where id = ?", (stamp, cluster["id"]))
    db.commit()


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
    db.execute("update clusters set decision = ? where id = ?", (choice, int(number)))
    db.commit()
    note = f"Tell Claude: R-{int(number):04d}" if choice == "do" else "Skipped"
    call("answerCallbackQuery", callback_query_id=query["id"], text=note)
    # The buttons go away once answered, and the choice stays visible under the message.
    call("editMessageReplyMarkup", chat_id=message["chat"]["id"], message_id=message["message_id"],
         reply_markup={"inline_keyboard": [[{"text": "Do ✓" if choice == "do" else "Skip ✓", "callback_data": "done"}]]})
    # The brief is written right away, so it is ready by the time the editor opens a session.
    if choice == "do":
        try:
            build_brief(db, int(number))
            send(f"Brief ready for R-{int(number):04d}.")
        except Exception as error:  # A failed brief must not stop the poll loop.
            send(f"Brief for R-{int(number):04d} failed: {escape(str(error))}")


def poll(db: sqlite3.Connection) -> None:
    """
    Waits for button presses forever. Telegram holds each request open until something happens,
    so the loop costs almost nothing while the editor is away.
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
