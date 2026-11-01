# Handoff

This file is a single report for the next agent. It describes the project as it stands now and what comes next. It is not a log.

## How to use this document

Each run reads this file first. At the end of the run, the Current state, Next tasks and Open items sections are replaced with new text, so nothing from older runs builds up here. A step that is finished leaves this file and is recorded in the journal folder, which is the only place for history. This file stays short enough to read in a few minutes.

Everything here is public, so secrets and personal data are never written in it. The how to use section and the section headings stay as they are.

The sections are filled in as follows.

- Current state describes the project at the end of the latest run. It covers what works, what is broken and what is unfinished.
- Next tasks lists the work for the next run, most important first, with enough detail to start without other context.
- Open items lists unresolved questions and known risks that are not tasks yet. An item is removed once it is resolved.
- Owner actions has two parts. Waiting for the owner lists work that needs a real person, written by agents. Requested by the owner holds notes added by the owner for the next run. Those requests come first in the run, subject to the editorial policy and the agent manual. A request leaves this file once it is done, and the journal records the result.

## Current state

The site builds into 36 static pages in English and Turkish, with four stories in src/content/stories. Tests, the secret scan and the check of locked files all pass on main.

Releases are switched off, so nothing pushed to main reaches readers yet. bitpulse.cloud still serves a temporary page, and the statistics describe that page and not the real site.

This is the first automated run, so the journal folder and the design-proposals folder do not exist yet.

## Next tasks

1. Publish one story, passing through the writer, fact checker and editor as three separate agents.
2. Work on the mission in docs/agent-manual.md. Research it, then carry out what the run can do alone, and write everything else down as the mission section asks.
3. Write the first report at journal/2026-11-01-01.md and rewrite this file for the next run.

## Open items

- The run has a usage limit and can end without warning. Commits stay small and the Current state section stays accurate for that reason.
- Real statistics start after the first release, so any decision made before then rests on research and not on readers.

## Owner actions

### Waiting for the owner

### Requested by the owner

- This run is a controlled test and publishes one story only.
