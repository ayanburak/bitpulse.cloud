/**
 * file: tests/stories.test.ts
 * importable: nothing, the test runner loads this file
 *
 * description: Checks that invalid stories stop the build and valid ones are paired correctly.
 */

import { describe, expect, it } from "vitest";
import { buildStories } from "../src/stories";

// --- Helpers ---

const FOLDER = "2026-10-20-sample-story";
const IMAGE = "\n  file: image.jpg\n  alt: Alt\n  credit: Someone\n  license: CC0\n  licenseUrl: https://example.com/l\n  source: https://example.com/p";

function file(overrides: Record<string, string> = {}, body = "Text.\n"): string {
  const fields: Record<string, string> = {
    slug: "sample-story",
    title: "Title",
    summary: "Summary",
    category: "science",
    date: "2026-10-20",
    kind: "news",
    sources: "\n  - name: Example\n    url: https://example.com/a",
    image: IMAGE,
    ...overrides,
  };
  const lines = Object.entries(fields).map(([key, value]) => `${key}: ${value}`);
  return `---\n${lines.join("\n")}\n---\n${body}`;
}

function story(en = file(), tr = file({ slug: "ornek-haber" }), key = FOLDER): Record<string, string> {
  return { [`./content/stories/${key}/en.md`]: en, [`./content/stories/${key}/tr.md`]: tr };
}

// --- Tests ---

describe("buildStories", () => {
  it("pairs both languages under the folder key", () => {
    const [result] = buildStories(story());
    expect(result.key).toBe(FOLDER);
    expect(result.versions.en.slug).toBe("sample-story");
    expect(result.versions.tr.slug).toBe("ornek-haber");
    expect(result.versions.en.html).toContain("<p>Text.</p>");
  });

  it("sorts stories from newest to oldest", () => {
    const older = story(file({ date: "2026-10-13", slug: "old" }), file({ date: "2026-10-13", slug: "eski" }), "2026-10-13-old");
    const keys = buildStories({ ...older, ...story() }).map((item) => item.key);
    expect(keys).toEqual([FOLDER, "2026-10-13-old"]);
  });

  it("drops raw HTML from the body", () => {
    const [result] = buildStories(story(file({}, 'Safe.\n\n<script>alert(1)</script>\n')));
    expect(result.versions.en.html).not.toContain("<script");
    expect(result.versions.en.html).toContain("Safe.");
  });

  it("gives second level headings stable ids", () => {
    const [result] = buildStories(story(file({}, "Intro.\n\n## First part\n\nText.\n")));
    expect(result.versions.en.html).toContain('<h2 id="section-1">First part</h2>');
    expect(result.versions.en.headings).toEqual([{ id: "section-1", text: "First part" }]);
  });

  it("rejects a story with one language", () => {
    const { [`./content/stories/${FOLDER}/en.md`]: only } = story();
    expect(() => buildStories({ [`./content/stories/${FOLDER}/en.md`]: only })).toThrow("both en.md and tr.md");
  });

  it("rejects a story with no sources", () => {
    expect(() => buildStories(story(file({ sources: "[]" })))).toThrow("missing sources");
  });

  it("rejects a source without a web address", () => {
    const sources = "\n  - name: Bad\n    url: javascript:alert(1)";
    expect(() => buildStories(story(file({ sources })))).toThrow("invalid source address");
  });

  it("rejects an unknown category", () => {
    expect(() => buildStories(story(file({ category: "politics" })))).toThrow("unknown category");
  });

  it("rejects languages that disagree on the category", () => {
    const tr = file({ slug: "ornek-haber", category: "sports" });
    expect(() => buildStories(story(file(), tr))).toThrow("category differs");
  });

  it("reads an optional updated date and checks it", () => {
    expect(buildStories(story())[0].updated).toBeUndefined();
    const withDate = (updated: string, trUpdated = updated) => story(file({ updated }), file({ slug: "ornek-haber", updated: trUpdated }));
    expect(buildStories(withDate("2026-10-25"))[0].updated).toBe("2026-10-25");
    expect(() => buildStories(withDate("2026-10-19"))).toThrow("before the story date");
    expect(() => buildStories(withDate("soon"))).toThrow("invalid updated date");
    expect(() => buildStories(withDate("2026-10-25", "2026-10-26"))).toThrow("differs between languages");
  });

  it("rejects a date that does not match the folder", () => {
    expect(() => buildStories(story(file({ date: "2026-10-21" })))).toThrow("date does not match");
  });

  it("rejects an image without a license", () => {
    const image = "\n  file: photo.jpg\n  alt: Alt\n  credit: Someone\n  source: https://example.com/p";
    expect(() => buildStories(story(file({ image })))).toThrow("missing license");
  });

  it("rejects a story with no image", () => {
    expect(() => buildStories(story(file({ image: "null" })))).toThrow("missing image");
  });

  it("rejects two stories with the same slug", () => {
    const second = story(undefined, file({ slug: "ikinci" }), "2026-10-20-second");
    expect(() => buildStories({ ...story(), ...second })).toThrow("duplicate en slug");
  });
});
