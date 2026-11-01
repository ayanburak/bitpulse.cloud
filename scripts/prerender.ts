/**
 * file: scripts/prerender.ts
 * importable: nothing, the build command runs this file directly
 *
 * Expects the client build in dist and the server bundle in .ssr. Both come from the
 * earlier steps of npm run build.
 *
 * description: Writes every page, resized story image, the sitemap and robots.txt into dist.
 */

import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { pathToFileURL } from "node:url";
import sharp from "sharp";

// --- Types ---

interface Assets {
  css: string[];
  js: string[];
}

interface ManifestEntry {
  file: string;
  css?: string[];
}

interface Story {
  key: string;
  versions: { en: { image: { file: string } } };
}

interface RenderModule {
  stories: Story[];
  listPagePaths(): string[];
  renderPage(path: string, assets: Assets): string;
}

// --- Constants ---

const OUT = "dist";
const ENTRY = "src/client/main.ts";
const MANIFEST = join(OUT, ".vite", "manifest.json");
const CONTENT = join("src", "content", "stories");
const SITE_URL = "https://bitpulse.cloud";
const IMAGE_WIDTHS = [640, 1280, 2000];
const IMAGE_QUALITY = 80;

// --- Helpers ---

// Vite puts a content hash in asset names, so real addresses only exist in its manifest.
function readAssets(): Assets {
  const manifest: Record<string, ManifestEntry> = JSON.parse(readFileSync(MANIFEST, "utf8"));
  const entry = manifest[ENTRY];
  if (!entry) throw new Error(`Missing manifest entry: ${ENTRY}`);
  return {
    css: (entry.css ?? []).map((file) => `/${file}`),
    js: [`/${entry.file}`],
  };
}

// An address ending in a slash becomes a folder with index.html, which is what nginx serves.
function outputFile(path: string): string {
  return join(OUT, path.endsWith("/") ? `${path}index.html` : path);
}

// Smaller copies keep a card thumbnail from downloading the full size image.
async function writeImages(stories: Story[]): Promise<void> {
  mkdirSync(join(OUT, "media"), { recursive: true });
  for (const story of stories) {
    const source = join(CONTENT, story.key, story.versions.en.image.file);
    for (const width of IMAGE_WIDTHS) {
      await sharp(source)
        .resize({ width, withoutEnlargement: true })
        .jpeg({ quality: IMAGE_QUALITY, mozjpeg: true })
        .toFile(join(OUT, "media", `${story.key}-${width}.jpg`));
    }
  }
}

// Error pages and the search page are left out, neither is useful as a search engine result.
function writeSitemap(paths: string[]): void {
  const pages = paths.filter((path) => !path.endsWith("404.html") && !path.endsWith("/search/"));
  const urls = pages.map((path) => `<url><loc>${SITE_URL}${path}</loc></url>`).join("");
  writeFileSync(
    join(OUT, "sitemap.xml"),
    `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls}</urlset>\n`,
  );
  writeFileSync(join(OUT, "robots.txt"), `User-agent: *\nAllow: /\nSitemap: ${SITE_URL}/sitemap.xml\n`);
}

// --- Build ---

const assets = readAssets();
const bundle = pathToFileURL(join(".ssr", "render.js")).href;
const { stories, listPagePaths, renderPage } = (await import(bundle)) as RenderModule;

// The live site must never be built without real content.
if (stories.length === 0) throw new Error("No stories found, refusing to build an empty site");

const paths = listPagePaths();
for (const path of paths) {
  const file = outputFile(path);
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(file, renderPage(path, assets));
}
await writeImages(stories);
writeSitemap(paths);

// The manifest and the server bundle are build tools, neither belongs on the live site.
rmSync(join(OUT, ".vite"), { recursive: true });
rmSync(".ssr", { recursive: true });

console.log(`Wrote ${paths.length} pages and ${stories.length} story images to ${OUT}`);
