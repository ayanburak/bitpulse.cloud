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

The site has fifteen pieces in English and Turkish on main. The latest is the news story "Humanoid Maker Agility Lists on Nasdaq With $1.8M in Revenue" in economy (src/content/stories/2026-11-06-agility-nasdaq-debut), with a social.yaml that has no video field. Before it came the news stories on the space station's last new solar array (2026-11-06-iss-final-solar-array, with a video field) and on Nintendo's digital share of sales (2026-11-05-nintendo-digital-share), and the explainer on RAM prices (2026-11-05-why-ram-is-expensive, kind: long). The run report is journal/2026-11-06-02.md.

Releases from main are switched off and happen manually after a run, so this file does not say which pieces are live. https://bitpulse.cloud/sitemap.xml lists every published page.

Tests and CI pass on main. No draft branch is open. Two proposals are open: design-proposals/2026-11-05-check-earlier-stories.md on proposal/check-earlier-stories, and design-proposals/2026-11-06-readable-footage.md on proposal/readable-footage. The other proposal/ branches belong to proposals that have already been decided.

## Next tasks

1. Publish one piece, chosen as described under Choosing a piece in docs/agent-manual.md. The three latest pieces are news stories and the one before them an explainer, so one more news story comes before the next explainer.
2. Until proposal/readable-footage is decided, tell the writer that footage counts only at an address that npm run video-scan opens, with its own sound. A YouTube page does not count.
3. Until proposal/check-earlier-stories is decided, tell every role that a sentence summarising an earlier Bitpulse story is checked against that story.
4. Tell the writer and the final checker to run the browser tests as well as the unit tests (npm run build, then npx playwright test) before handing on. A NASA image must link to https://www.nasa.gov/nasa-brand-center/images-and-media/ as its licenseUrl, and only the browser tests check it.
5. Tell the writer and the editor that every background explanation, including the meaning of a financial or technical term, needs an opened source like any other claim.
6. Read 2026-11-06 and later days in /stats/index.json and record them.
7. Write the journal report at the next free run number and rewrite this file.

## Open items

- The statistics job runs at 00:40 UTC and writes the previous day. The published days include the owner's own devices and privately shared links, so they do not show reach. The latest published day, 2026-11-05, had 142 views, 125 bot views and 30 not found responses, and t.co sent 4 visits.
- The video in the ISS story's social.yaml points to the HLS address of NASA's live event stream, at 28,190 seconds. Such an address may stop working once NASA moves the replay. If it fails, the NASA+ page or the YouTube replay (https://youtube.com/live/25JEQqgv5I4) is the place to find the same moment.
- The Agility story's image is a photo of another company's humanoid robot, the AgiBot X2, with alt text that says so. No Agility photo larger than 2000 pixels in a real scene was found. If one appears, the image can be replaced.
- Reports of Agility's first trading day give an open of $11.26, and Nasdaq's data gives $11.38, so the story says "just over $11".
- The RAM explainer rests on market figures that will change. If a figure turns out to be wrong, the story gets a dated correction note in its text.
- More detailed reader statistics and a consent notice wait until the AdSense review has ended, by the owner's decision.
- Search Console showed 26 impressions and 3 clicks for 2026-10-26 to 2026-11-01, all on the root address. After a release, it can show per page which headlines bring searches.
- The headline limits are not enforced by a test. A test would be a separate locked change.
- The Turkish length test sets a minimum of 500 words for a news story, which pushes writers to pad short Turkish stories. Changing it would be a locked change and has not been proposed.
- Measured costs, not counting the main agent: about 154,000 to 205,000 tokens for a news story with no returns, about 315,000 with one return, about 34,000 to 56,000 more for its social posts, and about 225,000 to 238,000 for an explainer.
- Closing lines, summaries, link sentences and social posts need the same source check as the body. An editor's added explanation needs it too, which the final checker caught on 2026-11-06.
- When an editor cuts from one language only, the final checker has to confirm that both versions still carry the same facts.
- For a news story about a live broadcast, a replay offset is set from the frames with npm run video-scan, not worked out from a timeline.
- Stories have no field for a correction note, so the corrections page lists only titles and dates, and a note has to go in the story text.
- The owner posts every news story on X and Instagram by hand from its social.yaml. Explainers are not posted.

## Owner actions

### Waiting for the owner

- Review the proposal in design-proposals/2026-11-05-check-earlier-stories.md (branch proposal/check-earlier-stories). It changes role files only.
- Review the proposal in design-proposals/2026-11-06-readable-footage.md (branch proposal/readable-footage). It changes agents/writer.md only.
- Run npm run social for the ISS story soon, because its video comes from NASA's live stream address, which may expire.
- A short daily list of the most requested missing paths, in aggregated form, would show whether readers hit broken links or bots probe for files. The statistics job runs on the server, so only the owner can add it.

### Requested by the owner

## Social results

Written by the owner before a run. Each line is one post: the date it was posted, the story folder, the platform, the format, views, average watch time for videos, likes, saves, shares and new followers. Agents read this section and keep it as it is.

| Posted | Story | Platform | Format | Views | Avg watch | Likes | Saves | Shares | Follows |
|---|---|---|---|---|---|---|---|---|---|
