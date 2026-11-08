/**
 * file: src/components/Layout.tsx
 * importable: Layout, Logo, useLang
 *
 * description: Header, menu, footer and head tags around every page.
 */

import type { ReactNode } from "react";
import { useLocation, useParams } from "react-router";
import { counterpart, feedPath, longStories } from "../catalog";
import { PUBLISHER_URL, REPO_URL, SITE_URL, SOCIAL_URLS, X_HANDLE } from "../config";
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

// Both menus share this link, so the current page is marked the same way in each.
function MenuLink({ href, children }: { href: string; children: ReactNode }) {
  const { pathname } = useLocation();
  return <li><a href={href} aria-current={pathname === href ? "page" : undefined}>{children}</a></li>;
}

// Phones use this instead of the rail, because seven links do not fit one row. The native details
// element opens without JavaScript, and main.ts only adds closing on an outside tap or Escape.
// The section has no page until its first article exists, so no link may point to it before that.
function ExplainedLink({ lang }: { lang: Lang }) {
  if (longStories().length === 0) return null;
  return <MenuLink href={`/${lang}/explained/`}>{ui[lang].explained}</MenuLink>;
}

function Drawer({ lang }: { lang: Lang }) {
  const t = ui[lang];
  return (
    <details className="drawer" data-drawer>
      <summary aria-label={t.mainMenu}><i></i><i></i><i></i></summary>
      <nav className="drawer__panel" aria-label={t.mainMenu}>
        <ul>
          <MenuLink href={`/${lang}/`}>{t.topStories}</MenuLink>
          <ExplainedLink lang={lang} />
          {categories.map((key) => <MenuLink key={key} href={`/${lang}/category/${key}/`}>{categoryNames[lang][key]}</MenuLink>)}
          <MenuLink href={`/${lang}/archive/`}>{t.archive}</MenuLink>
        </ul>
      </nav>
    </details>
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
        <Drawer lang={lang} />
      </div>
    </header>
  );
}

function Menu({ lang }: { lang: Lang }) {
  const t = ui[lang];
  return (
    <nav className="menu" aria-label={t.mainMenu}>
      <div className="rail">
        <ul>
          <MenuLink href={`/${lang}/`}>{t.topStories}</MenuLink>
          <ExplainedLink lang={lang} />
        </ul>
        <ul>
          {categories.map((key) => <MenuLink key={key} href={`/${lang}/category/${key}/`}>{categoryNames[lang][key]}</MenuLink>)}
        </ul>
        <ul><MenuLink href={`/${lang}/archive/`}>{t.archive}</MenuLink></ul>
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
              <ExplainedLink lang={lang} />
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
              <li><a href={`/${lang}/editorial-policy/`}>{t.editorialPolicy}</a></li>
              <li><a href={`/${lang}/corrections/`}>{t.corrections}</a></li>
              <li><a href={`/${lang}/contact/`}>{t.contact}</a></li>
              <li><a href={`/${lang}/privacy/`}>{t.privacy}</a></li>
              {Object.entries(SOCIAL_URLS).map(([name, href]) => <li key={name}><a href={href} rel="me">{name}</a></li>)}
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

// A story title can hold any text, and an unescaped closing tag would end the script early.
export function jsonForScript(data: object): string {
  return JSON.stringify(data).replace(/</g, "\\u003c");
}

// A story passes its image and structured data, and every other page shares as a plain website.
export interface StoryHead {
  image: string;
  imageAlt: string;
  published: string;
  modified: string;
  data: object;
}

interface Props {
  title?: string;
  description?: string;
  story?: StoryHead;
  children: ReactNode;
}

// The root address counts as the shared language entry, so it is the x-default of the home page.
// On other pages the x-default is the English version, which on a story has its own slug.
// The root redirects here, so the language home pages are where Google reads the site name.
function HeadTags({ lang, title, description, story }: { lang: Lang; title: string; description: string; story?: StoryHead }) {
  const { pathname } = useLocation();
  const url = (path: string) => `${SITE_URL}${path}`;
  const other = counterpart(pathname);
  const isHome = pathname === `/${lang}/`;
  return (
    <>
      <title>{title}</title>
      <meta name="description" content={description} />
      <meta name="robots" content="max-image-preview:large" />
      <meta property="og:type" content={story ? "article" : "website"} />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={url(pathname)} />
      <meta property="og:site_name" content="Bitpulse" />
      {story && (
        <>
          <meta property="og:image" content={story.image} />
          <meta property="og:image:alt" content={story.imageAlt} />
          <meta property="article:published_time" content={story.published} />
          <meta property="article:modified_time" content={story.modified} />
          <meta name="twitter:card" content="summary_large_image" />
          <meta name="twitter:site" content={`@${X_HANDLE}`} />
          <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonForScript(story.data) }} />
        </>
      )}
      {isHome && (
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonForScript({ "@context": "https://schema.org", "@type": "WebSite", name: "Bitpulse", url: `${SITE_URL}/`, sameAs: Object.values(SOCIAL_URLS) }) }} />
      )}
      <link rel="canonical" href={url(pathname)} />
      <link rel="alternate" hrefLang={lang} href={url(pathname)} />
      <link rel="alternate" hrefLang={otherLang(lang)} href={url(other)} />
      <link rel="alternate" hrefLang="x-default" href={url(isHome ? "/" : lang === "en" ? pathname : other)} />
      <link rel="alternate" type="application/rss+xml" title="Bitpulse" href={url(feedPath(lang))} />
    </>
  );
}

export function Layout({ title, description, story, children }: Props) {
  const lang = useLang();
  const t = ui[lang];
  return (
    <>
      <HeadTags lang={lang} title={title ? `${title} | Bitpulse` : t.homeTitle} description={description ?? t.metaDescription} story={story} />
      <a className="skip-link" href="#content">{t.skip}</a>
      <Header lang={lang} />
      <Menu lang={lang} />
      <main id="content">{children}</main>
      <Footer lang={lang} />
    </>
  );
}
