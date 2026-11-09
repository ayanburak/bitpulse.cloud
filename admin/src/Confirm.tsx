/**
 * file: src/Confirm.tsx
 * importable: Confirm, type ConfirmRequest
 *
 * description: The dialog that asks for a passkey before a dangerous action and follows its job.
 */

// NOTE: The server gives one permission for this exact action and target, and it works once. The
// dialog asks for it right before running the action, never ahead of time.

import { useEffect, useRef, useState } from "react";
import { call, ApiError, type Job } from "./api";
import { usePasskey } from "./passkey";

export interface ConfirmRequest {
  action: string;
  target: string;
  heading: string;
  text: string;
  subject: string;
  run: () => Promise<{ job?: number; secret?: string } | void>;
  done?: () => void;
}

const STEPS = ["Queued", "Building and checking pages", "Live"];

function stepsDone(job: Job | null): number {
  if (!job || job.status === "failed") return 0;
  if (job.status === "queued") return 1;
  return job.status === "dispatched" ? 2 : 3;
}

function message(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return "The passkey was not used. Try again.";
}

export function Confirm({ request, close }: { request: ConfirmRequest; close: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [useCode, setUseCode] = useState(false);
  const [code, setCode] = useState("");
  const [jobId, setJobId] = useState<number | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [secret, setSecret] = useState("");

  useEffect(() => {
    const element = dialog.current;
    element?.showModal();
    return () => element?.close();
  }, []);

  // A job is read once a second until the worker has answered.
  useEffect(() => {
    if (jobId === null) return;
    let stopped = false;
    const read = async () => {
      const current = await call<Job>("GET", `/jobs/${jobId}`);
      if (stopped) return;
      setJob(current);
      if (current.status === "queued" || current.status === "dispatched") setTimeout(read, 1000);
      else request.done?.();
    };
    void read();
    return () => { stopped = true; };
  }, [jobId, request]);

  async function proceed(answer: { credential?: unknown; code?: string }) {
    await call("POST", "/auth/action/answer", { action: request.action, target: request.target, ...answer });
    const result = await request.run();
    if (result?.job !== undefined) return setJobId(result.job);
    if (result?.secret) return setSecret(result.secret);
    request.done?.();
    close();
  }

  async function confirm() {
    setBusy(true);
    setError("");
    try {
      if (useCode) {
        await proceed({ code });
      } else {
        const body = { action: request.action, target: request.target };
        const { options } = await call<{ options: never }>("POST", "/auth/action/options", body);
        await proceed({ credential: await usePasskey(options) });
      }
    } catch (failure) {
      setError(message(failure));
    } finally {
      setBusy(false);
    }
  }

  if (secret) {
    return (
      <dialog ref={dialog} className="confirm"><div className="confirm__inner">
        <h2 className="head-3">Copy this key now</h2>
        <p className="summary">It will not be shown again.</p>
        <p className="secret">{secret}</p>
        <div className="actions"><button className="button" type="button" onClick={() => { request.done?.(); close(); }}>Done</button></div>
      </div></dialog>
    );
  }

  if (jobId !== null) {
    const failed = job?.status === "failed";
    const finished = failed || job?.status === "succeeded";
    return (
      <dialog ref={dialog} className="confirm"><div className="confirm__inner">
        <h2 className="head-3">{failed ? "It did not go live" : finished ? "Done" : "Working"}</h2>
        <ul className="steps">
          {STEPS.map((name, index) => (
            <li key={name} className={index < stepsDone(job) ? "done" : ""}>
              <span>{name}</span><b>{index < stepsDone(job) ? "Done" : ""}</b>
            </li>
          ))}
        </ul>
        {failed && <p className="form-error">The live site did not change. {job?.error}</p>}
        {job?.status === "succeeded" && <p className="confirm__what">{job.release}, {job.duration_ms} ms</p>}
        {finished && <div className="actions"><button className="button" type="button" onClick={close}>Close</button></div>}
      </div></dialog>
    );
  }

  return (
    <dialog ref={dialog} className="confirm" onCancel={close}><div className="confirm__inner">
      <h2 className="head-3">{request.heading}</h2>
      <p className="summary">{request.text}</p>
      <p className="confirm__what">{request.subject}</p>
      {useCode && <label className="field"><span>Backup code</span><input value={code} autoComplete="off" onChange={(event) => setCode(event.target.value)} /></label>}
      {error && <p className="form-error" role="alert">{error}</p>}
      <div className="actions">
        <button className="button button--outline" type="button" onClick={close}>Cancel</button>
        <button className="button" type="button" disabled={busy} onClick={confirm}>{useCode ? "Use code" : "Use passkey"}</button>
      </div>
      <button className="login__alt" type="button" onClick={() => setUseCode(!useCode)}>{useCode ? "Use a passkey" : "Use a backup code"}</button>
    </div></dialog>
  );
}
