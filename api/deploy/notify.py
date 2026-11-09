"""
file: deploy/notify.py
importable: nothing, the notify service runs this file

Sends every waiting notice to Telegram and removes it. systemd starts this file when a notice
appears in /var/lib/bitpulse/notify, and starts it again while any are left.

description: Sends the notices written by the API to Telegram.
"""

# NOTE: This is the only part of the system that holds the notice bot token and talks to Telegram,
# and it can read nothing but the notice folder. Only the standard library is used, so there is no
# package here to keep up to date.
#
# NOTE: Exceptions are reported by type alone. The request address contains the token, and it must
# never end up in the system log.

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable

# --- Constants ---

FOLDER = Path("/var/lib/bitpulse/notify")
RETRY_SECONDS = 30
MAX_DETAIL = 300

# --- Messages ---

def message(event: dict[str, str]) -> str:
    """Writes the text of one notice.

    Args:
        event: One audit entry.

    Returns:
        Plain text. No markup, the fields come from elsewhere and must not be able to format it.
    """
    lines = [f"Bitpulse: {event['action']}", f"{event['target']}, by {event['actor']}, {event['at']} UTC"]
    if event["detail"]:
        lines.append(event["detail"][:MAX_DETAIL])
    return "\n".join(lines)


def _send(token: str, chat: str, text: str) -> None:
    data = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
    urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data=data, timeout=20).read()

# --- Sending ---

# Oldest first and stop at the first failure, so notices never arrive out of order.
def drain(folder: Path, send: Callable[[str], None]) -> bool:
    """Sends the waiting notices.

    Args:
        folder: Notice folder.
        send: Delivers one text. Raises when it can not.

    Returns:
        True when nothing is left unsent.
    """
    for path in sorted(folder.glob("*.json")):
        try:
            send(message(json.loads(path.read_text(encoding="utf-8"))))
        except OSError as error:
            print(f"sending failed: {type(error).__name__}", file=sys.stderr)
            return False
        path.unlink()
    return True


# A failed run waits before ending, because systemd starts it again at once while files remain.
def main() -> None:
    """Sends the notices with the bot named in the environment."""
    token, chat = os.environ["NOTIFY_BOT_TOKEN"], os.environ["NOTIFY_CHAT_ID"]
    if not drain(FOLDER, lambda text: _send(token, chat, text)):
        time.sleep(RETRY_SECONDS)


if __name__ == "__main__":
    main()
