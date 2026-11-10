/**
 * file: src/pages/Instagram.tsx
 * importable: Instagram
 *
 * description: The Instagram posts with their pictures and latest numbers, and the account numbers of the last days.
 */

// NOTE: Everything here was read from Instagram by the insights service. The page only reads, so
// nothing on it can change a post. A number Instagram does not give for a kind of post shows a dash.

import { useCallback, useEffect, useState } from "react";
import { call, type InstagramDay, type InstagramPost } from "../api";

const FILTERS = [["", "All"], ["reel", "Reels"], ["image", "Images"], ["carousel", "Carousels"]];
const KINDS: Record<InstagramPost["kind"], string> = { reel: "Reel", image: "Image", carousel: "Carousel" };
const NUMBERS: [Exclude<keyof NonNullable<InstagramPost["counts"]>, "at" | "watch_ms">, string][] = [
  ["views", "Views"], ["reach", "Reach"], ["likes", "Likes"], ["comments", "Comments"], ["saves", "Saves"], ["shares", "Shares"],
];

const plain = (value: number | null | undefined) => (value === null || value === undefined ? "–" : value.toLocaleString("en-US"));
const seconds = (ms: number | null | undefined) => (ms === null || ms === undefined ? "–" : `${(ms / 1000).toFixed(1)} s`);
// Instagram gives times like 2026-11-05T14:02:11+0000, the panel shows them in the form it uses everywhere.
const moment = (value: string) => value.slice(0, 16).replace("T", " ");

function Account({ days }: { days: InstagramDay[] }) {
  const today = days[0];
  const past = days.filter((day) => day !== today);
  const sum = (key: "profile_views" | "link_taps") => past.slice(0, 7).reduce((total, day) => total + (day[key] ?? 0), 0);
  if (!today) return null;
  return (
    <dl className="insta-account">
      <div><dt>Followers</dt><dd>{plain(today.followers)}</dd></div>
      <div><dt>Profile views, last 7 days</dt><dd>{plain(sum("profile_views"))}</dd></div>
      <div><dt>Link taps, last 7 days</dt><dd>{plain(sum("link_taps"))}</dd></div>
    </dl>
  );
}

function Post({ post }: { post: InstagramPost }) {
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
          {post.kind === "reel" && <div><dt>Avg. watch</dt><dd>{seconds(counts?.watch_ms)}</dd></div>}
        </dl>
        <p className="status">
          {counts ? <>Read {counts.at} UTC</> : <>Not read yet</>}
          {" · "}
          <a className="text-button" href={post.permalink} target="_blank" rel="noopener noreferrer">Open on Instagram</a>
        </p>
      </div>
    </article>
  );
}

export function Instagram() {
  const [filter, setFilter] = useState("");
  const [rows, setRows] = useState<InstagramPost[] | null>(null);
  const [days, setDays] = useState<InstagramDay[]>([]);
  const [more, setMore] = useState(false);

  const load = useCallback(async (offset: number) => {
    const query = new URLSearchParams({ offset: String(offset) });
    if (filter) query.set("kind", filter);
    const page = await call<{ rows: InstagramPost[]; more: boolean; days: InstagramDay[] }>("GET", `/instagram?${query}`);
    setRows((current) => (offset && current ? [...current, ...page.rows] : page.rows));
    setDays(page.days);
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
      <div className="filters">
        {FILTERS.map(([key, name]) => <button key={key} type="button" aria-pressed={key === filter} onClick={() => setFilter(key)}>{name}</button>)}
      </div>
      {rows && rows.length === 0 && <p className="empty">Nothing here.</p>}
      {rows?.map((post) => <Post key={post.id} post={post} />)}
      {more && <button className="button button--outline load-more" type="button" onClick={() => void load(rows!.length)}>More posts</button>}
    </>
  );
}
