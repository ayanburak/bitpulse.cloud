/**
 * file: src/pages/StoryPage.tsx
 * importable: StoryPage
 *
 * description: The article page, with one layout for news and one for long reads.
 */

import { useParams } from "react-router";
import { findStory, imageUrl, longStories, stories, storyPath } from "../catalog";
import { AdSide, AdStrip } from "../components/Ads";
import { Layout, useLang, type StoryHead } from "../components/Layout";
import { ImageCredit, Photo, RowItem, StoryCard } from "../components/Story";
import { ADS_ENABLED, PUBLISHER_URL, SITE_URL } from "../config";
import { categoryNames, formatDate, ui, type Lang } from "../i18n";
import type { Story } from "../stories";

// --- Constants ---

const RELATED_SIZE = 4;
const NEXT_SIZE = 4;

// Google asks for at least 1200 pixels for large previews, and the 1280 copy meets that at a
// fraction of the size of the 2000 copy.
const SHARE_IMAGE_WIDTH = 1280;

// --- Helpers ---

// The inline ad sits in the middle of the text, so the body is cut after a paragraph near there.
function splitBody(html: string): [string, string] {
  const middle = html.indexOf("</p>", Math.floor(html.length / 2));
  if (!ADS_ENABLED || middle < 0) return [html, ""];
  const cut = middle + "</p>".length;
  return [html.slice(0, cut), html.slice(cut)];
}

// Same category first, then newest stories, so the lists stay full while the archive is small.
function otherStories(story: Story): Story[] {
  const others = stories.filter((item) => item.key !== story.key);
  return [...others.filter((item) => item.category === story.category), ...others.filter((item) => item.category !== story.category)];
}

// The author is the site itself, because the editorial policy allows no personal bylines.
function storyHead(story: Story, lang: Lang): StoryHead {
  const version = story.versions[lang];
  const image = `${SITE_URL}${imageUrl(story, SHARE_IMAGE_WIDTH)}`;
  return {
    image,
    imageAlt: version.image.alt,
    data: {
      "@context": "https://schema.org",
      "@type": story.kind === "long" ? "Article" : "NewsArticle",
      headline: version.title,
      description: version.summary,
      image: [image],
      datePublished: story.date,
      inLanguage: lang,
      mainEntityOfPage: `${SITE_URL}${storyPath(story, lang)}`,
      author: { "@type": "Organization", name: "Bitpulse", url: `${SITE_URL}/${lang}/about/` },
      publisher: { "@type": "Organization", name: "PaktLabs", url: PUBLISHER_URL },
    },
  };
}

// --- Shared Parts ---

// Pagefind reads these hidden values to draw search results.
function SearchData({ story, lang }: { story: Story; lang: Lang }) {
  return (
    <>
      <span hidden data-pagefind-meta="summary">{story.versions[lang].summary}</span>
      <span hidden data-pagefind-meta="category">{categoryNames[lang][story.category]}</span>
      <span hidden data-pagefind-meta="date">{formatDate(story.date, lang, "long")}</span>
    </>
  );
}

function Body({ story, lang, className }: { story: Story; lang: Lang; className: string }) {
  const [before, after] = splitBody(story.versions[lang].html);
  return (
    <>
      <div className={className} dangerouslySetInnerHTML={{ __html: before }} />
      <AdStrip lang={lang} />
      {after && <div className={className} dangerouslySetInnerHTML={{ __html: after }} />}
    </>
  );
}

function Sources({ story, lang }: { story: Story; lang: Lang }) {
  const t = ui[lang];
  return (
    <div className="prose">
      <aside className="key-points">
        <h2 className="head">{t.sources}</h2>
        <ul>
          {story.versions[lang].sources.map((source) => (
            <li key={source.url}><a href={source.url}>{source.name}</a></li>
          ))}
        </ul>
      </aside>
      <p className="caption">{t.disclosure}</p>
    </div>
  );
}

function ShareLinks({ story, lang }: { story: Story; lang: Lang }) {
  const t = ui[lang];
  const url = encodeURIComponent(`${SITE_URL}${storyPath(story, lang)}`);
  const title = encodeURIComponent(story.versions[lang].title);
  return (
    <div className="right">
      <button type="button" data-copy>{t.copyLink}</button>
      <a href={`https://x.com/intent/post?url=${url}&text=${title}`}>X</a>
      <a href={`https://www.linkedin.com/sharing/share-offsite/?url=${url}`}>LinkedIn</a>
    </div>
  );
}

// --- News ---

function NewsStory({ story, lang }: { story: Story; lang: Lang }) {
  const t = ui[lang];
  const version = story.versions[lang];
  const others = otherStories(story);
  return (
    <>
      <article className="container" data-reading data-pagefind-body>
        <SearchData story={story} lang={lang} />
        <div className="grid story-head">
          <nav className="breadcrumb" aria-label={t.breadcrumb} data-pagefind-ignore>
            <a href={`/${lang}/category/${story.category}/`}>{categoryNames[lang][story.category]}</a>
          </nav>
          <h1 className="head-1">{version.title}</h1>
          <p className="summary-large">{version.summary}</p>
          <div className="story-meta" data-pagefind-ignore>
            <span><time dateTime={story.date}>{formatDate(story.date, lang, "long")}</time></span>
            <span>{t.minRead(version.minutes)}</span>
            <ShareLinks story={story} lang={lang} />
          </div>
        </div>
        <div className="story-photo" data-pagefind-ignore>
          <figure>
            <Photo story={story} lang={lang} ratio="21-9" sizes="(max-width: 1520px) 100vw, 1424px" priority />
            <figcaption className="caption"><ImageCredit story={story} lang={lang} /></figcaption>
          </figure>
        </div>
        <div className="grid story-body">
          {version.headings.length > 0 && (
            <aside className="story-left" data-pagefind-ignore>
              <div>
                <b>{t.inThisStory}</b>
                <ul>{version.headings.map((heading) => <li key={heading.id}><a href={`#${heading.id}`}>{heading.text}</a></li>)}</ul>
              </div>
            </aside>
          )}
          <div className="story-text">
            <Body story={story} lang={lang} className="prose" />
            <Sources story={story} lang={lang} />
          </div>
          <aside className="story-right" data-pagefind-ignore>
            <div>
              <h2>{t.related}</h2>
              <ol className="rows">
                {others.slice(0, RELATED_SIZE).map((item) => <RowItem key={item.key} story={item} lang={lang} />)}
              </ol>
              <AdSide lang={lang} />
            </div>
          </aside>
        </div>
      </article>
      <section className="container section" aria-labelledby="next-heading">
        <div className="section-head">
          <h2 id="next-heading">{t.nextStories}</h2>
          <a className="link-line" href={`/${lang}/archive/`}>{t.archive}</a>
        </div>
        <div className="four-up">
          {stories.filter((item) => item.key !== story.key).slice(0, NEXT_SIZE).map((item) => (
            <StoryCard key={item.key} story={item} lang={lang} head="head-4" ratio="3-2" sizes="(max-width: 680px) 50vw, 360px" />
          ))}
        </div>
      </section>
    </>
  );
}

// --- Long Read ---

function LongStory({ story, lang }: { story: Story; lang: Lang }) {
  const t = ui[lang];
  const version = story.versions[lang];
  const more = longStories().filter((item) => item.key !== story.key).slice(0, NEXT_SIZE);
  return (
    <>
      <article data-reading data-pagefind-body>
        <SearchData story={story} lang={lang} />
        <section className="inverted long-cover">
          <div className="container">
            <p className="meta" data-pagefind-ignore><b>{t.longRead}</b></p>
            <h1 className="wide-1">{version.title}</h1>
            <p className="summary">{version.summary}</p>
            <div className="long-cover__meta" data-pagefind-ignore>
              <span><time dateTime={story.date}>{formatDate(story.date, lang, "long")}</time></span>
              <span>{t.minRead(version.minutes)}</span>
            </div>
          </div>
        </section>
        <div className="full-photo" data-pagefind-ignore>
          <Photo story={story} lang={lang} ratio="21-9" sizes="100vw" priority />
        </div>
        <div className="container">
          <p className="caption" data-pagefind-ignore><ImageCredit story={story} lang={lang} /></p>
          <div className="grid long-body">
            {version.headings.length > 0 && (
              <aside className="long-side" data-pagefind-ignore>
                <nav aria-label={t.contents}>
                  <b>{t.contents}</b>
                  <ul data-toc>{version.headings.map((heading) => <li key={heading.id}><a href={`#${heading.id}`}>{heading.text}</a></li>)}</ul>
                </nav>
              </aside>
            )}
            <div className="long-text">
              <Body story={story} lang={lang} className="long-text prose drop-cap" />
              <Sources story={story} lang={lang} />
            </div>
          </div>
        </div>
      </article>
      {more.length > 0 && (
        <section className="inverted long-read">
          <div className="container">
            <div className="section-head"><h2>{t.moreLong}</h2></div>
            <div className="four-up">
              {more.map((item) => <StoryCard key={item.key} story={item} lang={lang} head="wide-3" ratio="3-2" />)}
            </div>
          </div>
        </section>
      )}
    </>
  );
}

// --- Page ---

export function StoryPage() {
  const lang = useLang();
  const { slug } = useParams();
  const story = findStory(lang, slug);
  if (!story) throw new Error(`Unknown story: ${slug}`);
  const version = story.versions[lang];
  const Article = story.kind === "long" ? LongStory : NewsStory;
  return (
    <Layout title={version.title} description={version.summary} story={storyHead(story, lang)}>
      <Article story={story} lang={lang} />
    </Layout>
  );
}
