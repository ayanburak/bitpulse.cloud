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

The site has twelve pieces in English and Turkish on main. The latest is the explainer "Why AI Data Centers Are Making Your RAM So Expensive" in economy (src/content/stories/2026-11-05-why-ram-is-expensive, kind: long). Before it came the news story "Nintendo Switch Cartridge Chips Lose a Maker to the AI Boom" (src/content/stories/2026-11-04-macronix-rom-switch) with its social.yaml. The two link to each other in both languages, and so do the Alphabet story and the AI chip race story. The run report is journal/2026-11-05-01.md.

Releases from main are switched off and happen manually after a run. Neither the Macronix story nor the RAM explainer has been released yet. The latest release was on 2026-11-04 at 19:18 UTC.

Tests and CI pass on main. No draft branch is open. No proposal is open. The old proposal/ branches in the repository belong to proposals that have already been decided.

## Next tasks

1. Publish one news story, because the latest published piece is an explainer. Nintendo's half-year results were due on 5 November 2026. If they say anything about physical games, cartridges or the digital share, they suit a follow-up to the Macronix story with a link back in both languages. Otherwise choose freely. The two latest pieces are games and economy, and the two before them science and technology, so culture is the least recent category. Write social.yaml for the news story as described in docs/agent-manual.md.
2. Tell every role that a sentence summarising an earlier Bitpulse story is checked against that story. In two runs in a row, a sentence tied Macronix's capacity shift to AI memory, which the Macronix story says only of NOR chips.
3. Read 2026-11-05 and later days in /stats/index.json and record them. Watch the not found count, which rose from 8 to 27 on 2026-11-04.
4. ESA's first detailed images of Dimorphos are due on 25 November 2026, for a follow-up to src/content/stories/2026-11-04-hera-dimorphos.
5. Explainer candidates for the run after next, ranked on 2026-11-04 on indirect evidence of demand: what happens to passkeys when a phone is lost (FIDO Alliance and WebAuthn sources), when solid-state batteries will be in cars (filings and papers, separating semi-solid from all solid-state), the energy and water used by one AI prompt (not right after an AI piece) and how the Rubin Observatory helps find dark matter.
6. Write the journal report at the next free run number and rewrite this file.

## Open items

- The statistics job runs at 00:40 UTC and writes the previous day. The published days include the owner's own devices and privately shared links, so they do not show reach. The job can only separate visitors by the browser name they send. 2026-11-04 had 37 views, 117 bot views and 27 not found responses. The statistics do not list which paths were not found.
- The RAM explainer rests on market figures that will change, many of them from TrendForce or from Korean outlets relayed by TrendForce. If a figure turns out to be wrong, the story gets a dated correction note in its text.
- More detailed reader statistics and a consent notice wait until the AdSense review has ended, by the owner's decision.
- Search Console showed 26 impressions and 3 clicks for 2026-10-26 to 2026-11-01, all on the root address. After a release, it can show per page whether the shorter headlines and the RAM question bring searches.
- The headline limits are not enforced by a test. A test would be a separate locked change.
- The Turkish length test sets a minimum of 500 words for a news story. It leaves editors no room to cut a short Turkish story, which pushes writers to pad. Changing the test would be a locked change and has not been proposed.
- Measured costs, not counting the main agent: about 154,000 to 182,000 tokens for a news story with no returns, about 34,000 more for its social posts, and about 225,000 to 238,000 for an explainer.
- Closing lines, summaries, link sentences and social posts need the same source check as the body. Unsourced or stretched sentences in these places have reached the main agent in three runs.
- A social image taken from a news page is credited as that page names its owner, and the outlet is added.
- Stories have no field for a correction note, so the corrections page lists only titles and dates, and a note has to go in the story text.
- Claims that Google News ignores Publisher Center submissions rest on one trade source. Apple News, MSN and Reddit rules were not confirmed by research.
- The owner posts every news story on X and Instagram by hand from its social.yaml. Explainers are not posted. The owner does not plan to post stories in outside communities for now.

## Owner actions

### Waiting for the owner

- Release main so that the Macronix story, its social posts and the RAM explainer go live, then post the Macronix story on X and Instagram with npm run social.
- Consider adding a short list of the most requested not found paths to the daily statistics, in aggregated form and without query strings. Not found responses rose from 8 to 27 in a day, and without paths nobody can tell broken links from bots probing for files. The statistics job runs on the server, which agents do not touch.

### Requested by the owner

