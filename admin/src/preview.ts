/**
 * file: src/preview.ts
 * importable: previewDocument
 *
 * description: Builds the page shown inside the isolated preview frame.
 */

// NOTE: The frame has an empty sandbox, so nothing inside it can run a script or reach the panel.
// Raw HTML in the Markdown is dropped as well, the same as the site does, so the preview can not
// show something the site would not.

import { Marked } from "marked";
import stylesheet from "../../site/src/styles/site.css?url";
import type { Language } from "./api";

const markdown = new Marked({ renderer: { html: () => "" } });

function escape(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

/**
 * Builds the preview of one language.
 *
 * @param story Fields of the language.
 * @param image Cover as a data address, because the frame has no access to the session.
 * @param dark True when the panel is in the dark theme.
 * @returns Whole HTML document.
 */
export function previewDocument(story: Language, image: string | null, dark: boolean): string {
  const cover = image ? `<div class="photo ratio-16-9 photo-gap"><img src="${escape(image)}" alt=""></div>` : "";
  return `<!doctype html><html lang="en" data-theme="${dark ? "dark" : "light"}"><head><meta charset="utf-8">
    <link rel="stylesheet" href="${new URL(stylesheet, location.href).href}"></head>
    <body class="preview-body"><p class="meta"><b>${escape(story.category)}</b></p>
    <h1 class="head-2">${escape(story.title || "Headline")}</h1>
    <p class="summary-large">${escape(story.summary)}</p>${cover}
    <p class="caption">${escape(story.image.credit)}</p>
    <div class="prose">${markdown.parse(story.body, { async: false })}</div></body></html>`;
}
