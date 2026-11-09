/**
 * file: tests/panel.spec.ts
 * importable: nothing, playwright loads it
 *
 * description: Follows the panel from the first passkey to publishing and withdrawing a story.
 */

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { expect, test, type Page } from "@playwright/test";

const WORK = process.env.BITPULSE_TEST_DIR!;
const PASSWORD = "a long enough password";

test.describe.configure({ mode: "serial" });

let page: Page;
const blocked: string[] = [];

test.beforeAll(async ({ browser }) => {
  page = await browser.newPage({ viewport: { width: 1360, height: 900 } });
  page.on("console", (message) => {
    if (message.type() === "error" && /Content Security Policy|violates/.test(message.text())) blocked.push(message.text());
  });
  const client = await page.context().newCDPSession(page);
  await client.send("WebAuthn.enable");
  await client.send("WebAuthn.addVirtualAuthenticator", {
    options: { protocol: "ctap2", transport: "internal", hasResidentKey: true, hasUserVerification: true, isUserVerified: true, automaticPresenceSimulation: true },
  });
});

async function signIn() {
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Use passkey" }).click();
  await expect(page.getByRole("heading", { name: "Stories", level: 1 })).toBeVisible();
}

async function fillStory() {
  await page.getByLabel("Headline").fill("A Sample Headline");
  await page.getByLabel("Summary").fill("A summary of the sample.");
  await page.getByLabel("Address", { exact: true }).fill("sample-story");
  await page.getByLabel("Story", { exact: true }).fill('First paragraph.\n\n<img src=x id="injected"><script>document.title="owned"</script>');
  await page.getByLabel(/Sources/).fill("A Source  https://example.com/a");
  await page.getByLabel(/Alt text/).fill("Alt text");
  await page.getByLabel("Credit").fill("Someone");
  await page.getByLabel("License", { exact: true }).fill("CC0");
  await page.getByLabel("License address").fill("https://example.com/license");
  await page.getByLabel("Image source").fill("https://example.com/image");
  await page.getByRole("button", { name: "Turkish" }).click();
  await page.getByLabel("Headline").fill("Örnek başlık");
  await page.getByLabel("Summary").fill("Örnek özet.");
  await page.getByLabel("Address", { exact: true }).fill("ornek-haber");
  await page.getByLabel("Story", { exact: true }).fill("İlk paragraf.");
  await page.getByLabel(/Sources/).fill("Bir Kaynak  https://example.com/a");
  await page.getByLabel(/Alt text/).fill("Alt metin");
  await page.getByRole("button", { name: "English" }).click();
}

async function confirmWithPasskey() {
  await page.getByRole("dialog").getByRole("button", { name: "Use passkey" }).click();
}

test("registers the first passkey with the one time link", async () => {
  const token = readFileSync(join(WORK, "enrol.txt"), "utf8");
  await page.goto(`/#enrol=${token}`);
  await page.getByRole("button", { name: "Create passkey" }).click();
  await expect(page.getByRole("heading", { name: "Passkey registered" })).toBeVisible();
  expect(page.url()).not.toContain(token);
});

test("the wrong password does not open the panel", async () => {
  await page.goto("/");
  await page.reload();
  await page.getByLabel("Password").fill("this is not the password");
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("alert")).toHaveText("That did not work.");
});

test("signs in with password and passkey", async () => {
  await signIn();
  await expect(page.getByText("No release yet.")).toBeVisible();
});

test("a page reload keeps the session and can still change things", async () => {
  await page.reload();
  await expect(page.getByRole("heading", { name: "Stories", level: 1 })).toBeVisible();
  await page.goto("/#edit/new");
  await page.getByRole("button", { name: "Save draft" }).click();
  await expect(page.getByRole("status")).toHaveText("Add a cover image first.");
});

test("saves a draft in both languages", async () => {
  await fillStory();
  await page.getByLabel("Replace image").setInputFiles(join(WORK, "cover.jpg"));
  await expect(page.locator(".editor__side .photo img")).toBeVisible();
  await page.getByRole("button", { name: "Save draft" }).click();
  await expect(page).toHaveURL(/#edit\/sample-story$/);
  await expect(page.getByLabel("Headline")).toHaveValue("A Sample Headline");
});

test("the preview uses the site design and drops raw HTML", async () => {
  await page.getByRole("button", { name: "Preview" }).click();
  const frame = page.frameLocator("iframe.preview-frame");
  await expect(frame.locator("h1")).toHaveText("A Sample Headline");
  await expect(frame.locator("h1")).toHaveCSS("font-stretch", "75%");
  await expect(frame.locator(".photo img")).toBeVisible();
  await expect(frame.locator("#injected")).toHaveCount(0);
  await expect(frame.locator("script")).toHaveCount(0);
  await expect(page).toHaveTitle("Bitpulse Editor");
  await page.getByRole("button", { name: "Write" }).click();
});

test("cancelling the confirmation publishes nothing", async () => {
  await page.getByRole("button", { name: "Publish", exact: true }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Cancel" }).click();
  await page.goto("/#stories");
  await expect(page.locator(".story-row", { hasText: "A Sample Headline" }).locator(".story-row__state")).toHaveText("Draft");
});

test("publishes after a passkey", async () => {
  await page.locator(".story-row").first().click();
  await page.getByRole("button", { name: "Publish", exact: true }).click();
  await confirmWithPasskey();
  await expect(page.getByRole("dialog").getByText("release-test")).toBeVisible();
  await page.getByRole("dialog").getByRole("button", { name: "Close" }).click();
  await expect(page.getByRole("button", { name: "Publish update" })).toBeVisible();
});

test("withdraws after a passkey", async () => {
  await page.getByRole("button", { name: "Withdraw" }).click();
  await confirmWithPasskey();
  await expect(page.getByRole("dialog").getByRole("heading", { name: "Done" })).toBeVisible();
  await page.getByRole("dialog").getByRole("button", { name: "Close" }).click();
  await page.goto("/#stories");
  await expect(page.locator(".story-row", { hasText: "A Sample Headline" }).locator(".story-row__state")).toHaveText("Withdrawn");
});

test("creates a device key and shows it once", async () => {
  await page.goto("/#access");
  await page.getByLabel("Device name").fill("second-device");
  await page.getByRole("button", { name: "New device key" }).click();
  await confirmWithPasskey();
  await expect(page.getByRole("dialog").getByText("Copy this key now")).toBeVisible();
  await page.getByRole("dialog").getByRole("button", { name: "Done" }).click();
  await expect(page.locator(".key-row").last()).toContainText("Active");
});

test("the audit log records the work", async () => {
  await page.goto("/#audit");
  for (const action of ["login.ok", "publish.request", "withdraw.request", "key.create"]) {
    await expect(page.locator(".audit-row", { hasText: action }).first()).toBeVisible();
  }
});

test("the radar shows what was sent", async () => {
  await page.goto("/#radar");
  await expect(page.getByRole("heading", { name: "Radar", level: 1 })).toBeVisible();
  await expect(page.locator(".event-row")).toHaveCount(1);
  await expect(page.locator(".event-row__title")).toHaveText("A candidate sent to Telegram");
});

test("the left out list opens with the scored events in pages", async () => {
  await page.getByRole("link", { name: "Left out" }).click();
  await expect(page.locator(".event-row")).toHaveCount(50);
  await expect(page.getByRole("button", { name: "Scored 121" })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByText("Never read by the model")).toHaveCount(0);
  await page.getByRole("button", { name: "Next fifty" }).click();
  await expect(page.locator(".event-row")).toHaveCount(100);
  await page.getByRole("button", { name: /^Not read/ }).click();
  await expect(page.locator(".event-row__title")).toHaveText("Never read by the model");
});

test("a headline from the web stays plain text", async () => {
  await page.getByRole("button", { name: /^Passed the bar/ }).click();
  await expect(page.locator(".event-row__title")).toContainText("<img src=x");
  await expect(page.locator("#injected-title")).toHaveCount(0);
});

test("search narrows the list and a row keeps its size", async () => {
  await page.getByRole("button", { name: /^Below the bar/ }).click();
  await page.getByLabel("Headline").fill("event 77");
  await expect(page.locator(".event-row")).toHaveCount(1);
  await page.getByLabel("Headline").fill("");
  await expect(page.locator(".event-row")).toHaveCount(50);
});

test("do on a left out event asks the radar for a brief", async () => {
  await page.getByRole("button", { name: /^Passed the bar/ }).click();
  await page.locator(".event-row__head").first().click();
  await expect(page.getByRole("link", { name: "The article" })).toHaveAttribute("rel", "noopener noreferrer");
  await expect(page.getByRole("button", { name: "Skip" })).toHaveCount(0);
  await page.getByRole("button", { name: "Do", exact: true }).click();
  await expect(page.getByText("The radar is writing the brief.")).toBeVisible();
  await expect(page.locator(".event-row__state")).toHaveText("Do");
  await page.getByRole("link", { name: "Candidates" }).click();
  await expect(page.locator(".event-row")).toHaveCount(2);
});

test("a link waits for the radar", async () => {
  await page.getByRole("link", { name: "Add link" }).click();
  await page.getByLabel("Address").fill("https://example.com/news");
  await page.getByRole("button", { name: "Add" }).click();
  await expect(page.getByText("Waiting for the radar")).toBeVisible();
});

test("the social page shows a post ready to share", async () => {
  await page.goto("/#social");
  await expect(page.getByRole("heading", { name: "A Shared Sample" })).toBeVisible();
  await expect(page.getByText("The X post")).toBeVisible();
  const image = page.locator(".social-post__page");
  await expect.poll(() => image.evaluate((node: HTMLImageElement) => node.naturalWidth)).toBe(1080);
  await page.getByRole("button", { name: "Mark as shared" }).click();
  await expect(page.getByText("Nothing here.")).toBeVisible();
  await page.getByRole("button", { name: "Shared", exact: true }).click();
  await expect(page.getByRole("heading", { name: "A Shared Sample" })).toBeVisible();
});

test("the new pages fit a phone", async () => {
  await page.setViewportSize({ width: 390, height: 800 });
  for (const address of ["/#radar/eliminated", "/#social"]) {
    await page.goto(address);
    await page.waitForTimeout(300);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    const last = await page.getByRole("link", { name: "Access" }).boundingBox();
    expect(last!.x + last!.width).toBeLessThanOrEqual(390);
  }
  await page.setViewportSize({ width: 1360, height: 900 });
});

test("signing out ends the session", async () => {
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page.getByRole("heading", { name: "Editor sign in" })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("heading", { name: "Editor sign in" })).toBeVisible();
});

test("a backup code signs in once", async () => {
  const code = readFileSync(join(WORK, "code.txt"), "utf8");
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Use a backup code" }).click();
  await page.getByLabel("Code").fill(code);
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("heading", { name: "Stories", level: 1 })).toBeVisible();
});

test("the browser blocked nothing under the real policy", async () => {
  expect(blocked).toEqual([]);
});
