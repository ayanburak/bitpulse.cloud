// Draws reels/assets/brand.png, the bitpulse logo of the top left corner, from the same CSS as the
// Instagram page in the site repository, so the reel and the post show the very same logo.
// It runs with the site's Playwright and is only needed again when the site logo changes:
//
//   NODE_PATH=../site/node_modules node tools/brand.cjs
//
// The picture is drawn at SCALE times its size, so the closing card can show it large and sharp.
// It has PAD pixels of clear space on every side for its shadow, counted before the scale.
// reels/style.py places it PAD pixels up and left of where the logo itself sits.

const { chromium } = require("@playwright/test");
const path = require("node:path");
const fs = require("node:fs");

const FONTS = path.join(__dirname, "..", "..", "site", "public", "fonts");
const OUT = path.join(__dirname, "..", "reels", "assets", "brand.png");
const PAD = 20;
const SCALE = 3;

// The font goes into the page itself. A page opened with setContent has no address, and the
// browser refuses it a font from a file address and quietly draws a serif instead.
const FONT = fs.readFileSync(path.join(FONTS, "archivo-latin.woff2")).toString("base64");

// The shadow keeps the white letters readable over bright footage. The page itself uses a dark
// fade at the top of the photo for the same reason, a reel has no fixed photo to shade.
const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><style>
@font-face { font-family: Archivo; src: url(data:font/woff2;base64,${FONT}) format("woff2"); font-weight: 100 900; font-stretch: 62% 125%; }
* { margin: 0; padding: 0; }
html, body { background: transparent; }
.wrap { display: inline-block; padding: ${PAD}px; }
.logo { display: flex; align-items: center; gap: 14px; font-family: Archivo; font-size: 44px; font-weight: 780; letter-spacing: -.035em; line-height: 1; color: #f3f4f0; filter: drop-shadow(0 2px 8px rgba(0,0,0,.5)); }
.logo svg { width: 46px; height: 46px; }
</style></head><body><div class="wrap"><div class="logo">
<svg viewBox="0 0 32 32"><rect width="32" height="32" fill="#1430d6"/><path fill="#f3f4f0" fill-rule="evenodd" d="M6 3h8v8h12v18H6zM14 17v6h4v-6z"/></svg>bitpulse
</div></div></body></html>`;

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH });
  const page = await browser.newPage({ deviceScaleFactor: SCALE });
  await page.setContent(html);
  const loaded = await page.evaluate(async () => { await document.fonts.ready; return document.fonts.check("780 44px Archivo"); });
  if (!loaded) throw new Error("Archivo did not load, the logo would be drawn in another font");
  await page.locator(".wrap").screenshot({ path: OUT, omitBackground: true });
  await browser.close();
  console.log(OUT);
})();
