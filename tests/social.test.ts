/**
 * file: tests/social.test.ts
 * importable: nothing, the test runner loads this file
 *
 * description: Checks that every news story has valid social text, that explainers have none and
 * that a broken video field is refused.
 */

// NOTE: The social text is written after the final check, so a story on a draft/ branch may not
// have it yet. A file that exists is still checked there. On every other branch it is required.

import { execSync } from "node:child_process";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { buildSocial } from "../src/social";
import { buildStories } from "../src/stories";

const ROOT = "src/content/stories";

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

// --- Video field ---

// A real story is used, because buildSocial takes the link and the story kind from it. Only the
// video field changes between the cases, the rest is the smallest valid file.
// The folder name sits in its own constant. Written right after story.key, the secret scan took
// it for an API key.
const FOLDER = "2026-11-04-hera-dimorphos";
const HERA = buildStories(readStoryFiles()).find((story) => story.key === FOLDER)!;
const BASE = `x: A post.
pages:
  - image: https://example.com/a.png
    credit: ESA
    text: A page.
caption: A caption.
`;
const VIDEO = {
  source: "https://example.com/clip.mp4",
  start: 55.5,
  duration: 15.5,
  text: "NASA hit this asteroid on purpose. The push was *bigger than predicted.*",
  credit: "NASA/Johns Hopkins APL",
};

function withVideo(video: Record<string, unknown>): string {
  return `${BASE}video:\n${Object.entries(video).map(([key, value]) => `  ${key}: ${JSON.stringify(value)}`).join("\n")}\n`;
}

describe("video", () => {
  it("is optional", () => {
    expect(buildSocial(BASE, HERA).video).toBeUndefined();
  });

  it("is read and credited first in the caption", () => {
    const post = buildSocial(withVideo({ ...VIDEO, crop: "1215:1080:352:0" }), HERA);
    expect(post.video).toEqual({ ...VIDEO, crop: "1215:1080:352:0" });
    expect(post.caption).toContain("Video: NASA/Johns Hopkins APL. Image: ESA.");
  });

  it("says in the caption when a clip is sped up and where its sound comes from", () => {
    const fast = buildSocial(withVideo({ ...VIDEO, speed: 25.25, sound: 28820 }), HERA);
    expect(fast.video).toEqual({ ...VIDEO, speed: 25.25, sound: 28820 });
    expect(fast.caption).toContain("Video: NASA/Johns Hopkins APL, sped up 25 times, sound in real time. Image: ESA.");
    const silent = buildSocial(withVideo({ ...VIDEO, speed: 10 }), HERA);
    expect(silent.caption).toContain("Video: NASA/Johns Hopkins APL, sped up 10 times. Image: ESA.");
  });

  it.each([
    ["a missing address", { ...VIDEO, source: undefined }, "missing source"],
    ["a clip that is too short", { ...VIDEO, duration: 5 }, "must be between"],
    ["a clip that is too long", { ...VIDEO, duration: 25 }, "must be between"],
    ["three sentences", { ...VIDEO, text: "One. Two. Three." }, "3 sentences"],
    ["a line that is too long", { ...VIDEO, text: "word ".repeat(20) }, "the limit is 80"],
    ["an asterisk without its pair", { ...VIDEO, text: "One *two." }, "without its pair"],
    ["a crop that is not four numbers", { ...VIDEO, crop: "iw:ih" }, "crop must be"],
    ["an unknown field", { ...VIDEO, music: "loud" }, "unknown field: music"],
    ["a speed that is too low", { ...VIDEO, speed: 1.5 }, "must be between 2 and 60"],
    ["a speed that is too high", { ...VIDEO, speed: 90 }, "must be between 2 and 60"],
    ["a sound second without a speed", { ...VIDEO, sound: 100 }, "only used with speed"],
  ])("refuses %s", (_, video, message) => {
    const clean = Object.fromEntries(Object.entries(video).filter(([, value]) => value !== undefined));
    expect(() => buildSocial(withVideo(clean), HERA)).toThrow(message);
  });
});
