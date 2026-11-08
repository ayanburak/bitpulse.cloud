/**
 * file: src/routes.tsx
 * importable: SiteRoutes
 *
 * description: The route table that matches each generated address to its page.
 */

import { Route, Routes } from "react-router";
import { Layout, Logo, useLang } from "./components/Layout";
import { SITE_URL } from "./config";
import { ui } from "./i18n";
import { Archive } from "./pages/Archive";
import { Category } from "./pages/Category";
import { Explained } from "./pages/Explained";
import { Home } from "./pages/Home";
import { About, Contact, Privacy } from "./pages/Info";
import { Corrections, EditorialPolicy } from "./pages/Policy";
import { Search } from "./pages/Search";
import { StoryPage } from "./pages/StoryPage";

// The server redirects the root address, so this view only shows when that does not happen.
function LanguagePicker() {
  return (
    <>
      <title>Bitpulse</title>
      <meta name="description" content={ui.en.metaDescription} />
      <link rel="canonical" href={`${SITE_URL}/`} />
      <link rel="alternate" hrefLang="tr" href={`${SITE_URL}/tr/`} />
      <link rel="alternate" hrefLang="en" href={`${SITE_URL}/en/`} />
      <link rel="alternate" hrefLang="x-default" href={`${SITE_URL}/`} />
      <main className="root-page">
        <Logo href="/en/" />
        <p>
          <a className="link-line" href="/tr/" lang="tr">Türkçe</a>
          <a className="link-line" href="/en/">English</a>
        </p>
      </main>
    </>
  );
}

function NotFound() {
  const lang = useLang();
  const t = ui[lang];
  return (
    <Layout title={t.notFoundTitle}>
      <div className="container not-found">
        <p className="not-found__code" aria-hidden="true">404</p>
        <h1 className="head-2">{t.notFoundTitle}</h1>
        <p className="summary">{t.notFoundText}</p>
        <div className="not-found__actions">
          <a className="button" href={`/${lang}/`}>{t.backHome}</a>
          <a className="button button--outline" href={`/${lang}/search/`}>{t.searchSite}</a>
        </div>
      </div>
    </Layout>
  );
}

export function SiteRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LanguagePicker />} />
      <Route path="/:lang/" element={<Home />} />
      <Route path="/:lang/stories/:slug/" element={<StoryPage />} />
      <Route path="/:lang/category/:key/" element={<Category />} />
      <Route path="/:lang/explained/" element={<Explained />} />
      <Route path="/:lang/archive/" element={<Archive />} />
      <Route path="/:lang/archive/:year/:month/" element={<Archive />} />
      <Route path="/:lang/search/" element={<Search />} />
      <Route path="/:lang/about/" element={<About />} />
      <Route path="/:lang/contact/" element={<Contact />} />
      <Route path="/:lang/privacy/" element={<Privacy />} />
      <Route path="/:lang/editorial-policy/" element={<EditorialPolicy />} />
      <Route path="/:lang/corrections/" element={<Corrections />} />
      <Route path="/:lang/404.html" element={<NotFound />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
