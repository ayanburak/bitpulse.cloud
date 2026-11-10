/**
 * file: src/pages/InstagramChart.tsx
 * importable: InstagramChart
 *
 * description: The numbers of one Instagram post over time, drawn from every reading the service stored.
 */

// NOTE: Meta gives totals, not hourly numbers, so a count only ever rises or stays flat. The rise
// between two readings is what the tooltip adds, that is the number of that hour. The skip rate is a
// share, not a total, and it can also fall.
//
// NOTE: The drawing is as wide as its box in real pixels, so the labels keep their size on a phone
// instead of shrinking with the picture.
//
// NOTE: One series and one axis that starts at zero. The line takes the panel accent, the grid and
// the labels stay in the muted ink, so the chart follows the light and the dark theme by itself.

import { useEffect, useMemo, useRef, useState } from "react";
import { call, type InstagramCounts } from "../api";

type Reading = InstagramCounts & { at: string };
type Metric = keyof InstagramCounts;

const METRICS: [Metric, string][] = [
  ["views", "Views"], ["reach", "Reach"], ["likes", "Likes"], ["saves", "Saves"], ["shares", "Shares"], ["interactions", "Interactions"],
  ["skip_rate", "Skip rate"],
];
const BASE_WIDTH = 640;
const HEIGHT = 200;
const MIN_WIDTH = 280;
const PAD = { top: 12, right: 12, bottom: 26, left: 44 };
const GRID = 4;

const time = (at: string) => Date.parse(`${at.replace(" ", "T")}:00Z`);
const plain = (value: number) => value.toLocaleString("en-US");

// A round top keeps the grid labels readable, 1, 2 or 5 times a power of ten.
function ceiling(value: number): number {
  if (value <= 0) return GRID;
  const step = 10 ** Math.floor(Math.log10(value / GRID));
  const nice = [1, 2, 5, 10].find((factor) => factor * step * GRID >= value) ?? 10;
  return nice * step * GRID;
}

// Near an edge the tooltip grows inward, so it never leaves the chart on a narrow screen.
function tip(at: number): React.CSSProperties {
  const shift = at < 0.25 ? "0" : at > 0.75 ? "-100%" : "-50%";
  return { left: `${at * 100}%`, transform: `translateX(${shift})` };
}

function Plot({ rows, metric }: { rows: { at: string; value: number }[]; metric: string }) {
  const [hover, setHover] = useState<number | null>(null);
  const [width, setWidth] = useState(BASE_WIDTH);
  const box = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const node = box.current!.parentElement!;
    const watch = new ResizeObserver(() => setWidth(Math.max(MIN_WIDTH, Math.round(node.clientWidth))));
    watch.observe(node);
    return () => watch.disconnect();
  }, []);

  const top = ceiling(Math.max(...rows.map((row) => row.value)));
  const first = time(rows[0].at);
  const span = Math.max(time(rows[rows.length - 1].at) - first, 1);
  const x = (at: string) => PAD.left + ((time(at) - first) / span) * (width - PAD.left - PAD.right);
  const y = (value: number) => HEIGHT - PAD.bottom - (value / top) * (HEIGHT - PAD.top - PAD.bottom);
  const points = rows.map((row) => `${x(row.at).toFixed(1)},${y(row.value).toFixed(1)}`).join(" ");

  // The nearest reading to the pointer, measured along the time axis only.
  function move(event: React.PointerEvent<SVGSVGElement>) {
    const rect = box.current!.getBoundingClientRect();
    const position = ((event.clientX - rect.left) / rect.width) * width;
    let best = 0;
    rows.forEach((row, index) => { if (Math.abs(x(row.at) - position) < Math.abs(x(rows[best].at) - position)) best = index; });
    setHover(best);
  }

  const active = hover === null ? null : rows[hover];
  const rise = hover ? rows[hover].value - rows[hover - 1].value : null;
  return (
    <div className="insta-chart__plot">
      <svg ref={box} viewBox={`0 0 ${width} ${HEIGHT}`} role="img" aria-label={`${metric} over time`}
        onPointerMove={move} onPointerLeave={() => setHover(null)}>
        {Array.from({ length: GRID + 1 }, (_, index) => {
          const value = (top / GRID) * index;
          return (
            <g key={index} className="insta-chart__grid">
              <line x1={PAD.left} x2={width - PAD.right} y1={y(value)} y2={y(value)} />
              <text x={PAD.left - 8} y={y(value)} dy="0.32em" textAnchor="end">{plain(value)}</text>
            </g>
          );
        })}
        <text className="insta-chart__axis" x={PAD.left} y={HEIGHT - 6}>{rows[0].at}</text>
        <text className="insta-chart__axis" x={width - PAD.right} y={HEIGHT - 6} textAnchor="end">{rows[rows.length - 1].at}</text>
        {rows.length > 1
          ? <polyline className="insta-chart__line" points={points} />
          : <circle className="insta-chart__dot" cx={x(rows[0].at)} cy={y(rows[0].value)} r={4} />}
        {active && <>
          <line className="insta-chart__cross" x1={x(active.at)} x2={x(active.at)} y1={PAD.top} y2={HEIGHT - PAD.bottom} />
          <circle className="insta-chart__dot" cx={x(active.at)} cy={y(active.value)} r={4} />
        </>}
      </svg>
      {active && (
        <p className="insta-chart__tip" style={tip(x(active.at) / width)}>
          <b>{plain(active.value)}</b> {metric.toLowerCase()}<br />
          {rise !== null && <>{rise < 0 ? "" : "+"}{plain(rise)} since the reading before<br /></>}
          {active.at} UTC
        </p>
      )}
    </div>
  );
}

export function InstagramChart({ id }: { id: string }) {
  const [rows, setRows] = useState<Reading[] | null>(null);
  const [metric, setMetric] = useState<Metric>("views");

  useEffect(() => { void call<Reading[]>("GET", `/instagram/${id}/history`).then(setRows); }, [id]);

  const series = useMemo(
    () => (rows ?? []).flatMap((row) => (row[metric] === null ? [] : [{ at: row.at, value: row[metric] as number }])),
    [rows, metric],
  );
  const name = METRICS.find(([key]) => key === metric)?.[1] ?? "";
  if (rows === null) return null;
  return (
    <div className="insta-chart">
      <div className="filters filters--wrap">
        {METRICS.map(([key, label]) => (
          <button key={key} type="button" aria-pressed={key === metric} onClick={() => setMetric(key)}>{label}</button>
        ))}
      </div>
      {series.length === 0 ? <p className="status">Instagram gives no {name.toLowerCase()} for this post.</p> : <Plot rows={series} metric={name} />}
      <p className="status">{rows.length === 1 ? "One reading so far. A post is read every hour in its first week." : `${rows.length} readings.`}</p>
      <details className="insta-chart__table">
        <summary>Readings as a table</summary>
        <table>
          <thead><tr><th>Read at, UTC</th>{METRICS.map(([key, label]) => <th key={key}>{label}</th>)}</tr></thead>
          <tbody>
            {[...rows].reverse().map((row) => (
              <tr key={row.at}><td>{row.at}</td>{METRICS.map(([key]) => <td key={key}>{row[key] === null ? "–" : plain(row[key] as number)}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  );
}
