/**
 * file: src/pages/Archive.tsx
 * importable: Archive
 *
 * description: Month pages with a calendar that marks the days with published stories.
 */

import { useParams } from "react-router";
import { monthKeys, storiesInMonth, storyPath } from "../catalog";
import { Layout, useLang } from "../components/Layout";
import { categoryNames, formatDate, ui, type Lang } from "../i18n";
import type { Story } from "../stories";

// --- Constants ---

const MONTHS_PER_YEAR = 12;
const FIRST_MONDAY = "2026-01-05";
const DAY_MS = 86_400_000;

// --- Helpers ---

function monthPath(lang: Lang, month: string): string {
  return `/${lang}/archive/${month.replace("-", "/")}/`;
}

// Weekday names come from a known Monday, so the calendar follows the language without a word list.
function weekdayNames(lang: Lang): string[] {
  const monday = Date.parse(`${FIRST_MONDAY}T00:00:00Z`);
  return Array.from({ length: 7 }, (_, day) => formatDate(new Date(monday + day * DAY_MS), lang, "weekday"));
}

// --- Parts ---

function MonthTabs({ lang, month }: { lang: Lang; month: string }) {
  const t = ui[lang];
  const year = month.slice(0, 4);
  const published = new Set(monthKeys());
  return (
    <nav className="tabs" aria-label={t.months}>
      <div className="rail">
        <ul>
          {Array.from({ length: MONTHS_PER_YEAR }, (_, index) => {
            const key = `${year}-${String(index + 1).padStart(2, "0")}`;
            const name = formatDate(`${key}-01`, lang, "monthName");
            if (!published.has(key)) return <li key={key}><a aria-disabled="true">{name}</a></li>;
            return <li key={key}><a href={monthPath(lang, key)} aria-current={key === month ? "page" : undefined}>{name}</a></li>;
          })}
        </ul>
        <i className="pulse" aria-hidden="true"><b></b></i>
      </div>
    </nav>
  );
}

// The months list runs from newest to oldest, so the next index is the older month.
function MonthArrows({ lang, month }: { lang: Lang; month: string }) {
  const t = ui[lang];
  const list = monthKeys();
  const index = list.indexOf(month);
  const older = list[index + 1];
  const newer = list[index - 1];
  return (
    <div>
      {older && <a className="arrow" href={monthPath(lang, older)} aria-label={t.prevMonth}>←</a>}
      {newer && <a className="arrow" href={monthPath(lang, newer)} aria-label={t.nextMonth}>→</a>}
    </div>
  );
}

function Calendar({ lang, month, items }: { lang: Lang; month: string; items: Story[] }) {
  const [year, monthNumber] = month.split("-").map(Number);
  const dayCount = new Date(Date.UTC(year, monthNumber, 0)).getUTCDate();
  // The site calendar starts on Monday, while JavaScript counts weeks from Sunday.
  const offset = (new Date(Date.UTC(year, monthNumber - 1, 1)).getUTCDay() + 6) % 7;
  const trailing = (7 - ((offset + dayCount) % 7)) % 7;

  // Stories are sorted newest first, so writing them in reverse keeps the newest story of a day.
  const byDay = new Map([...items].reverse().map((story) => [Number(story.date.slice(8)), story]));

  return (
    <div className="calendar">
      {weekdayNames(lang).map((name) => <div key={name} className="calendar__day-name">{name}</div>)}
      {Array.from({ length: offset }, (_, index) => <div key={`start-${index}`} className="calendar__empty" />)}
      {Array.from({ length: dayCount }, (_, index) => {
        const day = index + 1;
        const story = byDay.get(day);
        if (!story) return <div key={day} className="calendar__empty">{day}</div>;
        return <a key={day} href={storyPath(story, lang)} aria-label={story.versions[lang].title}><b>{day}</b></a>;
      })}
      {Array.from({ length: trailing }, (_, index) => <div key={`end-${index}`} className="calendar__empty" />)}
    </div>
  );
}

// --- Page ---

export function Archive() {
  const lang = useLang();
  const t = ui[lang];
  const { year, month } = useParams();
  const key = year && month ? `${year}-${month}` : monthKeys()[0];
  const items = storiesInMonth(key);
  const label = formatDate(`${key}-01`, lang, "month");

  return (
    <Layout title={year ? `${t.archive}: ${label}` : t.archive}>
      <div className="container">
        <div className="page-head"><h1 className="head-1">{t.archive}</h1></div>
        <MonthTabs lang={lang} month={key} />
        <div className="grid archive">
          <section className="archive__calendar">
            <div className="month">
              <h2>{label}</h2>
              <MonthArrows lang={lang} month={key} />
            </div>
            <Calendar lang={lang} month={key} items={items} />
            <p className="caption">{t.calendarNote}</p>
          </section>
          <section className="archive__list">
            <h2 className="head-3">{t.monthStories(label)}</h2>
            <ol className="count-list">
              {items.map((story) => (
                <li key={story.key}>
                  <a href={storyPath(story, lang)}>
                    <time dateTime={story.date}>{formatDate(story.date, lang, "tiny")}</time>
                    <span className="link-line">{story.versions[lang].title}</span>
                    <small>{categoryNames[lang][story.category]}</small>
                  </a>
                </li>
              ))}
            </ol>
          </section>
        </div>
      </div>
    </Layout>
  );
}
