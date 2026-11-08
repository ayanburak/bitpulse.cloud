/**
 * file: tests/story-images.test.ts
 * importable: nothing, the test runner loads this file
 *
 * description: Checks that every real story has a stored image of a usable size and format.
 */

import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { imageSize } from "image-size";
import { describe, expect, it } from "vitest";
import { buildStories } from "../src/stories";

const ROOT = "src/content/stories";
// A smaller original is never enlarged, so the stored copy keeps its own width up to 2000.
const MIN_WIDTH = 1200;
const MAX_WIDTH = 2000;
const MAX_BYTES = 1_000_000;

// Reads the real content folder, so a story with a bad image fails here before any release.
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

describe.each(buildStories(readStoryFiles()))("$key", (story) => {
  it("uses one image file for both languages", () => {
    expect(story.versions.en.image.file).toBe(story.versions.tr.image.file);
  });

  it("has a landscape JPEG or PNG of a usable size", () => {
    const data = readFileSync(join(ROOT, story.key, story.versions.en.image.file));
    const { width, height, type } = imageSize(data);
    expect(["jpg", "png"]).toContain(type);
    expect(width).toBeGreaterThanOrEqual(MIN_WIDTH);
    expect(width).toBeLessThanOrEqual(MAX_WIDTH);
    expect(width).toBeGreaterThan(height);
    expect(data.byteLength).toBeLessThanOrEqual(MAX_BYTES);
  });
});
