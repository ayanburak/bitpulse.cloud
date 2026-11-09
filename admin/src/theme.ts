/**
 * file: src/theme.ts
 * importable: applySavedTheme, toggleTheme
 *
 * description: Remembers the light or dark theme of the panel.
 */

const KEY = "bitpulse-editor-theme";

// Storage can be refused by the browser, and the theme is not worth an error page.
function saved(): string | null {
  try {
    return localStorage.getItem(KEY);
  } catch {
    return null;
  }
}

export function applySavedTheme(): void {
  document.documentElement.dataset.js = "1";
  const theme = saved() ?? (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  document.documentElement.dataset.theme = theme;
}

export function toggleTheme(): void {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  try {
    localStorage.setItem(KEY, next);
  } catch {
    // The choice simply lasts until the page is closed.
  }
}
