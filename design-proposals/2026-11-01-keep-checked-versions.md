# Proposal: keep each checked version of a story

Status: open, waiting for review.

Branch: proposal/keep-checked-versions

Fingerprint of the locked files on the branch: 51ffe822c4cf4146dfce5fac759d5ef2e0aa026ef9e472be135c03db8b868dfa

## The problem

The final checker opens the sources behind the headline, the summary and the main figures, plus everything that changed after the fact check. That limit only works if the changes can be seen. The story on Alphabet reached its branch as a single commit, so the version the fact checker approved was not kept, and the editor's changes could not be identified.

The final check therefore covered every claim and all 11 sources. It used about 105,000 tokens, in a run with a small usage limit. Fewer stories per usage window means fewer chances to reach readers.

## The change

One sentence is added under Writing stories in docs/agent-manual.md. Each role commits its finished version to the draft branch before the next role starts, so the final checker can see exactly what changed after the fact check.

## Effect on the design

Nothing changes on screen, so screenshots are not included. The proposal is here because the manual is locked.

## Checks

The change touches only docs/agent-manual.md. The design-lock check fails on the branch by design until a new fingerprint is approved. This proposal and proposal/search-and-sharing-metadata each carry their own fingerprint, so the second one approved needs a new value.
