/**
 * file: playwright.config.ts
 * importable: default Playwright config, read by the playwright command
 *
 * Tests run against the finished dist folder, so npm run build has to come first. Setting
 * CHROME_PATH uses an already installed browser instead of the one Playwright downloads.
 *
 * description: Browser test settings for the built site.
 */

import { defineConfig } from "@playwright/test";

const PORT = 4300;

export default defineConfig({
  testDir: "tests/e2e",
  fullyParallel: true,
  reporter: "line",
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    launchOptions: { executablePath: process.env.CHROME_PATH },
  },
  webServer: {
    command: `node scripts/serve.ts ${PORT}`,
    url: `http://127.0.0.1:${PORT}/en/`,
    reuseExistingServer: false,
  },
});
