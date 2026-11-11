/**
 * file: tests/clip.test.ts
 * importable: nothing, the test runner loads this file
 *
 * description: Checks the rules of clip.yaml, the file behind a post that goes to Instagram only.
 */

import { describe, expect, it } from "vitest";
import { buildClip } from "../src/social";

const BASE = {
  source: "https://www.youtube.com/shorts/example",
  credit: "A Channel",
  text: "Turkey held a moment of silence at 9:05.",
  caption: "Sirens sounded across Turkey at 9:05 on Tuesday.",
  start: 22,
};

function yaml(fields: Record<string, unknown>): string {
  return Object.entries(fields).filter(([, value]) => value !== undefined).map(([key, value]) => `${key}: ${JSON.stringify(value)}`).join("\n");
}

describe("buildClip", () => {
  it("adds the source line and keeps the cut", () => {
    const clip = buildClip(yaml(BASE), "clip");
    expect(clip.caption.endsWith("\n\nSource: A Channel, https://www.youtube.com/shorts/example")).toBe(true);
    expect([clip.start, clip.end, clip.position]).toEqual([22, null, "50% 50%"]);
  });

  it.each([
    [{ ...BASE, text: "x".repeat(71) }, "limit is 70"],
    [{ ...BASE, caption: "A caption — with a dash." }, "dash"],
    [{ ...BASE, source: "not an address" }, "invalid source"],
    [{ ...BASE, end: 10 }, "end must come after start"],
    [{ ...BASE, start: "soon" }, "number of seconds"],
    [{ ...BASE, pages: [] }, "unknown field"],
    [{ ...BASE, credit: undefined }, "missing credit"],
  ])("refuses a broken file %#", (fields, message) => {
    expect(() => buildClip(yaml(fields), "clip")).toThrow(message);
  });
});
