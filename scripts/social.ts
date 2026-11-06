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
 * A story with a video field also gets video/reel.mp4, a vertical video for Instagram and X.
 * ffmpeg fetches only the part of the source that is used, so a long recording is not
 * downloaded whole. The logo, the line and the closing screen come from scripts/social-reel.html.
 * This part needs ffmpeg and ffprobe on the machine.
 *
 * description: Writes the X post, the Instagram caption, the Instagram pages and the video of a story.
 */

// NOTE: The output folder is in .gitignore. The page images may be press or news photos that can
// be shared on a social account but must not be republished in this repository.
//
// NOTE: The video layout is fixed. The clip keeps its own sound, a blurred copy of the picture
// fills the frame behind it, the line never changes, and the closing screen runs for a moment
// while the sound fades. Sound is brought to -14 LUFS, the level Instagram and X play at.
//
// XXX: A page whose text climbs too far over the photo stops the script instead of being saved.
// src/social.ts limits the characters on a page so this should not happen. TEXT_TOP below is
// the last guard, because the real height of a text also depends on its words.

import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, readdirSync, renameSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { chromium, type Page } from "@playwright/test";
import { buildSocial, type SocialPost, type SocialVideo } from "../src/social.ts";
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

const REEL_TEMPLATE = pathToFileURL(resolve("scripts/social-reel.html")).href;
const REEL_SIZE = { width: 1080, height: 1920 };

// A fourth line runs into the account name Instagram draws over the bottom of a reel.
const MAX_LINES = 3;
const END_SECONDS = 2.2;

// Without a crop the clip is cut from the middle to the 9:8 window it is shown in. The commas
// are escaped because they would split the filter otherwise.
const CENTER = "min(iw\\,ih*9/8):min(ih\\,iw*8/9)";

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

// --- Video ---

// ffmpeg names the cause in its first lines, the last ones only say that nothing was written.
function run(command: string, args: string[]): string {
  const result = spawnSync(command, args, { encoding: "utf8" });
  if (result.error) throw new Error(`${command} could not be started, the video needs it: ${result.error.message}`);
  if (result.status !== 0) throw new Error(`${command} failed: ${result.stderr.trim().split("\n").slice(0, 4).join(" ")}`);
  return result.stdout;
}

// The line is drawn once over a clear background, then the same page draws the closing screen.
// Words between asterisks become em, which the template colors.
async function drawLayers(page: Page, line: string, key: string, folder: string): Promise<void> {
  await page.setViewportSize(REEL_SIZE);
  await page.goto(REEL_TEMPLATE);
  const lines = await page.evaluate(async (line) => {
    const text = document.querySelector(".text")!;
    for (const [index, part] of line.split("*").entries()) {
      if (!part) continue;
      const node = index % 2 ? document.createElement("em") : document.createTextNode(part);
      if (node instanceof HTMLElement) node.textContent = part;
      text.append(node);
    }
    await document.fonts.ready;
    return Math.round(text.getBoundingClientRect().height / parseFloat(getComputedStyle(text).lineHeight));
  }, line);
  if (lines > MAX_LINES) throw new Error(`${key}: the video line takes ${lines} lines, the limit is ${MAX_LINES}`);
  await page.screenshot({ path: join(folder, "line.png"), omitBackground: true });
  await page.evaluate(() => document.body.classList.add("end"));
  await page.screenshot({ path: join(folder, "end.png") });
}

// One ffmpeg call cuts the clip, lays the line over it, adds the closing screen and fades the
// sound, which keeps running under the closing screen. The source is read from the start second
// for the whole length, so the sound does not jump where the closing screen begins. A sped up
// clip reads a longer stretch of picture without its sound, and its own sound, when it has one,
// comes in as a second input that starts at its own second and plays in real time.
function encode(video: SocialVideo, key: string, folder: string, out: string): void {
  const total = video.duration + END_SECONDS;
  const agent = ["-user_agent", HEADERS["User-Agent"]];
  const speed = video.speed ?? 1;
  const span = video.speed === undefined ? total : video.duration * speed;
  const inputs = ["-ss", String(video.start), "-t", String(span), ...agent, "-i", video.source];
  const hasAudio = run("ffprobe", ["-v", "error", ...agent, "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", video.source]).trim() !== "";
  let sound = "";
  if (hasAudio && video.speed === undefined) sound = "[0:a]";
  if (hasAudio && video.sound !== undefined) {
    inputs.push("-ss", String(video.sound), "-t", String(total), ...agent, "-i", video.source);
    sound = "[1:a]";
  }
  const layer = inputs.filter((value) => value === "-i").length;
  const graph = [
    `[0:v]setpts=(PTS-STARTPTS)/${speed},trim=duration=${video.duration},setpts=PTS-STARTPTS,fps=30,split[a][b]`,
    "[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=40:2,eq=brightness=-0.22[bg]",
    `[b]crop=${video.crop ?? CENTER},scale=1080:960[fg]`,
    "[bg][fg]overlay=0:360[clip]",
    `[${layer}:v]format=rgba,fade=in:st=0:d=0.25:alpha=1[line]`,
    `[clip][line]overlay=0:0:shortest=1,trim=duration=${video.duration},format=yuv420p,setsar=1[main]`,
    `[${layer + 1}:v]fade=in:st=0:d=0.2,format=yuv420p,setsar=1[end]`,
    "[main][end]concat=n=2:v=1:a=0[v]",
  ];
  if (sound) graph.push(`${sound}loudnorm=I=-14:TP=-1.5:LRA=11,afade=in:st=0:d=0.2,afade=out:st=${total - 2}:d=2,atrim=duration=${total}[s]`);
  run("ffmpeg", [
    "-v", "error", "-y", ...inputs,
    "-loop", "1", "-framerate", "30", "-t", String(video.duration), "-i", join(folder, "line.png"),
    "-loop", "1", "-framerate", "30", "-t", String(END_SECONDS), "-i", join(folder, "end.png"),
    "-filter_complex", graph.join(";"), "-map", "[v]", ...(sound ? ["-map", "[s]", "-c:a", "aac", "-b:a", "160k"] : []),
    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", "30", "-movflags", "+faststart", out,
  ]);

  // A start second too close to the end of the source gives a short clip without any error.
  // The line layer stops with the clip, otherwise ffmpeg would hold the last frame to fill it.
  const length = Number(run("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out]));
  if (length < total - 0.5) throw new Error(`${key}: the video is ${length.toFixed(1)} seconds instead of ${total}, the source ends before the clip does`);
}

async function makeReel(page: Page, video: SocialVideo, key: string, out: string): Promise<void> {
  const folder = mkdtempSync(join(tmpdir(), "bitpulse-reel-"));
  try {
    await drawLayers(page, video.text, key, folder);
    mkdirSync(join(out, "video"), { recursive: true });
    encode(video, key, folder, join(out, "video", "reel.mp4"));
  } finally {
    rmSync(folder, { recursive: true, force: true });
  }
}

// --- Posts ---

// Writes every file of one post into dir. Any broken rule or failed download throws, and the
// caller then throws the half written folder away.
async function write(page: Page, post: SocialPost, key: string, dir: string): Promise<void> {
  writeFileSync(join(dir, "x.txt"), `${post.x}\n`);
  writeFileSync(join(dir, "caption.txt"), `${post.caption}\n`);

  const images = await download(post.pages.map((item) => item.image), join(dir, "images"));
  for (const [index, { image, paragraphs }] of post.pages.entries()) {
    await page.setViewportSize(SIZE);
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

    if (top < TEXT_TOP) throw new Error(`${key}: page ${index + 1} is too long, its text starts at ${Math.round(top)} pixels and the limit is ${TEXT_TOP}`);
    await page.screenshot({ path: join(dir, `page-${index + 1}.png`) });
  }
  if (post.video) await makeReel(page, post.video, key, dir);
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
    console.log(`${out}: x.txt, caption.txt, ${post.pages.length} page${post.pages.length > 1 ? "s" : ""}${post.video ? " and video/reel.mp4" : ""}`);
  }
} finally {
  await browser.close();
}
