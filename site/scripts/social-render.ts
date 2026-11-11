/**
 * file: scripts/social-render.ts
 * importable: SIZE, openBrowser, drawPage, makeStill, runFfmpeg
 *
 * The drawing that story posts and clips share. drawPage fills scripts/social-card.html with a
 * photo and a text and saves it as a PNG. Without a photo it saves only the logo, the shade and the
 * text on a transparent background, which a clip lays over its video.
 *
 * description: Draws an Instagram page and turns a page into a still video.
 */

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
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { chromium, type Browser, type Page } from "@playwright/test";

// --- Constants ---

const TEMPLATE = pathToFileURL(resolve("scripts/social-card.html")).href;
export const SIZE = { width: 1080, height: 1350 };

// The text block ends no lower than TEXT_BOTTOM, the bottom margin of the page, and may not start
// higher than TEXT_TOP, otherwise it covers most of the photo.
const TEXT_BOTTOM = 1262;
const TEXT_TOP = 680;

// The page sits 285 pixels below the top of the still video, half of the 570 left over.
export const FRAME_PAD = "pad=1080:1920:0:285:color=0x141513,format=yuv420p";
const STILL_SECONDS = 3;

// --- Browser ---

/**
 * Starts the browser that draws the pages. CHROME_PATH points to an installed browser when the one
 * Playwright expects is not downloaded.
 *
 * @returns The browser and one page of the card size.
 */
export async function openBrowser(): Promise<{ browser: Browser; page: Page }> {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH });
  return { browser, page: await browser.newPage({ viewport: SIZE }) };
}

// --- Drawing ---

/**
 * Draws one Instagram page and saves it.
 *
 * @param page Browser page from openBrowser.
 * @param card Address of the photo, or null for a transparent page, the photo position and the paragraphs.
 * @param path Where the PNG is written.
 * @param where Name used in the error message.
 * @throws Error if the text is too tall for the page.
 */
export async function drawPage(page: Page, card: { image: string | null; position: string; paragraphs: string[] }, path: string, where: string): Promise<void> {
  await page.setViewportSize(SIZE);
  await page.goto(TEMPLATE);
  const top = await page.evaluate(async ({ image, position, paragraphs, limit }) => {
    const photo = document.querySelector("img")!;
    if (image) {
      photo.src = image;
      photo.style.objectPosition = position;
      await photo.decode();
    } else {
      photo.remove();
      document.documentElement.style.background = "transparent";
      document.body.style.background = "transparent";
    }
    const text = document.querySelector(".text")!;
    for (const words of paragraphs) {
      const paragraph = document.createElement("p");
      paragraph.textContent = words;
      text.append(paragraph);
    }
    await document.fonts.ready;
    const box = text.getBoundingClientRect();
    if (box.bottom > limit) (text as HTMLElement).style.top = `${limit - box.height}px`;
    return text.getBoundingClientRect().top;
  }, { ...card, limit: TEXT_BOTTOM });

  if (top < TEXT_TOP) throw new Error(`${where} is too long, its text starts at ${Math.round(top)} pixels and the limit is ${TEXT_TOP}`);
  await page.screenshot({ path, omitBackground: card.image === null });
}

// --- Video ---

/**
 * Runs ffmpeg and turns a failure into an error that names its cause.
 *
 * @param args Arguments after the program name.
 * @throws Error if ffmpeg is missing or fails.
 */
export function runFfmpeg(args: string[]): void {
  const result = spawnSync("ffmpeg", ["-v", "error", "-y", ...args], { encoding: "utf8" });
  // ffmpeg names the cause in its first lines, the last ones only say that nothing was written.
  if (result.error) throw new Error(`ffmpeg could not be started, the video needs it: ${result.error.message}`);
  if (result.status !== 0) throw new Error(`ffmpeg failed: ${result.stderr.trim().split("\n").slice(0, 4).join(" ")}`);
}

/**
 * Saves a page as a silent vertical video of three seconds in which nothing moves.
 *
 * @param png The page.
 * @param out Where the mp4 is written.
 */
export function makeStill(png: string, out: string): void {
  // stillimage tells the encoder that no frame changes, which keeps the file small.
  runFfmpeg([
    "-loop", "1", "-framerate", "30", "-t", String(STILL_SECONDS), "-i", png,
    "-vf", FRAME_PAD, "-c:v", "libx264", "-tune", "stillimage", "-preset", "medium", "-crf", "18", "-r", "30", "-movflags", "+faststart", out,
  ]);
}
