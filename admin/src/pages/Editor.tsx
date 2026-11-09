/**
 * file: src/pages/Editor.tsx
 * importable: Editor
 *
 * description: Writes a story in both languages, shows its preview and acts on the live site.
 */

// NOTE: Publishing always saves first. What goes live is then exactly what the form shows, and the
// save itself needs no passkey because a draft changes nothing a reader can see.

import { useEffect, useMemo, useState } from "react";
import { ApiError, call, type Language, type StoryFields } from "../api";
import type { ConfirmRequest } from "../Confirm";
import { previewDocument } from "../preview";

type Lang = "en" | "tr";

interface Version { id: number; number: number; actor: string; created_at: string }
interface Loaded { number: number; content: StoryFields; image: string; live_version: number | null; published_at: string | null; versions: Version[] }

const CATEGORIES = ["world", "economy", "technology", "science", "health", "culture", "sports"];

function emptyLanguage(): Language {
  return {
    slug: "", title: "", summary: "", category: "world", kind: "news", sources: [],
    image: { file: "image.jpg", alt: "", credit: "", license: "", licenseUrl: "", source: "" },
    updates: [], corrected: null, body: "",
  };
}

// One source per line, the address is whatever comes after the last space.
function sourcesToText(sources: Language["sources"]): string {
  return sources.map((item) => `${item.name}  ${item.url}`).join("\n");
}

function textToSources(text: string): Language["sources"] {
  return text.split("\n").map((line) => line.trim()).filter(Boolean).map((line) => {
    const cut = line.lastIndexOf(" ");
    return cut < 0 ? { name: line, url: "" } : { name: line.slice(0, cut).trim(), url: line.slice(cut + 1) };
  });
}

function asDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(blob);
  });
}

export function Editor({ handle, ask }: { handle: string; ask: (request: ConfirmRequest) => void }) {
  const isNew = handle === "new";
  const [story, setStory] = useState<Loaded | null>(null);
  const [fields, setFields] = useState<StoryFields>({ en: emptyLanguage(), tr: emptyLanguage(), social: "" });
  const [sources, setSources] = useState<Record<Lang, string>>({ en: "", tr: "" });
  const [image, setImage] = useState("");
  const [lang, setLang] = useState<Lang>("en");
  const [mode, setMode] = useState<"write" | "preview">("write");
  const [cover, setCover] = useState<string | null>(null);
  const [message, setMessage] = useState("");

  async function reload() {
    if (isNew) return;
    const loaded = await call<Loaded>("GET", `/stories/${handle}`);
    setStory(loaded);
    setFields(loaded.content);
    setSources({ en: sourcesToText(loaded.content.en.sources), tr: sourcesToText(loaded.content.tr.sources) });
    setImage(loaded.image);
  }

  useEffect(() => { void reload(); }, [handle]);

  useEffect(() => {
    if (mode !== "preview" || !image) return;
    void fetch(`/panel-api/images/${image}`).then((response) => response.blob()).then(asDataUrl).then(setCover);
  }, [mode, image]);

  const current = fields[lang];
  const dark = document.documentElement.dataset.theme === "dark";
  const preview = useMemo(() => (mode === "preview" ? previewDocument(current, cover, dark) : ""), [mode, current, cover, dark]);

  function set(change: Partial<Language>) {
    setFields((old) => ({ ...old, [lang]: { ...old[lang], ...change } }));
  }

  // Category, kind and the facts about the image must match in both languages, so one edit sets both.
  function setShared(change: Partial<Language>) {
    setFields((old) => ({ ...old, en: { ...old.en, ...change }, tr: { ...old.tr, ...change } }));
  }

  function setImageFact(change: Partial<Language["image"]>) {
    setFields((old) => ({
      ...old,
      en: { ...old.en, image: { ...old.en.image, ...change } },
      tr: { ...old.tr, image: { ...old.tr.image, ...change } },
    }));
  }

  function addUpdate() {
    const blank = { time: null, note: "", promote: false };
    setFields((old) => ({ ...old, en: { ...old.en, updates: [...old.en.updates, blank] }, tr: { ...old.tr, updates: [...old.tr.updates, blank] } }));
  }

  function setUpdate(index: number, note: string) {
    set({ updates: current.updates.map((item, position) => (position === index ? { ...item, note } : item)) });
  }

  function setPromote(index: number, promote: boolean) {
    const mark = (list: Language["updates"]) => list.map((item, position) => (position === index ? { ...item, promote } : item));
    setFields((old) => ({ ...old, en: { ...old.en, updates: mark(old.en.updates) }, tr: { ...old.tr, updates: mark(old.tr.updates) } }));
  }

  async function upload(file: File) {
    setMessage("");
    try {
      setImage((await call<{ sha: string }>("POST", "/images", file)).sha);
    } catch (failure) {
      setMessage(failure instanceof ApiError ? failure.message : "The image was not uploaded.");
    }
  }

  // A new story takes its lasting name from the English address on its first save.
  async function save(): Promise<string | null> {
    setMessage("");
    const name = isNew ? fields.en.slug : handle;
    const body = {
      en: { ...fields.en, sources: textToSources(sources.en) },
      tr: { ...fields.tr, sources: textToSources(sources.tr) },
      social: fields.social,
      image,
    };
    try {
      if (!image) throw new ApiError(422, "Add a cover image first.");
      if (!name) throw new ApiError(422, "Fill in the English address first.");
      await call("PUT", `/stories/${name}/draft`, body);
      if (isNew) location.hash = `edit/${name}`;
      else await reload();
      setMessage("Saved.");
      return name;
    } catch (failure) {
      setMessage(failure instanceof ApiError ? failure.message : "The draft was not saved.");
      return null;
    }
  }

  async function publish() {
    const name = await save();
    if (!name) return;
    ask({
      action: "publish", target: name,
      heading: "Publish this story", text: "It goes live on bitpulse.cloud in both languages.", subject: fields.en.title,
      run: async () => ({ job: (await call<{ job: number }>("POST", `/stories/${name}/publish`)).job }),
      done: reload,
    });
  }

  const liveAction = (action: "undo" | "withdraw", heading: string, text: string) => () => ask({
    action, target: handle, heading, text, subject: fields.en.title,
    run: async () => ({ job: (await call<{ job: number }>("POST", `/stories/${handle}/${action}`)).job }),
    done: reload,
  });

  const live = Boolean(story?.live_version);
  const liveNumber = story?.versions.find((item) => item.id === story.live_version)?.number;

  return (
    <>
      <div className="page-top">
        <div><a className="top-link" href="#stories">Stories</a><h1 className="head-3 title-gap">{fields.en.title || "New draft"}</h1></div>
        <p className="status">{live ? <b>Live</b> : story?.published_at ? "Withdrawn" : "Draft"}{story?.published_at ? `, ${story.published_at} UTC` : ""}</p>
      </div>
      <div className="grid editor">
        <section className="editor__main">
          <div className="switches">
            <div className="filters">
              <button type="button" aria-pressed={lang === "en"} onClick={() => setLang("en")}>English</button>
              <button type="button" aria-pressed={lang === "tr"} onClick={() => setLang("tr")}>Turkish</button>
            </div>
            <div className="filters">
              <button type="button" aria-pressed={mode === "write"} onClick={() => setMode("write")}>Write</button>
              <button type="button" aria-pressed={mode === "preview"} onClick={() => setMode("preview")}>Preview</button>
            </div>
          </div>
          {mode === "preview" ? (
            <iframe className="preview-frame" sandbox="" title="Preview" srcDoc={preview} />
          ) : (
            <>
              <label className="field"><span>Headline</span><input className="title-input" value={current.title} onChange={(event) => set({ title: event.target.value })} /></label>
              <label className="field"><span>Summary</span><textarea rows={2} value={current.summary} onChange={(event) => set({ summary: event.target.value })} /></label>
              <div className="fields-2">
                <label className="field"><span>Category</span>
                  <select value={current.category} onChange={(event) => setShared({ category: event.target.value })}>
                    {CATEGORIES.map((name) => <option key={name} value={name}>{name}</option>)}
                  </select>
                </label>
                <label className="field"><span>Address</span><input value={current.slug} onChange={(event) => set({ slug: event.target.value })} /></label>
              </div>
              <label className="field"><span>Story</span><textarea className="body-input" value={current.body} onChange={(event) => set({ body: event.target.value })} /></label>
              <label className="field"><span>Sources, one per line, name then address</span><textarea rows={3} value={sources[lang]} onChange={(event) => setSources({ ...sources, [lang]: event.target.value })} /></label>
              <div className="field">
                <span>Updates</span>
                {current.updates.map((item, index) => (
                  <div className="update-row" key={index}>
                    <label className="field"><input aria-label={`Update ${index + 1}`} value={item.note} onChange={(event) => setUpdate(index, event.target.value)} /></label>
                    <label className="check"><input type="checkbox" checked={item.promote} onChange={(event) => setPromote(index, event.target.checked)} />Raise on the home page</label>
                    <p className="field-note">{item.time ? `${item.time} UTC` : "New, gets its time when published"}</p>
                  </div>
                ))}
                <button className="text-button" type="button" onClick={addUpdate}>Add update</button>
              </div>
            </>
          )}
        </section>
        <aside className="editor__side">
          <div>
            <div className="actions">
              <button className="button button--outline" type="button" onClick={save}>Save draft</button>
              <button className="button" type="button" onClick={publish}>{live ? "Publish update" : "Publish"}</button>
            </div>
            {message && <p className="form-error" role="status">{message}</p>}
          </div>
          <div>
            <h2 className="side-title">Cover image</h2>
            <div className="photo ratio-3-2">{image && <img src={`/panel-api/images/${image}`} alt="" />}</div>
            <p className="caption">Metadata is removed on upload.</p>
            <label className="field"><span>Alt text, {lang === "en" ? "English" : "Turkish"}</span><input value={current.image.alt} onChange={(event) => set({ image: { ...current.image, alt: event.target.value } })} /></label>
            <label className="field"><span>Credit</span><input value={current.image.credit} onChange={(event) => setImageFact({ credit: event.target.value })} /></label>
            <label className="field"><span>License</span><input value={current.image.license} onChange={(event) => setImageFact({ license: event.target.value })} /></label>
            <label className="field"><span>License address</span><input value={current.image.licenseUrl} onChange={(event) => setImageFact({ licenseUrl: event.target.value })} /></label>
            <label className="field"><span>Image source</span><input value={current.image.source} onChange={(event) => setImageFact({ source: event.target.value })} /></label>
            <label className="field"><span>Replace image</span><input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => { const file = event.target.files?.[0]; if (file) void upload(file); }} /></label>
          </div>
          {story && (
            <div>
              <h2 className="side-title">Versions</h2>
              <ul className="side-rows">
                {story.versions.slice(0, 10).map((item) => (
                  <li key={item.id}><span>v{item.number}, {item.actor}, {item.created_at}</span>{item.number === liveNumber && <b>Live</b>}</li>
                ))}
              </ul>
            </div>
          )}
          {live && (
            <div>
              <h2 className="side-title">Live story</h2>
              <div className="actions">
                <button className="button button--outline" type="button" onClick={liveAction("undo", "Undo the last publish", "The previous version goes live again.")}>Undo last publish</button>
                <button className="button button--outline" type="button" onClick={liveAction("withdraw", "Withdraw this story", "It disappears from the site. Its versions stay on record.")}>Withdraw</button>
              </div>
              <p className="danger-note">Withdraw removes the story from the site. Its versions stay on record.</p>
            </div>
          )}
        </aside>
      </div>
    </>
  );
}
