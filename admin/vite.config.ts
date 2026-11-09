/**
 * file: vite.config.ts
 * importable: default Vite config, read by the vite command
 *
 * description: Build settings of the admin panel and the local route to the API.
 */

// NOTE: The API has its own port in a local run. On the server nginx sends /panel-api to the API.

import { readFileSync } from "node:fs";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const proxy = { "/panel-api": `http://127.0.0.1:${process.env.BITPULSE_API_PORT ?? 8010}` };

// The browser tests run under the same policy the server sends, so a block shows up there first.
const policy = /Content-Security-Policy "([^"]+)"/.exec(readFileSync("deploy/security-headers.conf", "utf8"))![1];

export default defineConfig({
  plugins: [react()],
  server: { proxy, fs: { allow: [".."] } },
  preview: { proxy, headers: { "Content-Security-Policy": policy, "Access-Control-Allow-Origin": "*" } },
  build: { assetsInlineLimit: 0 },
});
