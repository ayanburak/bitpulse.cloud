/**
 * file: tests/feed.test.ts
 * importable: nothing, the test runner loads this file
 *
 * description: Checks the RSS feed, the sitemap entries and the text placed inside structured data.
 */

import { describe, expect, it } from "vitest";
import { correctedStories, counterpart, frontStories, listPagePaths, longStories, modifiedTime, newsEntries, sitemapEntries, stories, storyPath } from "../src/catalog";
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
    expect(renderFeed("en", [stories[0]])).toContain(`<pubDate>${new Date(stories[0].published).toUTCString()}</pubDate>`);
  });
});

describe("jsonForScript", () => {
  it("can not close the script tag it sits in", () => {
    expect(jsonForScript({ headline: "</script><b>" })).not.toContain("<");
  });
});

describe("listPagePaths", () => {
  it("builds the explainer list only when an explainer exists", () => {
    expect(listPagePaths().includes("/tr/explained/")).toBe(longStories().length > 0);
  });
});

describe("policy pages", () => {
  it("builds the editorial policy and corrections pages in both languages", () => {
    const paths = listPagePaths();
    for (const lang of ["en", "tr"]) {
      expect(paths).toContain(`/${lang}/editorial-policy/`);
      expect(paths).toContain(`/${lang}/corrections/`);
    }
  });

  it("lists only corrected stories, newest correction first", () => {
    const corrected = correctedStories();
    expect(corrected.every((story) => story.corrected !== undefined)).toBe(true);
    expect(corrected.map((story) => story.corrected)).toEqual([...corrected.map((story) => story.corrected)].sort().reverse());
    expect(corrected.length).toBe(stories.filter((story) => story.corrected).length);
  });

  it("links the pages with their counterparts and puts them in the sitemap", () => {
    expect(counterpart("/tr/corrections/")).toBe("/en/corrections/");
    expect(sitemapEntries().some((entry) => entry.path === "/tr/editorial-policy/")).toBe(true);
  });
});

describe("newsEntries", () => {
  const newest = stories.find((story) => story.kind === "news")!;
  const moment = Date.parse(newest.published);

  it("lists a recent news story in both languages", () => {
    expect(newsEntries(moment + 1000).filter((entry) => entry.published === newest.published).map((entry) => entry.lang).sort()).toEqual(["en", "tr"]);
  });

  it("leaves out a story older than two days", () => {
    expect(newsEntries(moment + 3 * 24 * 60 * 60 * 1000).some((entry) => entry.published === newest.published)).toBe(false);
  });
});

describe("sitemapEntries", () => {
  const entries = sitemapEntries();

  it("dates story pages with their latest change", () => {
    const story = stories[0];
    expect(modifiedTime({ ...story, corrected: undefined })).toBe(story.published);
    expect(modifiedTime({ ...story, corrected: "2099-01-01T00:00:00Z" })).toBe("2099-01-01T00:00:00Z");
    const update = { time: "2099-02-01T00:00:00Z", note: "Note", promote: false };
    const updated = { ...story, versions: { ...story.versions, en: { ...story.versions.en, updates: [update] } } };
    expect(modifiedTime(updated)).toBe("2099-02-01T00:00:00Z");
    expect(entries.find((entry) => entry.path === storyPath(story, "en"))?.lastmod).toBe(modifiedTime(story));
  });

  it("puts promoted stories first on the home page and keeps the rest in publishing order", () => {
    const rank = (story: (typeof stories)[number]) => story.promoted ?? story.published;
    expect(frontStories.map(rank)).toEqual([...frontStories.map(rank)].sort().reverse());
    expect(frontStories.length).toBe(stories.length);
  });

  it("gives no other page a date and leaves out search and error pages", () => {
    expect(entries.find((entry) => entry.path === "/en/about/")?.lastmod).toBeUndefined();
    expect(entries.some((entry) => entry.path.endsWith("/search/") || entry.path.endsWith("404.html"))).toBe(false);
  });

  it("leaves out the root address, which only redirects", () => {
    expect(entries.some((entry) => entry.path === "/")).toBe(false);
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
