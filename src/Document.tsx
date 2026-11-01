/**
 * file: src/Document.tsx
 * importable: Document, Assets
 *
 * description: The HTML shell shared by every page.
 */

import type { ReactNode } from "react";
import type { Lang } from "./i18n";

// Asset addresses are passed in because they differ between the dev server and a build.
export interface Assets {
  css: string[];
  js: string[];
}

interface Props {
  lang: Lang;
  assets: Assets;
  children: ReactNode;
}

// Runs before the first paint, so a reader who chose the dark theme never sees a white flash.
// The data-js mark lets CSS show the theme button only where it can work.
const THEME_SCRIPT = `document.documentElement.dataset.js="";try{if(localStorage.getItem("bp_theme")==="dark")document.documentElement.dataset.theme="dark"}catch(e){}`;

// Page titles and meta tags are rendered by each page, and React moves them into this head.
export function Document({ lang, assets, children }: Props) {
  return (
    <html lang={lang}>
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} />
        {/* Google Search does not list SVG among its favicon formats, so the PNG goes first. */}
        <link rel="icon" href="/favicon.png" type="image/png" sizes="512x512" />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="preload" href="/fonts/archivo-latin.woff2" as="font" type="font/woff2" crossOrigin="" />
        {assets.css.map((href) => <link key={href} rel="stylesheet" href={href} />)}
        {assets.js.map((src) => <script key={src} type="module" src={src} />)}
      </head>
      <body>{children}</body>
    </html>
  );
}
