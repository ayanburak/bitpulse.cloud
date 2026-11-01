/**
 * file: tests/feed.test.ts
 * importable: nothing, the test runner loads this file
 *
 * description: Checks the RSS feed, the sitemap entries and the text placed inside structured data.
 */

import { describe, expect, it } from "vitest";
import { modifiedDate, sitemapEntries, stories, storyPath } from "../src/catalog";
import { jsonForScript } from "../src/components/Layout";
import { escapeXml, renderFeed } from "../src/feed";

// --- Tests ---

describe("renderFeed", () => {
  it("escapes characters that would break the XML", () => {
    expect(escapeXml(`Q&A <"now">`)).toBe("Q&amp;A &lt;&quot;now&quot;&gt;");
  });

  it("lists stories from the requested language", () => {
    const feed = renderFeed("tr");
    expect(feed).toContain("<language>tr</language>");
    expect(feed).toContain(`/tr/stories/${stories[0].versions.tr.slug}/`);
    expect(feed).not.toContain("/en/stories/");
  });

  it("keeps at most twenty stories", () => {
    const many = Array.from({ length: 25 }, () => stories[0]);
    expect(renderFeed("en", many).match(/<item>/g)).toHaveLength(20);
  });

  it("dates items in the RSS format", () => {
    expect(renderFeed("en", [stories[0]])).toMatch(/<pubDate>\w{3}, \d{2} \w{3} \d{4} 00:00:00 GMT<\/pubDate>/);
  });
});

describe("jsonForScript", () => {
  it("can not close the script tag it sits in", () => {
    expect(jsonForScript({ headline: "</script><b>" })).not.toContain("<");
  });
});

describe("sitemapEntries", () => {
  const entries = sitemapEntries();

  it("dates story pages with the updated date or else the story date", () => {
    const story = stories[0];
    expect(modifiedDate(story)).toBe(story.updated ?? story.date);
    expect(modifiedDate({ ...story, updated: "2099-01-01" })).toBe("2099-01-01");
    expect(entries.find((entry) => entry.path === storyPath(story, "en"))?.lastmod).toBe(modifiedDate(story));
  });

  it("gives no other page a date and leaves out search and error pages", () => {
    expect(entries.find((entry) => entry.path === "/en/about/")?.lastmod).toBeUndefined();
    expect(entries.some((entry) => entry.path.endsWith("/search/") || entry.path.endsWith("404.html"))).toBe(false);
  });

  it("links each story to its counterpart in the other language", () => {
    const story = stories[0];
    const entry = entries.find((item) => item.path === storyPath(story, "tr"));
    expect(entry?.alternates).toEqual([
      { hreflang: "tr", path: storyPath(story, "tr") },
      { hreflang: "en", path: storyPath(story, "en") },
      { hreflang: "x-default", path: storyPath(story, "en") },
    ]);
  });
});
