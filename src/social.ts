/**
 * file: src/social.ts
 * importable: buildSocial, SocialPost, SITE
 *
 * A news story can carry a social.yaml file next to en.md. It holds the English text for the
 * social accounts: one X post, one or more Instagram pages and an Instagram caption. Every page
 * has its own image, given as an address and a credit. Agents write the text and choose the
 * images. The link, the credit line and the disclosure are added here, so they are the same on
 * every post and can not be forgotten.
 *
 * description: Validates the social text of a story and completes it into ready to share posts.
 */

// NOTE: The site never reads social.yaml. The story loader only picks up en.md and tr.md, so a
// mistake in this file can not break a page. scripts/social.ts and tests/social.test.ts use it.
//
// NOTE: Social images are not stored in the repository, only their addresses. Many of them are
// press or news photos that may be shared on a social account but not republished under the
// licenses of this repository. scripts/social.ts downloads them outside of git.

import { parse as parseYaml } from "yaml";
import type { Story } from "./stories";

// --- Types ---

export interface SocialPage {
  image: string;
  credit: string;
  paragraphs: string[];
}

export interface SocialPost {
  x: string;
  pages: SocialPage[];
  caption: string;
}

// --- Constants ---

export const SITE = "https://bitpulse.cloud";

// X counts every link as 23 characters, whatever its real length.
const X_LIMIT = 280;
const X_LINK_LENGTH = 23;
const MAX_PARAGRAPHS = 2;

// About eight lines on a page. Longer text climbs over the photo, so it goes on another page.
const PAGE_LIMIT = 300;

// Instagram allows twenty pages in one post and cuts captions at 2,200 characters.
const MAX_PAGES = 20;
const CAPTION_LIMIT = 2200;
const FIELDS = ["x", "pages", "caption"];
const PAGE_FIELDS = ["image", "credit", "text"];

// The site says the same thing under every article, the caption keeps that wording close.
const DISCLOSURE = "Written by artificial intelligence. Every claim is sourced in the full story.";

// --- Helpers ---

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function text(value: unknown, field: string, where: string): string {
  if (typeof value !== "string" || !value.trim()) throw new Error(`${where}: missing ${field}`);
  return value.trim();
}

function httpUrl(value: unknown, field: string, where: string): string {
  const url = text(value, field, where);
  if (!URL.canParse(url) || !/^https?:$/.test(new URL(url).protocol)) throw new Error(`${where}: invalid ${field} address: ${url}`);
  return url;
}

// The text of a page is written as one block, with an empty line between its paragraphs.
function readPages(value: unknown, where: string): SocialPage[] {
  if (!Array.isArray(value) || value.length === 0) throw new Error(`${where}: missing pages`);
  if (value.length > MAX_PAGES) throw new Error(`${where}: more than ${MAX_PAGES} pages`);
  return value.map((page, index) => {
    const at = `${where}: page ${index + 1}`;
    if (!isRecord(page)) throw new Error(`${at}: invalid page`);
    const unknown = Object.keys(page).find((field) => !PAGE_FIELDS.includes(field));
    if (unknown) throw new Error(`${at}: unknown field: ${unknown}`);
    const paragraphs = text(page.text, "text", at).split(/\n\s*\n/).map((part) => part.replace(/\s+/g, " ").trim());
    if (paragraphs.length > MAX_PARAGRAPHS) throw new Error(`${at}: more than ${MAX_PARAGRAPHS} paragraphs`);
    const length = paragraphs.join(" ").length;
    if (length > PAGE_LIMIT) throw new Error(`${at}: text is ${length} characters, the limit is ${PAGE_LIMIT}`);
    return { image: httpUrl(page.image, "image", at), credit: text(page.credit, "credit", at), paragraphs };
  });
}

// Pages that share an image or a photographer name them once.
function credits(pages: SocialPage[]): string {
  const names = [...new Set(pages.map((page) => page.credit))];
  return `${names.length > 1 ? "Images" : "Image"}: ${names.join(" · ")}.`;
}

// --- Building ---

/**
 * Validates the social text of a news story and adds the parts that come from the story.
 *
 * @param raw Contents of the story's social.yaml.
 * @param story The story the file belongs to.
 * @returns The X post with its link, the Instagram pages and the full caption.
 * @throws Error if a field is missing or unknown, an address is invalid, or the X post, a page
 *   or the caption is over its limit.
 */
export function buildSocial(raw: string, story: Story): SocialPost {
  const where = `${story.key}/social.yaml`;
  if (story.kind !== "news") throw new Error(`${where}: only news stories are shared`);
  const data: unknown = parseYaml(raw);
  if (!isRecord(data)) throw new Error(`${where}: invalid file`);
  const unknown = Object.keys(data).find((field) => !FIELDS.includes(field));
  if (unknown) throw new Error(`${where}: unknown field: ${unknown}`);

  const link = `${SITE}/en/stories/${story.versions.en.slug}/`;
  const x = text(data.x, "x", where);
  const length = x.length + 2 + X_LINK_LENGTH;
  if (length > X_LIMIT) throw new Error(`${where}: X post is ${length} characters with the link, the limit is ${X_LIMIT}`);

  const pages = readPages(data.pages, where);
  const caption = [text(data.caption, "caption", where), "Full story and sources: link in bio.", `${credits(pages)} ${DISCLOSURE}`];
  const full = caption.join("\n\n");
  if (full.length > CAPTION_LIMIT) throw new Error(`${where}: caption is ${full.length} characters, the limit is ${CAPTION_LIMIT}`);
  return { x: `${x}\n\n${link}`, pages, caption: full };
}
