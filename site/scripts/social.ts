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
// NOTE: The still video puts the 1080 by 1350 page in the middle of a 1080 by 1920 frame, on the
// dark color of the page itself. Instagram shows a reel in the feed cut to 4:5, which is exactly
// the page, and in the reels tab the whole frame, where the text of the page stays above the
// account name drawn over the bottom.
//
// XXX: The text of a page starts at the top of the dark band in scripts/social-card.html. A text
// too tall for the band is moved up so it ends at TEXT_BOTTOM, and one that would then climb too
// far over the photo stops the script instead of being saved. src/social.ts limits the
// characters on a page so this should not happen. TEXT_TOP is the last guard, because the real
// height of a text also depends on its words.

import { spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, readdirSync, renameSync, rmSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { chromium, type Page } from "@playwright/test";
import { buildSocial, type SocialPost } from "../src/social.ts";
import { buildStories, type Story } from "../src/stories.ts";

// --- Constants ---

const ROOT = "src/content/stories";
const OUT = "social-posts";
const TEMPLATE = pathToFileURL(resolve("scripts/social-card.html")).href;
const SIZE = { width: 1080, height: 1350 };

// Wikimedia and several press sites refuse requests that do not name the client.
const HEADERS = { "User-Agent": "BitpulseSocial/1.0 (+https://bitpulse.cloud)" };

// The text block ends no lower than TEXT_BOTTOM, the bottom margin of the page, and may not start
// higher than TEXT_TOP, otherwise it covers most of the photo.
const TEXT_BOTTOM = 1262;
const TEXT_TOP = 680;

// The page sits 285 pixels below the top of the still video, half of the 570 left over.
const STILL_SECONDS = 6;
const STILL_FILTER = "pad=1080:1920:0:285:color=0x141513,format=yuv420p";

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

// --- Still video ---

// ffmpeg names the cause in its first lines, the last ones only say that nothing was written.
// stillimage tells the encoder that no frame changes, which keeps the file small.
function makeStill(page: string, out: string): void {
  const result = spawnSync("ffmpeg", [
    "-v", "error", "-y", "-loop", "1", "-framerate", "30", "-t", String(STILL_SECONDS), "-i", page,
    "-vf", STILL_FILTER, "-c:v", "libx264", "-tune", "stillimage", "-preset", "medium", "-crf", "18", "-r", "30", "-movflags", "+faststart", out,
  ], { encoding: "utf8" });
  if (result.error) throw new Error(`ffmpeg could not be started, the still video needs it: ${result.error.message}`);
  if (result.status !== 0) throw new Error(`ffmpeg failed: ${result.stderr.trim().split("\n").slice(0, 4).join(" ")}`);
}

// --- Posts ---

// Writes every file of one post into dir. Any broken rule or failed download throws, and the
// caller then throws the half written folder away.
async function write(page: Page, post: SocialPost, key: string, dir: string): Promise<void> {
  writeFileSync(join(dir, "x.txt"), `${post.x}\n`);
  writeFileSync(join(dir, "caption.txt"), `${post.caption}\n`);

  const images = await download(post.pages.map((item) => item.image), join(dir, "images"));
  for (const [index, { image, position, paragraphs }] of post.pages.entries()) {
    await page.setViewportSize(SIZE);
    await page.goto(TEMPLATE);
    const top = await page.evaluate(async ({ image, position, paragraphs, limit }) => {
      const photo = document.querySelector("img")!;
      photo.src = image;
      photo.style.objectPosition = position;
      const text = document.querySelector(".text")!;
      for (const words of paragraphs) {
        const paragraph = document.createElement("p");
        paragraph.textContent = words;
        text.append(paragraph);
      }
      await photo.decode();
      await document.fonts.ready;
      const box = text.getBoundingClientRect();
      if (box.bottom > limit) (text as HTMLElement).style.top = `${limit - box.height}px`;
      return text.getBoundingClientRect().top;
    }, { image: images.get(image)!, position, paragraphs, limit: TEXT_BOTTOM });

    if (top < TEXT_TOP) throw new Error(`${key}: page ${index + 1} is too long, its text starts at ${Math.round(top)} pixels and the limit is ${TEXT_TOP}`);
    await page.screenshot({ path: join(dir, `page-${index + 1}.png`) });
  }
  makeStill(join(dir, "page-1.png"), join(dir, "post.mp4"));
}

// --- Run ---

const stories = pick(readStories(), process.argv.slice(2));
const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH });
const page = await browser.newPage({ viewport: SIZE });

try {
  for (const story of stories) {
    const post = buildSocial(readFileSync(join(ROOT, story.key, "social.yaml"), "utf8"), story);
    const out = join(OUT, story.key);

    // The post is built in a side folder and takes the place of the old one only when every
    // file is made, so a run that stops halfway, for example on an image address that moved,
    // leaves the last good post untouched. The old folder goes away whole, a post that got
    // shorter must not keep a stale last page.
    const draft = join(OUT, `.${story.key}.new`);
    rmSync(draft, { recursive: true, force: true });
    mkdirSync(draft, { recursive: true });
    try {
      await write(page, post, story.key, draft);
    } catch (error) {
      rmSync(draft, { recursive: true, force: true });
      throw error;
    }
    rmSync(out, { recursive: true, force: true });
    renameSync(draft, out);
    console.log(`${out}: x.txt, caption.txt, ${post.pages.length} page${post.pages.length > 1 ? "s" : ""} and post.mp4`);
  }
} finally {
  await browser.close();
}
