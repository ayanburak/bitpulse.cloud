# Handoff

This file is a single report for the next agent. It describes the project as it stands now and what comes next. It is not a log.

## How to use this document

Each run reads this file first. At the end of the run, the Current state, Next tasks and Open items sections are replaced with new text, so nothing from older runs builds up here. A step that is finished leaves this file and is recorded in the journal folder, which is the only place for history. This file stays short enough to read in a few minutes.

Everything here is public, so secrets and personal data are never written in it. The how to use section and the section headings stay as they are.

The sections are filled in as follows.

- Current state describes the project at the end of the latest run. It covers what works, what is broken and what is unfinished.
- Next tasks lists the work for the next run, most important first, with enough detail to start without other context.
- Open items lists unresolved questions and known risks that are not tasks yet. An item is removed once it is resolved.
- Social results is written by the owner before a run. It shows how each post did on X and Instagram. Agents read it and keep it as it is.
- Owner actions has two parts. Waiting for the owner lists work that needs a real person, written by agents. Requested by the owner holds notes added by the owner for the next run. Those requests come first in the run, subject to the editorial policy and the agent manual. A request leaves this file once it is done, and the journal records the result.

## Current state

The site has fourteen pieces in English and Turkish on main. The latest is the news story "Astronauts Unroll the Space Station's Last New Solar Array" in science (src/content/stories/2026-11-06-iss-final-solar-array), with a social.yaml that has a video field. Before it came the news story on Nintendo's digital share of sales (2026-11-05-nintendo-digital-share) and the explainer on RAM prices (2026-11-05-why-ram-is-expensive, kind: long). The run report is journal/2026-11-06-01.md.

Releases from main are switched off and happen manually after a run, so this file does not say which pieces are live. https://bitpulse.cloud/sitemap.xml lists every published page.

Tests and CI pass on main. No draft branch is open. Two proposals are open: design-proposals/2026-11-05-check-earlier-stories.md on proposal/check-earlier-stories, and design-proposals/2026-11-06-categories-scope.md on proposal/categories-scope. The second answers the owner's request on categories and scope. The other proposal/ branches belong to proposals that have already been decided.

## Next tasks

1. Publish one news story, chosen as described under Choosing a piece in docs/agent-manual.md. The two latest pieces are news stories and the one before them an explainer, so three more news stories come before the next explainer.
2. Until proposal/check-earlier-stories is decided, tell every role that a sentence summarising an earlier Bitpulse story is checked against that story.
3. Tell the writer and the final checker to run the browser tests as well as the unit tests (npm run build, then npx playwright test) before handing on. A NASA image must link to https://www.nasa.gov/nasa-brand-center/images-and-media/ as its licenseUrl, and only the browser tests check it.
4. Read 2026-11-06 and later days in /stats/index.json and record them.
5. Write the journal report at the next free run number and rewrite this file.

## Open items

- The statistics job runs at 00:40 UTC and writes the previous day. The published days include the owner's own devices and privately shared links, so they do not show reach. 2026-11-05 had 142 views, 125 bot views and 30 not found responses, and t.co sent 4 visits, the first X referrer in the published days.
- The video in the ISS story's social.yaml points to the HLS address of NASA's live event stream, at 28,190 seconds. Such an address may stop working once NASA moves the replay. If it fails, the NASA+ page or the YouTube replay (https://youtube.com/live/25JEQqgv5I4) is the place to find the same moment.
- The RAM explainer rests on market figures that will change. If a figure turns out to be wrong, the story gets a dated correction note in its text.
- More detailed reader statistics and a consent notice wait until the AdSense review has ended, by the owner's decision.
- Search Console showed 26 impressions and 3 clicks for 2026-10-26 to 2026-11-01, all on the root address. After a release, it can show per page which headlines bring searches.
- The headline limits are not enforced by a test. A test would be a separate locked change.
- The Turkish length test sets a minimum of 500 words for a news story, which pushes writers to pad short Turkish stories. Changing it would be a locked change and has not been proposed.
- Measured costs, not counting the main agent: about 154,000 to 205,000 tokens for a news story with no returns, about 34,000 to 52,000 more for its social posts, and about 225,000 to 238,000 for an explainer.
- Closing lines, summaries, link sentences and social posts need the same source check as the body.
- When an editor cuts from one language only, the final checker has to confirm that both versions still carry the same facts. This happened on 2026-11-06.
- For a news story about a live broadcast, a replay offset is set from the frames with npm run video-scan, not worked out from a timeline.
- Stories have no field for a correction note, so the corrections page lists only titles and dates, and a note has to go in the story text.
- The category research found no source that ranks the five categories by worldwide interest. The Reuters Institute topic charts for 2024 to 2026 could not be opened.
- The owner posts every news story on X and Instagram by hand from its social.yaml. Explainers are not posted.

## Owner actions

### Waiting for the owner

- Review the proposal in design-proposals/2026-11-06-categories-scope.md (branch proposal/categories-scope). It keeps the five categories and the menu, gives each category a focus and writes the footage rule into the scope. It changes docs/editorial-policy.md and the policy page text.
- Review the proposal in design-proposals/2026-11-05-check-earlier-stories.md (branch proposal/check-earlier-stories). It changes role files only.
- Run npm run social for the ISS story soon, because its video comes from NASA's live stream address, which may expire.
- A short daily list of the most requested missing paths, in aggregated form, would show whether readers hit broken links or bots probe for files. The statistics job runs on the server, so only the owner can add it.

### Requested by the owner

## Social results

Written by the owner before a run. Each line is one post: the date it was posted, the story folder, the platform, the format, views, average watch time for videos, likes, saves, shares and new followers. Agents read this section and keep it as it is.

| Posted | Story | Platform | Format | Views | Avg watch | Likes | Saves | Shares | Follows |
|---|---|---|---|---|---|---|---|---|---|
