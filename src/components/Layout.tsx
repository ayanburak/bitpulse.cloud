/**
 * file: src/components/Layout.tsx
 * importable: Layout, Logo, useLang
 *
 * description: Header, menu, footer and head tags around every page.
 */

import type { ReactNode } from "react";
import { useLocation, useParams } from "react-router";
import { counterpart } from "../catalog";
import { PUBLISHER_URL, REPO_URL, SITE_URL } from "../config";
import { categoryNames, formatDate, isLang, otherLang, ui, type Lang } from "../i18n";
import { categories } from "../stories";

// --- Language ---

// The 404 page at the root address has no language in its path and falls back to English.
export function useLang(): Lang {
  const { lang } = useParams();
  return isLang(lang) ? lang : "en";
}

// --- Parts ---

export function Logo({ href, label }: { href: string; label?: string }) {
  return (
    <a className="logo" href={href} aria-label={label}>
      <svg viewBox="0 0 32 32" aria-hidden="true">
        <rect width="32" height="32" fill="currentColor" />
        <path fillRule="evenodd" d="M6 3h8v8h12v18H6zM14 17v6h4v-6z" />
      </svg>
      bitpulse
    </a>
  );
}

// Both language links stay visible, and the current page counterpart comes from the catalog.
function LangSwitch({ lang }: { lang: Lang }) {
  const { pathname } = useLocation();
  const other = counterpart(pathname);
  const links = { [lang]: pathname, [otherLang(lang)]: other } as Record<Lang, string>;
  return (
    <nav className="lang-switch" aria-label={ui[lang].language}>
      <a href={links.tr} lang="tr" hrefLang="tr" aria-current={lang === "tr" ? "true" : undefined}>TR</a>
      <a href={links.en} lang="en" hrefLang="en" aria-current={lang === "en" ? "true" : undefined}>EN</a>
    </nav>
  );
}

// One button with both icons, and CSS shows the one that matches the current theme. It needs
// JavaScript to work, so it stays hidden for readers who have it turned off.
function ThemeToggle({ lang }: { lang: Lang }) {
  const t = ui[lang];
  return (
    <button className="theme-toggle" type="button" data-theme-toggle data-dark={t.darkTheme} data-light={t.lightTheme} aria-label={t.darkTheme}>
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

function Header({ lang }: { lang: Lang }) {
  const t = ui[lang];
  return (
    <header className="site-header">
      <div className="container site-header__inner">
        <Logo href={`/${lang}/`} label={t.home} />
        <p className="date" data-today={lang}>{formatDate(new Date(), lang, "full")}</p>
        <a className="site-header__link" href={`/${lang}/search/`}>{t.search}</a>
        <ThemeToggle lang={lang} />
        <LangSwitch lang={lang} />
      </div>
    </header>
  );
}

function Menu({ lang }: { lang: Lang }) {
  const t = ui[lang];
  const { pathname } = useLocation();
  const current = (href: string) => (pathname === href ? "page" : undefined);
  const home = `/${lang}/`;
  const archive = `/${lang}/archive/`;
  return (
    <nav className="menu" aria-label={t.mainMenu}>
      <div className="rail">
        <ul><li><a href={home} aria-current={current(home)}>{t.topStories}</a></li></ul>
        <ul>
          {categories.map((key) => {
            const href = `/${lang}/category/${key}/`;
            return <li key={key}><a href={href} aria-current={current(href)}>{categoryNames[lang][key]}</a></li>;
          })}
        </ul>
        <ul><li><a href={archive} aria-current={current(archive)}>{t.archive}</a></li></ul>
        <i className="pulse" aria-hidden="true"><b></b></i>
      </div>
    </nav>
  );
}

function Footer({ lang }: { lang: Lang }) {
  const t = ui[lang];
  const names = categoryNames[lang];
  const link = (key: (typeof categories)[number]) => (
    <li key={key}><a href={`/${lang}/category/${key}/`}>{names[key]}</a></li>
  );
  return (
    <footer className="site-footer">
      <div className="container">
        <div className="grid site-footer__inner">
          <div className="site-footer__brand">
            <Logo href={`/${lang}/`} />
            <p>{t.footerNote}</p>
          </div>
          <div className="site-footer__column">
            <h2>{t.site}</h2>
            <ul>
              <li><a href={`/${lang}/`}>{t.topStories}</a></li>
              <li><a href={`/${lang}/archive/`}>{t.archive}</a></li>
              <li><a href={`/${lang}/search/`}>{t.search}</a></li>
            </ul>
          </div>
          <div className="site-footer__column">
            <h2>{t.categories}</h2>
            <ul>{categories.slice(0, 3).map(link)}</ul>
          </div>
          <div className="site-footer__column">
            <h2>&nbsp;<span className="visually-hidden">{t.moreCategories}</span></h2>
            <ul>{categories.slice(3).map(link)}</ul>
          </div>
          <div className="site-footer__column">
            <h2>Bitpulse</h2>
            <ul>
              <li><a href={`/${lang}/about/`}>{t.about}</a></li>
              <li><a href={`/${lang}/contact/`}>{t.contact}</a></li>
              <li><a href={`/${lang}/privacy/`}>{t.privacy}</a></li>
            </ul>
          </div>
        </div>
        <div className="site-footer__bottom">
          <span>© {new Date().getUTCFullYear()} <a href={PUBLISHER_URL}>PaktLabs</a></span>
          <a href={REPO_URL}>{t.sourceCode}</a>
        </div>
      </div>
    </footer>
  );
}

// --- Layout ---

interface Props {
  title?: string;
  description?: string;
  children: ReactNode;
}

// The root address counts as the shared language entry, so it is the x-default of the home page.
function HeadTags({ lang, title, description }: { lang: Lang; title: string; description: string }) {
  const { pathname } = useLocation();
  const url = (path: string) => `${SITE_URL}${path}`;
  const other = counterpart(pathname);
  const isHome = pathname === `/${lang}/`;
  return (
    <>
      <title>{title}</title>
      <meta name="description" content={description} />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={url(pathname)} />
      <meta property="og:site_name" content="Bitpulse" />
      <link rel="canonical" href={url(pathname)} />
      <link rel="alternate" hrefLang={lang} href={url(pathname)} />
      <link rel="alternate" hrefLang={otherLang(lang)} href={url(other)} />
      <link rel="alternate" hrefLang="x-default" href={url(isHome ? "/" : `/en/${pathname.slice(4)}`)} />
    </>
  );
}

export function Layout({ title, description, children }: Props) {
  const lang = useLang();
  const t = ui[lang];
  return (
    <>
      <HeadTags lang={lang} title={title ? `${title} | Bitpulse` : "Bitpulse"} description={description ?? t.metaDescription} />
      <a className="skip-link" href="#content">{t.skip}</a>
      <Header lang={lang} />
      <Menu lang={lang} />
      <main id="content">{children}</main>
      <Footer lang={lang} />
    </>
  );
}
