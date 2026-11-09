/**
 * file: src/pages/Login.tsx
 * importable: Login, Enrol
 *
 * description: The password, passkey and backup code screens, and the first passkey registration.
 */

import { useState, type FormEvent, type ReactNode } from "react";
import { ApiError, call } from "../api";
import { createPasskey, usePasskey } from "../passkey";
import { Logo } from "../Shell";

type Step = "password" | "passkey" | "code";

function Frame({ children }: { children: ReactNode }) {
  return (
    <div className="login">
      <header className="site-header"><div className="container site-header__inner"><Logo /></div></header>
      <div className="login__rule"><span className="pulse"><b></b></span></div>
      <main className="login__body"><div className="container grid"><div className="login__box">{children}</div></div></main>
    </div>
  );
}

function reason(error: unknown): string {
  if (error instanceof ApiError) return error.status === 429 ? "Too many attempts. Try again later." : "That did not work.";
  return "The passkey was not used. Try again.";
}

export function Login({ entered }: { entered: (csrf: string) => void }) {
  const [step, setStep] = useState<Step>("password");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [options, setOptions] = useState<never | null>(null);
  const [error, setError] = useState("");

  async function attempt(work: () => Promise<void>) {
    setError("");
    try {
      await work();
    } catch (failure) {
      setError(reason(failure));
    }
  }

  const sendPassword = (event: FormEvent) => {
    event.preventDefault();
    void attempt(async () => {
      const answer = await call<{ options: never }>("POST", "/auth/password", { password });
      setPassword("");
      setOptions(answer.options);
      setStep("passkey");
    });
  };

  const sendPasskey = () => attempt(async () => {
    const credential = await usePasskey(options as never);
    entered((await call<{ csrf: string }>("POST", "/auth/passkey", { credential })).csrf);
  });

  const sendCode = (event: FormEvent) => {
    event.preventDefault();
    void attempt(async () => {
      entered((await call<{ csrf: string }>("POST", "/auth/backup-code", { code })).csrf);
    });
  };

  const problem = error && <p className="form-error" role="alert">{error}</p>;

  if (step === "passkey") {
    return (
      <Frame>
        <h1 className="head-2">Confirm it is you</h1>
        <p className="summary">Use the passkey on your phone or security key.</p>
        {problem}
        <button className="button" type="button" onClick={sendPasskey}>Use passkey</button>
        <button className="login__alt" type="button" onClick={() => { setError(""); setStep("code"); }}>Use a backup code</button>
      </Frame>
    );
  }
  if (step === "code") {
    return (
      <Frame>
        <h1 className="head-2">Backup code</h1>
        <p className="summary">Each code works once.</p>
        <form onSubmit={sendCode}>
          <label className="field"><span>Code</span><input value={code} autoComplete="off" onChange={(event) => setCode(event.target.value)} /></label>
          {problem}
          <button className="button" type="submit">Continue</button>
        </form>
        <button className="login__alt" type="button" onClick={() => { setError(""); setStep("passkey"); }}>Use a passkey instead</button>
      </Frame>
    );
  }
  return (
    <Frame>
      <h1 className="head-2">Editor sign in</h1>
      <p className="summary">This area is private.</p>
      <form onSubmit={sendPassword}>
        <label className="field"><span>Password</span><input type="password" value={password} autoComplete="current-password" onChange={(event) => setPassword(event.target.value)} /></label>
        {problem}
        <button className="button" type="submit">Continue</button>
      </form>
    </Frame>
  );
}

// The token is removed from the address as soon as it has been used.
export function Enrol({ token }: { token: string }) {
  const [name, setName] = useState("Phone");
  const [state, setState] = useState<"ready" | "done">("ready");
  const [error, setError] = useState("");

  async function register() {
    setError("");
    try {
      const { options } = await call<{ options: never }>("POST", "/auth/enrol/options", { token });
      const credential = await createPasskey(options);
      await call("POST", "/auth/enrol/finish", { token, credential, name });
      history.replaceState(null, "", location.pathname);
      setState("done");
    } catch (failure) {
      setError(failure instanceof ApiError ? "This link is not valid any more." : "The passkey was not created. Try again.");
    }
  }

  if (state === "done") {
    return (
      <Frame>
        <h1 className="head-2">Passkey registered</h1>
        <p className="summary">You can sign in now.</p>
        <a className="button" href="#" onClick={() => location.reload()}>Go to sign in</a>
      </Frame>
    );
  }
  return (
    <Frame>
      <h1 className="head-2">Register your passkey</h1>
      <p className="summary">This link works once.</p>
      <label className="field"><span>Name for this passkey</span><input value={name} onChange={(event) => setName(event.target.value)} /></label>
      {error && <p className="form-error" role="alert">{error}</p>}
      <button className="button" type="button" onClick={register}>Create passkey</button>
    </Frame>
  );
}
