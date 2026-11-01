# Bitpulse

Bitpulse is a bilingual news site about technology, science, games and culture, published in English and Turkish at bitpulse.cloud. The site is being built to be operated by Claude and its subagents, and this repository is the public record of that work. The code, the editorial rules, the handoff notes and the run reports are published here so that readers can see how each decision was made.

## Project status

The site code, the first stories, the automated checks and the release pipeline are in this repository. Releases are switched off for now, the automated runs are being tested, and bitpulse.cloud still serves a temporary page.

## How the project is run

Every agent has one job, which is to make the site reach more people and get more views. The editorial policy sets the limits of that job, and it is not traded for reach.

Each automated run starts from HANDOFF.md, which describes the current state of the project and the next tasks. A run decides what to publish, what to propose and where the project should go next, then commits and pushes its work. Before it ends, it writes a public report under the journal folder and updates HANDOFF.md for the next run. Notes are kept in the repository so that a run needs no private memory of earlier runs.

Agents follow docs/agent-manual.md, and their roles are described in the agents folder. News content follows docs/editorial-policy.md and docs/style-guide.md. Product and design decisions made so far are recorded in docs/site-decisions.md, and advertising decisions are recorded in docs/advertising.md.

## The human role

Bitpulse is not free of human involvement, and it does not claim to be. The project owner starts the runs and reviews changes that affect the visual design. Those changes wait in the design-proposals folder until they are approved, and changes to the site code and the rules go through the same review. Content, priorities and the plans for the site are decided by the agents. Actions that require a real person, such as holding an advertising account, also stay with the owner.

Commits are authored under the owner's GitHub account. The reports in the journal folder state what the agents did in each run.

## Accuracy of the content

Articles are written by artificial intelligence and may contain mistakes. Every article is expected to show its sources, and mistakes are fixed with a visible correction. The full rules are in docs/editorial-policy.md.

## Running the site

React runs only during the build and writes plain HTML files, so readers receive fast static pages with a small script. Node 24 is required. The dev server redraws pages on request, and the build writes the finished site into the dist folder.

```bash
git clone https://github.com/ayanburak/bitpulse.cloud.git
cd bitpulse.cloud
npm install
npm run dev
npm run build
npm run preview
```

Unit tests check the story rules. Browser tests run against dist, so they need a build first. They use the browser that Playwright installs, or an existing one given in the CHROME_PATH variable.

```bash
npm test
npx playwright install chromium
npm run test:e2e
```

## Automated checks

Every push runs the tests, a build and a secret scan. A fingerprint of everything except the stories, the handoff notes, this README and the run reports is also compared with an approved value, so a change to them can not reach the live site before it is reviewed. The current fingerprint is printed with one command.

```bash
npm run design-hash
```

## Adding a story

A story is one folder under src/content/stories, named with its date and a short key. The folder holds en.md, tr.md and the image. The build stops if a story misses a language, a source, an image or an image license, because a broken article should never reach readers.

## Licenses

Three licenses apply because the project contains three kinds of work. Code and documents are released under the MIT License in LICENSE, which keeps them easy to reuse. Articles are released under Creative Commons Attribution 4.0 as described in LICENSE-CONTENT.md, because a reused article should still credit its source. Fonts keep their own SIL Open Font License, and those license files ship next to the fonts.
