# bitpulse-radar

The radar listens to world news feeds for Bitpulse and sends the editor a few good candidates every hour on Telegram. The editor picks a story with the Do button and writes it with Claude. Nothing is published by the radar itself.

## How it works

Every few minutes `radar listen` reads the feeds in `sources.toml`. A new story is stored once and joins a cluster with the other stories about the same event, matched by the words of their titles. When five separate outlets report the same event within ninety minutes, it is sent at once as a big event.

Every hour inside the editor's hours, `radar rank` collects the clusters that appeared since the last round and asks Claude Haiku for the best few. The order is relative to the round, so a quiet morning still produces candidates and a busy evening does not flood the editor. The first round of the day covers the night and may send a few more. The model reads only titles, outlet names and short summaries, and the editor's earlier Do and Skip answers go into the request as examples.

`radar poll` runs all the time and records each Do and Skip. A Do answer gives the cluster number, such as R-0142, and `radar show R-0142` prints every story of that cluster with its link, which is where the writing starts.

## Sources

The list spans regions and sides on purpose, because a story seen from one place only is not a neutral starting point. State media are marked by name. A feed that fails is skipped and shown by `radar sources`.

## Running it

Python 3.10 or newer is needed, and uv for development. The database is written to `data/radar.db`, or to the path in `RADAR_DB`.

```bash
uv sync
uv run radar listen
uv run radar rank --dry-run
uv run radar show R-0142
uv run pytest
```

Sending needs three values in the environment. They are never written into this repository.

| Variable | Meaning |
|---|---|
| `TELEGRAM_TOKEN` | Token of the bot from BotFather |
| `TELEGRAM_CHAT_ID` | The editor's chat, found once with `radar chat-id` after writing to the bot |
| `ANTHROPIC_API_KEY` | API key used by the ranking |
| `RADAR_HOURS` | Editor's hours in UTC, `06-22` by default |

Without `TELEGRAM_TOKEN`, big events are only printed, which keeps a development machine quiet.
