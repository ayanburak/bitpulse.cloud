/**
 * file: src/catalog.ts
 * importable: stories, findStory, storyPath, storiesIn, longStories, monthKeys, storiesInMonth,
 *             counterpart, listPagePaths, imageUrl, imageSet, Category
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
    `/${lang}/search/`,
    `/${lang}/about/`,
    `/${lang}/contact/`,
    `/${lang}/privacy/`,
    `/${lang}/404.html`,
    ...categories.map((category) => `/${lang}/category/${category}/`),
    ...monthKeys().map((month) => `/${lang}/archive/${month.replace("-", "/")}/`),
    ...stories.map((story) => storyPath(story, lang)),
  ]);
  return ["/", "/404.html", ...shared];
}

// --- Images ---

export function imageUrl(story: Story, width: number): string {
  return `/media/${story.key}-${width}.jpg`;
}

export function imageSet(story: Story): string {
  return IMAGE_WIDTHS.map((width) => `${imageUrl(story, width)} ${width}w`).join(", ");
}
