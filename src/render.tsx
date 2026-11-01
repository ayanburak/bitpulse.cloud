/**
 * file: src/render.tsx
 * importable: renderPage, listPagePaths, stories
 *
 * Runs at build time and on the dev server, never in the browser. renderPage turns one
 * address from listPagePaths into a complete HTML document.
 *
 * description: Renders site pages to static HTML strings.
 */

import { renderToStaticMarkup } from "react-dom/server";
import { StaticRouter } from "react-router";
import { listPagePaths, stories } from "./catalog";
import { Document, type Assets } from "./Document";
import { SiteRoutes } from "./routes";

export { listPagePaths, stories };
export type { Assets };

// The markup carries no React attributes because nothing hydrates it in the browser.
export function renderPage(path: string, assets: Assets): string {
  const lang = path.startsWith("/tr/") ? "tr" : "en";
  const body = renderToStaticMarkup(
    <Document lang={lang} assets={assets}>
      <StaticRouter location={path}>
        <SiteRoutes />
      </StaticRouter>
    </Document>,
  );
  return `<!DOCTYPE html>\n${body}\n`;
}
