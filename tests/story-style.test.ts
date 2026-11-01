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

const ROOT = "src/content/stories";
const MIN_WORDS = 500;
const MAX_WORDS = 900;
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
    expect(words).toBeGreaterThanOrEqual(MIN_WORDS);
    expect(words).toBeLessThanOrEqual(MAX_WORDS);
  });
});

describe.each(LANGS)("subheadings in %s", (lang) => {
  it("are never reused between stories", () => {
    const headings = stories.flatMap((story) => story.versions[lang].headings.map((heading) => heading.text));
    expect(headings.length).toBe(new Set(headings).size);
  });
});
