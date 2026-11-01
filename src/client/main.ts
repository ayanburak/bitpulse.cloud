/**
 * file: src/client/main.ts
 * importable: nothing, every page loads this file as its only browser script
 *
 * The file is not a module with exports. On load it wires up whichever parts exist on the
 * current page and skips the rest, so one script is safe on all pages.
 *
 * description: Browser behavior of the site, kept small because React never reaches the reader.
 */

import { startSearch } from "./search";
import "../styles/site.css";

// --- Constants ---

const LANG = document.documentElement.lang === "tr" ? "tr" : "en";
const LOCALE = LANG === "tr" ? "tr-TR" : "en-US";
const COPIED = LANG === "tr" ? "Kopyalandı" : "Copied";
const COPY_FAILED = LANG === "tr" ? "Kopyalanamadı" : "Could not copy";
const ONE_YEAR = 31536000;
const THEME_KEY = "bp_theme";
const READING_WIDTH = 56;
const RISE = "9px";

// --- Today ---

// Pages are static, so the date in the header would freeze at the build day without this.
function showToday(): void {
  const date = document.querySelector("[data-today]");
  if (!date) return;
  date.textContent = new Intl.DateTimeFormat(LOCALE, {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date());
}

// --- Pulse Line ---

// Only --x and --w are written, the motion itself comes from CSS transitions. Offsets are read
// relative to the rail, so the line stays under the link even when the menu scrolls sideways.
function pointPulse(rail: HTMLElement, link: HTMLElement): void {
  rail.style.setProperty("--x", `${link.offsetLeft}px`);
  rail.style.setProperty("--w", `${link.offsetWidth}px`);
  rail.style.setProperty("--y", RISE);
}

// On reading pages the rise follows the scroll position, so no separate progress bar is needed.
function trackReading(rail: HTMLElement, target: Element): void {
  const box = target.getBoundingClientRect();
  const distance = box.height - innerHeight;
  const ratio = distance > 0 ? Math.min(1, Math.max(0, -box.top / distance)) : 0;
  rail.style.setProperty("--w", `${READING_WIDTH}px`);
  rail.style.setProperty("--y", RISE);
  rail.style.setProperty("--x", `${ratio * (rail.offsetWidth - READING_WIDTH)}px`);
}

// The line slides to a hovered or focused link and returns to its resting place afterwards.
// That place is the active link on normal pages and the reading position on story pages.
function startRail(rail: HTMLElement): void {
  const reading = rail.closest(".menu") ? document.querySelector("[data-reading]") : null;
  const pulse = rail.querySelector(".pulse");
  if (!pulse) return;

  const rest = () => {
    if (reading) return trackReading(rail, reading);
    const active = rail.querySelector<HTMLElement>("a[aria-current]");
    if (active) pointPulse(rail, active);
    else rail.style.removeProperty("--y");
  };

  // The first position is written with no transition, or the line would slide in on every page.
  pulse.classList.add("no-transition");
  rest();
  requestAnimationFrame(() => requestAnimationFrame(() => pulse.classList.remove("no-transition")));

  rail.querySelectorAll<HTMLElement>("a").forEach((link) => {
    link.addEventListener("mouseenter", () => pointPulse(rail, link));
    link.addEventListener("focus", () => pointPulse(rail, link));
    link.addEventListener("blur", rest);
  });
  rail.addEventListener("mouseleave", rest);
  addEventListener("resize", rest);
  void document.fonts.ready.then(rest);

  if (reading) {
    let waiting = false;
    addEventListener("scroll", () => {
      if (waiting) return;
      waiting = true;
      requestAnimationFrame(() => {
        trackReading(rail, reading);
        waiting = false;
      });
    }, { passive: true });
    return;
  }

  // On narrow screens the active link is scrolled into view.
  const active = rail.querySelector<HTMLElement>("a[aria-current]");
  const box = rail.parentElement;
  if (active && box && box.scrollWidth > box.clientWidth) {
    box.scrollLeft = active.offsetLeft - (box.clientWidth - active.offsetWidth) / 2;
  }
}

// --- Language ---

// The choice lives in a one year cookie, and the server reads it when a reader opens the root address.
function startLanguageSwitch(): void {
  document.querySelectorAll<HTMLAnchorElement>(".lang-switch a").forEach((link) => {
    link.addEventListener("click", () => {
      document.cookie = `bp_lang=${link.lang}; path=/; max-age=${ONE_YEAR}; SameSite=Lax`;
    });
  });
}

// --- Theme ---

// The head script applies the saved theme, so this only keeps the button in step with it.
function startThemeToggle(): void {
  const button = document.querySelector<HTMLButtonElement>("[data-theme-toggle]");
  if (!button) return;
  const root = document.documentElement;

  const label = () => {
    const dark = root.dataset.theme === "dark";
    button.setAttribute("aria-label", (dark ? button.dataset.light : button.dataset.dark) ?? "");
  };

  button.addEventListener("click", () => {
    const dark = root.dataset.theme !== "dark";
    if (dark) root.dataset.theme = "dark";
    else delete root.dataset.theme;
    try {
      localStorage.setItem(THEME_KEY, dark ? "dark" : "light");
    } catch {
      // Private browsing can block storage. The theme still changes for this page.
    }
    label();
  });
  label();
}

// --- Copy Link ---

function startCopyButtons(): void {
  document.querySelectorAll<HTMLButtonElement>("[data-copy]").forEach((button) => {
    const label = button.textContent;
    button.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(location.href);
        button.textContent = COPIED;
      } catch {
        button.textContent = COPY_FAILED;
      }
      setTimeout(() => { button.textContent = label; }, 1600);
    });
  });
}

// --- Contents ---

// Marks the section being read. The watched window is the upper third of the screen, and a
// heading entering it counts as the current section.
function startContents(): void {
  const links = [...document.querySelectorAll<HTMLAnchorElement>("[data-toc] a")];
  if (!links.length) return;
  const observer = new IntersectionObserver((entries) => {
    entries.filter((entry) => entry.isIntersecting).forEach((entry) => {
      links.forEach((link) => link.toggleAttribute("aria-current", link.hash === `#${entry.target.id}`));
    });
  }, { rootMargin: "-10% 0px -65% 0px" });
  links.forEach((link) => {
    const heading = document.querySelector(link.hash);
    if (heading) observer.observe(heading);
  });
}

// --- Start ---

showToday();
document.querySelectorAll<HTMLElement>(".rail").forEach(startRail);
startLanguageSwitch();
startThemeToggle();
startCopyButtons();
startContents();
void startSearch();
