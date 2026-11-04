/**
 * file: tests/social.test.ts
 * importable: nothing, the test runner loads this file
 *
 * description: Checks that every news story has valid social text and that explainers have none.
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
