/**
 * file: playwright.config.ts
 * importable: default Playwright config, read by the playwright command
 *
 * Tests run the built panel against the real API, so npm run build has to come first. Setting
 * CHROME_PATH uses an already installed browser instead of the one Playwright downloads.
 *
 * description: Browser test settings for the admin panel.
 */

import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { defineConfig } from "@playwright/test";

const WEB_PORT = 4320;
const API_PORT = 4321;
// Passkeys need localhost or HTTPS, an address written as numbers is refused by the browser.
const ORIGIN = `http://localhost:${WEB_PORT}`;
// The workers inherit the variable, so only the first process makes the folder and removes it.
if (!process.env.BITPULSE_TEST_DIR) {
  const made = mkdtempSync(join(tmpdir(), "bitpulse-admin-"));
  process.env.BITPULSE_TEST_DIR = made;
  process.once("exit", () => rmSync(made, { recursive: true, force: true }));
}
const WORK = process.env.BITPULSE_TEST_DIR;

export default defineConfig({
  testDir: "tests",
  reporter: "line",
  timeout: 60_000,
  use: {
    baseURL: ORIGIN,
    launchOptions: { executablePath: process.env.CHROME_PATH },
  },
  webServer: [
    {
      command: `uv run --locked --project ../api python tests/serve_api.py ${WORK} ${ORIGIN} ${API_PORT}`,
      port: API_PORT,
      reuseExistingServer: false,
    },
    {
      command: `npx vite preview --port ${WEB_PORT} --strictPort --host localhost`,
      url: ORIGIN,
      env: { BITPULSE_API_PORT: String(API_PORT) },
      reuseExistingServer: false,
    },
  ],
});
