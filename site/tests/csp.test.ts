/**
 * file: tests/csp.test.ts
 * importable: nothing, the test runner loads this file
 *
 * description: Checks that the content security policy allows the inline theme script.
 */

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { expect, it } from "vitest";
import { THEME_SCRIPT } from "../src/Document";

// A changed theme script would be blocked in every browser while all other tests still pass.
it("allows the inline theme script by its hash", () => {
  const hash = createHash("sha256").update(THEME_SCRIPT).digest("base64");
  expect(readFileSync("deploy/csp.conf", "utf8")).toContain(`'sha256-${hash}'`);
});
