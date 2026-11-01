/**
 * file: src/catalog.ts
 * importable: stories, findStory, storyPath, storiesIn, correctedStories, longStories, newsStories, monthKeys, storiesInMonth,
 *             counterpart, listPagePaths, sitemapEntries, modifiedDate, imageUrl, imageSet, feedPath, Category
 *
 * description: Answers page questions about published stories and site addresses.
 */

import { IMAGE_WIDTHS } from "./config";
import { langs, otherLang, type Lang } from "./i18n";
import { categories, loadStories, type Story } from "./stories";

export type Category = (typeof categories)[number];

export const stories = loadStories();

// --- Stories ---

export function findStory(lang: Lang, slug: string | undefined): Story | undefined {
  return stories.find((story) => story.versions[lang].slug === slug);
}

export function storyPath(story: Story, lang: Lang): string {
  return `/${lang}/stories/${story.versions[lang].slug}/`;
}

export function storiesIn(category: Category): Story[] {
  return stories.filter((story) => story.category === category);
}

export function longStories(): Story[] {
  return stories.filter((story) => story.kind === "long");
}

export function newsStories(): Story[] {
  return stories.filter((story) => story.kind === "news");
}

// Only stories with a dated correction are listed, the most recently corrected first.
export function correctedStories(): Story[] {
  return stories
    .filter((story) => story.updated !== undefined)
    .sort((a, b) => (b.updated as string).localeCompare(a.updated as string));
}

// --- Months ---

// Month keys have the form 2026-10 and stay sorted from newest to oldest like the stories.
export function monthKeys(): string[] {
  return [...new Set(stories.map((story) => story.date.slice(0, 7)))];
}

export function storiesInMonth(month: string): Story[] {
  return stories.filter((story) => story.date.startsWith(month));
}

// --- Addresses ---

/**
 * Finds the same page in the other language.
 *
 * @param path Address of the current page.
 * @returns Address of its counterpart. Story slugs differ per language, so stories are looked up.
 */
export function counterpart(path: string): string {
  const parts = /^\/(en|tr)\/stories\/([^/]+)\/$/.exec(path);
  if (parts) {
    const lang = parts[1] as Lang;
    const story = findStory(lang, parts[2]);
    if (story) return storyPath(story, otherLang(lang));
  }
  if (path.startsWith("/tr/")) return `/en/${path.slice(4)}`;
  if (path.startsWith("/en/")) return `/tr/${path.slice(4)}`;
  return `/tr${path}`;
}

/**
 * Lists every page the build has to write.
 *
 * @returns Addresses of all pages in both languages.
 */
export function listPagePaths(): string[] {
  const shared = langs.flatMap((lang) => [
    `/${lang}/`,
    `/${lang}/archive/`,
    ...(longStories().length > 0 ? [`/${lang}/explained/`] : []),
    `/${lang}/search/`,
    `/${lang}/about/`,
    `/${lang}/contact/`,
    `/${lang}/privacy/`,
    `/${lang}/editorial-policy/`,
    `/${lang}/corrections/`,
    `/${lang}/404.html`,
    ...categories.map((category) => `/${lang}/category/${category}/`),
    ...monthKeys().map((month) => `/${lang}/archive/${month.replace("-", "/")}/`),
    ...stories.map((story) => storyPath(story, lang)),
  ]);
  return ["/", "/404.html", ...shared];
}

export interface SitemapEntry {
  path: string;
  lastmod?: string;
  alternates: { hreflang: string; path: string }[];
}

// Stories have no publishing time, so the correction date or else the story date is all there is.
export function modifiedDate(story: Story): string {
  return story.updated ?? story.date;
}

/**
 * Lists the sitemap entries with the same language links the page head uses.
 *
 * @returns One entry per page worth indexing. The root is left out because it only redirects.
 * Only story pages carry a lastmod date.
 */
export function sitemapEntries(): SitemapEntry[] {
  const dates = new Map(stories.flatMap((story) => langs.map((lang) => [storyPath(story, lang), modifiedDate(story)] as const)));
  return listPagePaths()
    .filter((path) => path !== "/" && !path.endsWith("404.html") && !path.endsWith("/search/"))
    .map((path) => {
      const lang: Lang = path.startsWith("/tr/") ? "tr" : "en";
      const isHome = path === `/${lang}/`;
      const alternates = [
        { hreflang: lang, path },
        { hreflang: otherLang(lang), path: counterpart(path) },
        { hreflang: "x-default", path: isHome ? "/" : lang === "en" ? path : counterpart(path) },
      ];
      return { path, lastmod: dates.get(path), alternates };
    });
}

export function feedPath(lang: Lang): string {
  return `/${lang}/feed.xml`;
}

// --- Images ---

export function imageUrl(story: Story, width: number): string {
  return `/media/${story.key}-${width}.jpg`;
}

export function imageSet(story: Story): string {
  return IMAGE_WIDTHS.map((width) => `${imageUrl(story, width)} ${width}w`).join(", ");
}
