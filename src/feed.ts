/**
 * file: src/feed.ts
 * importable: renderFeed, escapeXml
 *
 * description: Writes the RSS feed of one language.
 */

import { feedPath, stories, storyPath } from "./catalog";
import { SITE_URL } from "./config";
import { ui, type Lang } from "./i18n";
import type { Story } from "./stories";

// --- Constants ---

const FEED_SIZE = 20;

// --- Helpers ---

export function escapeXml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// Stories record a date and no time, so every item is dated midnight UTC of that day.
function pubDate(story: Story): string {
  return new Date(`${story.date}T00:00:00Z`).toUTCString();
}

function item(story: Story, lang: Lang): string {
  const version = story.versions[lang];
  const link = `${SITE_URL}${storyPath(story, lang)}`;
  return [
    "<item>",
    `<title>${escapeXml(version.title)}</title>`,
    `<link>${link}</link>`,
    `<guid isPermaLink="true">${link}</guid>`,
    `<pubDate>${pubDate(story)}</pubDate>`,
    `<description>${escapeXml(version.summary)}</description>`,
    "</item>",
  ].join("");
}

// --- Feed ---

/**
 * Builds a complete RSS 2.0 document.
 *
 * @param lang Language of the feed.
 * @param list Stories from newest to oldest.
 * @returns The feed as text, with the newest stories only.
 */
export function renderFeed(lang: Lang, list: Story[] = stories): string {
  const home = `${SITE_URL}/${lang}/`;
  const self = `${SITE_URL}${feedPath(lang)}`;
  const items = list.slice(0, FEED_SIZE).map((story) => item(story, lang)).join("");
  return [
    '<?xml version="1.0" encoding="UTF-8"?>\n',
    '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>',
    "<title>Bitpulse</title>",
    `<link>${home}</link>`,
    `<description>${escapeXml(ui[lang].metaDescription)}</description>`,
    `<language>${lang}</language>`,
    `<atom:link href="${self}" rel="self" type="application/rss+xml"/>`,
    items,
    "</channel></rss>\n",
  ].join("");
}
