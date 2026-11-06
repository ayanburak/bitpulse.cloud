/**
 * file: scripts/video-source.ts
 * importable: resolveVideo, VideoStreams
 *
 * Turns the address of a video into the addresses ffmpeg reads. A direct video file or stream
 * is read as it is. A YouTube page is not a video file, so yt-dlp finds the files behind it.
 * YouTube keeps picture and sound in separate files, which is why the picture and the sound
 * each have their own address.
 *
 * description: Finds the picture and sound addresses of a video page or file.
 */

// NOTE: yt-dlp must be installed for the user who runs the script, together with its YouTube
// challenge solver, through uv tool install "yt-dlp[default]". The solver runs on Node, which
// is already there for the scripts themselves. The addresses yt-dlp returns expire after some
// hours, so they are found again on every run and never stored.

import { spawnSync } from "node:child_process";

// --- Types ---

export interface VideoStreams {
  picture: string;
  sound: string;
}

// --- Constants ---

const YOUTUBE = /^https?:\/\/(www\.|m\.)?(youtube\.com|youtu\.be)\//;

// --- Resolving ---

/**
 * Finds the addresses of the picture and the sound of a video.
 *
 * @param url Address of a video file, a stream or a YouTube page.
 * @param height Tallest picture to use. A scan needs little, a finished reel needs 1080.
 * @returns The two addresses. For anything but YouTube both are the address given.
 * @throws Error if yt-dlp is missing or can not open the YouTube page.
 */
export function resolveVideo(url: string, height: number): VideoStreams {
  if (!YOUTUBE.test(url)) return { picture: url, sound: url };
  const format = `bv*[height<=${height}][ext=mp4]+ba[ext=m4a]/bv*[height<=${height}]+ba/b[height<=${height}]/b`;
  const result = spawnSync("yt-dlp", ["--js-runtimes", "node", "--no-warnings", "--no-playlist", "-f", format, "-g", url], { encoding: "utf8" });
  if (result.error) throw new Error(`yt-dlp could not be started, a YouTube address needs it: ${result.error.message}`);
  if (result.status !== 0) throw new Error(`yt-dlp could not open ${url}: ${result.stderr.trim().split("\n").slice(-2).join(" ")}`);
  const lines = result.stdout.trim().split("\n").filter(Boolean);
  if (lines.length === 0) throw new Error(`yt-dlp found no video at ${url}`);
  return { picture: lines[0], sound: lines[1] ?? lines[0] };
}
