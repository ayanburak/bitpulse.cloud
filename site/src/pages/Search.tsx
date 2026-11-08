/**
 * file: src/pages/Search.tsx
 * importable: Search
 *
 * description: The search page. Results are filled in by the browser script.
 */

import { Layout, useLang } from "../components/Layout";
import { ui } from "../i18n";

export function Search() {
  const lang = useLang();
  const t = ui[lang];
  return (
    <Layout title={t.search}>
      <div className="container">
        <div className="page-head">
          <h1 className="visually-hidden">{t.search}</h1>
          <form className="search-form" data-search role="search">
            <label className="visually-hidden" htmlFor="search-input">{t.searchTerm}</label>
            <input id="search-input" type="search" placeholder={t.searchPlaceholder} autoComplete="off" />
            <button className="button" type="submit">{t.search}</button>
          </form>
          <p className="search-count" role="status"></p>
        </div>
        <div className="grid search-body">
          <div className="search-list">
            <ul className="rows"></ul>
            <div className="search-empty" hidden>
              <h2 className="head-2">{t.noResults}</h2>
              <p className="summary">{t.noResultsHint}</p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
