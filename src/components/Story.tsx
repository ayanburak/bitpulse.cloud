/**
 * file: src/components/Story.tsx
 * importable: Photo, ImageCredit, Meta, StoryCard, RowItem
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

export function Meta({ story, lang, dateStyle = "day" }: { story: Story; lang: Lang; dateStyle?: DateStyle | null }) {
  return (
    <p className="meta">
      <b>{categoryNames[lang][story.category]}</b>{" "}
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
