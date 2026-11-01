/**
 * file: tests/feed.test.ts
 * importable: nothing, the test runner loads this file
 *
 * description: Checks the RSS feed and the text placed inside structured data.
 */

import { describe, expect, it } from "vitest";
import { stories } from "../src/catalog";
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
