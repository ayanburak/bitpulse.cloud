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
 * description: Writes the X post, the Instagram caption and the Instagram pages of a story.
 */

// NOTE: The output folder is in .gitignore. The page images may be press or news photos that can
// be shared on a social account but must not be republished in this repository.
//
// XXX: A page whose text climbs too far over the photo stops the script instead of being saved.
// src/social.ts limits the characters on a page so this should not happen. TEXT_TOP below is
// the last guard, because the real height of a text also depends on its words.

import { mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { chromium } from "@playwright/test";
import { buildSocial } from "../src/social.ts";
import { buildStories, type Story } from "../src/stories.ts";

// --- Constants ---

const ROOT = "src/content/stories";
const OUT = "social-posts";
const TEMPLATE = pathToFileURL(resolve("scripts/social-card.html")).href;
const SIZE = { width: 1080, height: 1350 };

// Wikimedia and several press sites refuse requests that do not name the client.
const HEADERS = { "User-Agent": "BitpulseSocial/1.0 (+https://bitpulse.cloud)" };

// The text block may not start higher than this, otherwise it covers most of the photo.
const TEXT_TOP = 680;

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

// The same address is fetched once, even when several pages use it.
async function download(urls: string[], folder: string): Promise<Map<string, string>> {
  mkdirSync(folder, { recursive: true });
  const files = new Map<string, string>();
  for (const url of new Set(urls)) {
    const response = await fetch(url, { headers: HEADERS });
    const type = response.headers.get("content-type") ?? "";
    if (!response.ok || !type.startsWith("image/")) throw new Error(`Could not download an image from ${url}: ${response.status} ${type}`);
    const path = resolve(folder, `${files.size + 1}.${type.slice(6).split(/[+;]/)[0]}`);
    writeFileSync(path, Buffer.from(await response.arrayBuffer()));
    files.set(url, pathToFileURL(path).href);
  }
  return files;
}

// --- Run ---

const stories = pick(readStories(), process.argv.slice(2));
const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH });
const page = await browser.newPage({ viewport: SIZE });

try {
  for (const story of stories) {
    const folder = join(ROOT, story.key);
    const post = buildSocial(readFileSync(join(folder, "social.yaml"), "utf8"), story);
    const out = join(OUT, story.key);

    // Old pages are removed first, a post that got shorter must not leave a stale last page.
    rmSync(out, { recursive: true, force: true });
    mkdirSync(out, { recursive: true });
    writeFileSync(join(out, "x.txt"), `${post.x}\n`);
    writeFileSync(join(out, "caption.txt"), `${post.caption}\n`);

    const images = await download(post.pages.map((item) => item.image), join(out, "images"));
    for (const [index, { image, paragraphs }] of post.pages.entries()) {
      await page.goto(TEMPLATE);
      const top = await page.evaluate(async ({ image, paragraphs }) => {
        const photo = document.querySelector("img")!;
        photo.src = image;
        const text = document.querySelector(".text")!;
        for (const words of paragraphs) {
          const paragraph = document.createElement("p");
          paragraph.textContent = words;
          text.append(paragraph);
        }
        await photo.decode();
        await document.fonts.ready;
        return text.getBoundingClientRect().top;
      }, { image: images.get(image)!, paragraphs });

      if (top < TEXT_TOP) throw new Error(`${story.key}: page ${index + 1} is too long, its text starts at ${Math.round(top)} pixels and the limit is ${TEXT_TOP}`);
      await page.screenshot({ path: join(out, `page-${index + 1}.png`) });
    }
    console.log(`${out}: x.txt, caption.txt and ${post.pages.length} page${post.pages.length > 1 ? "s" : ""}`);
  }
} finally {
  await browser.close();
}
