/**
 * file: src/pages/Radar.tsx
 * importable: Radar
 *
 * description: Candidates, the events the radar left out and links added by hand.
 */

// NOTE: The radar reports thousands of events a day, so this page never holds a full list. The
// server filters and cuts it into pages, and a row loads its details only when it is opened.
//
// NOTE: Every title, summary and link here was read from the open web. They are shown as plain
// text, and the server has already refused any link that is not a web address.

import { useCallback, useEffect, useRef, useState } from "react";
import { call, type EventDetail, type EventPage, type EventRow, type LinkRow } from "../api";

type Group = "candidates" | "eliminated";

const STATES = [["", "All"], ["new", "New"], ["do", "Do"], ["skip", "Skip"], ["draft", "Draft"], ["published", "Published"]];
const STAGES = [["scored", "Scored"], ["reserve", "Passed the bar"], ["below", "Below the bar"], ["unseen", "Not read"], ["noise", "Filtered"], ["merged", "Merged"]];
const STAGE_NAMES: Record<string, string> = { sent: "Sent", reserve: "Waiting", below: "Below bar", unseen: "Not read", noise: "Filtered", merged: "Merged" };
const STATE_NAMES: Record<string, string> = { new: "New", do: "Do", skip: "Skip", draft: "Draft", published: "Published" };
const CATEGORIES = ["world", "economy", "technology", "science", "health", "culture", "sports"];
const SOURCE_STEPS = [0, 2, 3, 5];
const BRIEF_POLL_MS = 5000;
const TYPING_MS = 300;

const label = (number: number) => `R-${String(number).padStart(4, "0")}`;

// --- Details ---

function Links({ links }: { links: EventDetail["links"] }) {
  return (
    <ul className="event-links">
      {links.map((link) => (
        <li key={link.url}><span>{link.source}</span><a href={link.url} target="_blank" rel="noopener noreferrer">{link.title}</a></li>
      ))}
    </ul>
  );
}

// A brief takes a while because the radar reads every source, so the row asks again until it is there.
function Details({ number, changed }: { number: number; changed: (decision: "do" | "skip") => void }) {
  const [item, setItem] = useState<EventDetail | null>(null);
  const [brief, setBrief] = useState<string | null>(null);

  const load = useCallback(async () => setItem(await call<EventDetail>("GET", `/radar/events/${number}`)), [number]);
  useEffect(() => { void load(); }, [load]);

  const waiting = item?.decision === "do" && !item.has_brief && !item.brief_error;
  useEffect(() => {
    if (!waiting) return;
    const timer = setInterval(() => void load(), BRIEF_POLL_MS);
    return () => clearInterval(timer);
  }, [waiting, load]);

  if (!item) return <div className="event-detail"><p className="event-detail__meta">Loading.</p></div>;

  async function decide(decision: "do" | "skip") {
    await call("POST", `/radar/events/${number}/decision`, { decision });
    changed(decision);
    await load();
  }

  async function retry() {
    await call("POST", `/radar/events/${number}/retry-brief`);
    await load();
  }

  async function showBrief() {
    setBrief((await call<{ text: string }>("GET", `/radar/events/${number}/brief`)).text);
  }

  const open = item.status !== "draft" && item.status !== "published";
  return (
    <div className="event-detail">
      <p className="event-detail__title">{item.title}</p>
      {item.reason && <p>{item.reason}</p>}
      {item.summary && <p className="event-detail__meta">{item.summary}</p>}
      <p className="event-detail__meta">
        First seen {item.first_seen.slice(0, 16).replace("T", " ")} UTC, {item.sources} outlets
        {item.impact !== null && `, impact ${item.impact}, tension ${item.tension}, visual ${item.visual}`}
        {item.merged_into !== null && `, merged into ${label(item.merged_into)}`}
        {item.decided_at && `, decided ${item.decided_at} in ${item.decided_by}`}
        {item.handle && `, story ${item.handle}`}
      </p>
      <Links links={item.links} />
      <div className="event-actions">
        {open && <button className={`button${item.decision === "do" ? " button--outline" : ""}`} type="button" onClick={() => void decide("do")} disabled={item.decision === "do"}>Do</button>}
        {open && item.stage === "sent" && <button className="button button--outline" type="button" onClick={() => void decide("skip")} disabled={item.decision === "skip"}>Skip</button>}
        {item.has_brief && brief === null && <button className="text-button" type="button" onClick={() => void showBrief()}>Show brief</button>}
        {waiting && <span className="event-detail__meta">The radar is writing the brief.</span>}
        {item.brief_error && <><span className="event-detail__meta">The brief failed: {item.brief_error}</span><button className="text-button" type="button" onClick={() => void retry()}>Try again</button></>}
      </div>
      {brief !== null && <pre className="brief-text">{brief}</pre>}
    </div>
  );
}

function Row({ row, group, changed }: { row: EventRow; group: Group; changed: (number: number, decision: "do" | "skip") => void }) {
  const [open, setOpen] = useState(false);
  const active = row.status === "do" || row.status === "draft" || row.status === "published";
  return (
    <div className="event-row">
      <button className="event-row__head" type="button" aria-expanded={open} onClick={() => setOpen(!open)}>
        <span className="event-row__num">{label(row.number)}</span>
        <span className="event-row__score">{row.score === null ? "–" : row.score.toFixed(1)}</span>
        <span className="event-row__title">{row.title}</span>
        <span className="event-row__muted">{row.category ?? ""}</span>
        <span className="event-row__muted">{row.sources} outlet{row.sources === 1 ? "" : "s"}</span>
        <span className={`event-row__state${active ? " event-row__state--active" : ""}`}>{group === "candidates" || row.decision ? STATE_NAMES[row.status] : STAGE_NAMES[row.stage]}</span>
      </button>
      {open && <Details number={row.number} changed={(decision) => changed(row.number, decision)} />}
    </div>
  );
}

// --- Event List ---

function Events({ group }: { group: Group }) {
  const [choice, setChoice] = useState(group === "candidates" ? "" : "scored");
  const [day, setDay] = useState("");
  const [category, setCategory] = useState("");
  const [minSources, setMinSources] = useState(0);
  const [typed, setTyped] = useState("");
  const [text, setText] = useState("");
  const [page, setPage] = useState<EventPage | null>(null);
  const latest = useRef(0);

  useEffect(() => {
    const timer = setTimeout(() => setText(typed.trim()), TYPING_MS);
    return () => clearTimeout(timer);
  }, [typed]);

  // An answer that arrives after the filters changed again belongs to a list nobody is looking at.
  const load = useCallback(async (cursor?: string) => {
    const query = new URLSearchParams({ group });
    if (choice) query.set(group === "candidates" ? "status" : "stage", choice);
    if (group === "eliminated" && !day) query.set("recent", "true");
    if (day) query.set("day", day);
    if (category) query.set("category", category);
    if (minSources) query.set("min_sources", String(minSources));
    if (text) query.set("text", text);
    if (cursor) query.set("cursor", cursor);
    const ticket = ++latest.current;
    const answer = await call<EventPage>("GET", `/radar/events?${query}`);
    if (ticket !== latest.current) return;
    setPage((current) => (cursor && current ? { ...answer, rows: [...current.rows, ...answer.rows] } : answer));
  }, [group, choice, day, category, minSources, text]);

  useEffect(() => { void load(); }, [load]);

  const changed = (number: number, decision: "do" | "skip") => {
    setPage((current) => current && { ...current, rows: current.rows.map((row) => (row.number === number ? { ...row, decision, status: decision } : row)) });
  };

  const options = group === "candidates" ? STATES : STAGES;
  const counts = page?.counts ?? {};
  const total = (key: string) => {
    if (key === "") return Object.values(counts).reduce((sum, value) => sum + value, 0);
    return key === "scored" ? (counts.reserve ?? 0) + (counts.below ?? 0) : counts[key] ?? 0;
  };

  return (
    <>
      <div className="filters filters--wrap">
        {options.map(([key, name]) => (
          <button key={key} type="button" aria-pressed={key === choice} onClick={() => setChoice(key)}>{name} <small>{total(key)}</small></button>
        ))}
      </div>
      <div className="radar-tools">
        <label className="field"><span>Headline</span><input value={typed} maxLength={100} onChange={(event) => setTyped(event.target.value)} /></label>
        <label className="field"><span>{group === "eliminated" && !day ? "Day, now the last 24 hours" : "Day"}</span><input type="date" value={day} onChange={(event) => setDay(event.target.value)} /></label>
        <label className="field"><span>Category</span>
          <select value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="">All</option>
            {CATEGORIES.map((name) => <option key={name} value={name}>{name}</option>)}
          </select>
        </label>
        <label className="field"><span>Outlets</span>
          <select value={minSources} onChange={(event) => setMinSources(Number(event.target.value))}>
            {SOURCE_STEPS.map((step) => <option key={step} value={step}>{step ? `${step} or more` : "Any"}</option>)}
          </select>
        </label>
      </div>
      {page && page.rows.length === 0 && <p className="empty">Nothing here.</p>}
      {page?.rows.map((row) => <Row key={row.number} row={row} group={group} changed={changed} />)}
      {page?.next && <button className="button button--outline load-more" type="button" onClick={() => void load(page.next!)}>Next fifty</button>}
    </>
  );
}

// --- Links ---

function AddLink() {
  const [links, setLinks] = useState<LinkRow[]>([]);
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => setLinks(await call<LinkRow[]>("GET", "/radar/links")), []);
  useEffect(() => {
    void load();
    const timer = setInterval(() => void load(), BRIEF_POLL_MS);
    return () => clearInterval(timer);
  }, [load]);

  async function add(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await call("POST", "/radar/links", { url });
      setUrl("");
      await load();
    } catch (problem) {
      setError(problem instanceof Error ? problem.message : "the link was refused");
    }
  }

  const stateOf = (link: LinkRow) => {
    if (link.state === "waiting") return "Waiting for the radar";
    return link.state === "failed" ? `Failed: ${link.error}` : `Saved as ${label(link.number!)}`;
  };

  return (
    <>
      <form className="link-form" onSubmit={(event) => void add(event)}>
        <label className="field"><span>Address</span><input type="url" required value={url} maxLength={2000} onChange={(event) => setUrl(event.target.value)} /></label>
        <button className="button" type="submit">Add</button>
      </form>
      {error && <p className="form-error">{error}</p>}
      <p className="field-note">The radar opens the link, saves it as a chosen candidate and writes its brief.</p>
      {links.map((link) => <div className="data-row link-row" key={link.id}><span>{link.added_at}</span><span className="m">{link.url}</span><span>{stateOf(link)}</span></div>)}
    </>
  );
}

// --- Page ---

export function Radar({ view }: { view?: string }) {
  const current = view === "eliminated" || view === "links" ? view : "candidates";
  const tab = (key: string, name: string) => <a href={`#radar/${key}`} aria-current={current === key ? "page" : undefined}>{name}</a>;
  return (
    <>
      <div className="page-top"><div>
        <h1 className="head-2">Radar</h1>
        <p className="status">What the radar offered, what it left out and why. Lists update after each hourly round.</p>
      </div></div>
      <nav className="view-tabs" aria-label="Radar views">
        {tab("candidates", "Candidates")}{tab("eliminated", "Left out")}{tab("links", "Add link")}
      </nav>
      {current === "links" ? <AddLink /> : <Events key={current} group={current} />}
    </>
  );
}
