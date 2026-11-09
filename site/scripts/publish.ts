/**
 * file: scripts/publish.ts
 * importable: nothing, systemd runs this file when a job appears in the queue
 *
 *   node scripts/publish.ts            works through every waiting job, then exits
 *   node scripts/publish.ts rollback   puts the previous release back live
 *
 * Runs from an unpacked render package, see scripts/package-render.sh. Each job folder holds a
 * snapshot of the published stories and a job.json. The answer is one file in the results folder.
 *
 * description: Builds a new site release from a job folder and makes it live after checking it.
 */

// NOTE: This process can reach nothing but the server itself, and it never sees the database. The
// live check therefore talks to nginx on the local address and names the site itself.
//
// NOTE: The live site changes in exactly one place, the rename inside point. A release that fails
// before that point was never seen by a reader. One that fails after it is undone at once.

import { spawnSync } from "node:child_process";
import {
  chmodSync,
  cpSync,
  existsSync,
  lstatSync,
  mkdirSync,
  readdirSync,
  readFileSync,
  readlinkSync,
  renameSync,
  rmSync,
  symlinkSync,
  writeFileSync,
} from "node:fs";
import { get as httpGet } from "node:http";
import { get as httpsGet } from "node:https";
import { join } from "node:path";

// --- Types ---

interface Job {
  id: number;
  paths: string[];
  goLive: boolean;
}

interface Response {
  status: number;
  body: string;
}

// --- Constants ---

const PACKAGE = process.cwd();
const SPOOL = process.env.BITPULSE_SPOOL ?? "/var/lib/bitpulse/spool";
const RELEASES = process.env.BITPULSE_RELEASES ?? "/var/www/bitpulse-releases";
const MEDIA_CACHE = process.env.BITPULSE_MEDIA_CACHE ?? "/var/lib/bitpulse/render/media";
const CHECK_BASE = new URL(process.env.BITPULSE_CHECK_BASE ?? "https://127.0.0.1");

const SITE_HOST = "bitpulse.cloud";
const CHECK_TIMEOUT_MS = 10_000;
const KEEP = 3;
const COMMON_PATHS = ["/en/", "/tr/", "/en/about/", "/tr/archive/", "/en/privacy/", "/sitemap.xml"];
const REQUIRED_FILES = ["index.html", "en/index.html", "tr/index.html", "en/404.html", "tr/404.html", "sitemap.xml"];

// A build that loses this much of the site is treated as broken. Removing a few stories stays well
// above the line, an empty or half read snapshot falls far below it.
const MIN_PAGE_SHARE = 0.7;

// --- Links ---

function link(name: string): string | undefined {
  const path = join(RELEASES, name);
  return existsSync(path) || lstatExists(path) ? readlinkSync(path) : undefined;
}

// existsSync follows a link, so a link whose target was removed would look absent.
function lstatExists(path: string): boolean {
  try {
    lstatSync(path);
    return true;
  } catch {
    return false;
  }
}

// A rename replaces the link in one step, nginx never finds it missing or half written.
function point(name: string, target: string): void {
  const next = join(RELEASES, `.${name}.next`);
  rmSync(next, { force: true });
  symlinkSync(target, next);
  renameSync(next, join(RELEASES, name));
}

// Names start with the build time, so sorting them puts the newest first.
function prune(): void {
  const kept = new Set([link("current"), link("previous")]);
  const releases = readdirSync(RELEASES)
    .filter((name) => name.startsWith("release-"))
    .sort()
    .reverse();
  for (const name of releases.slice(KEEP)) {
    if (!kept.has(name)) rmSync(join(RELEASES, name), { recursive: true });
  }
}

// --- Build ---

function run(command: string, args: string[], env: Record<string, string>): void {
  const result = spawnSync(command, args, { cwd: PACKAGE, env: { ...process.env, ...env }, encoding: "utf8" });
  if (result.status !== 0) {
    throw new Error(`${args[0]} failed: ${(result.stderr || result.stdout || String(result.error)).slice(-1500)}`);
  }
}

function releaseName(job: Job): string {
  const stamp = new Date().toISOString().replace(/[-:]/g, "").replace("T", "-").slice(0, 15);
  return `release-${stamp}-job${job.id}`;
}

function build(job: Job, name: string): string {
  const target = join(RELEASES, name);
  cpSync(join(PACKAGE, "template"), target, { recursive: true });
  run(process.execPath, ["scripts/prerender.ts"], {
    BITPULSE_OUT: target,
    BITPULSE_SSR: join(PACKAGE, "ssr"),
    BITPULSE_STORIES: join(SPOOL, "jobs", String(job.id), "stories"),
    BITPULSE_MEDIA_CACHE: MEDIA_CACHE,
  });
  run(join(PACKAGE, "node_modules", ".bin", "pagefind"), ["--site", target, "--silent"], {});
  return target;
}

// --- Checks ---

function htmlCount(root: string): number {
  return readdirSync(root, { recursive: true, encoding: "utf8" }).filter((file) => file.endsWith(".html")).length;
}

// Permissions are set here because nginx reads these files as another user.
function verifyFiles(job: Job, target: string): void {
  for (const file of REQUIRED_FILES) {
    if (!existsSync(join(target, file))) throw new Error(`missing file: ${file}`);
  }
  for (const path of job.paths) {
    if (!existsSync(join(target, path, "index.html"))) throw new Error(`missing page: ${path}`);
  }
  for (const entry of readdirSync(target, { recursive: true, encoding: "utf8" })) {
    const path = join(target, entry);
    const stat = lstatSync(path);
    if (stat.isSymbolicLink()) throw new Error(`link in release: ${entry}`);
    chmodSync(path, stat.isDirectory() ? 0o755 : 0o644);
  }
  chmodSync(target, 0o755);

  const current = link("current");
  if (current) {
    const before = htmlCount(join(RELEASES, current));
    const after = htmlCount(target);
    if (after < before * MIN_PAGE_SHARE) throw new Error(`release has ${after} pages, live site has ${before}`);
  }
}

function fetchLocal(path: string): Promise<Response> {
  const get = CHECK_BASE.protocol === "https:" ? httpsGet : httpGet;
  const options = { host: CHECK_BASE.hostname, port: CHECK_BASE.port, path, servername: SITE_HOST, headers: { Host: SITE_HOST } };
  return new Promise((resolve, reject) => {
    // A silent nginx counts as a failed check, otherwise the job would wait with a new release live.
    const request = get(options, (response) => {
      const chunks: Buffer[] = [];
      response.on("data", (chunk: Buffer) => chunks.push(chunk));
      response.on("end", () => resolve({ status: response.statusCode ?? 0, body: Buffer.concat(chunks).toString("utf8") }));
    });
    request.setTimeout(CHECK_TIMEOUT_MS, () => request.destroy(new Error(`${path} timed out`)));
    request.on("error", reject);
  });
}

// The cover image is checked on top of the pages, because a page can load fine with a broken image.
async function verifyLive(job: Job): Promise<void> {
  for (const path of [...COMMON_PATHS, ...job.paths]) {
    const { status } = await fetchLocal(path);
    if (status !== 200) throw new Error(`${path} answered ${status}`);
  }
  if (job.paths.length === 0) return;
  const { body } = await fetchLocal(job.paths[0]);
  const image = /<meta property="og:image" content="https?:\/\/[^/]+([^"]+)"/.exec(body)?.[1];
  if (!image) throw new Error("story page has no cover image tag");
  const { status } = await fetchLocal(image);
  if (status !== 200) throw new Error(`cover image answered ${status}`);
}

// --- Jobs ---

async function runJob(job: Job, name: string): Promise<void> {
  const target = build(job, name);
  verifyFiles(job, target);
  if (!job.goLive) return;

  const current = link("current");
  const previous = link("previous");
  if (current) point("previous", current);
  point("current", name);
  try {
    await verifyLive(job);
  } catch (error) {
    if (current) point("current", current);
    if (previous) point("previous", previous);
    throw error;
  }
  prune();
}

// The answer is renamed into place, the API can never read half of it.
function answer(id: number, result: object): void {
  const partial = join(SPOOL, "results", `.${id}.json`);
  writeFileSync(partial, JSON.stringify(result));
  renameSync(partial, join(SPOOL, "results", `${id}.json`));
}

async function handle(id: number): Promise<void> {
  const started = Date.now();
  const job = JSON.parse(readFileSync(join(SPOOL, "jobs", String(id), "job.json"), "utf8")) as Job;
  const name = releaseName(job);
  try {
    await runJob(job, name);
    answer(id, { id, ok: true, release: name, ms: Date.now() - started });
    console.log(`job ${id}: ${name} in ${Date.now() - started} ms`);
  } catch (error) {
    rmSync(join(RELEASES, name), { recursive: true, force: true });
    const message = error instanceof Error ? error.message : String(error);
    answer(id, { id, ok: false, error: message, ms: Date.now() - started });
    console.error(`job ${id} failed: ${message}`);
  }
}

// Names that start with a dot are still being written by the API.
function waiting(): number[] {
  return readdirSync(join(SPOOL, "queue"))
    .filter((name) => /^\d+$/.test(name))
    .map(Number)
    .sort((a, b) => a - b);
}

function rollback(): void {
  const current = link("current");
  const previous = link("previous");
  if (!current || !previous) throw new Error("no previous release");
  point("current", previous);
  point("previous", current);
  console.log(`live release: ${previous}`);
}

// --- Start ---

if (process.argv[2] === "rollback") {
  rollback();
} else {
  mkdirSync(RELEASES, { recursive: true });
  for (let jobs = waiting(); jobs.length > 0; jobs = waiting()) {
    await handle(jobs[0]);
    rmSync(join(SPOOL, "queue", String(jobs[0])), { force: true });
  }
}
