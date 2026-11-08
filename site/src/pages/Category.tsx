/**
 * file: src/pages/Category.tsx
 * importable: Category
 *
 * description: The page of one category, with its lead story and the rest of its stories.
 */

import { useParams } from "react-router";
import { storiesIn, type Category as Key } from "../catalog";
import { Layout, useLang } from "../components/Layout";
import { StoryIndex } from "../components/Story";
import { categoryIntros, categoryNames } from "../i18n";
import { categories } from "../stories";

// --- Page ---

export function Category() {
  const lang = useLang();
  const { key } = useParams();
  const category = categories.find((item) => item === key) as Key | undefined;
  if (!category) throw new Error(`Unknown category: ${key}`);

  const name = categoryNames[lang][category];

  return (
    <Layout title={name} description={categoryIntros[lang][category]}>
      <div className="container">
        <div className="page-head">
          <h1 className="head-1">{name}</h1>
          <p className="summary">{categoryIntros[lang][category]}</p>
        </div>
        <StoryIndex stories={storiesIn(category)} lang={lang} />
      </div>
    </Layout>
  );
}
