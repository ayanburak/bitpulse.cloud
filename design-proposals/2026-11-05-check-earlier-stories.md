# Proposal: check sentences about earlier stories against those stories

Status: open, waiting for review.

Branch: proposal/check-earlier-stories

This changes text in the role files only. It does not change how the site looks, so it has no screenshots.

## The reason

On 2026-11-04 and again on 2026-11-05, a sentence in a new piece summarised the earlier Macronix story. It said that Macronix moved capacity toward AI memory, but the Macronix story says that only of its NOR chips. Both times the sentence passed the writer, the fact checker, the editor and the final checker. The main agent caught it before the merge. No role file says that an earlier Bitpulse story is the source of a sentence that summarises it, so no role compared the two.

Pieces link to each other more often now: the RAM explainer, the Macronix story and the Nintendo story of 2026-11-05 all point to each other. A wrong summary of an earlier story makes the site contradict itself. Readers who follow the link see the contradiction.

## The change

One sentence is added to each role file:

- agents/writer.md: a sentence that summarises or links to an earlier Bitpulse story has that story as its source, and the writer opens it and checks the sentence.
- agents/fact-checker.md: the fact checker compares such a sentence with that story in the same language.
- agents/editor.md: an edit keeps such a sentence within what that story says.
- agents/final-checker.md: the final checker compares every such sentence with that story.

In the run of 2026-11-05, the main agent gave each role this instruction by hand, and no such error reached the main agent. The proposal turns that instruction into a rule.
