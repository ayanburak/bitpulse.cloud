/**
 * file: src/pages/Audit.tsx
 * importable: Audit
 *
 * description: The record of every change on the system.
 */

import { useEffect, useState } from "react";
import { call } from "../api";

interface Entry { id: number; at: string; actor: string; action: string; target: string; detail: string }

const PAGE = 100;

export function Audit() {
  const [rows, setRows] = useState<Entry[]>([]);
  const [more, setMore] = useState(false);

  async function load(before?: number) {
    const query = before === undefined ? "" : `&before=${before}`;
    const page = await call<Entry[]>("GET", `/audit?limit=${PAGE}${query}`);
    setRows((current) => (before === undefined ? page : [...current, ...page]));
    setMore(page.length === PAGE);
  }

  useEffect(() => { void load(); }, []);

  return (
    <>
      <div className="page-top"><div>
        <h1 className="head-2">Audit log</h1>
        <p className="status">Every change on the system. Entries can not be edited or removed.</p>
      </div></div>
      <div className="data-row audit-row head-row"><span>Time</span><span>Who</span><span>Action</span><span>Target</span><span>Detail</span></div>
      {rows.map((row) => (
        <div className="data-row audit-row" key={row.id}>
          <span>{row.at}</span><span>{row.actor}</span><span>{row.action}</span><span>{row.target}</span><span className="m">{row.detail}</span>
        </div>
      ))}
      {more && <button className="button button--outline load-more" type="button" onClick={() => load(rows[rows.length - 1].id)}>Older entries</button>}
    </>
  );
}
