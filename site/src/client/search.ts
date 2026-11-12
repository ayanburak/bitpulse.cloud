/**
 * file: src/client/search.ts
 * importable: startSearch
 *
 * description: Connects the search page to the index that Pagefind writes at build time.
 */

// NOTE: Results are built with textContent, never innerHTML, so a story title can not inject markup.
// The index only exists after a full build, so search stays empty on the dev server.

// --- Types ---

interface Result {
  url: string;
  meta: { title?: string; summary?: string; category?: string; date?: string };
}

interface Hit {
  data(): Promise<Result>;
}

interface Pagefind {
  search(query: string): Promise<{ results: Hit[] }>;
}

// --- Constants ---

const INDEX = "/pagefind/pagefind.js";
const TR = document.documentElement.lang === "tr";

// --- Rendering ---

function resultCount(count: number): string {
  return TR ? `${count} sonuç bulundu` : `${count} results found`;
}

function append<K extends keyof HTMLElementTagNameMap>(parent: Element, tag: K, text = ""): HTMLElementTagNameMap[K] {
  const element = document.createElement(tag);
  element.textContent = text;
  parent.append(element);
  return element;
}

function renderResult(list: Element, result: Result): void {
  const card = append(append(list, "li"), "article");
  card.className = "card";

  const meta = append(card, "p");
  meta.className = "meta";
  append(meta, "b", result.meta.category);
  meta.append(" ");
  append(meta, "time", result.meta.date);

  const heading = append(card, "h2");
  heading.className = "head-3";
  const link = append(heading, "a");
  link.href = result.url;
  append(link, "span", result.meta.title).className = "link-line";

  append(card, "p", result.meta.summary).className = "summary";
}

// --- Search ---

/**
 * Starts search if the current page has a search form.
 *
 * @returns Resolves once the first search from the address has finished.
 */
export async function startSearch(): Promise<void> {
  const form = document.querySelector<HTMLFormElement>("[data-search]");
  const input = form?.querySelector("input");
  const list = document.querySelector(".search-list ul");
  const count = document.querySelector(".search-count");
  const empty = document.querySelector<HTMLElement>(".search-empty");
  if (!form || !input || !list || !count || !empty) return;

  // The listeners start before the index has loaded, so a word typed while it loads is searched
  // as soon as the index is there.
  const loading = import(/* @vite-ignore */ INDEX).catch(() => null) as Promise<Pagefind | null>;

  // A newer search can finish before an older one, so only the latest may draw its results.
  let latest = 0;
  const run = async (query: string) => {
    const id = ++latest;
    const pagefind = await loading;
    if (!pagefind || id !== latest) return;
    const hits = query.trim() ? (await pagefind.search(query)).results : [];
    const results = await Promise.all(hits.slice(0, 20).map((hit) => hit.data()));
    if (id !== latest) return;
    list.replaceChildren();
    results.forEach((result) => renderResult(list, result));
    count.textContent = query.trim() ? resultCount(results.length) : "";
    empty.hidden = !query.trim() || results.length > 0;
  };

  // A word the reader already typed wins over the one in the address.
  if (!input.value) input.value = new URLSearchParams(location.search).get("q") ?? "";
  input.addEventListener("input", () => void run(input.value));
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    void run(input.value);
  });
  await run(input.value);
}
