/**
 * file: scripts/social.ts
 * importable: nothing, run with npm run social
 *
 * Turns the social.yaml of a news story into files that are ready to share, in
 * social-posts/<story folder>. Without arguments it takes the newest news story, story folder
 * names as arguments pick other stories:
 *
 *   npm run social
 *   npm run social -- 2026-11-04-hera-dimorphos
 *
 * Each page image is downloaded from the address in social.yaml into the images folder of the
 * output. The Instagram pages are drawn by a real browser from scripts/social-card.html.
 * CHROME_PATH points to an installed browser when the one Playwright expects is not downloaded.
 *
 * The first page is also saved as post.mp4, a silent vertical video that shows the page without
 * any movement, so it can be shared on Instagram as a reel. This part needs ffmpeg on the machine.
 *
 * description: Writes the X post, the Instagram caption, the Instagram pages and the still video of a story.
 */

// NOTE: The output folder is in .gitignore. The page images may be press or news photos that can
// be shared on a social account but must not be republished in this repository.
//
// NOTE: Drawing a page and making the still video live in scripts/social-render.ts, because clips
// use them too.

import { copyFileSync, existsSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { setDefaultAutoSelectFamilyAttemptTimeout } from "node:net";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import type { Page } from "@playwright/test";
import { buildSocial, type SocialPost } from "../src/social.ts";
import { buildStories, type Story } from "../src/stories.ts";
import { replacePost } from "./social-output.ts";
import { drawPage, makeStill, openBrowser } from "./social-render.ts";

// --- Constants ---

const ROOT = process.env.BITPULSE_STORIES ?? "src/content/stories";
const OUT = "social-posts";

// Wikimedia and several press sites refuse requests that do not name the client.
const HEADERS = { "User-Agent": "BitpulseSocial/1.0 (+https://bitpulse.cloud)" };

// Node gives an address a quarter of a second before it tries the next one. On a slow connection
// the only reachable address runs out of time and the download fails.
setDefaultAutoSelectFamilyAttemptTimeout(2_000);
const ATTEMPTS = 3;
const ATTEMPT_MS = 30_000;
const RETRY_MS = 2_000;

// Which address each saved image came from, so a later run can reuse exactly that image.
const SOURCES = "sources.json";

// --- Reading ---

function readStories(): Story[] {
  const files: Record<string, string> = {};
  for (const folder of readdirSync(ROOT)) {
    for (const lang of ["en", "tr"]) {
      const path = join(ROOT, folder, `${lang}.md`);
      files[path] = readFileSync(path, "utf8");
    }
  }
  return buildStories(files);
}

// Stories come sorted from newest to oldest, so the first news story is the latest one.
function pick(stories: Story[], keys: string[]): Story[] {
  if (keys.length === 0) return stories.filter((story) => story.kind === "news").slice(0, 1);
  return keys.map((key) => {
    const story = stories.find((item) => item.key === key);
    if (!story) throw new Error(`No story folder named ${key}`);
    return story;
  });
}

// --- Images ---

class NotAnImage extends Error {}

// A connection that fails is tried again. An answer that is not an image will not change.
async function fetchImage(url: string): Promise<{ data: Buffer; extension: string }> {
  for (let attempt = 1; ; attempt++) {
    try {
      const response = await fetch(url, { headers: HEADERS, signal: AbortSignal.timeout(ATTEMPT_MS) });
      const type = response.headers.get("content-type") ?? "";
      if (!response.ok || !type.startsWith("image/")) throw new NotAnImage(`Could not download an image from ${url}: ${response.status} ${type}`);
      return { data: Buffer.from(await response.arrayBuffer()), extension: type.slice(6).split(/[+;]/)[0] };
    } catch (error) {
      if (error instanceof NotAnImage || attempt === ATTEMPTS) throw error;
      await new Promise((done) => setTimeout(done, RETRY_MS));
    }
  }
}

function readSources(folder: string): Record<string, string> {
  const path = join(folder, SOURCES);
  return existsSync(path) ? JSON.parse(readFileSync(path, "utf8")) : {};
}

// The same address is fetched once, even when several pages use it. When a download fails, the image
// the last run saved from that same address is used instead.
async function download(urls: string[], folder: string, previous: string): Promise<Map<string, string>> {
  mkdirSync(folder, { recursive: true });
  const saved = readSources(previous);
  const sources: Record<string, string> = {};
  const files = new Map<string, string>();
  for (const url of new Set(urls)) {
    let name: string;
    try {
      const image = await fetchImage(url);
      name = `${files.size + 1}.${image.extension}`;
      writeFileSync(join(folder, name), image.data);
    } catch (error) {
      const old = saved[url];
      if (!old || !existsSync(join(previous, old))) throw error;
      name = old;
      copyFileSync(join(previous, old), join(folder, name));
      console.warn(`Could not download ${url}, using the copy from the last run.`);
    }
    sources[url] = name;
    files.set(url, pathToFileURL(resolve(folder, name)).href);
  }
  writeFileSync(join(folder, SOURCES), JSON.stringify(sources, null, 2));
  return files;
}

// --- Posts ---

// Writes every file of one post into dir. Any broken rule or failed download throws, and the
// caller then throws the half written folder away.
async function write(page: Page, post: SocialPost, key: string, dir: string): Promise<void> {
  writeFileSync(join(dir, "x.txt"), `${post.x}\n`);
  writeFileSync(join(dir, "caption.txt"), `${post.caption}\n`);

  const images = await download(post.pages.map((item) => item.image), join(dir, "images"), join(OUT, key, "images"));
  for (const [index, { image, position, paragraphs }] of post.pages.entries()) {
    await drawPage(page, { image: images.get(image)!, position, paragraphs }, join(dir, `page-${index + 1}.png`), `${key}: page ${index + 1}`);
  }
  makeStill(join(dir, "page-1.png"), join(dir, "post.mp4"));
}

// --- Run ---

const stories = pick(readStories(), process.argv.slice(2));
const { browser, page } = await openBrowser();

try {
  for (const story of stories) {
    const post = buildSocial(readFileSync(join(ROOT, story.key, "social.yaml"), "utf8"), story);
    const out = join(OUT, story.key);

    // The post is built in a side folder and takes the place of the old one only when every
    // file is made, so a run that stops halfway, for example on an image address that moved,
    // leaves the last good post untouched.
    const draft = join(OUT, `.${story.key}.new`);
    rmSync(draft, { recursive: true, force: true });
    mkdirSync(draft, { recursive: true });
    try {
      await write(page, post, story.key, draft);
    } catch (error) {
      rmSync(draft, { recursive: true, force: true });
      throw error;
    }
    replacePost(draft, out);
    console.log(`${out}: x.txt, caption.txt, ${post.pages.length} page${post.pages.length > 1 ? "s" : ""} and post.mp4`);
  }
} finally {
  await browser.close();
}
