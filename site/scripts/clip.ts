/**
 * file: scripts/clip.ts
 * importable: nothing, run with npm run clip
 *
 * Turns a clip folder into a post for Instagram only. The folder holds clip.yaml and the media that
 * bitpulse fetch saved as source.mp4 or source.jpg, .png or .webp:
 *
 *   npm run clip -- social-posts/2026-11-10-sirens
 *
 * A video is cut to the seconds in clip.yaml, cut to fill the photo area of the page and laid under
 * the logo and the text, its sound kept. A picture becomes a page with a still video, like a story
 * post. The folder then also holds caption.txt, title.txt, page-1.png and post.mp4, ready for
 * bitpulse clip.
 *
 * description: Makes the page, the video and the caption of a clip.
 */

// NOTE: The photo area of the page is 1080 by 960, so a vertical video loses about a fifth at its top
// and bottom. position in clip.yaml moves the cut the same way it moves a photo on a story page.
//
// NOTE: The video is kept under four megabits a second, so ninety seconds stay below the clip limit
// of the API. page-1.png only serves the panel. It is the most typical frame of the first three
// seconds rather than the first one, because a cut often starts on a black frame between two scenes.

import { existsSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { basename, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { buildClip } from "../src/social.ts";
import { FRAME_PAD, drawPage, makeStill, openBrowser, runFfmpeg } from "./social-render.ts";

// --- Constants ---

const PHOTO = { width: 1080, height: 960 };
const OVERLAY = ".overlay.png";
const IMAGE = /^source\.(jpg|png|webp)$/;

// --- Run ---

const folder = process.argv[2];
if (!folder || !existsSync(join(folder, "clip.yaml"))) throw new Error("Give a clip folder that holds clip.yaml");
const where = basename(resolve(folder));
const clip = buildClip(readFileSync(join(folder, "clip.yaml"), "utf8"), where);
const picture = readdirSync(folder).find((name) => IMAGE.test(name));
const video = existsSync(join(folder, "source.mp4")) ? "source.mp4" : null;
if (!video && !picture) throw new Error(`${where}: no source.mp4 or source picture, run bitpulse fetch first`);

const { browser, page } = await openBrowser();
const out = (name: string) => join(folder, name);
try {
  if (video) {
    await drawPage(page, { image: null, position: clip.position, paragraphs: [clip.text] }, out(OVERLAY), where);

    // The two percents of position place the cut inside the part of the video that does not fit.
    const [across, down] = clip.position.split(" ").map((part) => Number.parseFloat(part) / 100);
    const cut = `scale=${PHOTO.width}:${PHOTO.height}:force_original_aspect_ratio=increase,crop=${PHOTO.width}:${PHOTO.height}:(iw-${PHOTO.width})*${across}:(ih-${PHOTO.height})*${down},setsar=1`;
    const graph = `[0:v]${cut}[v];color=c=0x141513:s=1080x1350:r=30[bg];[bg][v]overlay=0:0:shortest=1[b];[b][1:v]overlay=0:0,${FRAME_PAD}[out]`;
    const range = ["-ss", String(clip.start), ...(clip.end === null ? [] : ["-to", String(clip.end)])];
    runFfmpeg([
      ...range, "-i", out(video), "-i", out(OVERLAY), "-filter_complex", graph, "-map", "[out]", "-map", "0:a?",
      "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "4M", "-bufsize", "8M", "-r", "30",
      "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out("post.mp4"),
    ]);
    runFfmpeg(["-i", out("post.mp4"), "-frames:v", "1", "-vf", "thumbnail=90,crop=1080:1350:0:285", out("page-1.png")]);
    rmSync(out(OVERLAY));
  } else {
    const image = pathToFileURL(resolve(folder, picture!)).href;
    await drawPage(page, { image, position: clip.position, paragraphs: [clip.text] }, out("page-1.png"), where);
    makeStill(out("page-1.png"), out("post.mp4"));
  }
  writeFileSync(out("caption.txt"), `${clip.caption}\n`);
  writeFileSync(out("title.txt"), `${clip.title}\n`);
  console.log(`${folder}: caption.txt, title.txt, page-1.png and post.mp4`);
} finally {
  await browser.close();
}
