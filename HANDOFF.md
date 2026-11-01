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

The site has five stories. The latest, on Alphabet's record one-day share price fall, passed the final check and is on main. No draft branch is open.

Releases are switched off, so nothing on main reaches readers yet. bitpulse.cloud still serves a temporary page, and the statistics describe that page and not the real site. The only statistics day, 2026-10-31, shows 0 views.

Tests and CI pass on main. Two proposals are open in design-proposals. CI fails on their branches by design, because the locked files differ there.

## Next tasks

1. Publish new stories. The target is three or four per week, and one has gone out this week. Stories age quickly, so pick fresh news over more follow-ups on the Alphabet fall. Commit after each role on the draft branch, because that needs no approval and spares the final checker a full recheck. Record the tokens used per story in the journal.
2. Research what brings readers to a new site with no audience, then put each idea in a proposal or in Owner actions. The last run did none of this research.
3. Write the journal report at the next free run number and rewrite this file.

## Open items

- The cost of a whole story under the model plan is unknown. The last run measured only a final check of the full story, at about 105,000 tokens.
- Real statistics start after the first release, so any decision made before then rests on research and not on readers.
- Both proposals set their own fingerprint, so the second one approved needs a new value.

## Owner actions

### Waiting for the owner

- Review the two proposals in design-proposals. The metadata proposal matters most for reach, because shared links have no picture today.
- Switch on releases. No idea can reach a reader until the site is live, and no statistics can guide the work. It takes setting DEPLOY_ENABLED to true for the repository.
- After the first release, register the site with Google Search Console and Bing Webmaster Tools and submit /sitemap.xml. Search engines find a new site sooner this way. It takes an account with each service and proof of owning the domain.
- Decide whether Bitpulse should have social accounts for sharing new stories. A new site has no regular readers, and agents can not create accounts. It takes creating the accounts and a decision on how posts are made.

### Requested by the owner

None.
