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

The site has eleven pieces in English and Turkish on main. The latest is the news story "Nintendo Switch Cartridge Chips Lose a Maker to the AI Boom" in games (src/content/stories/2026-11-04-macronix-rom-switch), with its social.yaml. Before it came the news story on ESA's Hera probe and the explainer "Will Quantum Computers Break Encryption?". The run report is journal/2026-11-04-03.md.

Releases from main are switched off and happen manually after a run. The Macronix story has not been released yet. The latest release, on 2026-11-04 at 19:18 UTC, added links to the X and Instagram accounts in the footer, together with the social post setup described in docs/agent-manual.md.

The headline rule is in docs/style-guide.md. The Alphabet story and the AI chip race story link to each other in the text. The other stories have no real neighbour yet.

The git history of main was condensed into eleven commits on 2026-11-04, one for each milestone, with the files unchanged. The journal folder holds the detailed history. Tests and CI pass on main. No draft branch is open. No proposal is open. The old proposal/ branches in the repository belong to proposals that have already been decided.

## Next tasks

1. Publish one explainer, because the latest published piece is a news story. Candidates were ranked by a research agent on 2026-11-04. The evidence of demand is indirect, because Google Trends, Reddit and Quora could not be opened.
   1. "Why is RAM so expensive right now and when will prices come down?" This is timely, but it dates quickly. Use Micron and SK Hynix filings. As an economy piece it must not predict prices as if the outcome were known. The Macronix story touches the same shortage, so an in-body link between them may fit if the explainer mentions memory makers moving capacity to AI.
   2. "What happens to my passkeys if I lose my phone?" Use FIDO Alliance and WebAuthn sources, not vendor blogs.
   3. "When will solid-state batteries actually be in cars?" Separate semi-solid batteries from all solid-state ones, and use filings and papers.
   4. "How much energy and water does one AI prompt actually use?" Published figures differ by orders of magnitude. It touches AI, so do not run it right after an AI piece.
   5. "How does the Rubin Observatory help find dark matter?" This one has the weakest evidence of demand.
2. Plan follow-up news stories that link back in both languages. ESA's first detailed images of Dimorphos are due on 25 November 2026, for src/content/stories/2026-11-04-hera-dimorphos. Nintendo's half-year results were due on 5 November 2026; if they say anything about physical games, cartridges or the digital share, they suit a follow-up to src/content/stories/2026-11-04-macronix-rom-switch.
3. Read 2026-11-04 and later days in /stats/index.json, the first full days after the release of 2026-11-03 at 21:45 UTC, and record what they show.
4. When a new story has a real connection to an earlier one, add an in-body link in both languages, wrapping existing words and changing no fact.
5. Write the journal report at the next free run number and rewrite this file.

## Open items

- The statistics job runs at 00:40 UTC and writes the previous day. The published days include the owner's own devices and privately shared links, so they do not show reach. The job can only separate visitors by the browser name they send. The latest listed day, 2026-11-03, had 23 views, 113 bot views and 8 not found responses.
- More detailed reader statistics and a consent notice wait until the AdSense review has ended, by the owner's decision.
- Search Console showed 26 impressions and 3 clicks for 2026-10-26 to 2026-11-01, all on the root address. The effect of the shorter headlines can be read there per page after a release.
- The headline limits are not enforced by a test. A test would be a separate locked change.
- The Turkish length test sets a minimum of 500 words for a news story. It leaves editors no room to cut a short Turkish story, which pushes writers to pad. The Macronix story ended at 506 Turkish words after the final check. Changing the test would be a locked change and has not been proposed.
- Measured costs, not counting the main agent: about 154,000 to 182,000 tokens for a news story with no returns, about 34,000 more for its social posts, and about 225,000 for an explainer whose question was researched in advance.
- Closing lines, summaries and social posts need the same source check as the body. On 2026-11-04 an unsourced closing sentence passed all four roles, and in run 03 two social sentences went beyond the story. The main agent caught both.
- Social images taken from news pages often name no owner. They are then credited to the outlet alone.
- Stories have no field for a correction note, so the corrections page lists only titles and dates, and a note has to go in the story text.
- Claims that Google News ignores Publisher Center submissions rest on one trade source. Apple News, MSN and Reddit rules were not confirmed by research.
- The owner opened X and Instagram accounts on 2026-11-04 and posts every news story by hand. Agents prepare the posts in social.yaml, as described under Social posts in docs/agent-manual.md. Every news story published so far has its social.yaml. The owner does not plan to post stories in outside communities for now.

## Owner actions

### Waiting for the owner

- Release main so that the Macronix story and its social posts go live, then post it on X and Instagram with npm run social.

### Requested by the owner

