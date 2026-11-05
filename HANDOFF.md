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

The site has thirteen pieces in English and Turkish on main. The latest is the news story "Nintendo's Game Software Sales Were 60.7% Digital in Six Months" in games (src/content/stories/2026-11-05-nintendo-digital-share) with its social.yaml. Before it came the explainer "Why AI Data Centers Are Making Your RAM So Expensive" (src/content/stories/2026-11-05-why-ram-is-expensive, kind: long). The Nintendo, Macronix and RAM pieces link to each other in both languages, and so do the Alphabet story and the AI chip race story. The run report is journal/2026-11-05-02.md.

Releases from main are switched off and happen manually after a run, so this file does not say which pieces are live. https://bitpulse.cloud/sitemap.xml lists every published page.

Tests and CI pass on main. No draft branch is open. One proposal is open: design-proposals/2026-11-05-check-earlier-stories.md on proposal/check-earlier-stories, which adds a rule to the role files on sentences that summarise earlier stories. The other proposal/ branches belong to proposals that have already been decided.

## Next tasks

1. Publish one explainer, because the latest published piece is a news story. Candidates, ranked on 2026-11-04 on indirect evidence of demand: what happens to passkeys when a phone is lost (FIDO Alliance and WebAuthn sources), when solid-state batteries will be in cars (filings and papers, separating semi-solid from all solid-state), how the Rubin Observatory helps find dark matter, and the energy and water used by one AI prompt (not right after an AI piece). The three latest pieces are games, economy and games, so a technology or science explainer adds variety.
2. Until the open proposal is decided, tell every role that a sentence summarising an earlier Bitpulse story is checked against that story. That instruction was given by hand in this run, and no such error reached the main agent.
3. Read 2026-11-05 and later days in /stats/index.json and record them. The 2026-11-05 day was not yet published during this run.
4. ESA's first detailed images of Dimorphos are due on 25 November 2026, for a follow-up to src/content/stories/2026-11-04-hera-dimorphos.
5. A later games story can use two leads found by the final checker on 2026-11-05: Circana's US figure that spending on Switch 2 game-key card games rose 631% this year, and the report that Nintendo counts game-key cards as physical sales. Both need their pages opened and confirmed. Such a story would link to the Nintendo and Macronix stories.
6. Write the journal report at the next free run number and rewrite this file.

## Open items

- The statistics job runs at 00:40 UTC and writes the previous day. The published days include the owner's own devices and privately shared links, so they do not show reach. The job can only separate visitors by the browser name they send. 2026-11-04 had 37 views, 117 bot views and 27 not found responses. The server log for that day was read once: the not found responses came from release checks and from one crawler that requested lists of image sizes as if they were single addresses. No reader reached a broken link.
- The RAM explainer rests on market figures that will change, many of them from TrendForce or from Korean outlets relayed by TrendForce. If a figure turns out to be wrong, the story gets a dated correction note in its text.
- More detailed reader statistics and a consent notice wait until the AdSense review has ended, by the owner's decision.
- Search Console showed 26 impressions and 3 clicks for 2026-10-26 to 2026-11-01, all on the root address. After a release, it can show per page whether the shorter headlines, the RAM question and the Nintendo digital share bring searches.
- The headline limits are not enforced by a test. A test would be a separate locked change.
- The Turkish length test sets a minimum of 500 words for a news story. It leaves editors no room to cut a short Turkish story, which pushes writers to pad. In this run the editor added words to the Turkish ending to stay above it. Changing the test would be a locked change and has not been proposed.
- Measured costs, not counting the main agent: about 154,000 to 205,000 tokens for a news story with no returns, about 34,000 to 52,000 more for its social posts, and about 225,000 to 238,000 for an explainer.
- Closing lines, summaries, link sentences and social posts need the same source check as the body. Unsourced or stretched sentences in these places have reached the main agent in three runs.
- The social writer should run the tests before its first commit. On 2026-11-05 an X post over 280 characters failed CI on the draft branch once.
- A social image taken from a news page is credited as that page names its owner, and the outlet is added. For stories about financial results there is often no image of the event, so a page may fall back on the company's logo or product images.
- Stories have no field for a correction note, so the corrections page lists only titles and dates, and a note has to go in the story text.
- Claims that Google News ignores Publisher Center submissions rest on one trade source. Apple News, MSN and Reddit rules were not confirmed by research.
- The owner posts every news story on X and Instagram by hand from its social.yaml. Explainers are not posted. The owner does not plan to post stories in outside communities for now.

## Owner actions

### Waiting for the owner

- Post the Macronix story and the Nintendo digital share story on X and Instagram with npm run social.
- Review the proposal in design-proposals/2026-11-05-check-earlier-stories.md (branch proposal/check-earlier-stories). It changes role files only.
- A short daily list of the most requested missing paths, in aggregated form, would show whether readers hit broken links or bots probe for files. The statistics job runs on the server, so only the owner can add it.

### Requested by the owner
