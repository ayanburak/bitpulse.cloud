/**
 * file: src/pages/Category.tsx
 * importable: Category
 *
 * description: The page of one category, with its lead story and the rest of its stories.
 */

import { useParams } from "react-router";
import { storiesIn, type Category as Key } from "../catalog";
import { Layout, useLang } from "../components/Layout";
import { StoryCard } from "../components/Story";
import { categoryIntros, categoryNames, ui } from "../i18n";
import { categories } from "../stories";

// --- Constants ---

const LEAD_SIDE_SIZE = 4;

// --- Page ---

export function Category() {
  const lang = useLang();
  const t = ui[lang];
  const { key } = useParams();
  const category = categories.find((item) => item === key) as Key | undefined;
  if (!category) throw new Error(`Unknown category: ${key}`);

  const [first, ...rest] = storiesIn(category);
  const side = rest.slice(0, LEAD_SIDE_SIZE);
  const remaining = rest.slice(LEAD_SIDE_SIZE);
  const name = categoryNames[lang][category];

  return (
    <Layout title={name} description={categoryIntros[lang][category]}>
      <div className="container">
        <div className="page-head">
          <h1 className="head-1">{name}</h1>
          <p className="summary">{categoryIntros[lang][category]}</p>
        </div>
        {!first && <p className="summary">{t.noStories}</p>}
        {first && (
          <div className="grid cat-lead">
            <div className="cat-lead__main">
              <StoryCard story={first} lang={lang} head="head-2" ratio="16-9" sizes="(max-width: 1180px) 100vw, 840px" summary />
            </div>
            {side.length > 0 && (
              <div className="cat-lead__side">
                {side.map((story) => (
                  <StoryCard key={story.key} story={story} lang={lang} head="head-4" ratio="3-2" sizes="(max-width: 680px) 50vw, 280px" />
                ))}
              </div>
            )}
          </div>
        )}
        {remaining.length > 0 && (
          <section className="section">
            <div className="section-head"><h2>{t.latest}</h2></div>
            <div className="rows">
              {remaining.map((story) => (
                <StoryCard key={story.key} story={story} lang={lang} head="head-3" ratio="3-2" sizes="200px" summary className="list-entry" />
              ))}
            </div>
          </section>
        )}
      </div>
    </Layout>
  );
}
