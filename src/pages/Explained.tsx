/**
 * file: src/pages/Explained.tsx
 * importable: Explained
 *
 * description: The list of every explainer, named Merak on Turkish pages.
 */

import { longStories } from "../catalog";
import { Layout, useLang } from "../components/Layout";
import { StoryIndex } from "../components/Story";
import { ui } from "../i18n";

// An explainer also stays in its own category, so this page is a section and not a sixth category.
export function Explained() {
  const lang = useLang();
  const t = ui[lang];
  return (
    <Layout title={t.explained} description={t.explainedIntro}>
      <div className="container">
        <div className="page-head">
          <h1 className="head-1">{t.explained}</h1>
          <p className="summary">{t.explainedIntro}</p>
        </div>
        <StoryIndex stories={longStories()} lang={lang} />
      </div>
    </Layout>
  );
}
