/**
 * file: tests/e2e/site.spec.ts
 * importable: nothing, Playwright loads this file
 *
 * description: Checks the built site the way a reader and a search engine would see it.
 */

import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";
import { expect, test, type Page } from "@playwright/test";

// --- Helpers ---

const DIST = "dist";

// Lists built pages from the disk, so a new page is covered without touching this file.
function builtPages(folder = DIST): string[] {
  return readdirSync(folder).flatMap((name) => {
    const path = join(folder, name);
    if (statSync(path).isDirectory()) return name === "pagefind" ? [] : builtPages(path);
    return name.endsWith(".html") ? [path] : [];
  });
}

function toAddress(file: string): string {
  const address = `/${relative(DIST, file).split(sep).join("/")}`;
  return address.replace(/index\.html$/, "");
}

function storyAddresses(lang: string): string[] {
  return readdirSync(join(DIST, lang, "stories")).map((slug) => `/${lang}/stories/${slug}/`);
}

async function collectErrors(page: Page): Promise<string[]> {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  return errors;
}

// --- Static Checks ---

test("every page links only to pages and files that exist", () => {
  const known = new Set(builtPages().map(toAddress));
  const broken: string[] = [];
  for (const file of builtPages()) {
    const html = readFileSync(file, "utf8");
    for (const [, href] of html.matchAll(/(?:href|src)="(\/[^"#?]*)/g)) {
      const onDisk = statSync(join(DIST, href), { throwIfNoEntry: false });
      if (!known.has(href) && !onDisk) broken.push(`${toAddress(file)} -> ${href}`);
    }
  }
  expect(broken).toEqual([]);
});

test("no placeholder text or form is published", () => {
  for (const file of builtPages()) {
    const html = readFileSync(file, "utf8");
    expect(html, file).not.toMatch(/lorem|ipsum|<form(?! class="search-form")/i);
    expect(html, file).not.toContain("adsbygoogle");
  }
});

test("each story has sources, an image credit and the disclosure", () => {
  for (const lang of ["en", "tr"]) {
    for (const address of storyAddresses(lang)) {
      const html = readFileSync(join(DIST, address, "index.html"), "utf8");
      expect(html, address).toContain('class="key-points"');
      expect(html, address).toMatch(/creativecommons\.org|nasa\.gov\/nasa-brand-center/);
      expect(html, address).toMatch(/artificial intelligence|yapay zekâ/);
    }
  }
});

// --- Reader Checks ---

test("each language points to its counterpart story", async ({ page }) => {
  for (const address of storyAddresses("en")) {
    await page.goto(address);
    const other = await page.locator('.lang-switch a[hreflang="tr"]').getAttribute("href");
    expect(other).toMatch(/^\/tr\/stories\//);
    await page.goto(other as string);
    await expect(page.locator("html")).toHaveAttribute("lang", "tr");
    expect(await page.locator('.lang-switch a[hreflang="en"]').getAttribute("href")).toBe(address);
    expect(await page.locator('link[rel="alternate"][hreflang="en"]').getAttribute("href")).toContain(address);
    expect(await page.locator('link[rel="alternate"][hreflang="x-default"]').getAttribute("href")).toContain(address);
  }
});

test("stories can be read with JavaScript turned off", async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto(storyAddresses("tr")[0]);
  await expect(page.locator("h1")).toBeVisible();
  await expect(page.locator(".story-text .prose").first()).toContainText(/\S{4}/);
  await context.close();
});

test("pages load with no browser errors", async ({ page }) => {
  const errors = await collectErrors(page);
  for (const address of ["/en/", "/tr/", "/en/archive/", "/tr/category/science/", storyAddresses("en")[0]]) {
    await page.goto(address, { waitUntil: "networkidle" });
  }
  expect(errors).toEqual([]);
});

test("search finds a story in the page language", async ({ page }) => {
  await page.goto("/tr/search/?q=Narnia");
  await expect(page.locator(".search-list article")).toHaveCount(1);
  await expect(page.locator(".search-list article h2")).toContainText("Narnia");
  await expect(page.locator(".search-list a")).toHaveAttribute("href", /\/tr\/stories\//);

  await page.fill("#search-input", "zzzzqqqq");
  await expect(page.locator(".search-empty")).toBeVisible();
});

test("the menu pulse rises under the active link", async ({ page }) => {
  await page.goto("/en/category/science/");
  const rail = page.locator(".menu .rail");
  await expect(rail).toHaveAttribute("style", /--y: 9px/);
  await expect(page.locator(".menu a[aria-current]")).toHaveText("Science");
});

test("the language switch stores the reader choice", async ({ page, context }) => {
  await page.goto("/en/");
  await page.locator('.lang-switch a[hreflang="tr"]').click();
  await expect(page).toHaveURL(/\/tr\/$/);
  const cookies = await context.cookies();
  expect(cookies.find((cookie) => cookie.name === "bp_lang")?.value).toBe("tr");
});

test("the page does not scroll sideways on a phone", async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: 360, height: 760 } });
  const page = await context.newPage();
  for (const address of ["/en/", storyAddresses("tr")[0], "/en/archive/", "/tr/about/", "/en/privacy/"]) {
    await page.goto(address);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    expect(overflow, address).toBeLessThanOrEqual(0);
  }
  await context.close();
});

test("the phone menu shows every link and closes again", async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: 320, height: 640 } });
  const page = await context.newPage();
  await page.goto("/en/");
  const panel = page.locator(".drawer__panel");
  const button = page.locator(".drawer summary");

  expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(0);
  await expect(page.locator(".menu .rail a").first()).toBeHidden();
  await expect(panel).toBeHidden();

  await button.click();
  const links = panel.locator("a");
  await expect(links).toHaveCount(7);
  for (const link of await links.all()) await expect(link).toBeInViewport();

  await page.keyboard.press("Escape");
  await expect(panel).toBeHidden();
  await expect(button).toBeFocused();

  await button.click();
  await page.locator("main").click({ position: { x: 10, y: 500 } });
  await expect(panel).toBeHidden();
  await context.close();
});

test("the phone menu is hidden on a wide screen", async ({ page }) => {
  await page.goto("/en/");
  await expect(page.locator(".drawer summary")).toBeHidden();
  await expect(page.locator(".menu .rail a").first()).toBeVisible();
});

test("the theme button switches themes and remembers the choice", async ({ page }) => {
  await page.goto("/en/");
  const root = page.locator("html");
  const button = page.locator("[data-theme-toggle]");
  await expect(root).not.toHaveAttribute("data-theme", "dark");
  await expect(page.locator(".theme-toggle__sun")).toBeVisible();

  await button.click();
  await expect(root).toHaveAttribute("data-theme", "dark");
  await expect(page.locator(".theme-toggle__moon")).toBeVisible();
  await expect(button).toHaveAttribute("aria-label", "Switch to light theme");

  await page.goto("/tr/about/");
  await expect(root).toHaveAttribute("data-theme", "dark");
  await expect(page.locator("[data-theme-toggle]")).toHaveAttribute("aria-label", "Açık temaya geç");
});

test("the theme button is hidden without JavaScript", async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto("/en/");
  await expect(page.locator("[data-theme-toggle]")).toBeHidden();
  await context.close();
});
