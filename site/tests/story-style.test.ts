/**
 * file: tests/story-style.test.ts
 * importable: nothing, the test runner loads this file
 *
 * description: Checks the parts of the style guide that a machine can measure.
 */

// NOTE: Tone and repeated comparisons can not be measured here, the editor role handles those.

import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { buildStories } from "../src/stories";

const ROOT = process.env.BITPULSE_STORIES ?? "src/content/stories";
// News stories became short on 2026-11-07. Stories published before that keep the old length,
// because published stories are not rewritten. Turkish says the same thing in fewer words, so its
// lower limit sits a little below the English one.
const SHORT_SINCE = "2026-11-07";
const NEWS_WORDS = { en: [300, 500], tr: [250, 500] } as const;
const OLD_NEWS_WORDS = [500, 900] as const;
// Turkish says the same thing in fewer words, so the lower limit sits below the 1,500 of the guide.
const MIN_LONG_WORDS = 1200;
const MAX_LONG_WORDS = 2600;
const LANGS = ["en", "tr"] as const;

function readStoryFiles(): Record<string, string> {
  const files: Record<string, string> = {};
  for (const folder of readdirSync(ROOT)) {
    for (const lang of LANGS) {
      const path = join(ROOT, folder, `${lang}.md`);
      files[path] = readFileSync(path, "utf8");
    }
  }
  return files;
}

function wordCount(html: string): number {
  return html.replace(/<[^>]+>/g, " ").trim().split(/\s+/).length;
}

const stories = buildStories(readStoryFiles());

describe.each(stories.filter((story) => story.kind === "news"))("$key", (story) => {
  it.each(LANGS)("has a news length in %s", (lang) => {
    const words = wordCount(story.versions[lang].html);
    // The folder name starts with the date, and ISO dates compare correctly as text.
    const [min, max] = story.key.slice(0, 10) >= SHORT_SINCE ? NEWS_WORDS[lang] : OLD_NEWS_WORDS;
    expect(words).toBeGreaterThanOrEqual(min);
    expect(words).toBeLessThanOrEqual(max);
  });
});

describe.each(stories.filter((story) => story.kind === "long"))("$key", (story) => {
  it.each(LANGS)("has an explainer length in %s", (lang) => {
    const words = wordCount(story.versions[lang].html);
    expect(words).toBeGreaterThanOrEqual(MIN_LONG_WORDS);
    expect(words).toBeLessThanOrEqual(MAX_LONG_WORDS);
  });
});

describe.each(LANGS)("subheadings in %s", (lang) => {
  it("are never reused between stories", () => {
    const headings = stories.flatMap((story) => story.versions[lang].headings.map((heading) => heading.text));
    expect(headings.length).toBe(new Set(headings).size);
  });
});
