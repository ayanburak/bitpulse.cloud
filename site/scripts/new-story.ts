/**
 * file: scripts/new-story.ts
 * importable: nothing, run with npm run new-story
 *
 * Opens the folder of a new news story with everything that does not need writing:
 *
 *   npm run new-story -- <key> <image-address> [brief.md]
 *
 * The folder is named with today's date in UTC and the key. The publishing time is now, in UTC.
 * The image is downloaded, checked for the 1200 pixel minimum and stored as image.jpg. When a
 * brief from the radar is given, its sources block goes into both language files.
 *
 * Every field that needs writing is left empty, so the build refuses the story until it is done.
 *
 * description: Creates the folder, frontmatter and image of a new story.
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import sharp from "sharp";
import type { Sharp } from "sharp";

// --- Constants ---

const ROOT = "src/content/stories";
const MIN_WIDTH = 1200;
const AGENT = "Mozilla/5.0 (compatible; Bitpulse/1.0; +https://bitpulse.cloud)";
const KEY = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

// --- Helpers ---

function fail(message: string): never {
  console.error(message);
  process.exit(1);
}

// The brief ends with a fenced yaml block that starts with sources:, written by the radar.
function sourcesFrom(briefPath: string | undefined): string {
  if (!briefPath) return "sources:\n";
  const match = /```yaml\n(sources:\n[\s\S]*?)```/.exec(readFileSync(briefPath, "utf8"));
  if (!match) fail(`No sources block in ${briefPath}`);
  return match[1];
}

// The image is downloaded and checked before the folder exists, so a bad address leaves
// nothing behind that would block the next try with "already exists".
async function loadImage(address: string): Promise<{ image: Sharp; width: number }> {
  const response = await fetch(address, { headers: { "User-Agent": AGENT } });
  if (!response.ok) fail(`Image could not be downloaded: HTTP ${response.status}`);
  const image = sharp(Buffer.from(await response.arrayBuffer()));
  const { width = 0, height = 0 } = await image.metadata();
  if (width < MIN_WIDTH) fail(`Image is ${width} pixels wide, at least ${MIN_WIDTH} are needed.`);
  if (height > width) fail("Image is in portrait format, a landscape image is needed.");
  return { image, width };
}

function frontmatter(date: string, time: string, sources: string, imageAddress: string): string {
  return [
    "---",
    "slug: ",
    "title: ",
    "summary: ",
    "category: ",
    `date: ${date}`,
    `time: "${time}"`,
    "kind: news",
    sources.trimEnd(),
    "image:",
    "  file: image.jpg",
    "  alt: ",
    "  credit: ",
    "  license: ",
    `  licenseUrl: ${imageAddress}`,
    `  source: ${imageAddress}`,
    "---",
    "",
  ].join("\n");
}

// --- Run ---

const [key, imageAddress, briefPath] = process.argv.slice(2);
if (!key || !imageAddress) fail("Usage: npm run new-story -- <key> <image-address> [brief.md]");
if (!KEY.test(key)) fail(`The key may only hold lowercase letters, digits and dashes: ${key}`);

const now = new Date().toISOString();
const date = now.slice(0, 10);
const time = now.slice(11, 16);
const folder = join(ROOT, `${date}-${key}`);
if (existsSync(folder)) fail(`${folder} already exists.`);

const sources = sourcesFrom(briefPath);
const { image, width } = await loadImage(imageAddress);
mkdirSync(folder, { recursive: true });
await image.jpeg({ quality: 90 }).toFile(join(folder, "image.jpg"));
for (const lang of ["en", "tr"]) writeFileSync(join(folder, `${lang}.md`), frontmatter(date, time, sources, imageAddress));
console.log(`${folder} created, published ${date} ${time} UTC, image ${width} pixels wide.`);
