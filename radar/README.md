# bitpulse-radar

The radar listens to world news feeds for Bitpulse and sends the editor a few good candidates every hour on Telegram. The editor picks a story with the Do button and writes it with Claude. Nothing is published by the radar itself.

## How it works

Every few minutes `radar listen` reads the feeds in `sources.toml`. A new story is stored once and joins a cluster with the other stories about the same event, matched by the words of their titles. When five separate outlets report the same event within ninety minutes, it is sent at once as a big event.

Every hour, day and night, `radar rank` sends each new event of the last day to Claude Haiku once. The events go in parts small enough to keep every request cheap. For each event the model answers four questions. Is it about the countries the site covers, or does it touch them directly? Does something change? Is there a clash, a surprise or a known name? Can a picture tell it? An event outside the covered countries is dropped. The others get a score in which change counts most, tension nearly as much and the picture least. The number of outlets is not part of the score and only breaks a tie. The model also gets the titles of every event it scored that day and of the events sent in the last three days, so pieces of one story that the title matching split apart are merged and a follow-up of a story already sent is not sent again.

Only events above a fixed bar are sent, so a weak hour sends nothing, and each round sends at most two events per category. An event that passes the bar but loses its place waits and competes again in the following rounds, without another call to the model. The model reads only titles, outlet names and short summaries, and the editor's earlier Do and Skip answers are not sent to it.

`radar poll` runs all the time and records each Do and Skip on the Bitpulse API, which is the only place a decision is kept. Each ranking round also copies its events, with their scores and the stage they reached, to the API, so the admin panel can show what was sent and what was left out. The same loop does what the panel asks for: it updates the Telegram post of a decision made there, opens a link added there and writes briefs. A Do answer gives the cluster number, such as R-0142, and `radar show R-0142` prints every story of that cluster with its link, which is where the writing starts.

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

Sending needs the values below in the environment. They are never written into this repository.

| Variable | Meaning |
|---|---|
| `TELEGRAM_TOKEN` | Token of the bot from BotFather |
| `TELEGRAM_CHAT_ID` | The editor's chat, found once with `radar chat-id` after writing to the bot |
| `ANTHROPIC_API_KEY` | API key used by the ranking |
| `RADAR_API_KEY` | Key of the Bitpulse API, limited to the radar routes |

Without `TELEGRAM_TOKEN`, big events are only printed, which keeps a development machine quiet.
