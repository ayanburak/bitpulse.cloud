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

The site is live at bitpulse.cloud with eight pieces in English and Turkish. The latest is a news story in culture, on the first century tomb found inside the ancient theater at Gölyazı, Bursa (src/content/stories/2026-11-03-apollonia-theater-tomb). The one explainer so far, "Why Do AI Chatbots Make Things Up?", opened the Explained section. Link previews, structured data, RSS feeds, a sitemap with dates and language links, and editorial policy and corrections pages in both languages are part of the site.

Releases from main are switched off. A new piece on main reaches readers only after a manual release, which happens after the run ends.

Tests and CI pass on main. No draft branch is open. One proposal is open, design-proposals/2026-11-03-reader-statistics.md, which is a decision proposal with no branch yet.

## Next tasks

1. Publish one explainer, because the latest published piece is a news story. Choose a lasting technology or science question in the words a Turkish reader would type, and do not repeat the AI chatbot subject. If task 2 below has been done by then, take the top question from its list.
2. Research explainer questions for reach. This task has now been carried over twice. Find how Turkish readers phrase lasting questions on technology and science and which of those are not answered well in Turkish. Write a short ranked list into this file, each question in a reader's own words. If usage is short, do it before the explainer's writer starts, so the explainer can use it.
3. Add in-body links between pieces where they truly help a reader. Stories are open files, and a link must not change any fact in the text.
4. Write the journal report at the next free run number and rewrite this file.

## Open items

- The statistics job runs at 00:40 UTC and writes the previous day. The bot filter was corrected on 2026-11-03. The published days include the owner's own devices and privately shared links, so they do not show reach. The job can only separate visitors by the browser name they send.
- About 41 not found responses a day appear in the statistics, and their paths are not published. A log check on 2026-11-03 found that 36 of the 41 on 2026-11-02 were Let's Encrypt validation requests and 3 were probes for wp-login.php, so that day points to no broken links.
- The privacy page says the aggregated statistics are published in the project's public repository. They are published at bitpulse.cloud/stats. The text is in site code, which is locked, and the statistics proposal includes the fix.
- The Turkish length test sets a minimum of 500 words. It leaves editors no room to cut a short Turkish news story, which pushes writers to pad. Changing it would be a locked change and has not been proposed.
- Measured costs, not counting the main agent: about 172,000 tokens for a news story with no returns, and about 304,000 for an explainer. Editors who leave fact-checked text in place keep the final check cheaper.
- Stories have no field for a correction note, so the corrections page lists only titles and dates, and a note has to go in the story text.
- Claims that Google News ignores Publisher Center submissions rest on one trade source.
- Apple News, MSN, Reddit rules and Turkish aggregators were not confirmed by research.
- Social accounts are on hold by the owner's decision until the AdSense review has ended.

## Owner actions

### Waiting for the owner

- Decide on design-proposals/2026-11-03-reader-statistics.md. Its first steps need no notice and no consent from readers. One was a better bot filter in the server's log job, which is done. The other is verifying the site in Google Search Console, which would show which language earns impressions, the first real test of the Turkish idea. The deeper statistics after an Accept choice need a decision on the consent tool, retention periods for the privacy text and server work. The full list is in the proposal.
- Add the most requested not found paths to the daily statistics, with query strings removed, so agents can find broken links and old addresses. This is server work.

### Requested by the owner

