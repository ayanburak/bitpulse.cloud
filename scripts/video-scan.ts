/**
 * file: scripts/video-scan.ts
 * importable: nothing, run with npm run video-scan
 *
 * Looks at a video by its address, without downloading it whole, so an agent can decide in one
 * step whether the video shows the event and where its strongest moment is:
 *
 *   npm run video-scan -- <address>
 *   npm run video-scan -- <address> --from 200 --to 240
 *
 * It prints the length of the video, whether it has sound and its five loudest moments, and it
 * draws one image of sixteen frames with the second of each frame written on it. Without --from
 * and --to, a video of up to two minutes is covered evenly. A longer one gets eight frames
 * spread over the whole video and eight around its loudest moment. With --from and --to the
 * sixteen frames cover only that window, which is how the start of a clip is settled.
 *
 * description: Prints the length, sound and loudest moments of a video and draws a sheet of its frames.
 */

// NOTE: Reading the loudness needs the whole sound track, and the sound sits between the
// pictures in the file, so for that step ffmpeg reads the whole file over the network. Sources
// often offer the same video in several sizes with the same timing, the smallest one is enough
// to scan. The frames themselves are read one by one at their own second, which needs a server
// that can send part of a file. Most video hosts can.
//
// NOTE: The sheet is always written to the same file in the temporary folder, a new scan
// replaces the last one. Nothing else is kept. It is 1280 by 720 pixels, small enough to keep
// the cost of reading it low and large enough to read the seconds and see what happens.

import { spawnSync } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir, userInfo } from "node:os";
import { join } from "node:path";
import { parseArgs } from "node:util";

// --- Constants ---

// The temporary folder is shared by every user of the machine, and the owner and the agents
// run as different users. Each gets its own sheet, one could not overwrite the other's file.
const SHEET = join(tmpdir(), `bitpulse-video-scan-${userInfo().username}.jpg`);
const FRAMES = 16;
const SHORT_VIDEO = 120;

// Frames around the loudest moment of a long video reach this far to each side of it.
const AROUND = 15;

// Loud moments closer together than this are one moment, a cheer lasts a few seconds.
const GAP = 5;

const AGENT = "BitpulseSocial/1.0 (+https://bitpulse.cloud)";

// --- Helpers ---

// ffmpeg names the cause in its first lines, the last ones only say that nothing was written.
function run(command: string, args: string[]): string {
  const result = spawnSync(command, args, { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
  if (result.error) throw new Error(`${command} could not be started, the scan needs it: ${result.error.message}`);
  if (result.status !== 0) throw new Error(`${command} failed: ${result.stderr.trim().split("\n").slice(0, 4).join(" ")}`);
  return result.stdout + result.stderr;
}

function clock(seconds: number): string {
  const whole = Math.floor(seconds);
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, "0")}${seconds % 1 ? `.${Math.round((seconds % 1) * 10)}` : ""}`;
}

// Spreads count points evenly over a window, keeping clear of its very ends, where a frame
// is often black or a title card.
function spread(from: number, to: number, count: number): number[] {
  const step = (to - from) / count;
  return Array.from({ length: count }, (_, index) => Math.round((from + step * (index + 0.5)) * 10) / 10);
}

// --- Sound ---

// The momentary loudness of every tenth of a second, averaged per second. ebur128 writes one
// line per measurement to stderr, the time and the M value are read from it.
function loudest(url: string): { second: number; level: number }[] {
  const output = run("ffmpeg", ["-hide_banner", "-nostats", "-user_agent", AGENT, "-i", url, "-vn", "-af", "ebur128", "-f", "null", "-"]);
  const seconds = new Map<number, number[]>();
  for (const match of output.matchAll(/t:\s*([\d.]+)\s+TARGET.*?M:\s*(-?[\d.]+)/g)) {
    const second = Math.floor(Number(match[1]));
    seconds.set(second, [...(seconds.get(second) ?? []), Number(match[2])]);
  }
  const levels = [...seconds].map(([second, values]) => ({ second, level: values.reduce((sum, value) => sum + value, 0) / values.length }));
  levels.sort((a, b) => b.level - a.level);

  const peaks: { second: number; level: number }[] = [];
  for (const item of levels) {
    if (peaks.every((peak) => Math.abs(peak.second - item.second) >= GAP)) peaks.push(item);
    if (peaks.length === 5) break;
  }
  return peaks;
}

// --- Frames ---

function sheet(url: string, times: number[]): void {
  const folder = mkdtempSync(join(tmpdir(), "bitpulse-scan-"));
  try {
    for (const [index, time] of times.entries()) {
      run("ffmpeg", [
        "-v", "error", "-y", "-ss", String(time), "-user_agent", AGENT, "-i", url, "-frames:v", "1",
        "-vf", `scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:-1:-1,drawtext=text='${clock(time).replace(":", "\\:")}':x=6:y=6:fontsize=20:fontcolor=yellow:box=1:boxcolor=black@0.7:boxborderw=4`,
        join(folder, `${String(index + 1).padStart(2, "0")}.png`),
      ]);
    }
    run("ffmpeg", ["-v", "error", "-y", "-i", join(folder, "%02d.png"), "-vf", "tile=4x4", "-frames:v", "1", "-q:v", "4", SHEET]);
  } finally {
    rmSync(folder, { recursive: true, force: true });
  }
}

// --- Run ---

const { positionals, values } = parseArgs({ allowPositionals: true, options: { from: { type: "string" }, to: { type: "string" } } });
const url = positionals[0];
if (!url || !/^https?:\/\//.test(url)) throw new Error("Give the address of a video file: npm run video-scan -- <address>");

const length = Number(run("ffprobe", ["-v", "error", "-user_agent", AGENT, "-show_entries", "format=duration", "-of", "csv=p=0", url]).trim());
const sound = run("ffprobe", ["-v", "error", "-user_agent", AGENT, "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", url]).trim() !== "";
console.log(`Length: ${clock(length)}, ${sound ? "with sound" : "no sound"}`);

let times: number[];
if (values.from !== undefined || values.to !== undefined) {
  const from = Math.max(0, Number(values.from ?? 0));
  const to = Math.min(length, Number(values.to ?? length));
  if (!(to > from)) throw new Error(`--from must come before --to, within the ${clock(length)} of the video`);
  times = spread(from, to, FRAMES);
} else {
  const peaks = sound ? loudest(url) : [];
  if (peaks.length) console.log(`Loudest moments: ${peaks.map((peak) => `${clock(peak.second)} ${peak.level.toFixed(0)} LUFS`).join(", ")}`);
  if (length <= SHORT_VIDEO || !peaks.length) {
    times = spread(0, length, FRAMES);
  } else {
    const center = peaks[0].second;
    times = [...spread(0, length, FRAMES / 2), ...spread(Math.max(0, center - AROUND), Math.min(length, center + AROUND), FRAMES / 2)];
    times.sort((a, b) => a - b);
  }
}

sheet(url, times);
console.log(`Frames at ${times.map(clock).join(", ")}`);
console.log(`Sheet: ${SHEET}`);
