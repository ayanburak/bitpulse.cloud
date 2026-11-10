/**
 * file: src/App.tsx
 * importable: App
 *
 * description: Decides which page of the panel to show.
 */

// NOTE: Pages live in the part of the address after the hash. The server then only needs to know
// one file, and the one time registration token never reaches a server log.

import { useCallback, useEffect, useState } from "react";
import { call, onSignedOut, setCsrf } from "./api";
import { Confirm, type ConfirmRequest } from "./Confirm";
import { Shell } from "./Shell";
import { Access } from "./pages/Access";
import { Audit } from "./pages/Audit";
import { Editor } from "./pages/Editor";
import { Enrol, Login } from "./pages/Login";
import { Radar } from "./pages/Radar";
import { Instagram } from "./pages/Instagram";
import { Stories } from "./pages/Stories";

type Me = { signed_in: boolean; csrf?: string };

function useHash(): string {
  const [hash, setHash] = useState(location.hash.slice(1));
  useEffect(() => {
    const change = () => {
      setHash(location.hash.slice(1));
      scrollTo(0, 0);
    };
    addEventListener("hashchange", change);
    return () => removeEventListener("hashchange", change);
  }, []);
  return hash;
}

export function App() {
  const hash = useHash();
  const [signedIn, setSignedIn] = useState<boolean | null>(null);
  const [confirm, setConfirm] = useState<ConfirmRequest | null>(null);

  useEffect(() => {
    onSignedOut(() => setSignedIn(false));
    void call<Me>("GET", "/auth/me").then((me) => {
      setCsrf(me.csrf ?? "");
      setSignedIn(me.signed_in);
    });
  }, []);

  const entered = useCallback((csrf: string) => {
    setCsrf(csrf);
    setSignedIn(true);
    location.hash = "stories";
  }, []);

  const signOut = useCallback(async () => {
    await call("POST", "/auth/logout");
    setCsrf("");
    setSignedIn(false);
  }, []);

  if (hash.startsWith("enrol=")) return <Enrol token={hash.slice("enrol=".length)} />;
  if (signedIn === null) return null;
  if (!signedIn) return <Login entered={entered} />;

  const [name, argument] = hash.split("/");
  const section = ["audit", "access", "radar", "instagram"].includes(name) ? name : "stories";
  return (
    <Shell section={section} signOut={signOut}>
      {name === "radar" && <Radar view={argument} />}
      {name === "instagram" && <Instagram />}
      {name === "audit" && <Audit />}
      {name === "access" && <Access ask={setConfirm} />}
      {name === "edit" && <Editor key={argument} handle={argument} ask={setConfirm} />}
      {section === "stories" && name !== "edit" && <Stories />}
      {confirm && <Confirm request={confirm} close={() => setConfirm(null)} />}
    </Shell>
  );
}
