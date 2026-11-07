# Bitpulse

Bitpulse is a world news site published in English and Turkish at bitpulse.cloud. It follows global events around the clock and researches the most interesting stories with the help of AI. The code and the editorial rules are published here so that readers can see how the site works.

## Project status

The site code, the stories, the automated checks and the release pipeline are in this repository. The site is live at bitpulse.cloud. Automatic releases are switched off, so a new story reaches readers after a manual release.

## How the project is run

The project owner follows world news sources and chooses the stories worth publishing. Each chosen story is researched with the help of AI, checked against its sources and published under the editorial policy. News content follows docs/editorial-policy.md and docs/style-guide.md, and social posts follow docs/social-posts.md. Product and design decisions made so far are recorded in docs/site-decisions.md, and advertising decisions are recorded in docs/advertising.md.

## Accuracy of the content

Every article shows its sources, and mistakes are fixed with a visible correction. The full rules are in docs/editorial-policy.md.

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

Every push runs the tests, a build and a secret scan.

## Adding a story

A story is one folder under src/content/stories, named with its date and a short key. The folder holds en.md, tr.md and the image. The build stops if a story misses a language, a source, an image or an image license, because a broken article should never reach readers.

Times are written in UTC. The time field gives the publishing time on the day in the folder name, written as 14:20. A story that grows gets an entry under updates with its time, written as 2026-11-07 16:05, and a short note. When the update also sets promote to true, the story returns to the top of the home page with an Updated label. A correction sets corrected to the time of the fix and adds a dated note to the text. The site shows every time in the reader's own time zone.

## Social posts

Every news story is also shared on X and Instagram, and the owner publishes the posts by hand. The format is described in docs/social-posts.md. The story folder holds a social.yaml file with the English text and the image addresses. One command downloads the images and writes the X post, the Instagram caption and the Instagram pages into the social-posts folder, which git ignores. Without a folder name it takes the newest news story.

```bash
npm run social
npm run social -- 2026-11-04-hera-dimorphos
```

Social images are often press or news photos. They may be shared with credit on a social account, but they are not covered by the licenses of this repository, so only their addresses are stored here.

## Licenses

Three licenses apply because the project contains three kinds of work. Code and documents are released under the MIT License in LICENSE, which keeps them easy to reuse. Articles are released under Creative Commons Attribution 4.0 as described in LICENSE-CONTENT.md, because a reused article should still credit its source. Fonts keep their own SIL Open Font License, and those license files ship next to the fonts.
