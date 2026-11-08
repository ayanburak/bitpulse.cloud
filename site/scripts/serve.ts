/**
 * file: scripts/serve.ts
 * importable: nothing, run with npm run preview
 *
 * Takes an optional port as its only argument.
 *
 * description: Serves dist the way the live nginx setup does, for previews and browser tests.
 */

import { createReadStream, statSync } from "node:fs";
import { createServer } from "node:http";
import { extname, join, normalize } from "node:path";

// --- Constants ---

const ROOT = "dist";
const PORT = Number(process.argv[2] ?? 4173);
const HOST = "127.0.0.1";

const TYPES: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css",
  ".js": "text/javascript",
  ".mjs": "text/javascript",
  ".json": "application/json",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".woff2": "font/woff2",
  ".wasm": "application/wasm",
  ".xml": "application/xml",
  ".txt": "text/plain; charset=utf-8",
};

// --- Lookup ---

// Follows the nginx try_files order: the file itself, then the index file of a folder.
function resolveFile(address: string): string | null {
  const path = join(ROOT, normalize(decodeURIComponent(address)));
  if (!path.startsWith(ROOT)) return null;
  for (const candidate of [path, join(path, "index.html")]) {
    if (statSync(candidate, { throwIfNoEntry: false })?.isFile()) return candidate;
  }
  return null;
}

// --- Server ---

createServer((request, response) => {
  const address = (request.url ?? "/").split("?")[0];
  const file = resolveFile(address);
  const language = address.startsWith("/tr/") ? "tr/" : "en/";
  response.writeHead(file ? 200 : 404, {
    "Content-Type": TYPES[extname(file ?? ".html")] ?? "application/octet-stream",
  });
  createReadStream(file ?? join(ROOT, language, "404.html")).pipe(response);
}).listen(PORT, HOST, () => console.log(`Serving ${ROOT} at http://${HOST}:${PORT}`));
