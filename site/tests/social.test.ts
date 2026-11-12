/**
 * file: tests/social.test.ts
 * importable: nothing, the test runner loads this file
 *
 * description: Checks that every news story has valid social text, that explainers have none and
 * that newer posts keep to one short page.
 */

// NOTE: The social text is written after the final check, so a story on a draft/ branch may not
// have it yet. A file that exists is still checked there. On every other branch it is required.

import { execSync } from "node:child_process";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { buildSocial, postFolder } from "../src/social";
import { buildStories } from "../src/stories";

const ROOT = process.env.BITPULSE_STORIES ?? "src/content/stories";

// GitHub Actions checks out a commit without a branch, so it names the branch in variables.
// GITHUB_HEAD_REF is set for pull requests and GITHUB_REF_NAME for pushes.
const BRANCH = process.env.GITHUB_HEAD_REF || process.env.GITHUB_REF_NAME || execSync("git branch --show-current", { encoding: "utf8" }).trim();
const DRAFT = BRANCH.startsWith("draft/");

function readStoryFiles(): Record<string, string> {
  const files: Record<string, string> = {};
  for (const folder of readdirSync(ROOT)) {
    for (const lang of ["en", "tr"]) {
      const path = join(ROOT, folder, `${lang}.md`);
      files[path] = readFileSync(path, "utf8");
    }
  }
  return files;
}

// buildSocial throws on every broken rule, so one call covers the fields and all the limits.
describe.each(buildStories(readStoryFiles()))("$key", (story) => {
  const path = join(ROOT, story.key, "social.yaml");

  if (story.kind === "news") {
    it("has social text within the limits", () => {
      if (DRAFT && !existsSync(path)) return;
      expect(existsSync(path)).toBe(true);
      expect(() => buildSocial(readFileSync(path, "utf8"), story)).not.toThrow();
    });
  } else {
    it("has no social text, explainers are not shared", () => {
      expect(existsSync(path)).toBe(false);
    });
  }
});

// --- Page rules ---

// A real story is used, because buildSocial takes the link and the story kind from it. Only the
// pages change between the cases, the rest is the smallest valid file.
// The folder name sits in its own constant. Written right after story.key, the secret scan took
// it for an API key.
const FOLDER = "2026-11-04-hera-dimorphos";
// Any news story works, the rules depend on the date in its folder name and that is set here.
const HERA = { ...buildStories(readStoryFiles()).find((story) => story.kind === "news")!, key: FOLDER };
const BASE = `x: A post.
pages:
  - image: https://example.com/a.png
    credit: ESA
    text: A page.
caption: A caption.
`;

it("refuses the old video field", () => {
  expect(() => buildSocial(`${BASE}video:\n  source: https://example.com/clip.mp4\n`, HERA)).toThrow("unknown field: video");
});

it("takes a position for a photo whose subject is off center", () => {
  const at = (position: string) => BASE.replace("    credit: ESA\n", `    credit: ESA\n    position: ${position}\n`);
  expect(buildSocial(BASE, HERA).pages[0].position).toBe("50% 50%");
  expect(buildSocial(at("85% 50%"), HERA).pages[0].position).toBe("85% 50%");
  expect(() => buildSocial(at("right"), HERA)).toThrow("invalid position");
  expect(() => buildSocial(at("120% 50%"), HERA)).toThrow("invalid position");
});

// The same story under a later folder name, so the rule for pages from 7 November applies to it.
// The name sits in its own constant for the same reason as FOLDER above.
const LATER_FOLDER = "2026-11-07-hera-dimorphos";
const TIGHT_FOLDER = "2026-11-12-hera-dimorphos";

describe("pages from 7 November", () => {
  const later = { ...HERA, key: LATER_FOLDER };
  const page = (text: string) => BASE.replace("text: A page.", `text: |\n      ${text.replace(/\n/g, "\n      ")}`);

  it("take one short sentence", () => {
    expect(() => buildSocial(page("The US is offering up to $20 million for tips about Iran's nuclear program."), later)).not.toThrow();
  });

  it("refuse a second paragraph and a long text, which older posts may keep", () => {
    const two = page("One sentence.\n\nAnother one.");
    expect(() => buildSocial(two, later)).toThrow("more than 1 paragraph");
    expect(() => buildSocial(two, HERA)).not.toThrow();
    expect(() => buildSocial(page("word ".repeat(30).trim()), later)).toThrow("the limit is 120");
  });

  it("from 12 November take at most 70 characters", () => {
    const tight = { ...HERA, key: TIGHT_FOLDER };
    expect(() => buildSocial(page("The Iran war could help cut fossil fuel emissions."), tight)).not.toThrow();
    expect(() => buildSocial(page("Fossil fuel emissions are set to fall for the first time since 2020, partly due to war."), tight)).toThrow("the limit is 70");
    expect(() => buildSocial(page("Fossil fuel emissions are set to fall for the first time since 2020, partly due to war."), later)).not.toThrow();
  });
});

// The name sits in its own constant for the same reason as FOLDER above.
const PLAIN_FOLDER = "2026-11-10-hera-dimorphos";

describe("Instagram text from 10 November", () => {
  const later = { ...HERA, key: PLAIN_FOLDER };
  const post = (page: string, caption = "A caption.") => `x: A post.\npages:\n  - image: https://example.com/a.png\n    credit: ESA\n    text: "${page}"\ncaption: "${caption}"\n`;

  it.each(["A Houthi-run ministry spoke.", "It ended 3-0.", "He spoke — then left.", "He spoke - then left."])("refuses the dash in: %s", (page) => {
    expect(() => buildSocial(post(page), later)).toThrow("has a dash");
    expect(() => buildSocial(post("A page.", page), later)).toThrow("has a dash");
  });

  it.each(["Jean-Noël Barrot spoke.", "Al-Asbahi spoke.", "Abdel Fattah al-Sisi spoke.", "An F-35 landed."])("keeps the dash of a name in: %s", (page) => {
    expect(() => buildSocial(post(page), later)).not.toThrow();
  });

  it.each(["**Big** news.", "Big news 🔥", "Big #news."])("refuses formatting in: %s", (page) => {
    expect(() => buildSocial(post(page), later)).toThrow("has formatting");
  });

  it("leaves older posts as they were shared", () => {
    expect(() => buildSocial(post("A Houthi-run ministry spoke."), HERA)).not.toThrow();
  });
});

// The name sits in its own constant for the same reason as FOLDER above.
const ONE_PAGE_FOLDER = "2026-11-08-hera-dimorphos";

describe("posts from 8 November", () => {
  const later = { ...HERA, key: ONE_PAGE_FOLDER };
  const two = BASE.replace("caption:", "  - image: https://example.com/b.png\n    credit: ESA\n    text: Another page.\ncaption:");

  it("have one page, which older posts may go beyond", () => {
    expect(buildSocial(BASE, later).pages).toHaveLength(1);
    expect(() => buildSocial(two, later)).toThrow("more than 1 page");
    expect(buildSocial(two, HERA).pages).toHaveLength(2);
  });
});

// --- Folder ---

describe("post folder", () => {
  it("puts the publishing time after the day so a day's posts sort in order", () => {
    const story = { ...HERA, published: "2026-11-04T10:37:00Z" };
    expect(postFolder(story)).toBe("2026-11-04-1037-hera-dimorphos");
  });
});
