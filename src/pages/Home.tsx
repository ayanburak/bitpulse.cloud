/**
 * file: src/pages/Home.tsx
 * importable: Home
 *
 * description: The front page with the lead story, the feed and the optional sections.
 */

// NOTE: Every section below the lead appears only when there are enough stories to fill it, so
// the page never shows half empty rows while the archive is still small. There is no most read
// section yet because it needs real readership numbers, and invented rankings are not acceptable.

import { longStories, newsStories, stories, storiesIn, storyPath } from "../catalog";
import { Layout, useLang } from "../components/Layout";
import { ImageCredit, Meta, Photo, StoryCard } from "../components/Story";
import { categoryNames, formatDate, ui, type Lang } from "../i18n";
import { categories, type Story } from "../stories";

// --- Constants ---

const FEED_SIZE = 9;
const SECONDARY_SIZE = 3;
const MIN_BOXES = 6;
const MIN_CATEGORY_STORIES = 3;
const LOOKBACK_DAYS = 30;
const DAY_MS = 86_400_000;

const LAYOUTS = ["layout-a", "layout-a", "layout-a", "layout-a", "layout-a"];

// --- Sections ---

function Lead({ story, lang }: { story: Story; lang: Lang }) {
  const version = story.versions[lang];
  return (
    <div className="lead__main">
      <article className="card">
        <Meta story={story} lang={lang} />
        <h1 className="head-1">
          <a href={storyPath(story, lang)}><span className="link-line">{version.title}</span></a>
        </h1>
        <p className="summary-large">{version.summary}</p>
        <div className="lead__photo">
          <Photo story={story} lang={lang} ratio="16-9" sizes="(max-width: 960px) 100vw, 1000px" priority />
        </div>
      </article>
      <p className="caption"><ImageCredit story={story} lang={lang} /></p>
    </div>
  );
}

function Feed({ lang }: { lang: Lang }) {
  const t = ui[lang];
  return (
    <aside className="lead__side" aria-labelledby="latest-heading">
      <div className="feed-head">
        <h2 id="latest-heading">{t.latest}</h2>
        <a className="link-line" href={`/${lang}/archive/`}>{t.archive}</a>
      </div>
      <ol className="feed rows">
        {stories.slice(0, FEED_SIZE).map((story, index) => (
          <li key={story.key} className={index === 0 ? "current" : undefined}>
            <time dateTime={story.date}>{formatDate(story.date, lang, "tiny")}</time>
            <div className="card">
              <h3 className="head-4">
                <a href={storyPath(story, lang)}><span className="link-line">{story.versions[lang].title}</span></a>
              </h3>
              <p className="meta">{categoryNames[lang][story.category]}</p>
            </div>
          </li>
        ))}
      </ol>
    </aside>
  );
}

function Secondary({ lang }: { lang: Lang }) {
  const [first, ...rest] = newsStories().slice(1, 1 + SECONDARY_SIZE);
  if (!first) return null;
  return (
    <div className="grid secondary">
      <StoryCard story={first} lang={lang} head="head-2" ratio="16-9" sizes="(max-width: 960px) 100vw, 720px" summary />
      {rest.map((story) => (
        <StoryCard key={story.key} story={story} lang={lang} head="head-3" ratio="4-3" sizes="(max-width: 960px) 50vw, 360px" />
      ))}
    </div>
  );
}

function LastThirtyDays({ lang }: { lang: Lang }) {
  const t = ui[lang];
  const newest = Date.parse(stories[0].date);
  const recent = stories.filter((story) => newest - Date.parse(story.date) <= LOOKBACK_DAYS * DAY_MS);
  if (recent.length < MIN_BOXES) return null;
  return (
    <section className="container section" aria-labelledby="last-30-heading">
      <div className="section-head">
        <h2 id="last-30-heading">{t.last30}</h2>
        <a className="link-line" href={`/${lang}/archive/`}>{t.archive}</a>
      </div>
      <ol className="boxes">
        {recent.map((story) => (
          <li key={story.key} className="card box">
            <Meta story={story} lang={lang} />
            <h3 className="head-4">
              <a href={storyPath(story, lang)}><span className="link-line">{story.versions[lang].title}</span></a>
            </h3>
          </li>
        ))}
      </ol>
    </section>
  );
}

function LongRead({ lang }: { lang: Lang }) {
  const t = ui[lang];
  const [story, ...others] = longStories();
  if (!story) return null;
  const version = story.versions[lang];
  return (
    <section className="inverted long-read" aria-labelledby="long-read-heading">
      <div className="container">
        <div className="grid long-read__inner">
          <a className="long-read__cover" href={storyPath(story, lang)} aria-label={version.title}>
            <Photo story={story} lang={lang} ratio="4-5" sizes="(max-width: 680px) 100vw, 40vw" />
          </a>
          <div className="long-read__text">
            <p className="meta"><b>{t.explained}</b> <span>{t.minutes(version.minutes)}</span></p>
            <h2 className="wide-1" id="long-read-heading">
              <a href={storyPath(story, lang)}><span className="link-line">{version.title}</span></a>
            </h2>
            <p className="summary">{version.summary}</p>
            {others.length > 0 && (
              <ol className="index-list">
                {others.slice(0, 4).map((other) => (
                  <li key={other.key}>
                    <a href={storyPath(other, lang)}>
                      <span className="wide-3"><span className="link-line">{other.versions[lang].title}</span></span>
                      <small>{t.minutes(other.versions[lang].minutes)}</small>
                    </a>
                  </li>
                ))}
              </ol>
            )}
            <div className="long-read__actions">
              <a className="button" href={storyPath(story, lang)}>{t.readStory}</a>
              <a className="button button--outline" href={`/${lang}/explained/`}>{t.explained}</a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function CategoryRows({ lang }: { lang: Lang }) {
  const t = ui[lang];
  const rows = categories.filter((key) => storiesIn(key).length >= MIN_CATEGORY_STORIES);
  if (rows.length === 0) return null;
  return (
    <section className="container section" aria-label={t.categories}>
      {rows.map((key, index) => {
        const [first, ...rest] = storiesIn(key);
        return (
          <div key={key} className="grid category-row">
            <div className="category-row__name">
              <div>
                <h2>{categoryNames[lang][key]}</h2>
                <p><a className="link-line" href={`/${lang}/category/${key}/`}>{t.all}</a></p>
              </div>
            </div>
            <div className={`category-row__body ${LAYOUTS[index]}`}>
              <StoryCard story={first} lang={lang} head="head-2" ratio="16-9" sizes="(max-width: 680px) 100vw, 640px" summary />
              <div className="list rows">
                {rest.slice(0, 4).map((story) => <StoryCard key={story.key} story={story} lang={lang} head="head-4" />)}
              </div>
            </div>
          </div>
        );
      })}
    </section>
  );
}

// --- Page ---

export function Home() {
  const lang = useLang();
  return (
    <Layout>
      <div className="container">
        <div className="grid lead">
          <Lead story={newsStories()[0]} lang={lang} />
          <Feed lang={lang} />
        </div>
        <Secondary lang={lang} />
      </div>
      <LastThirtyDays lang={lang} />
      <LongRead lang={lang} />
      <CategoryRows lang={lang} />
    </Layout>
  );
}
