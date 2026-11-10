/**
 * file: src/Shell.tsx
 * importable: Shell, Logo
 *
 * description: Header and menu around every signed in page of the panel.
 */

import { useEffect, useRef, type ReactNode } from "react";
import { toggleTheme } from "./theme";

const SECTIONS = [["stories", "Stories"], ["radar", "Radar"], ["instagram", "Instagram"], ["audit", "Audit log"], ["access", "Access"]];
const SITE = "https://bitpulse.cloud/";
const TODAY = new Intl.DateTimeFormat("en-US", { dateStyle: "full" }).format(new Date());

export function Logo() {
  return (
    <span className="logo">
      <svg viewBox="0 0 32 32" aria-hidden="true">
        <rect width="32" height="32" fill="currentColor" />
        <path fillRule="evenodd" d="M6 3h8v8h12v18H6zM14 17v6h4v-6z" />
      </svg>
      bitpulse<small>editor</small>
    </span>
  );
}

function ThemeButton() {
  return (
    <button className="theme-toggle" type="button" aria-label="Switch theme" onClick={toggleTheme}>
      <svg className="theme-toggle__sun" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="12" r="4.5" />
        <path d="M12 1.5v3M12 19.5v3M1.5 12h3M19.5 12h3M4.6 4.6l2.1 2.1M17.3 17.3l2.1 2.1M4.6 19.4l2.1-2.1M17.3 6.7l2.1-2.1" />
      </svg>
      <svg className="theme-toggle__moon" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M20.5 14.2A8.5 8.5 0 1 1 9.8 3.5a7 7 0 0 0 10.7 10.7z" />
      </svg>
    </button>
  );
}

// The pulse line rises under the current section, the same mark the site uses for its menu.
export function Shell({ section, signOut, children }: { section: string; signOut: () => void; children: ReactNode }) {
  const rail = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const place = () => {
      const link = rail.current?.querySelector<HTMLElement>('a[aria-current="page"]');
      const pulse = rail.current?.querySelector<HTMLElement>(".pulse");
      if (!link || !pulse) return;
      pulse.style.setProperty("--x", `${link.offsetLeft}px`);
      pulse.style.setProperty("--w", `${link.offsetWidth}px`);
      pulse.style.setProperty("--y", "9px");
    };
    place();
    void document.fonts.ready.then(place);
    addEventListener("resize", place);
    return () => removeEventListener("resize", place);
  }, [section]);

  return (
    <>
      <header className="site-header"><div className="container site-header__inner">
        <a href="#stories" aria-label="Stories"><Logo /></a>
        <p className="date">{TODAY}</p>
        <button className="site-header__link" type="button" onClick={signOut}>Sign out</button>
        <ThemeButton />
      </div></header>
      <nav className="menu" aria-label="Sections"><div className="rail" ref={rail}>
        <ul>{SECTIONS.map(([key, label]) => <li key={key}><a href={`#${key}`} aria-current={section === key ? "page" : undefined}>{label}</a></li>)}</ul>
        <ul><li><a href={SITE} target="_blank" rel="noopener noreferrer">View site</a></li></ul>
        <span className="pulse"><b></b></span>
      </div></nav>
      <main className="container page">{children}</main>
    </>
  );
}
