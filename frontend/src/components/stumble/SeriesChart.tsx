"use client";

import { useId, useState } from "react";

import type { SeriesPointDto } from "@/types/api";

/**
 * Three cumulative lines over ten days. The story is the "struggling" line staying flat while the
 * other two climb. One y-axis, thin 2px lines, a legend plus end labels, crosshair + tooltip on
 * hover, and a table view for anyone the picture doesn't serve.
 *
 * Series colors are the ink-strength steps of the app hues; validated on the paper surface.
 */
const SERIES = [
  { key: "caught", label: "caught", color: "#2b7fd0" },
  { key: "mastered", label: "mastered", color: "#1f9d55" },
  { key: "struggling", label: "still due", color: "#ff3d7f" },
] as const;

type Key = (typeof SERIES)[number]["key"];

const W = 320;
const H = 150;
const PAD = { top: 18, right: 62, bottom: 22, left: 26 };

const shortDate = new Intl.DateTimeFormat("en", { month: "short", day: "numeric" });

/**
 * End labels sit at each line's last value. Two lines that end at the same value (caught and still
 * due on day one; mastered and due when the deck is clear) would print on top of each other, so
 * labels are nudged apart to at least one line-height, keeping their vertical order.
 */
const LABEL_GAP = 12;

function endLabels(items: { key: string; y: number }[]): { key: string; y: number }[] {
  const sorted = [...items].sort((a, b) => a.y - b.y);
  for (let i = 1; i < sorted.length; i++) {
    const prev = sorted[i - 1];
    const cur = sorted[i];
    if (prev && cur && cur.y - prev.y < LABEL_GAP) cur.y = prev.y + LABEL_GAP;
  }
  // If the stack ran past the bottom of the plot, push up from the bottom, only as far as the
  // gaps require, so a label that wasn't in the way stays on its line.
  const bottom = H - PAD.bottom;
  const last = sorted[sorted.length - 1];
  if (last && last.y > bottom) {
    last.y = bottom;
    for (let i = sorted.length - 2; i >= 0; i--) {
      const cur = sorted[i];
      const next = sorted[i + 1];
      if (cur && next && cur.y > next.y - LABEL_GAP) cur.y = next.y - LABEL_GAP;
    }
  }
  return sorted;
}

export function SeriesChart({ points }: { points: SeriesPointDto[] }) {
  const [hover, setHover] = useState<number | null>(null);
  const id = useId();
  const n = points.length;
  const max = Math.max(4, ...points.map((p) => Math.max(p.caught, p.mastered, p.struggling)));
  const innerW = W - PAD.left - PAD.right;
  const innerH = H - PAD.top - PAD.bottom;
  const x = (i: number) => PAD.left + (n <= 1 ? innerW / 2 : (i / (n - 1)) * innerW);
  const y = (v: number) => PAD.top + innerH - (v / max) * innerH;
  const path = (key: Key) => points.map((p, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(p[key]).toFixed(1)}`).join(" ");
  const ticks = [0, Math.round(max / 2), max];
  const last = points[n - 1];

  const onMove = (e: React.PointerEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const px = ((e.clientX - rect.left) / rect.width) * W;
    let best = 0;
    let dist = Infinity;
    for (let i = 0; i < n; i++) {
      const d = Math.abs(x(i) - px);
      if (d < dist) {
        dist = d;
        best = i;
      }
    }
    setHover(best);
  };

  const hp = hover !== null ? points[hover] : undefined;

  return (
    <figure className="m-0">
      <div className="relative">
        <svg
          overflow="visible"
          viewBox={`0 0 ${W} ${H}`}
          className="block w-full touch-none"
          role="img"
          aria-labelledby={`${id}-t`}
          onPointerMove={onMove}
          onPointerLeave={() => setHover(null)}
        >
          <title id={`${id}-t`}>Caught, mastered and still-due cards over the last {n} days</title>
          {ticks.map((t) => (
            <g key={t}>
              <line x1={PAD.left} x2={W - PAD.right} y1={y(t)} y2={y(t)} stroke="currentColor" strokeOpacity={0.1} strokeWidth={1} />
              <text x={PAD.left - 6} y={y(t) + 3.5} textAnchor="end" fontSize={9} fontWeight={700} fill="currentColor" fillOpacity={0.55}>
                {t}
              </text>
            </g>
          ))}
          {points.length > 0 ? (
            <>
              <text x={x(0)} y={H - 6} textAnchor="start" fontSize={9} fontWeight={700} fill="currentColor" fillOpacity={0.55}>
                {shortDate.format(new Date(points[0]!.date))}
              </text>
              <text x={x(n - 1)} y={H - 6} textAnchor="end" fontSize={9} fontWeight={700} fill="currentColor" fillOpacity={0.55}>
                today
              </text>
            </>
          ) : null}
          {SERIES.map((s) => (
            <path key={s.key} d={path(s.key)} fill="none" stroke={s.color} strokeWidth={s.key === "struggling" ? 2.5 : 2} strokeLinejoin="round" strokeLinecap="round" />
          ))}
          {last
            ? endLabels(SERIES.map((s) => ({ key: s.key, y: y(last[s.key]) }))).map((l) => {
                const s = SERIES.find((q) => q.key === l.key);
                return s ? (
                  <text key={s.key} x={x(n - 1) + 8} y={l.y + 3.5} fontSize={10} fontWeight={800} fill="currentColor">
                    {last[s.key]} {s.label}
                  </text>
                ) : null;
              })
            : null}
          {hover !== null && hp ? (
            <g>
              <line x1={x(hover)} x2={x(hover)} y1={PAD.top} y2={PAD.top + innerH} stroke="currentColor" strokeOpacity={0.35} strokeWidth={1} strokeDasharray="3 3" />
              {SERIES.map((s) => (
                <circle key={s.key} cx={x(hover)} cy={y(hp[s.key])} r={4.5} fill={s.color} stroke="#ffffff" strokeWidth={2} />
              ))}
            </g>
          ) : null}
        </svg>
        {hover !== null && hp ? (
          <div
            className="pointer-events-none absolute top-0 rounded-xl bg-ink px-2.5 py-1.5 text-[11px] font-bold text-paper shadow-lg"
            style={{ left: `${(x(hover) / W) * 100}%`, transform: `translateX(${hover > n / 2 ? "-110%" : "10%"})` }}
          >
            <div className="text-paper-2">{shortDate.format(new Date(hp.date))}</div>
            {SERIES.map((s) => (
              <div key={s.key} className="flex items-center gap-1.5">
                <i className="inline-block size-2 rounded-full" style={{ background: s.color }} />
                {hp[s.key]} {s.label}
              </div>
            ))}
          </div>
        ) : null}
      </div>
      <figcaption className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-[11px] font-bold text-ink/65">
        {SERIES.map((s) => (
          <span key={s.key} className="flex items-center gap-1.5">
            <i className="inline-block h-0.5 w-3 rounded-full" style={{ background: s.color }} />
            {s.label}
          </span>
        ))}
      </figcaption>
      <details className="mt-2 text-xs">
        <summary className="cursor-pointer font-bold text-ink/65">as a table</summary>
        <table className="mt-1 w-full text-left">
          <thead>
            <tr className="text-ink/65">
              <th className="font-bold">day</th>
              {SERIES.map((s) => (
                <th key={s.key} className="font-bold">
                  {s.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {points.map((p) => (
              <tr key={p.date}>
                <td>{shortDate.format(new Date(p.date))}</td>
                <td>{p.caught}</td>
                <td>{p.mastered}</td>
                <td>{p.struggling}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}
