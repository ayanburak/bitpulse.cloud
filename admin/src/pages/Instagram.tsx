/**
 * file: src/pages/Instagram.tsx
 * importable: Instagram
 *
 * description: The Instagram account numbers, its audience and every post with its picture, numbers and chart.
 */

// NOTE: Everything here was read from Instagram by the insights service. The page only reads, so
// nothing on it can change a post. A number Instagram does not give for a kind of post shows a dash.
//
// NOTE: The account numbers are summed over the last seven finished days. The newest day is today,
// which every round writes with the follower count. It is left out of the sums because Meta has no
// totals for it yet.

import { useCallback, useEffect, useState } from "react";
import { call, type InstagramAudience, type InstagramDay, type InstagramPost } from "../api";
import { InstagramChart } from "./InstagramChart";

type Counts = NonNullable<InstagramPost["counts"]>;
type DayNumber = Exclude<keyof InstagramDay, "day">;

const FILTERS = [["", "All"], ["reel", "Reels"], ["image", "Images"], ["carousel", "Carousels"]];
const KINDS: Record<InstagramPost["kind"], string> = { reel: "Reel", image: "Image", carousel: "Carousel" };
const NUMBERS: [Exclude<keyof Counts, "at" | "watch_ms" | "watch_total_ms">, string][] = [
  ["views", "Views"], ["reach", "Reach"], ["likes", "Likes"], ["comments", "Comments"], ["saves", "Saves"], ["shares", "Shares"],
  ["reposts", "Reposts"], ["interactions", "Interactions"],
];
const WEEK: [DayNumber, string][] = [
  ["reach", "Reach"], ["views", "Views"], ["engaged", "Accounts engaged"], ["interactions", "Interactions"],
  ["profile_views", "Profile views"], ["link_taps", "Bio link taps"], ["follows", "Follows"], ["unfollows", "Unfollows"],
];
const GROUPS: [InstagramAudience["rows"][number]["breakdown"], string][] = [["age", "Age"], ["gender", "Gender"], ["country", "Country"], ["city", "City"]];
const TOP = 5;

const plain = (value: number | null | undefined) => (value === null || value === undefined ? "–" : value.toLocaleString("en-US"));
const seconds = (ms: number | null | undefined) => (ms === null || ms === undefined ? "–" : `${(ms / 1000).toFixed(1)} s`);
const hours = (ms: number | null | undefined) => (ms === null || ms === undefined ? "–" : `${(ms / 3_600_000).toFixed(1)} h`);
const share = (part: number, whole: number) => (whole ? `${Math.round((part / whole) * 100)}%` : "–");
// Instagram gives times like 2026-11-05T14:02:11+0000, the panel shows them in the form it uses everywhere.
const moment = (value: string) => value.slice(0, 16).replace("T", " ");

// A sum stays a dash when no day of the week had the number at all.
function total(days: InstagramDay[], key: DayNumber): number | null {
  const known = days.map((day) => day[key]).filter((value): value is number => value !== null);
  return known.length ? known.reduce((sum, value) => sum + value, 0) : null;
}

function Account({ days }: { days: InstagramDay[] }) {
  if (!days.length) return null;
  const week = days.filter((day) => day.day < days[0].day).slice(0, 7);
  // Meta counts the split apart from the total, and its parts can add up to a little more than the
  // reach of the same day. The share is taken within the split, over the days that have one.
  const split = week.filter((day) => day.reach_followers !== null && day.reach_others !== null);
  const others = total(split, "reach_others");
  const reached = others === null ? null : others + (total(split, "reach_followers") ?? 0);
  return (
    <section className="insta-section">
      <h2 className="head-4">Account, last seven days</h2>
      <dl className="insta-account">
        <div><dt>Followers now</dt><dd>{plain(days[0].followers)}</dd></div>
        {WEEK.map(([key, name]) => <div key={key}><dt>{name}</dt><dd>{plain(total(week, key))}</dd></div>)}
        <div><dt>Reach from non-followers</dt><dd>{reached !== null && others !== null ? share(others, reached) : "–"}</dd></div>
      </dl>
    </section>
  );
}

function Audience({ audience }: { audience: InstagramAudience }) {
  const rows = audience.rows.filter((row) => row.audience === "followers");
  return (
    <section className="insta-section">
      <h2 className="head-4">Followers</h2>
      {rows.length === 0
        ? <p className="status">Instagram shows age, gender, country, city and online hours of the followers once the account has one hundred followers.</p>
        : <div className="insta-audience">
            {GROUPS.map(([key, name]) => {
              const group = rows.filter((row) => row.breakdown === key);
              const sum = group.reduce((all, row) => all + row.value, 0);
              return (
                <div key={key}>
                  <h3 className="status"><b>{name}</b></h3>
                  <ol>{group.slice(0, TOP).map((row) => <li key={row.key}><span>{row.key}</span><span>{share(row.value, sum)}</span></li>)}</ol>
                </div>
              );
            })}
          </div>}
      {audience.day && <p className="status">Read {audience.day}.</p>}
    </section>
  );
}

function Post({ post }: { post: InstagramPost }) {
  const [open, setOpen] = useState(false);
  const counts = post.counts;
  return (
    <article className="insta-post">
      {post.thumb
        ? <img className="insta-post__thumb" src={`/panel-api/instagram/${post.id}/thumb`} alt="" loading="lazy" />
        : <div className="insta-post__thumb insta-post__thumb--empty" />}
      <div className="insta-post__body">
        <p className="status"><b>{KINDS[post.kind]}</b> {moment(post.posted_at)} UTC</p>
        <p className="insta-post__caption">{post.caption || "No caption"}</p>
        <dl className="insta-numbers">
          {NUMBERS.map(([key, name]) => <div key={key}><dt>{name}</dt><dd>{plain(counts?.[key])}</dd></div>)}
          {post.kind === "reel" && <>
            <div><dt>Avg. watch</dt><dd>{seconds(counts?.watch_ms)}</dd></div>
            <div><dt>Total watch</dt><dd>{hours(counts?.watch_total_ms)}</dd></div>
          </>}
        </dl>
        <p className="status">
          {counts ? <>Read {counts.at} UTC</> : <>Not read yet</>}
          {" · "}
          <button className="text-button" type="button" aria-expanded={open} onClick={() => setOpen(!open)}>{open ? "Hide chart" : "Chart"}</button>
          {" · "}
          <a className="text-button" href={post.permalink} target="_blank" rel="noopener noreferrer">Open on Instagram</a>
        </p>
        {open && <InstagramChart id={post.id} />}
      </div>
    </article>
  );
}

export function Instagram() {
  const [filter, setFilter] = useState("");
  const [rows, setRows] = useState<InstagramPost[] | null>(null);
  const [days, setDays] = useState<InstagramDay[]>([]);
  const [audience, setAudience] = useState<InstagramAudience>({ day: null, rows: [] });
  const [more, setMore] = useState(false);

  const load = useCallback(async (offset: number) => {
    const query = new URLSearchParams({ offset: String(offset) });
    if (filter) query.set("kind", filter);
    const page = await call<{ rows: InstagramPost[]; more: boolean; days: InstagramDay[]; audience: InstagramAudience }>("GET", `/instagram?${query}`);
    setRows((current) => (offset && current ? [...current, ...page.rows] : page.rows));
    setDays(page.days);
    setAudience(page.audience);
    setMore(page.more);
  }, [filter]);

  useEffect(() => { void load(0); }, [load]);

  return (
    <>
      <div className="page-top"><div>
        <h1 className="head-2">Instagram</h1>
        <p className="status">Numbers are read every hour for a week after a post goes out, then once a day.</p>
      </div></div>
      <Account days={days} />
      <Audience audience={audience} />
      <h2 className="head-4">Posts</h2>
      <div className="filters">
        {FILTERS.map(([key, name]) => <button key={key} type="button" aria-pressed={key === filter} onClick={() => setFilter(key)}>{name}</button>)}
      </div>
      {rows && rows.length === 0 && <p className="empty">Nothing here.</p>}
      {rows?.map((post) => <Post key={post.id} post={post} />)}
      {more && <button className="button button--outline load-more" type="button" onClick={() => void load(rows!.length)}>More posts</button>}
    </>
  );
}
