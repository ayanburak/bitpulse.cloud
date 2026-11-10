/**
 * file: src/api.ts
 * importable: ApiError, call, setCsrf, onSignedOut, type Language, type StoryFields, type Job, type StoryRow,
 *             type EventRow, type EventDetail, type EventPage, type LinkRow, type InstagramPost, type InstagramDay
 *
 * call talks to the panel routes and adds the token every change needs. When the session ends on
 * the server, the handler given to onSignedOut sends the user back to the login page.
 *
 * description: The HTTP client and the data shapes of the admin panel.
 */

// --- Data Shapes ---

export interface Language {
  slug: string;
  title: string;
  summary: string;
  category: string;
  kind: string;
  sources: { name: string; url: string }[];
  image: { file: string; alt: string; credit: string; license: string; licenseUrl: string; source: string };
  updates: { time: string | null; note: string; promote: boolean }[];
  corrected: string | null;
  body: string;
}

export interface StoryFields {
  en: Language;
  tr: Language;
  social: string;
}

export interface Job {
  id: number;
  kind: string;
  handle: string | null;
  status: "queued" | "dispatched" | "succeeded" | "failed";
  release: string | null;
  error: string | null;
  duration_ms: number | null;
  finished_at: string | null;
}

export interface StoryRow {
  handle: string;
  title: string;
  category: string;
  state: "live" | "changed" | "draft" | "withdrawn";
  latest: number;
  live: number | null;
  published_at: string | null;
  saved_at: string;
}

export interface EventRow {
  number: number;
  title: string;
  first_seen: string;
  sources: number;
  stage: "sent" | "reserve" | "below" | "unseen" | "noise" | "merged";
  score: number | null;
  category: string | null;
  reason: string;
  decision: "do" | "skip" | null;
  clip: number;
  handle: string | null;
  has_brief: boolean;
  status: "new" | "do" | "skip" | "draft" | "published";
}

export interface EventDetail extends EventRow {
  summary: string;
  last_seen: string;
  importance: number | null;
  shareable: number | null;
  visual: number | null;
  merged_into: number | null;
  links: { source: string; title: string; url: string }[];
  decided_by: string | null;
  decided_at: string | null;
  brief_error: string | null;
  brief_at: string | null;
}

export interface EventPage {
  rows: EventRow[];
  next: string | null;
  counts: Record<string, number>;
}

export interface LinkRow {
  id: number;
  url: string;
  state: "waiting" | "done" | "failed";
  number: number | null;
  error: string | null;
  added_at: string;
}

export interface InstagramPost {
  id: string;
  kind: "reel" | "image" | "carousel";
  posted_at: string;
  permalink: string;
  caption: string;
  thumb: boolean;
  counts: {
    at: string;
    views: number | null;
    reach: number | null;
    likes: number | null;
    comments: number | null;
    saves: number | null;
    shares: number | null;
    watch_ms: number | null;
  } | null;
}

export interface InstagramDay {
  day: string;
  followers: number | null;
  profile_views: number | null;
  link_taps: number | null;
}

// --- Client ---

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

const BASE = "/panel-api";
let csrf = "";
let signedOut: () => void = () => {};

export function setCsrf(value: string): void {
  csrf = value;
}

export function onSignedOut(handler: () => void): void {
  signedOut = handler;
}

// The token only exists in memory. It comes back from the server after a page reload.
/**
 * Calls one panel route.
 *
 * @param method HTTP method.
 * @param path Route after /panel-api.
 * @param body Sent as JSON, or as it is when it is a file.
 * @returns The answer, or undefined when the route has none.
 * @throws ApiError when the server refuses the call.
 */
export async function call<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = {};
  if (method !== "GET") headers["X-CSRF-Token"] = csrf;
  const isFile = body instanceof Blob;
  if (body !== undefined && !isFile) headers["Content-Type"] = "application/json";
  const response = await fetch(BASE + path, {
    method,
    headers,
    credentials: "same-origin",
    body: body === undefined ? undefined : isFile ? body : JSON.stringify(body),
  });
  if (response.status === 401 && !path.startsWith("/auth/")) signedOut();
  if (!response.ok) {
    const detail = await response.json().then((data) => data.detail, () => response.statusText);
    throw new ApiError(response.status, typeof detail === "string" ? detail : "the request was refused");
  }
  return (response.status === 204 ? undefined : await response.json()) as T;
}
