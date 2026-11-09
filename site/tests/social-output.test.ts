/**
 * file: tests/social-output.test.ts
 * importable: nothing, the test runner loads this file
 *
 * description: Checks that a new social post replaces only the files of the old post.
 */

import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterAll, describe, expect, it } from "vitest";
import { replacePost } from "../scripts/social-output";

const roots: string[] = [];
afterAll(() => roots.forEach((root) => rmSync(root, { recursive: true, force: true })));

function folders() {
  const root = mkdtempSync(join(tmpdir(), "bitpulse-social-"));
  roots.push(root);
  const draft = join(root, ".new");
  const out = join(root, "story");
  mkdirSync(join(draft, "images"), { recursive: true });
  writeFileSync(join(draft, "x.txt"), "new post");
  writeFileSync(join(draft, "page-1.png"), "new page");
  writeFileSync(join(draft, "images", "1.jpeg"), "new image");
  return { draft, out };
}

describe("replacePost", () => {
  it("creates the folder of a new post", () => {
    const { draft, out } = folders();
    replacePost(draft, out);
    expect(readFileSync(join(out, "x.txt"), "utf8")).toBe("new post");
    expect(existsSync(draft)).toBe(false);
  });

  it("keeps a file it did not make", () => {
    const { draft, out } = folders();
    mkdirSync(out);
    writeFileSync(join(out, "notes.txt"), "the notes");
    replacePost(draft, out);
    expect(readFileSync(join(out, "notes.txt"), "utf8")).toBe("the notes");
  });

  it("does not keep a stale last page or old images", () => {
    const { draft, out } = folders();
    mkdirSync(join(out, "images"), { recursive: true });
    writeFileSync(join(out, "page-2.png"), "old page");
    writeFileSync(join(out, "post.mp4"), "old video");
    writeFileSync(join(out, "images", "2.jpeg"), "old image");
    replacePost(draft, out);
    expect(existsSync(join(out, "page-2.png"))).toBe(false);
    expect(existsSync(join(out, "post.mp4"))).toBe(false);
    expect(existsSync(join(out, "images", "2.jpeg"))).toBe(false);
    expect(readFileSync(join(out, "images", "1.jpeg"), "utf8")).toBe("new image");
  });
});
