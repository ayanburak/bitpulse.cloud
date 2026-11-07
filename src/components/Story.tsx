/**
 * file: src/components/Story.tsx
 * importable: Photo, ImageCredit, Meta, StoryCard, RowItem, StoryIndex
 *
 * description: Reusable story pieces such as images, cards and meta lines.
 */

import { imageSet, imageUrl, storyPath } from "../catalog";
import { categoryNames, formatDate, ui, type Lang } from "../i18n";
import type { Story } from "../stories";

type Ratio = "21-9" | "16-9" | "3-2" | "4-3" | "4-5";
type DateStyle = "day" | "long";

// --- Image ---

interface PhotoProps {
  story: Story;
  lang: Lang;
  ratio: Ratio;
  sizes: string;
  priority?: boolean;
}

// Images high on the page load straight away, the rest wait until the reader gets near them.
export function Photo({ story, lang, ratio, sizes, priority = false }: PhotoProps) {
  return (
    <div className={`photo ratio-${ratio}`}>
      <img
        src={imageUrl(story, 1280)}
        srcSet={imageSet(story)}
        sizes={sizes}
        alt={story.versions[lang].image.alt}
        loading={priority ? "eager" : "lazy"}
        decoding="async"
      />
    </div>
  );
}

// Licenses such as CC BY require the credit, the license and a link next to the image.
export function ImageCredit({ story, lang }: { story: Story; lang: Lang }) {
  const t = ui[lang];
  const { credit, license, licenseUrl, source } = story.versions[lang].image;
  return (
    <>
      {t.photo}: {credit}. {t.license}: <a href={licenseUrl}>{license}</a>. <a href={source}>{t.imageSource}</a>
    </>
  );
}

// --- Text ---

/**
 * Shows a time in UTC. The browser script rewrites it in the reader's own time zone, so readers
 * without JavaScript still see a correct time with its zone.
 *
 * @param time Full ISO time in UTC.
 * @param style stamp gives the day and the time, clock only the time.
 */
export function LocalTime({ time, lang, style }: { time: string; lang: Lang; style: "stamp" | "clock" }) {
  return <time dateTime={time} data-local={style}>{formatDate(time, lang, style)} UTC</time>;
}

export function Meta({ story, lang, dateStyle = "day" }: { story: Story; lang: Lang; dateStyle?: DateStyle | null }) {
  return (
    <p className="meta">
      <b>{categoryNames[lang][story.category]}</b>{" "}
      {story.promoted && <span className="meta__updated">{ui[lang].updated}</span>}{" "}
      {dateStyle && <time dateTime={story.date}>{formatDate(story.date, lang, dateStyle)}</time>}
    </p>
  );
}

// --- Card ---

interface CardProps {
  story: Story;
  lang: Lang;
  head: "head-2" | "head-3" | "head-4" | "wide-3";
  ratio?: Ratio;
  sizes?: string;
  summary?: boolean;
  className?: string;
}

// Headings stay h3 because cards always sit under a section heading.
export function StoryCard({ story, lang, head, ratio, sizes = "400px", summary = false, className = "" }: CardProps) {
  const version = story.versions[lang];
  return (
    <article className={`card ${className}`.trim()}>
      {ratio && <Photo story={story} lang={lang} ratio={ratio} sizes={sizes} />}
      <Meta story={story} lang={lang} />
      <h3 className={head}>
        <a href={storyPath(story, lang)}><span className="link-line">{version.title}</span></a>
      </h3>
      {summary && <p className="summary">{version.summary}</p>}
    </article>
  );
}

export function RowItem({ story, lang }: { story: Story; lang: Lang }) {
  return (
    <li>
      <article className="card">
        <Meta story={story} lang={lang} dateStyle={null} />
        <h3 className="head-4">
          <a href={storyPath(story, lang)}><span className="link-line">{story.versions[lang].title}</span></a>
        </h3>
      </article>
    </li>
  );
}

// --- List ---

const INDEX_SIDE_SIZE = 4;

// Category pages and the Explained page show their stories the same way: one lead, a few beside
// it and the rest as rows.
export function StoryIndex({ stories, lang }: { stories: Story[]; lang: Lang }) {
  const t = ui[lang];
  const [first, ...rest] = stories;
  const side = rest.slice(0, INDEX_SIDE_SIZE);
  const remaining = rest.slice(INDEX_SIDE_SIZE);
  if (!first) return <p className="summary">{t.noStories}</p>;
  return (
    <>
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
    </>
  );
}
