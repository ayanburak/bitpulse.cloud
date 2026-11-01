/**
 * file: scripts/design-hash.ts
 * importable: nothing, run with npm run design-hash
 *
 * Prints one fingerprint for every locked file. With --check it compares that fingerprint to
 * the EXPECTED_HASH environment variable and exits with an error when they differ.
 *
 * description: Detects changes to the files that need review before a release.
 */

// NOTE: The approved fingerprint lives in a GitHub Actions variable that the automated runs can
// not edit. A changed locked file therefore stops the release, but it does not stop the push.

import { createHash } from "node:crypto";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

// --- Constants ---

// The build settings and the code in src are here because they decide what reaches readers just
// as much as the styles do. stories.ts holds the source and image checks, config.ts the ad switch.
const LOCKED = [
  ".github",
  ".gitignore",
  ".gitleaks.toml",
  ".node-version",
  "LICENSE",
  "LICENSE-CONTENT.md",
  "agents",
  "docs/advertising.md",
  "docs/agent-manual.md",
  "docs/editorial-policy.md",
  "docs/site-decisions.md",
  "docs/style-guide.md",
  "package-lock.json",
  "package.json",
  "playwright.config.ts",
  "public",
  "scripts",
  "src",
  "tests",
  "tsconfig.json",
  "vite.config.ts",
];

// Stories stay open, publishing one must not need a review.
const UNLOCKED = "src/content";

// --- Helpers ---

function listFiles(path: string): string[] {
  if (path === UNLOCKED) return [];
  if (!statSync(path).isDirectory()) return [path];
  return readdirSync(path).flatMap((name) => listFiles(join(path, name)));
}

// Paths are part of the hash, so renaming a file counts as a change too. Sorting keeps the
// result the same on every machine.
function fingerprint(): string {
  const hash = createHash("sha256");
  for (const file of LOCKED.flatMap(listFiles).sort()) {
    hash.update(file);
    hash.update(readFileSync(file));
  }
  return hash.digest("hex");
}

// --- Run ---

const actual = fingerprint();

if (process.argv.includes("--check")) {
  const expected = process.env.EXPECTED_HASH;
  if (actual !== expected) {
    console.error("Locked files changed and are waiting for review.");
    console.error(`Approved: ${expected}`);
    console.error(`Current:  ${actual}`);
    process.exit(1);
  }
  console.log("Locked files match the approved state.");
} else {
  console.log(actual);
}
