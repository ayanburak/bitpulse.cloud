/**
 * file: src/stories.ts
 * importable: buildStories, loadStories, categories, kinds, Story, StoryVersion, Source, StoryImage, Heading
 *
 * Every story lives in its own folder under src/content/stories, named with the date and a
 * short key, and holds one en.md and one tr.md file. loadStories reads all of them.
 * buildStories does the real work and takes plain file contents, which keeps it testable.
 * Any invalid story stops the build, so a broken article can never reach the live site.
 *
 * description: Reads, validates and pairs the two language versions of every story.
 */

// NOTE: Raw HTML inside Markdown is dropped on purpose. Article text comes from automated runs
// and from web research, so it should not be able to put a script or an iframe on a page.

import { Marked } from "marked";
import { parse as parseYaml } from "yaml";
import type { Lang } from "./i18n";

// --- Types ---

export const categories = ["world", "economy", "technology", "science", "health", "culture", "sports"] as const;
export const kinds = ["news", "long"] as const;

type Category = (typeof categories)[number];
type Kind = (typeof kinds)[number];

export interface Source {
  name: string;
  url: string;
}

export interface StoryImage {
  file: string;
  alt: string;
  credit: string;
  license: string;
  licenseUrl: string;
  source: string;
}

export interface Heading {
  id: string;
  text: string;
}

export interface StoryVersion {
  slug: string;
  title: string;
  summary: string;
  html: string;
  headings: Heading[];
  minutes: number;
  sources: Source[];
  image: StoryImage;
}

export interface Story {
  key: string;
  date: string;
  updated?: string;
  category: Category;
  kind: Kind;
  versions: Record<Lang, StoryVersion>;
}

// --- Constants ---

const LANGS: Lang[] = ["en", "tr"];
const FRONTMATTER = /^---\n([\s\S]*?)\n---\n([\s\S]*)$/;
const DATE = /^\d{4}-\d{2}-\d{2}$/;
const FOLDER = /^(\d{4}-\d{2}-\d{2})-[a-z0-9-]+$/;
const FILE_PATH = /([^/]+)\/(en|tr)\.md$/;
const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const WORDS_PER_MINUTE = 200;

const markdown = new Marked({ renderer: { html: () => "" } });

// --- Validation ---

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

// Throws instead of returning a default, an empty title on a live page is worse than a failed build.
function text(data: Record<string, unknown>, field: string, where: string): string {
  const value = data[field];
  if (typeof value !== "string" || !value.trim()) throw new Error(`${where}: missing ${field}`);
  return value.trim();
}

function httpUrl(value: string, field: string, where: string): string {
  if (!URL.canParse(value) || !/^https?:$/.test(new URL(value).protocol)) {
    throw new Error(`${where}: invalid ${field} address: ${value}`);
  }
  return value;
}

function oneOf<T extends string>(allowed: readonly T[], value: string, field: string, where: string): T {
  const match = allowed.find((item) => item === value);
  if (!match) throw new Error(`${where}: unknown ${field}: ${value}`);
  return match;
}

// The editorial policy requires sources on every story, so an empty list is an error.
function readSources(data: Record<string, unknown>, where: string): Source[] {
  const list = data.sources;
  if (!Array.isArray(list) || list.length === 0) throw new Error(`${where}: missing sources`);
  return list.map((item) => {
    if (!isRecord(item)) throw new Error(`${where}: invalid source`);
    return { name: text(item, "name", where), url: httpUrl(text(item, "url", where), "source", where) };
  });
}

// Every story needs an image, and an image without its credit and license is never allowed.
function readImage(data: Record<string, unknown>, where: string): StoryImage {
  if (!isRecord(data.image)) throw new Error(`${where}: missing image`);
  const image = data.image;
  return {
    file: text(image, "file", where),
    alt: text(image, "alt", where),
    credit: text(image, "credit", where),
    license: text(image, "license", where),
    licenseUrl: httpUrl(text(image, "licenseUrl", where), "license", where),
    source: httpUrl(text(image, "source", where), "image source", where),
  };
}

// --- Parsing ---

// Section links need stable addresses, so each second level heading gets a numbered id.
function linkHeadings(html: string): { html: string; headings: Heading[] } {
  const headings: Heading[] = [];
  const linked = html.replace(/<h2>(.*?)<\/h2>/g, (_, inner: string) => {
    const id = `section-${headings.length + 1}`;
    headings.push({ id, text: inner.replace(/<[^>]+>/g, "") });
    return `<h2 id="${id}">${inner}</h2>`;
  });
  return { html: linked, headings };
}

function readingMinutes(html: string): number {
  const words = html.replace(/<[^>]+>/g, " ").trim().split(/\s+/).length;
  return Math.max(1, Math.round(words / WORDS_PER_MINUTE));
}

interface ParsedFile {
  version: StoryVersion;
  date: string;
  updated?: string;
  category: Category;
  kind: Kind;
}

// A dated correction sets this. It stays a plain date because stories have no publishing time.
function readUpdated(data: Record<string, unknown>, where: string): string | undefined {
  if (data.updated === undefined) return undefined;
  const value = String(data.updated).trim();
  if (!DATE.test(value)) throw new Error(`${where}: invalid updated date: ${value}`);
  return value;
}

function parseFile(raw: string, where: string): ParsedFile {
  const parts = FRONTMATTER.exec(raw.replace(/\r\n/g, "\n"));
  if (!parts) throw new Error(`${where}: missing frontmatter`);
  const data: unknown = parseYaml(parts[1]);
  if (!isRecord(data)) throw new Error(`${where}: invalid frontmatter`);

  const slug = text(data, "slug", where);
  if (!SLUG.test(slug)) throw new Error(`${where}: invalid slug: ${slug}`);

  const parsed = markdown.parse(parts[2], { async: false });
  if (!parsed.trim()) throw new Error(`${where}: empty body`);
  const { html, headings } = linkHeadings(parsed);

  return {
    date: text(data, "date", where),
    updated: readUpdated(data, where),
    category: oneOf(categories, text(data, "category", where), "category", where),
    kind: oneOf(kinds, text(data, "kind", where), "kind", where),
    version: {
      slug,
      title: text(data, "title", where),
      summary: text(data, "summary", where),
      html,
      headings,
      minutes: readingMinutes(html),
      sources: readSources(data, where),
      image: readImage(data, where),
    },
  };
}

// --- Pairing ---

// Facts shared by both languages must match, otherwise one reader sees a different story.
function pair(key: string, en: ParsedFile, tr: ParsedFile): Story {
  const date = FOLDER.exec(key)?.[1];
  if (!date) throw new Error(`${key}: invalid folder name`);
  if (en.date !== date || tr.date !== date) throw new Error(`${key}: date does not match the folder`);
  if (en.category !== tr.category) throw new Error(`${key}: category differs between languages`);
  if (en.kind !== tr.kind) throw new Error(`${key}: kind differs between languages`);
  if (en.updated !== tr.updated) throw new Error(`${key}: updated date differs between languages`);
  if (en.updated && en.updated < date) throw new Error(`${key}: updated date is before the story date`);
  return { key, date, updated: en.updated, category: en.category, kind: en.kind, versions: { en: en.version, tr: tr.version } };
}

// A shared slug would make two stories fight over one address.
function assertUniqueSlugs(stories: Story[]): void {
  for (const lang of LANGS) {
    const seen = new Set<string>();
    for (const story of stories) {
      const { slug } = story.versions[lang];
      if (seen.has(slug)) throw new Error(`${story.key}: duplicate ${lang} slug: ${slug}`);
      seen.add(slug);
    }
  }
}

/**
 * Validates story files and pairs their language versions.
 *
 * @param files File contents keyed by a path ending in folder/en.md or folder/tr.md.
 * @returns Stories sorted from newest to oldest.
 * @throws Error if any story is invalid or misses a language.
 */
export function buildStories(files: Record<string, string>): Story[] {
  const folders = new Map<string, Partial<Record<Lang, ParsedFile>>>();
  for (const [path, raw] of Object.entries(files)) {
    const match = FILE_PATH.exec(path);
    if (!match) throw new Error(`${path}: unexpected file name`);
    const key = match[1];
    const lang = oneOf(LANGS, match[2], "language", path);
    folders.set(key, { ...folders.get(key), [lang]: parseFile(raw, `${key}/${lang}.md`) });
  }

  const stories = [...folders].map(([key, { en, tr }]) => {
    if (!en || !tr) throw new Error(`${key}: both en.md and tr.md are required`);
    return pair(key, en, tr);
  });

  assertUniqueSlugs(stories);
  return stories.sort((a, b) => b.date.localeCompare(a.date) || a.key.localeCompare(b.key));
}

/**
 * Reads every story in the repository.
 *
 * @returns Stories sorted from newest to oldest.
 * @throws Error if any story is invalid or misses a language.
 */
export function loadStories(): Story[] {
  return buildStories(
    import.meta.glob<string>("./content/stories/*/*.md", { query: "?raw", import: "default", eager: true }),
  );
}
