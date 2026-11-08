/**
 * file: vite.config.ts
 * importable: default Vite config, read by the vite command
 *
 * description: Build settings and the dev server page renderer for the Bitpulse site.
 */

/// <reference types="vitest/config" />

// NOTE: The site has no index.html for Vite to start from. The client build only bundles the
// browser script and styles, and scripts/prerender.ts writes the HTML files afterwards.

import { readFileSync } from "node:fs";
import { join } from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";

const CLIENT_ENTRY = "src/client/main.ts";

// Renders pages on request during development, so that a change shows up without a full build.
// Addresses with a file extension are left to Vite, except 404.html which is a real page. Story
// images are served at full size here, because resized copies only exist after a build.
function devPages(): Plugin {
  return {
    name: "bitpulse-dev-pages",
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        const path = (req.url ?? "/").split("?")[0];
        const media = /^\/media\/(.+)-\d+\.jpg$/.exec(path);
        if (media) return res.end(readFileSync(join("src/content/stories", media[1], "image.jpg")));
        if (/\.[a-z0-9]+$/i.test(path) && !path.endsWith("404.html")) return next();
        try {
          const { renderPage } = await server.ssrLoadModule("/src/render.tsx");
          const html = renderPage(path, { css: [], js: [`/${CLIENT_ENTRY}`] });
          res.setHeader("Content-Type", "text/html; charset=utf-8");
          res.end(await server.transformIndexHtml(path, html));
        } catch (error) {
          next(error);
        }
      });
    },
  };
}

export default defineConfig(({ isSsrBuild }) => ({
  appType: "custom",
  plugins: [react(), devPages()],
  test: { include: ["tests/*.test.ts"] },
  build: {
    manifest: !isSsrBuild,
    rolldownOptions: isSsrBuild ? {} : { input: CLIENT_ENTRY },
  },
}));
