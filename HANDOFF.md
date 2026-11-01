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

The site is live at bitpulse.cloud with six stories in English and Turkish. The latest is on the crew leaving NASA's simulated Mars habitat. Link previews, structured data and RSS feeds are part of the site.

Releases from main are switched off. A new story on main reaches readers only after a manual release, which happens after the run ends.

Tests pass on main. The sitemap now has dates and language links, and the x-default link on Turkish stories points to the English story. No proposal or draft branch is open.

## Next tasks

1. Publish one new story. If its central event happened today, find a good source for the event before writing. Prefer a story with a strong Turkish angle and write the Turkish headline the way a reader would search for it. Consider one explainer with a lasting question, such as what a TPU is, linked to the news story behind it. In-body links to earlier stories need no locked file.
2. Prepare a proposal for separate editorial policy and corrections pages in both languages, linked from the footer. They need locked files and a visible change, so the proposal needs screenshots. Publisher and bylines stay as set in docs/site-decisions.md and docs/editorial-policy.md.
3. Write the journal report at the next free run number and rewrite this file.

## Open items

- The first statistics are still empty, so decisions rest on research and not on readers. Search Console data on which language earns impressions would be the first real signal for the Turkish idea, which so far rests on inference.
- A whole story costs about 190,000 tokens with no returns, not counting the main agent. The final check is the largest single cost.
- Claims that Google News ignores Publisher Center submissions rest on one trade source, as Google's own page could not be opened.
- Apple News, MSN, Reddit rules and Turkish aggregators were not confirmed by research.

## Owner actions

### Waiting for the owner

- Decide whether Bitpulse should have social accounts for sharing new stories. A new site has no regular readers, and agents can not create accounts. It takes creating the accounts and a decision on how posts are made.
- Consider submitting the English feed to Flipboard, which reviews publishers through its own self-service form. It takes one Flipboard account, and the evidence that it brings readers to unknown publishers is weak.
- After about a month of real data, consider one human written post on Hacker News about the open, AI-run newsroom. Its guidelines allow occasional self-submission and reject generated text, so an agent can not write or post it.
- Decide whether a PaktLabs logo should be added to public/ for the publisher field in structured data. No such image is in the repository.

### Requested by the owner

