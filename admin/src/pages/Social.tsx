/**
 * file: src/pages/Social.tsx
 * importable: Social
 *
 * description: The finished social posts, ready to copy, download and mark as shared.
 */

// NOTE: The files are made on the device and uploaded with the story. This page only shows them, so
// nothing here can change a post. The video is a download because the panel plays no media.
//
// NOTE: A clip goes to Instagram only and has no story. It has no X post and its own routes.

import { useCallback, useEffect, useState } from "react";
import { call, type SocialRow } from "../api";

const FILTERS = [["false", "Waiting"], ["true", "Shared"], ["", "All"]];
const COPIED_MS = 1500;

const base = (post: SocialRow) => `/${post.kind === "clip" ? "clips" : "social"}/${encodeURIComponent(post.handle)}`;
const fileUrl = (post: SocialRow, name: string) => `/panel-api${base(post)}/${name}`;

function Copyable({ name, text }: { name: string; text: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), COPIED_MS);
  }

  return (
    <div>
      <p className="social-label">{name}<button className="text-button" type="button" onClick={() => void copy()}>{copied ? "Copied" : "Copy"}</button></p>
      <p className="social-text">{text}</p>
    </div>
  );
}

function Post({ post, changed }: { post: SocialRow; changed: () => void }) {
  async function toggle() {
    await call("POST", `${base(post)}/shared`, { shared: !post.shared_at });
    changed();
  }

  return (
    <article className="social-post">
      <img className="social-post__page" src={fileUrl(post, post.pages[0])} alt="" loading="lazy" />
      <div className="social-post__body">
        <div>
          {post.kind === "clip" && <p className="status"><b>Clip</b> Instagram only</p>}
          <h2 className="head-4">{post.title}</h2>
          <p className="status">{post.shared_at ? <><b>Shared</b> {post.shared_at} UTC</> : <>Uploaded {post.uploaded_at} UTC</>}</p>
        </div>
        {post.x && <Copyable name="X" text={post.x} />}
        <Copyable name="Instagram caption" text={post.caption} />
        <div className="event-actions">
          {post.pages.map((name) => <a key={name} className="text-button" href={fileUrl(post, name)} download>{name}</a>)}
          <a className="text-button" href={fileUrl(post, "post.mp4")} download>post.mp4</a>
          <button className="button button--outline" type="button" onClick={() => void toggle()}>{post.shared_at ? "Mark as not shared" : "Mark as shared"}</button>
        </div>
      </div>
    </article>
  );
}

export function Social() {
  const [filter, setFilter] = useState("false");
  const [rows, setRows] = useState<SocialRow[] | null>(null);
  const [more, setMore] = useState(false);

  const load = useCallback(async (offset: number) => {
    const query = new URLSearchParams({ offset: String(offset) });
    if (filter) query.set("shared", filter);
    const page = await call<{ rows: SocialRow[]; more: boolean }>("GET", `/social?${query}`);
    setRows((current) => (offset && current ? [...current, ...page.rows] : page.rows));
    setMore(page.more);
  }, [filter]);

  useEffect(() => { void load(0); }, [load]);

  return (
    <>
      <div className="page-top"><div>
        <h1 className="head-2">Social</h1>
        <p className="status">Posts stay here for thirty days after they are uploaded.</p>
      </div></div>
      <div className="filters">
        {FILTERS.map(([key, name]) => <button key={key} type="button" aria-pressed={key === filter} onClick={() => setFilter(key)}>{name}</button>)}
      </div>
      {rows && rows.length === 0 && <p className="empty">Nothing here.</p>}
      {rows?.map((post) => <Post key={post.handle} post={post} changed={() => void load(0)} />)}
      {more && <button className="button button--outline load-more" type="button" onClick={() => void load(rows!.length)}>More posts</button>}
    </>
  );
}
