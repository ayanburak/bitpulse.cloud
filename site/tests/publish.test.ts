/**
 * file: tests/publish.test.ts
 * importable: nothing, vitest loads it
 *
 * description: Runs the real publishing worker on a small site and checks what reaches the live link.
 */

// NOTE: The worker is run as its own process, the same way systemd starts it. A plain local server
// plays the part of nginx, and it can be told to fail after a release goes live.

import { execFile, spawnSync } from "node:child_process";
import { cpSync, existsSync, mkdirSync, mkdtempSync, readFileSync, readlinkSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { createServer, type Server } from "node:http";
import type { AddressInfo } from "node:net";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { promisify } from "node:util";
import sharp from "sharp";
import { afterAll, beforeAll, beforeEach, describe, expect, it } from "vitest";

const run = promisify(execFile);
const SITE = resolve(".");
let root: string;
let pack: string;
let spool: string;
let releases: string;
let server: Server;
let port: number;
let failLive = false;
let image: Buffer;

function storyFile(slug: string): string {
  return `---
slug: ${slug}
title: "A Sample Story"
summary: "A summary of the sample."
category: world
date: 2026-01-01
time: "09:00"
kind: news
sources:
  - name: "A source"
    url: https://example.com/a
image:
  file: image.jpg
  alt: "Alt text"
  credit: "Someone"
  license: "CC0"
  licenseUrl: https://example.com/license
  source: https://example.com/image
---

Body text of the sample.
`;
}

function queueJob(id: number, en: string, tr: string, goLive = true): void {
  const stories = join(spool, "jobs", String(id), "stories", "2026-01-01-sample");
  mkdirSync(stories, { recursive: true });
  writeFileSync(join(stories, "en.md"), en);
  writeFileSync(join(stories, "tr.md"), tr);
  writeFileSync(join(stories, "image.jpg"), image);
  const paths = ["/en/stories/sample-en/", "/tr/stories/sample-tr/"];
  writeFileSync(join(spool, "jobs", String(id), "job.json"), JSON.stringify({ id, paths, goLive }));
  writeFileSync(join(spool, "queue", String(id)), "");
}

// The worker must run asynchronously here. A blocking spawn would freeze this process, and the
// stand-in for nginx lives in this process and could never answer the live check.
async function runWorker(...args: string[]): Promise<void> {
  const env = {
    ...process.env,
    BITPULSE_SPOOL: spool,
    BITPULSE_RELEASES: releases,
    BITPULSE_MEDIA_CACHE: join(root, "cache"),
    BITPULSE_CHECK_BASE: `http://127.0.0.1:${port}`,
  };
  await run(process.execPath, ["scripts/publish.ts", ...args], { cwd: pack, env, timeout: 50_000 });
}

function result(id: number): { ok: boolean; release?: string; error?: string } {
  return JSON.parse(readFileSync(join(spool, "results", `${id}.json`), "utf8"));
}

const live = (): string => readlinkSync(join(releases, "current"));

beforeAll(async () => {
  root = mkdtempSync(join(tmpdir(), "bitpulse-worker-"));
  pack = join(root, "package");
  mkdirSync(join(pack, "scripts"), { recursive: true });
  for (const name of ["prerender.ts", "publish.ts"]) cpSync(join(SITE, "scripts", name), join(pack, "scripts", name));
  symlinkSync(join(SITE, "node_modules"), join(pack, "node_modules"));
  writeFileSync(join(pack, "package.json"), '{"type":"module"}');
  const vite = join(SITE, "node_modules", ".bin", "vite");
  const options = { cwd: SITE, encoding: "utf8" as const };
  expect(spawnSync(vite, ["build", "--outDir", join(pack, "template"), "--logLevel", "error"], options).status).toBe(0);
  expect(spawnSync(vite, ["build", "--ssr", "src/render.tsx", "--outDir", join(pack, "ssr"), "--logLevel", "error"], options).status).toBe(0);
  image = await sharp({ create: { width: 1400, height: 800, channels: 3, background: "#336699" } }).jpeg().toBuffer();

  server = createServer((request, response) => {
    const url = (request.url ?? "/").split("?")[0];
    const file = join(releases, "current", url.endsWith("/") ? `${url}index.html` : url);
    response.statusCode = !failLive && existsSync(file) ? 200 : 503;
    response.end(response.statusCode === 200 ? readFileSync(file) : "");
  });
  await new Promise<void>((done) => server.listen(0, "127.0.0.1", done));
  port = (server.address() as AddressInfo).port;
}, 60_000);

afterAll(() => {
  server.close();
  rmSync(root, { recursive: true, force: true });
});

beforeEach(() => {
  failLive = false;
  spool = mkdtempSync(join(root, "spool-"));
  releases = mkdtempSync(join(root, "releases-"));
  for (const name of ["jobs", "queue", "results"]) mkdirSync(join(spool, name));
});

describe("publishing worker", () => {
  it("makes a valid release live and clears the queue", async () => {
    queueJob(1, storyFile("sample-en"), storyFile("sample-tr"));
    await runWorker();
    expect(result(1).ok).toBe(true);
    expect(live()).toBe(result(1).release);
    expect(existsSync(join(releases, live(), "en/stories/sample-en/index.html"))).toBe(true);
    expect(existsSync(join(releases, live(), "media/2026-01-01-sample-640.jpg"))).toBe(true);
    expect(existsSync(join(releases, live(), "pagefind/pagefind.js"))).toBe(true);
    expect(existsSync(join(spool, "queue", "1"))).toBe(false);
  }, 60_000);

  it("leaves the live site alone when a story is invalid", async () => {
    queueJob(1, storyFile("sample-en"), storyFile("sample-tr"));
    await runWorker();
    const before = live();
    queueJob(2, "no frontmatter here", storyFile("sample-tr"));
    await runWorker();
    expect(result(2).ok).toBe(false);
    expect(live()).toBe(before);
  }, 60_000);

  it("goes back to the old release when the live check fails", async () => {
    queueJob(1, storyFile("sample-en"), storyFile("sample-tr"));
    await runWorker();
    const before = live();
    failLive = true;
    queueJob(2, storyFile("sample-en"), storyFile("sample-tr"));
    await runWorker();
    expect(result(2).ok).toBe(false);
    expect(result(2).error).toContain("503");
    expect(live()).toBe(before);
  }, 60_000);

  it("builds without going live when asked to", async () => {
    queueJob(1, storyFile("sample-en"), storyFile("sample-tr"));
    await runWorker();
    const before = live();
    queueJob(2, storyFile("sample-en"), storyFile("sample-tr"), false);
    await runWorker();
    expect(result(2).ok).toBe(true);
    expect(live()).toBe(before);
    expect(existsSync(join(releases, result(2).release ?? ""))).toBe(true);
  }, 60_000);

  it("rolls back to the previous release on request", async () => {
    queueJob(1, storyFile("sample-en"), storyFile("sample-tr"));
    await runWorker();
    const first = live();
    await new Promise((done) => setTimeout(done, 1100));
    queueJob(2, storyFile("sample-en"), storyFile("sample-tr"));
    await runWorker();
    expect(live()).not.toBe(first);
    await runWorker("rollback");
    expect(live()).toBe(first);
  }, 60_000);
});
