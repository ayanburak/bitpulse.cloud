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

The site is live at bitpulse.cloud with nine pieces in English and Turkish. The latest is the explainer "Will Quantum Computers Break Encryption?" in technology (src/content/stories/2026-11-04-quantum-computers-encryption), the second explainer after "Why Do AI Chatbots Make Things Up?". Before it came a news story on the tomb in the ancient theater at Gölyazı, Bursa.

On 2026-11-04 the headlines of seven published stories were shortened in both languages, after research on headline length. The run report journal/2026-11-04-01.md lists them. The headline rule was approved and is in docs/style-guide.md. Every shortened headline is checked against its story, because a research draft got the Mars crew count wrong.

The Alphabet story and the AI chip race story link to each other in the text. The other stories have no real neighbour yet.

Releases from main are switched off. The explainer and the new headlines reach readers only after a manual release, which happens after the run ends.

Tests and CI pass on main. No draft branch is open. No proposal is open.

## Next tasks

1. Publish one news story, because the latest published piece is an explainer. Choose a recent event in a category other than technology and culture if a strong one exists. Its headline follows docs/style-guide.md.
2. Check whether 2026-11-03 and later days have appeared in /stats/index.json, and record what they show after the release.
3. Explainer candidates for later runs, ranked by a research agent on 2026-11-04. The evidence of demand is indirect, because Google Trends, Reddit and Quora could not be opened.
   1. "Why is RAM so expensive right now and when will prices come down?" This is timely, but it dates quickly. Use Micron and SK Hynix filings.
   2. "How much energy and water does one AI prompt actually use?" Published figures differ by orders of magnitude. It touches AI, so do not run it right after an AI piece.
   3. "What happens to my passkeys if I lose my phone?" Use FIDO Alliance and WebAuthn sources, not vendor blogs.
   4. "When will solid-state batteries actually be in cars?" Separate semi-solid batteries from all solid-state ones, and use filings and papers.
   5. "How does the Rubin Observatory help find dark matter?" This one has the weakest evidence of demand.
4. When a new story has a real connection to an earlier one, add an in-body link in both languages, wrapping existing words and changing no fact.
5. Write the journal report at the next free run number and rewrite this file.

## Open items

- The statistics job runs at 00:40 UTC and writes the previous day. The published days include the owner's own devices and privately shared links, so they do not show reach. The job can only separate visitors by the browser name they send. On 2026-11-04 the index listed days only up to 2026-11-02.
- More detailed reader statistics and a consent notice wait until the AdSense review has ended, by the owner's decision.
- Search Console showed 26 impressions and 3 clicks for 2026-10-26 to 2026-11-01, all on the root address. The effect of the shorter headlines can be read there per page after a release.
- The headline limits are not enforced by a test. A test would be a separate locked change.
- The Turkish length test sets a minimum of 500 words for a news story. It leaves editors no room to cut a short Turkish story, which pushes writers to pad. Changing it would be a locked change and has not been proposed.
- Measured costs, not counting the main agent: about 172,000 tokens for a news story with no returns, and about 225,000 for an explainer whose question was researched in advance.
- Stories have no field for a correction note, so the corrections page lists only titles and dates, and a note has to go in the story text.
- Claims that Google News ignores Publisher Center submissions rest on one trade source. Apple News, MSN and Reddit rules were not confirmed by research.
- Social accounts are on hold by the owner's decision until the AdSense review has ended. The owner does not plan to post stories in outside communities for now.

## Owner actions

### Waiting for the owner


### Requested by the owner
