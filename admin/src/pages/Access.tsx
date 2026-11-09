/**
 * file: src/pages/Access.tsx
 * importable: Access
 *
 * description: Device keys, passkeys and the count of backup codes.
 */

import { useCallback, useEffect, useState } from "react";
import { call } from "../api";
import type { ConfirmRequest } from "../Confirm";
import { createPasskey } from "../passkey";

interface Key { name: string; created_at: string; expires_at: string; revoked_at: string | null }
interface Passkey { id: string; name: string; created_at: string; used_at: string | null }
interface Account { passkeys: Passkey[]; backup_codes: number }

// Times share one form and one zone, so comparing them as text is enough.
function keyState(key: Key): string {
  if (key.revoked_at) return "Revoked";
  return key.expires_at <= new Date().toISOString().slice(0, 16).replace("T", " ") ? "Expired" : "Active";
}

export function Access({ ask }: { ask: (request: ConfirmRequest) => void }) {
  const [keys, setKeys] = useState<Key[]>([]);
  const [account, setAccount] = useState<Account | null>(null);
  const [keyName, setKeyName] = useState("");
  const [passkeyName, setPasskeyName] = useState("");

  const load = useCallback(() => {
    void call<Key[]>("GET", "/keys").then(setKeys);
    void call<Account>("GET", "/account").then(setAccount);
  }, []);

  useEffect(load, [load]);

  const newKey = () => ask({
    action: "key.create", target: keyName,
    heading: "Create a device key", text: "The key is shown once and lasts ninety days.", subject: keyName,
    run: async () => ({ secret: (await call<{ key: string }>("POST", "/keys", { name: keyName })).key }),
    done: () => { setKeyName(""); load(); },
  });

  const revoke = (name: string) => ask({
    action: "key.revoke", target: name,
    heading: "Revoke this key", text: "The device loses access immediately.", subject: name,
    run: async () => { await call("DELETE", `/keys/${name}`); },
    done: load,
  });

  const addPasskey = () => ask({
    action: "passkey.add", target: "panel",
    heading: "Add a passkey", text: "Confirm with an existing passkey first.", subject: passkeyName,
    run: async () => {
      const { options } = await call<{ options: never }>("POST", "/account/passkeys/options");
      await call("POST", "/account/passkeys", { credential: await createPasskey(options), name: passkeyName });
    },
    done: () => { setPasskeyName(""); load(); },
  });

  const removePasskey = (item: Passkey) => ask({
    action: "passkey.remove", target: item.id,
    heading: "Remove this passkey", text: "At least one passkey must remain.", subject: item.name,
    run: async () => { await call("DELETE", `/account/passkeys/${item.id}`); },
    done: load,
  });

  return (
    <>
      <div className="page-top"><div>
        <h1 className="head-2">Access</h1>
        <p className="status">Who can reach the system, and how.</p>
      </div></div>

      <div className="section-head"><h2>Device keys</h2></div>
      <div className="data-row key-row head-row"><span>Device</span><span>Created</span><span>Expires</span><span>State</span><span></span></div>
      {keys.map((key) => (
        <div className="data-row key-row" key={key.name}>
          <span>{key.name}</span><span className="m">{key.created_at}</span><span className="m">{key.expires_at}</span>
          <span>{keyState(key)}</span>
          {keyState(key) === "Active" ? <button className="text-button" type="button" onClick={() => revoke(key.name)}>Revoke</button> : <span></span>}
        </div>
      ))}
      <div className="after-list">
        <label className="field"><span>Device name</span><input value={keyName} onChange={(event) => setKeyName(event.target.value)} /></label>
        <button className="button button--outline" type="button" disabled={!keyName} onClick={newKey}>New device key</button>
      </div>

      <div className="section-head section-head--spaced"><h2>Passkeys</h2></div>
      <div className="data-row pk-row head-row"><span>Name</span><span>Added</span><span>Last used</span><span></span></div>
      {account?.passkeys.map((item) => (
        <div className="data-row pk-row" key={item.id}>
          <span>{item.name}</span><span className="m">{item.created_at}</span><span className="m">{item.used_at ?? "Never"}</span>
          {account.passkeys.length > 1 ? <button className="text-button" type="button" onClick={() => removePasskey(item)}>Remove</button> : <span></span>}
        </div>
      ))}
      <div className="after-list">
        <label className="field"><span>Passkey name</span><input value={passkeyName} onChange={(event) => setPasskeyName(event.target.value)} /></label>
        <button className="button button--outline" type="button" disabled={!passkeyName} onClick={addPasskey}>Add passkey</button>
      </div>

      <div className="section-head section-head--spaced"><h2>Backup codes</h2></div>
      {account && <p className="status">{account.backup_codes} of 10 codes are unused. New codes are made on the server.</p>}
    </>
  );
}
