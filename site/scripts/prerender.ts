/**
 * file: scripts/prerender.ts
 * importable: nothing, the build command runs this file directly
 *
 * Expects the client build in dist and the server bundle in .ssr. Both come from the
 * earlier steps of npm run build.
 *
 * description: Writes every page, resized story image, feed, the sitemap and robots.txt into dist.
 */

import { createHash } from "node:crypto";
import { copyFileSync, existsSync, mkdirSync, readFileSync, renameSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
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

interface SitemapEntry {
  path: string;
  lastmod?: string;
  alternates: { hreflang: string; path: string }[];
}

interface NewsEntry {
  path: string;
  lang: string;
  title: string;
  published: string;
}

interface RenderModule {
  stories: Story[];
  listPagePaths(): string[];
  sitemapEntries(): SitemapEntry[];
  newsEntries(): NewsEntry[];
  escapeXml(text: string): string;
  renderPage(path: string, assets: Assets): string;
  renderFeed(lang: string): string;
}

// --- Constants ---

// The defaults fit npm run build. The publishing worker sets all four for its own folders.
const OUT = process.env.BITPULSE_OUT ?? "dist";
const SSR = process.env.BITPULSE_SSR ?? ".ssr";
const CONTENT = process.env.BITPULSE_STORIES ?? join("src", "content", "stories");
const MEDIA_CACHE = process.env.BITPULSE_MEDIA_CACHE;
const ENTRY = "src/client/main.ts";
const MANIFEST = join(OUT, ".vite", "manifest.json");
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

async function resizeImage(source: string, width: number, target: string): Promise<void> {
  await sharp(source)
    .resize({ width, withoutEnlargement: true })
    .jpeg({ quality: IMAGE_QUALITY, mozjpeg: true })
    .toFile(target);
}

// Resizing is nearly all of the build time, and a published image rarely changes. On the server each
// copy is kept under the hash of its source, so a new publish only resizes the new picture. The
// finished copy is renamed into the cache, an interrupted job can not leave half a picture there.
async function cachedImage(source: string, sourceHash: string, width: number, target: string): Promise<void> {
  if (!MEDIA_CACHE) return resizeImage(source, width, target);
  const cached = join(MEDIA_CACHE, `${sourceHash}-${width}-q${IMAGE_QUALITY}.jpg`);
  if (!existsSync(cached)) {
    const partial = `${cached}.part.jpg`;
    await resizeImage(source, width, partial);
    renameSync(partial, cached);
  }
  copyFileSync(cached, target);
}

// Smaller copies keep a card thumbnail from downloading the full size image.
async function writeImages(stories: Story[]): Promise<void> {
  mkdirSync(join(OUT, "media"), { recursive: true });
  if (MEDIA_CACHE) mkdirSync(MEDIA_CACHE, { recursive: true });
  for (const story of stories) {
    const source = join(CONTENT, story.key, story.versions.en.image.file);
    const hash = createHash("sha256").update(readFileSync(source)).digest("hex");
    for (const width of IMAGE_WIDTHS) {
      await cachedImage(source, hash, width, join(OUT, "media", `${story.key}-${width}.jpg`));
    }
  }
}

// Error pages and the search page are left out, neither is useful as a search engine result.
// Only story pages get a lastmod date, because no other page has a date of its own.
function writeSitemap(entries: SitemapEntry[]): void {
  const urls = entries
    .map((entry) => {
      const lastmod = entry.lastmod ? `<lastmod>${entry.lastmod}</lastmod>` : "";
      const links = entry.alternates
        .map((link) => `<xhtml:link rel="alternate" hreflang="${link.hreflang}" href="${SITE_URL}${link.path}"/>`)
        .join("");
      return `<url><loc>${SITE_URL}${entry.path}</loc>${lastmod}${links}</url>`;
    })
    .join("");
  writeFileSync(
    join(OUT, "sitemap.xml"),
    `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">${urls}</urlset>\n`,
  );
  writeFileSync(join(OUT, "robots.txt"), `User-agent: *\nAllow: /\nSitemap: ${SITE_URL}/sitemap.xml\nSitemap: ${SITE_URL}/news-sitemap.xml\n`);
}

function writeNewsSitemap(entries: NewsEntry[]): void {
  const urls = entries
    .map((entry) => `<url><loc>${SITE_URL}${entry.path}</loc><news:news><news:publication><news:name>Bitpulse</news:name><news:language>${entry.lang}</news:language></news:publication><news:publication_date>${entry.published}</news:publication_date><news:title>${escapeXml(entry.title)}</news:title></news:news></url>`)
    .join("");
  writeFileSync(
    join(OUT, "news-sitemap.xml"),
    `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">${urls}</urlset>\n`,
  );
}

// --- Build ---

const assets = readAssets();
const bundle = pathToFileURL(resolve(SSR, "render.js")).href;
const { stories, listPagePaths, sitemapEntries, newsEntries, escapeXml, renderPage, renderFeed } = (await import(bundle)) as RenderModule;

// The live site must never be built without real content.
if (stories.length === 0) throw new Error("No stories found, refusing to build an empty site");

const paths = listPagePaths();
for (const path of paths) {
  const file = outputFile(path);
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(file, renderPage(path, assets));
}
await writeImages(stories);
writeSitemap(sitemapEntries());
writeNewsSitemap(newsEntries());
for (const lang of ["en", "tr"]) writeFileSync(join(OUT, lang, "feed.xml"), renderFeed(lang));

// The manifest and the server bundle are build tools, neither belongs on the live site.
// The worker keeps its bundle for the next job, so only the plain build removes it.
rmSync(join(OUT, ".vite"), { recursive: true });
if (!process.env.BITPULSE_SSR) rmSync(".ssr", { recursive: true });

console.log(`Wrote ${paths.length} pages and ${stories.length} story images to ${OUT}`);
