/**
 * file: src/pages/Stories.tsx
 * importable: Stories
 *
 * description: The list of every story and the state of the site.
 */

import { useEffect, useState } from "react";
import { call, type Job, type StoryRow } from "../api";

const FILTERS = ["All", "Live", "Drafts", "Withdrawn"] as const;
type Filter = (typeof FILTERS)[number];

function matches(row: StoryRow, filter: Filter): boolean {
  if (filter === "All") return true;
  if (filter === "Live") return row.state === "live" || row.state === "changed";
  return filter === "Drafts" ? row.state === "draft" : row.state === "withdrawn";
}

function State({ row }: { row: StoryRow }) {
  if (row.state === "live") return <b>Live</b>;
  if (row.state === "changed") return <><b>Live</b>, changes unpublished</>;
  return <>{row.state === "draft" ? "Draft" : "Withdrawn"}</>;
}

function SiteStatus({ status }: { status: { active: Job | null; last: Job | null } | null }) {
  if (!status) return null;
  const { active, last } = status;
  if (active) return <p className="status"><b>Working.</b> A {active.kind} job is running.</p>;
  if (!last) return <p className="status">No release yet.</p>;
  if (last.status === "failed") return <p className="status"><b>The last job failed.</b> The live site did not change.</p>;
  return <p className="status"><b>Site is live.</b> Last release {last.duration_ms} ms, {last.finished_at} UTC. Queue is empty.</p>;
}

export function Stories() {
  const [rows, setRows] = useState<StoryRow[] | null>(null);
  const [status, setStatus] = useState<{ active: Job | null; last: Job | null } | null>(null);
  const [filter, setFilter] = useState<Filter>("All");

  useEffect(() => {
    void call<StoryRow[]>("GET", "/stories").then(setRows);
    void call<{ active: Job | null; last: Job | null }>("GET", "/status").then(setStatus);
  }, []);

  const shown = rows?.filter((row) => matches(row, filter)) ?? [];
  return (
    <>
      <div className="page-top">
        <div><h1 className="head-2">Stories</h1><SiteStatus status={status} /></div>
        <a className="button" href="#edit/new">New draft</a>
      </div>
      <div className="filters">
        {FILTERS.map((name) => <button key={name} type="button" aria-pressed={name === filter} onClick={() => setFilter(name)}>{name}</button>)}
      </div>
      {rows && shown.length === 0 && <p className="empty">Nothing here.</p>}
      {shown.map((row) => (
        <a key={row.handle} className="story-row" href={`#edit/${row.handle}`}>
          <time className="status">{row.published_at ?? row.saved_at}</time>
          <div>
            <p className="meta"><b>{row.category}</b></p>
            <h2 className="head-4">{row.title}</h2>
            <small>{row.handle}</small>
          </div>
          <p className="status story-row__state"><State row={row} /></p>
          <p className="story-row__num">v{row.latest}</p>
        </a>
      ))}
    </>
  );
}
