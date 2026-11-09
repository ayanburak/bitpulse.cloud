/**
 * file: src/social.ts
 * importable: buildSocial, SocialPost, SITE
 *
 * A news story can carry a social.yaml file next to en.md. It holds the English text for the
 * social accounts: one X post, one or more Instagram pages and an Instagram caption. Every page
 * has its own image, given as an address, a credit and, when the subject is off center, a position. The text and the images are chosen
 * by hand. The link, the credit line and the source note are added here, so they are the same on
 * every post and can not be forgotten.
 *
 * From 8 November 2026 a post has exactly one page. Older posts keep the pages they were shared
 * with.
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
  position: string;
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

// From 2026-11-07 a page carries one short sentence and the caption carries the rest, because a
// page is looked at for a moment while scrolling. Older posts keep the old limits, since posts
// that were already shared are not rewritten.
const SHORT_PAGES_SINCE = "2026-11-07";
const SHORT_PAGE_LIMIT = 120;

// Instagram allows twenty pages in one post and cuts captions at 2,200 characters.
const MAX_PAGES = 20;
const CAPTION_LIMIT = 2200;
const FIELDS = ["x", "pages", "caption"];
const PAGE_FIELDS = ["image", "credit", "position", "text"];

// The page shows a wide photo cut to the shape of its upper part. When the subject sits near an
// edge, a position such as 85% 50% moves the cut there, the first number across, the second down.
const CENTER = "50% 50%";
const POSITION = /^(\d{1,3})% (\d{1,3})%$/;

// From 2026-11-08 the post is one page, also turned into a still video, and the caption carries
// everything else, so the post only has to stop a reader.
const ONE_PAGE_SINCE = "2026-11-08";

// From 2026-11-10 what Instagram shows is plain sentences: no dashes and no formatting. A dash stays
// only inside a name, because a name can not be rewritten: Jean-Noël, Al-Asbahi, F-35.
const PLAIN_SINCE = "2026-11-10";
const NAME_WITH_DASH = /\p{Lu}\p{L}*-(?:\p{Lu}\p{L}*|\d+)|\bal-\p{Lu}\p{L}*/gu;
const DASH = /[-‐-―]/u;
const FORMATTING = /[*_#`~]|\p{Extended_Pictographic}/u;

// Points readers to the full story, where every claim is linked to its source.
const SOURCE_NOTE = "Every claim is sourced in the full story.";

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

// A page without a position keeps the centered cut every older post was made with.
function readPosition(value: unknown, where: string): string {
  if (value === undefined) return CENTER;
  const match = typeof value === "string" ? POSITION.exec(value.trim()) : null;
  if (!match || Number(match[1]) > 100 || Number(match[2]) > 100) throw new Error(`${where}: invalid position, write two percents such as 85% 50%: ${value}`);
  return match[0];
}

// The text of a page is written as one block, with an empty line between its paragraphs.
function readPages(value: unknown, where: string, short: boolean, most: number): SocialPage[] {
  if (!Array.isArray(value) || value.length === 0) throw new Error(`${where}: missing pages`);
  if (value.length > most) throw new Error(`${where}: more than ${most} page${most > 1 ? "s" : ""}`);
  return value.map((page, index) => {
    const at = `${where}: page ${index + 1}`;
    if (!isRecord(page)) throw new Error(`${at}: invalid page`);
    const unknown = Object.keys(page).find((field) => !PAGE_FIELDS.includes(field));
    if (unknown) throw new Error(`${at}: unknown field: ${unknown}`);
    const paragraphs = text(page.text, "text", at).split(/\n\s*\n/).map((part) => part.replace(/\s+/g, " ").trim());
    const parts = short ? 1 : MAX_PARAGRAPHS;
    if (paragraphs.length > parts) throw new Error(`${at}: more than ${parts} paragraph${parts > 1 ? "s" : ""}`);
    const length = paragraphs.join(" ").length;
    const limit = short ? SHORT_PAGE_LIMIT : PAGE_LIMIT;
    if (length > limit) throw new Error(`${at}: text is ${length} characters, the limit is ${limit}`);
    return { image: httpUrl(page.image, "image", at), credit: text(page.credit, "credit", at), position: readPosition(page.position, at), paragraphs };
  });
}

function requirePlain(value: string, field: string, where: string): void {
  if (DASH.test(value.replace(NAME_WITH_DASH, ""))) throw new Error(`${where}: ${field} has a dash, write the sentence without one: ${value}`);
  if (FORMATTING.test(value)) throw new Error(`${where}: ${field} has formatting or an emoji, write plain text: ${value}`);
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
 * @throws Error if a field is missing or unknown, an address is invalid, the post has more pages
 *   than its date allows, the X post, a page or the caption is over its limit, or the Instagram
 *   text of a newer post is not plain.
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

  const day = story.key.slice(0, 10);
  const pages = readPages(data.pages, where, day >= SHORT_PAGES_SINCE, day >= ONE_PAGE_SINCE ? 1 : MAX_PAGES);
  if (day >= PLAIN_SINCE) {
    pages.forEach((page, index) => requirePlain(page.paragraphs.join(" "), `page ${index + 1}`, where));
    requirePlain(text(data.caption, "caption", where), "caption", where);
  }
  const caption = [text(data.caption, "caption", where), "Full story and sources: link in bio.", `${credits(pages)} ${SOURCE_NOTE}`];
  const full = caption.join("\n\n");
  if (full.length > CAPTION_LIMIT) throw new Error(`${where}: caption is ${full.length} characters, the limit is ${CAPTION_LIMIT}`);
  return { x: `${x}\n\n${link}`, pages, caption: full };
}
