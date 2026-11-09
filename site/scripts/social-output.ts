/**
 * file: scripts/social-output.ts
 * importable: replacePost
 *
 * description: Puts a finished social post into its folder and leaves everything else there alone.
 */

// NOTE: The folder of a post is shared. The reels workflow delivers reel.mp4 and reel.txt into it,
// so only the files this script makes are removed. A post that got shorter still loses its old last
// page, because every page matches the pattern.

import { mkdirSync, readdirSync, renameSync, rmSync } from "node:fs";
import { join } from "node:path";

const OWN = /^(x\.txt|caption\.txt|post\.mp4|page-\d+\.png|images)$/;

/**
 * Moves a finished post into the folder of its story.
 *
 * @param draft Side folder that holds every file of the new post. It is gone afterwards.
 * @param out Folder of the story.
 */
export function replacePost(draft: string, out: string): void {
  mkdirSync(out, { recursive: true });
  for (const name of readdirSync(out)) {
    if (OWN.test(name)) rmSync(join(out, name), { recursive: true, force: true });
  }
  for (const name of readdirSync(draft)) renameSync(join(draft, name), join(out, name));
  rmSync(draft, { recursive: true, force: true });
}
