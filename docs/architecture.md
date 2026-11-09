# Architecture

Bitpulse is a news site whose pages are plain files. Everything behind those files, from the first sign of a story to the post on a social account, is one system made of small parts. This document describes what the parts are and how they talk to each other. How the system is protected is in [security.md](security.md).

## The idea

A reader never reaches a program. Every page is built ahead of time and served as a finished file, so a sudden crowd costs almost nothing and there is no running application on the public site that could fail or be attacked. All the moving parts sit behind that line, on a small server shared with other sites, and they are kept simple for that reason.

Stories do not live in Git. A story changes when it is corrected or updated, and a commit for each of those would tie publishing to a code host. The database on the server is the source of every story and keeps all of its versions. Git carries the code, the rules and the documents.

## The parts

The API is a Python program built on FastAPI. It holds stories, images, publishing jobs, radar events and the audit log in one SQLite file, and it is the only part that opens that file. It listens only inside the server.

The render worker is the existing TypeScript site code. It receives a folder with the stories to build and answers with one result file. It never opens the database, and the API never writes pages. The two meet in a shared folder, so neither can reach into the other.

The admin panel is a React application on its own address. It is the one part of the API that can be reached from the internet, and it is limited to the routes under the panel path.

The bitpulse command runs on the editor's device. It uploads drafts, publishes, fetches briefs and uploads social files. It reaches the API through an SSH tunnel, using an account that can do nothing but open that tunnel.

The radar is a Python program with its own database. It reads news feeds, groups stories about one event, asks a small model to score the strongest events and sends the best to the editor on Telegram. It also copies each event, with its score and the stage it reached, to the API.

The notice service sends important events from the audit log to Telegram with a bot of its own. It exists because the API is not allowed to open a connection to the internet.

The social post generator runs on the editor's device, because they need a real browser and video tools that do not belong on a shared server.

The workflows folder holds the written procedures that a writing session follows. They are part of the code because they decide how a story is checked.

## From an event to a story

The radar reads the feeds every few minutes and scores events once an hour during the editor's working hours. An event that passes a fixed bar goes to Telegram, at most two from each category in a round. Once a day the best waiting event of every category that had nothing yet is sent as well, so no subject goes missing. One that passes the bar but loses its place waits and competes again in later rounds. Every other event is copied to the panel too, marked with how far it got, so the editor can see what was left out and why, and can still choose it.

The editor answers Do or Skip in Telegram or in the panel. The answer is stored by the API and nowhere else. A link can also be sent to the bot or added in the panel, and it becomes a chosen event of its own. Because the API can not reach the internet, it only records what is wanted and the radar picks the work up. The radar then reads the sources of the event and writes one file, the brief, which it hands back to the API.

A writing session starts from that brief. Software opens the folder, downloads the image and compares every number and quotation in the text with the brief. A model writes in both languages, and a separate check compares the headline, the summary and the social text with the story, because short text is where meaning slips most.

## Publishing

A draft goes to the API as a new version of its story, and the versions can never be changed afterwards. A publishing request enters a queue that runs one job at a time, and the publishing time is written by the server at that moment.

The worker builds a complete new release folder from the published versions. Pages are checked, and the live site then moves to the new release by switching one link in a single step, so a reader sees either the old site or the new one. When the new pages do not open, the site stays where it was.

Undoing a publish is an ordinary publish of the older version. Moving the link back alone would not be enough, since the database would still call the bad version live and the next build would restore it.

## Social posts

The text of a post is part of the story. The finished files are made on the device and uploaded to the API, where the panel shows them for the editor to copy, download and mark as shared. They are removed after thirty days, because they can always be made again.

## Releasing code

Each part has its own release script, and each script runs from the maintainer's machine, sends only committed code and runs the tests first. GitHub has no way to reach the server. A code release keeps the previous versions, and database migrations only add to the schema, so older code can still run on a newer database.

## What stays out of this repository

Stories and images, the real server configuration, keys and passwords, and the music and font files are kept outside. Sample stories in the tests stand in for the real ones.
