"use client";

import React, { CSSProperties, useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

/* ================================================================== */
/*  COMMAND CENTER HUD v5 — Single-Screen Iron-Man Mission Control    */
/*                                                                     */
/*  Compact components designed for dense 1-screen layouts.            */
/*  All components use theme-card/theme-elevated as their visual       */
/*  base, then layer sci-fi decorations on top.                        */
/* ================================================================== */

export const HUD = {
  cyan: "#22d3ee",
  teal: "#2dd4bf",
  green: "#34d399",
  amber: "#fbbf24",
  red: "#f87171",
  blue: "#60a5fa",
  purple: "#a78bfa",
  pink: "#f472b6",
  slate: "#94a3b8",
} as const;

export type HudColor = (typeof HUD)[keyof typeof HUD] | string;
type IconType = React.ComponentType<{ className?: string; style?: React.CSSProperties }>;

const hex = (c: HudColor): string => (c in HUD ? HUD[c as keyof typeof HUD] : c);
const neon = (c: string, s = 8): string => `0 0 ${s}px ${c}, 0 0 ${Math.round(s * 0.4)}px ${c}`;

/* ── Animated counter ────────────────────────────────────────────── */
function useCountUp(target: number, duration = 500): number {
  const [val, setVal] = useState(target);
  const ref = useRef({ from: target, raf: null as number | null, start: 0 });
  useEffect(() => {
    const ctx = ref.current;
    ctx.from = ctx.raf ? ctx.from : target;
    ctx.start = performance.now();
    if (ctx.raf) cancelAnimationFrame(ctx.raf);
    const tick = (now: number) => {
      const t = Math.min(1, (now - ctx.start) / duration);
      setVal(ctx.from + (target - ctx.from) * (1 - Math.pow(1 - t, 3)));
      if (t < 1) ctx.raf = requestAnimationFrame(tick);
      else ctx.from = target;
    };
    ctx.raf = requestAnimationFrame(tick);
    return () => { if (ctx.raf) cancelAnimationFrame(ctx.raf); };
  }, [target, duration]);
  return val;
}

/* ================================================================== */
/*  BACKGROUND — deep field + hex grid + dual scan lines              */
/* ================================================================== */
export function HudBackground() {
  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div className="absolute inset-0"
        style={{ background: `
          radial-gradient(800px 500px at 5% -5%, color-mix(in srgb, var(--color-brand) 14%, transparent), transparent 60%),
          radial-gradient(900px 600px at 95% 0%, color-mix(in srgb, var(--color-accent) 10%, transparent), transparent 55%),
          radial-gradient(700px 700px at 75% 110%, color-mix(in srgb, #22d3ee 8%, transparent), transparent 60%)
        ` }}
      />
      <svg className="absolute inset-0 h-full w-full opacity-[0.06]"
        xmlns="http://www.w3.org/2000/svg" width="100%" height="100%">
        <defs>
          <pattern id="hx" width="48" height="83" patternUnits="userSpaceOnUse" patternTransform="scale(0.7)">
            <path d="M24 0l24 14v28l-24 14-24-14V14z" fill="none" stroke="var(--color-text)" strokeWidth="0.4" opacity="0.25" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#hx)" />
      </svg>
      <div className="absolute -inset-x-20 top-0 h-px animate-[cc-scan_8s_ease-in-out_infinite]"
        style={{
          background: "linear-gradient(90deg, transparent, color-mix(in srgb, var(--color-accent) 70%, transparent) 50%, transparent)",
          boxShadow: "0 0 24px color-mix(in srgb, var(--color-accent) 40%, transparent)",
        }} />
      <div className="absolute -inset-x-20 top-0 h-px animate-[cc-scan_11s_ease-in-out_infinite_3s] opacity-50"
        style={{
          background: "linear-gradient(90deg, transparent, color-mix(in srgb, #22d3ee 60%, transparent) 50%, transparent)",
          boxShadow: "0 0 16px #22d3ee30",
        }} />
      </div>
    </div>
  );
}

/* ================================================================== */
/*  CORNER BRACKET                                                    */
/* ================================================================== */
function Corner({ pos, color, size = 14 }: { pos: "tl" | "tr" | "bl" | "br"; color: string; size?: number }) {
  const t = { top: 6, bottom: 6 } as CSSProperties;
  const l = { left: 6, right: 6 } as CSSProperties;
  return (
    <span aria-hidden className="pointer-events-none absolute z-10"
      style={{
        [pos.startsWith("t") ? "top" : "bottom"]: 6,
        [pos.endsWith("l") ? "left" : "right"]: 6,
        width: size, height: size,
        borderTop: pos.startsWith("t") ? `1.5px solid ${color}` : "none",
        borderLeft: pos.endsWith("l") ? `1.5px solid ${color}` : "none",
        borderRight: pos.endsWith("r") ? `1.5px solid ${color}` : "none",
        borderBottom: pos.startsWith("b") ? `1.5px solid ${color}` : "none",
        [pos.startsWith("t") && pos.endsWith("l") ? "borderTopLeftRadius" :
         pos.startsWith("t") && pos.endsWith("r") ? "borderTopRightRadius" :
         pos.startsWith("b") && pos.endsWith("l") ? "borderBottomLeftRadius" :
         "borderBottomRightRadius"]: 8,
        boxShadow: neon(color, 3),
      }}
    />
  );
}

/* ================================================================== */
/*  SECTION WRAPPER — compact framed container                         */
/* ================================================================== */
export function Section({ title, subtitle, icon: Icon, accent = "cyan", status, count, className, children }: {
  title: string; subtitle?: string; icon?: IconType; accent?: HudColor;
  status?: "live" | "warn" | "crit" | "idle"; count?: number;
  className?: string; children: React.ReactNode;
}) {
  const c = hex(accent);
  const sc = status === "crit" ? HUD.red : status === "warn" ? HUD.amber : status === "idle" ? HUD.slate : HUD.green;
  return (
    <section className={cn("theme-card rounded-xl relative overflow-hidden group", className)}
      style={{ boxShadow: `0 4px 20px -12px ${c}20, inset 0 0 0 1px ${c}10` }}>
      <Corner pos="tl" color={c} /><Corner pos="tr" color={c} />
      <Corner pos="bl" color={c} /><Corner pos="br" color={c} />
      <div className="absolute inset-x-0 top-0 h-px opacity-60"
        style={{ background: `linear-gradient(90deg, transparent, ${c}, transparent)`, boxShadow: `0 0 8px ${c}` }} />
      {/* Header */}
      <header className="relative flex items-center gap-2 border-b border-glass-border/30 px-3 py-2">
        {Icon && (
          <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-surface-2/50"
            style={{ border: `1px solid ${c}25`, boxShadow: `0 0 14px ${c}15` }}>
            <Icon className="h-3 w-3" style={{ color: c, filter: `drop-shadow(0 0 4px ${c})` }} />
          </div>
        )}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5">
            <h3 className="truncate text-[11px] font-bold tracking-tight text-text">{title}</h3>
            {typeof count === "number" && count > 0 && (
              <span className="theme-chip-danger rounded-full px-1.5 py-[1px] text-[9px] font-bold leading-tight">{count}</span>
            )}
          </div>
          {subtitle && <p className="truncate text-[8px] font-mono uppercase tracking-[0.18em] text-text-faint">{subtitle}</p>}
        </div>
        {status && (
          <span className="flex items-center gap-1.5 text-[9px] font-bold font-mono uppercase" style={{ color: sc }}>
            <span className="relative flex h-2 w-2">
              {status === "live" && <span className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-60" style={{ background: sc }} />}
              <span className="relative inline-flex h-2 w-2 rounded-full" style={{ background: sc, boxShadow: neon(sc, 5) }} />
            </span>
          </span>
        )}
      </header>
      <div className={cn("relative p-3", className)}>{children}</div>
    </section>
  );
}

/* ================================================================== */
/*  STAT — compact single metric card                                  */
/* ================================================================== */
export function Stat({ label, value, format, icon: Icon, accent = "cyan", trend, delta, sparkline, clickable, loading = false }: {
  label: string; value: number; format?: (n: number) => string;
  icon?: IconType; accent?: HudColor; trend?: "up" | "down" | "neutral";
  delta?: string; sparkline?: number[]; clickable?: boolean; loading?: boolean;
}) {
  const c = hex(accent);
  const animated = useCountUp(value);
  const display = format ? format(animated) : Math.round(animated).toLocaleString();
  const tc = trend === "up" ? HUD.green : trend === "down" ? HUD.red : HUD.slate;
  if (loading) return (
    <div className="theme-elevated rounded-lg p-2.5 animate-pulse"
      style={{ borderLeft: `2px solid ${c}30` }}>
      <div className="h-2 w-2/3 rounded bg-surface-2/60 mb-1.5" />
      <div className="h-5 w-1/2 rounded bg-surface-2/40" />
    </div>
  );
  return (
    <div className={cn("theme-elevated relative overflow-hidden rounded-lg p-2.5", clickable && "cursor-pointer hover:bg-surface-2/40 transition-colors")}
      style={{ borderLeft: `2px solid ${c}` }}>
      <div className="pointer-events-none absolute -right-6 -top-6 h-14 w-14 rounded-full opacity-[0.08] blur-2xl" style={{ background: c }} />
      <div className="relative flex items-center justify-between gap-1">
        <span className="text-[9px] font-bold font-mono uppercase tracking-[0.12em] text-text-faint">{label}</span>
        {Icon && <Icon className="h-3 w-3 shrink-0" style={{ color: c, filter: `drop-shadow(0 0 3px ${c})` }} />}
      </div>
      <div className="relative mt-1 flex items-end gap-1.5">
        <span className="text-base font-bold leading-none tracking-tight text-text tabular-nums"
          style={{ textShadow: `0 0 16px ${c}20` }}>{display}</span>
        {trend && <span className="mb-[1px] text-[10px] font-bold" style={{ color: tc }}>{trend === "up" ? "▲" : trend === "down" ? "▼" : "◆"}</span>}
      </div>
      {delta && <p className="relative mt-[2px] text-[9px] font-bold font-mono" style={{ color: tc }}>{delta}</p>}
      {sparkline && sparkline.length > 1 && (
        <div className="relative mt-1">
          <MicroChart data={sparkline} color={c} height={16} width={80} />
        </div>
      )}
    </div>
  );
}

/* ================================================================== */
/*  MICRO CHART — ultra-compact inline area sparkline                  */
/* ================================================================== */
export function MicroChart({ data, color = "cyan", height = 24, width = 60, fill = true }: {
  data: number[]; color?: HudColor; height?: number; width?: number; fill?: boolean;
}) {
  const c = hex(color);
  if (!data?.length) return <div className="inline-block align-middle" style={{ width, height }} />;
  const mn = Math.min(...data), mx = Math.max(...data), sp = mx - mn || 1;
  const st = data.length > 1 ? width / (data.length - 1) : width;
  const pts = data.map((d, i) => [i * st, height - ((d - mn) / sp) * (height - 2) - 1]);
  const line = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ");
  const id = `mc-${c.replace(/[#.]/g, "")}`;
  const last = pts[pts.length - 1];
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="inline-block align-middle overflow-visible" style={{ width, height }}>
      <defs><linearGradient id={id} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={c} stopOpacity={0.3} /><stop offset="100%" stopColor={c} stopOpacity={0} /></linearGradient></defs>
      {fill && <path d={`${line} L${width},${height} L0,${height} Z`} fill={`url(#${id})`} />}
      <path d={line} fill="none" stroke={c} strokeWidth={1.2} strokeLinecap="round" strokeLinejoin="round" style={{ filter: `drop-shadow(0 0 3px ${c})` }} />
      {last && <circle cx={last[0]} cy={last[1]} r={2} fill={c} style={{ filter: `drop-shadow(0 0 4px ${c})` }} />}
    </svg>
  );
}

/* ================================================================== */
/*  AREA CHART — compact (used for revenue trend)                     */
/* ================================================================== */
export function AreaChart({ data, color = "cyan", height = 80, loading = false }: {
  data: { label: string; value: number }[]; color?: HudColor; height?: number; loading?: boolean;
}) {
  if (loading) return <div className="w-full rounded-lg bg-surface-2/60 animate-pulse" style={{ height }} />;
  if (!data?.length) return <div className="flex w-full items-center justify-center rounded-lg bg-surface-2/30 text-[9px] text-text-faint" style={{ height }}>NO DATA</div>;
  const c = hex(color);
  const w = 300;
  const mx = Math.max(...data.map(d => d.value)) || 1;
  const mn = Math.min(...data.map(d => d.value));
  const sp = mx - mn || 1;
  const pd = 6;
  const sx = data.length > 1 ? (w - pd * 2) / (data.length - 1) : w;
  const pts = data.map((d, i) => [pd + i * sx, height - pd - ((d.value - mn) / sp) * (height - pd * 2)]);
  const line = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ");
  const gid = `ar-${c.replace(/[#.]/g, "")}`;
  const last = pts[pts.length - 1];
  return (
    <svg viewBox={`0 0 ${w} ${height}`} preserveAspectRatio="none" className="w-full" style={{ height }}>
      <defs><linearGradient id={gid} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={c} stopOpacity={0.3} /><stop offset="100%" stopColor={c} stopOpacity={0} /></linearGradient></defs>
      {[0.33, 0.66].map(g => <line key={g} x1={pd} x2={w - pd} y1={pd + g * (height - pd * 2)} y2={pd + g * (height - pd * 2)} stroke={c} strokeOpacity={0.08} strokeDasharray="2 4" />)}
      <path d={`${line} L${w - pd},${height - pd} L${pd},${height - pd} Z`} fill={`url(#${gid})`} />
      <path d={line} fill="none" stroke={c} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" style={{ filter: `drop-shadow(0 0 6px ${c})` }} />
      <circle cx={last[0]} cy={last[1]} r={2.5} fill={c} style={{ filter: `drop-shadow(0 0 8px ${c})` }} />
      <circle cx={last[0]} cy={last[1]} r={6} fill="none" stroke={c} strokeOpacity={0.25}>
        <animate attributeName="r" values="3;8;3" dur="2.5s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.4;0;0.4" dur="2.5s" repeatCount="indefinite" />
      </circle>
    </svg>
  );
}

/* ================================================================== */
/*  DONUT CHART — compact pie                                          */
/* ================================================================== */
export function DonutChart({ segments, centerLabel, centerValue, height = 80, loading = false }: {
  segments: { label: string; value: number; color: HudColor }[];
  centerLabel?: string; centerValue?: string; height?: number; loading?: boolean;
}) {
  if (loading) return <div className="w-full rounded-lg bg-surface-2/60 animate-pulse" style={{ height }} />;
  const total = segments.reduce((s, x) => s + x.value, 0) || 1;
  const size = 100, r = 34, cx = size / 2, cy = size / 2;
  const circ = 2 * Math.PI * r;
  let offset = 0;
  return (
    <div className="flex items-center gap-3" style={{ minHeight: height }}>
      <svg viewBox={`0 0 ${size} ${size}`} style={{ width: height, height }} className="shrink-0">
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--color-border)" strokeOpacity={0.3} strokeWidth={10} />
        {segments.map((s, i) => {
          const frac = s.value / total, len = frac * circ;
          const seg = (<circle key={i} cx={cx} cy={cy} r={r} fill="none" stroke={hex(s.color)} strokeWidth={10}
            strokeDasharray={`${len} ${circ - len}`} strokeDashoffset={-offset} strokeLinecap="butt"
            transform={`rotate(-90 ${cx} ${cy})`} style={{ filter: `drop-shadow(0 0 4px ${hex(s.color)})` }} />);
          offset += len;
          return seg;
        })}
        <text x={cx} y={cy - 2} textAnchor="middle" className="fill-text font-bold" style={{ fontSize: 14, fontWeight: 800 }}>
          {centerValue ?? ""}
        </text>
        <text x={cx} y={cy + 10} textAnchor="middle" className="fill-text-faint" style={{ fontSize: 7, letterSpacing: 1 }}>
          {centerLabel ?? ""}
        </text>
      </svg>
      <div className="flex-1 min-w-0 space-y-1">
        {segments.map((s, i) => (
          <div key={i} className="flex items-center justify-between gap-1 text-[9px]">
            <span className="flex min-w-0 items-center gap-1.5">
              <span className="h-2 w-2 shrink-0 rounded-[2px]" style={{ background: hex(s.color), boxShadow: neon(hex(s.color), 3) }} />
              <span className="truncate text-text-muted">{s.label}</span>
            </span>
            <span className="shrink-0 font-bold font-mono text-text tabular-nums">{Math.round((s.value / total) * 100)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ================================================================== */
/*  BAR CHART — compact vertical bars                                   */
/* ================================================================== */
export function Bars({ data, height = 80, loading = false, valueFormat }: {
  data: { label: string; value: number; color?: HudColor }[];
  height?: number; loading?: boolean; valueFormat?: (n: number) => string;
}) {
  if (loading) return <div className="w-full rounded-lg bg-surface-2/60 animate-pulse" style={{ height }} />;
  if (!data?.length) return <div className="flex w-full items-center justify-center rounded-lg bg-surface-2/30 text-[9px] text-text-faint" style={{ height }}>NO DATA</div>;
  const mx = Math.max(...data.map(d => d.value)) || 1;
  return (
    <div className="flex items-end gap-1.5" style={{ height }}>
      {data.map((d, i) => {
        const c = hex(d.color ?? "cyan");
        const pct = (d.value / mx) * 100;
        return (
          <div key={i} className="group flex flex-1 flex-col items-center justify-end gap-1">
            <span className="text-[8px] font-bold font-mono text-text tabular-nums opacity-0 group-hover:opacity-100 transition-opacity">
              {valueFormat ? valueFormat(d.value) : d.value.toLocaleString()}
            </span>
            <div className="relative flex w-full max-w-[24px] items-end justify-center" style={{ height: height - 18 }}>
              <div className="w-full rounded-t-sm transition-all duration-500"
                style={{ height: `${Math.max(3, pct)}%`, background: `linear-gradient(180deg, ${c}, ${c}10)`, boxShadow: `0 0 8px ${c}30` }} />
            </div>
            <span className="max-w-full truncate text-[7px] font-mono uppercase tracking-wide text-text-faint">{d.label}</span>
          </div>
        );
      })}
    </div>
  );
}

/* ================================================================== */
/*  GAUGE — tiny arc gauge                                             */
/* ================================================================== */
export function Gauge({ value, max = 100, label, unit = "%", color = "green", warn = 70, crit = 90, size = 48, loading = false }: {
  value: number; max?: number; label: string; unit?: string; color?: HudColor;
  warn?: number; crit?: number; size?: number; loading?: boolean;
}) {
  const c = hex(value >= crit ? HUD.red : value >= warn ? HUD.amber : color);
  const r = (size - 8) / 2, cx = size / 2, cy = size / 2, circ = 2 * Math.PI * r;
  const pct = Math.min(1, value / max);
  if (loading) return <div className="rounded-full bg-surface-2/60 animate-pulse" style={{ width: size, height: size }} />;
  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg viewBox={`0 0 ${size} ${size}`} className="h-full w-full -rotate-90">
          <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--color-border)" strokeOpacity={0.4} strokeWidth={5} />
          <circle cx={cx} cy={cy} r={r} fill="none" stroke={c} strokeWidth={5} strokeLinecap="round"
            strokeDasharray={`${pct * circ} ${circ}`} style={{ filter: `drop-shadow(0 0 5px ${c})`, transition: "stroke-dasharray 0.6s ease" }} />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-[10px] font-bold leading-none text-text tabular-nums" style={{ textShadow: `0 0 10px ${c}40` }}>
            {Math.round(value)}<span className="text-[7px] font-medium text-text-faint">{unit}</span>
          </span>
        </div>
      </div>
      <span className="mt-1 text-[8px] font-bold font-mono uppercase tracking-[0.14em] text-text-faint">{label}</span>
    </div>
  );
}

/* ================================================================== */
/*  METER — horizontal health bar                                      */
/* ================================================================== */
export function Meter({ value, max = 100, color = "green", warn, crit, label, loading = false }: {
  value: number; max?: number; color?: HudColor; warn?: number; crit?: number;
  label?: string; loading?: boolean;
}) {
  const c = hex(warn !== undefined && crit !== undefined && value >= crit ? HUD.red : warn !== undefined && value >= warn ? HUD.amber : color);
  const pct = Math.min(100, (value / max) * 100);
  if (loading) return <div className="h-2 w-full rounded-full bg-surface-2/60 animate-pulse" />;
  return (
    <div>
      {label && <div className="mb-[2px] flex items-center justify-between text-[8px] font-mono">
        <span className="font-semibold text-text-muted">{label}</span>
        <span className="font-bold tabular-nums" style={{ color: c, textShadow: `0 0 4px ${c}` }}>
          {typeof value === "number" ? value.toFixed(1) : value}{max > 1 ? `/${max}` : ""}
        </span>
      </div>}
      <div className="h-2 w-full overflow-hidden rounded-full bg-surface-2/50">
        <div className="h-full rounded-full transition-all duration-700 ease-out"
          style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${c}70, ${c})`, boxShadow: `0 0 8px ${c}30` }} />
      </div>
    </div>
  );
}

/* ================================================================== */
/*  TICKER — marquee news bar                                          */
/* ================================================================== */
export function Ticker({ items, loading = false }: {
  items: { title: string; category?: string; sentiment?: string }[];
  loading?: boolean;
}) {
  const sc = (s?: string) => s === "positive" ? HUD.green : s === "negative" ? HUD.red : HUD.cyan;
  if (loading) return <div className="h-7 w-full rounded bg-surface-2/60 animate-pulse" />;
  if (!items?.length) return (
    <div className="theme-elevated flex h-7 items-center gap-2 rounded px-3 text-[9px] text-text-faint">
      <span className="h-1.5 w-1.5 rounded-full bg-slate-500" /> Awaiting feed…
    </div>
  );
  const loop = [...items, ...items];
  return (
    <div className="theme-elevated relative overflow-hidden rounded" style={{ borderLeft: `2px solid ${HUD.cyan}` }}>
      <div className="pointer-events-none absolute left-0 top-0 z-10 h-full w-10" style={{ background: "linear-gradient(90deg, var(--color-surface-1), transparent)" }} />
      <div className="pointer-events-none absolute right-0 top-0 z-10 h-full w-10" style={{ background: "linear-gradient(270deg, var(--color-surface-1), transparent)" }} />
      <div className="flex w-max animate-[cc-marquee_40s_linear_infinite] gap-8 pl-3 py-1.5">
        {loop.map((it, i) => (
          <span key={i} className="flex items-center gap-1.5 whitespace-nowrap text-[9px]">
            <span className="h-1.5 w-1.5 rounded-full" style={{ background: sc(it.sentiment), boxShadow: neon(sc(it.sentiment), 3) }} />
            <span className="font-bold font-mono uppercase tracking-wider text-text-faint">[{it.category ?? "INTEL"}]</span>
            <span className="text-text">{it.title}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

/* ================================================================== */
/*  ALERT ROW                                                          */
/* ================================================================== */
export function AlertRow({ alert, onOpen }: {
  alert: { id: number; title: string; message?: string; severity?: string; country_code?: string | null };
  onOpen?: () => void;
}) {
  const sc = alert.severity === "critical" ? HUD.red : alert.severity === "warning" ? HUD.amber : HUD.blue;
  return (
    <button type="button" onClick={onOpen}
      className="theme-elevated group flex w-full items-start gap-2 rounded px-2.5 py-2 text-left transition-all hover:bg-surface-2/30"
      style={{ borderLeft: `2px solid ${sc}` }}>
      <span className="mt-0.5 flex h-1.5 w-1.5 shrink-0">
        {alert.severity === "critical" && <span className="absolute h-1.5 w-1.5 animate-ping rounded-full opacity-50" style={{ background: sc }} />}
        <span className="h-1.5 w-1.5 rounded-full" style={{ background: sc, boxShadow: neon(sc, 4) }} />
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <span className="truncate text-[10px] font-bold text-text group-hover:text-primary">{alert.title}</span>
          {alert.country_code && <span className="rounded bg-surface-2/60 px-1 py-[1px] text-[7px] font-bold font-mono uppercase text-text-faint">{alert.country_code}</span>}
        </div>
        {alert.message && <p className="mt-[1px] line-clamp-1 text-[9px] text-text-muted">{alert.message}</p>}
      </div>
      <span className="shrink-0 self-start rounded px-1.5 py-[1px] text-[7px] font-bold font-mono uppercase tracking-wider"
        style={{ background: `${sc}15`, color: sc }}>{alert.severity ?? "info"}</span>
    </button>
  );
}

/* ================================================================== */
/*  FRAUD ROW                                                          */
/* ================================================================== */
export function FraudRow({ fa, onOpen }: {
  fa: { id: number; score: number; triggered_rules?: string[]; priority?: string };
  onOpen?: () => void;
}) {
  const pc = fa.priority === "high" ? HUD.red : fa.priority === "medium" ? HUD.amber : HUD.slate;
  const score = Math.round((fa.score || 0) * 100);
  return (
    <button type="button" onClick={onOpen}
      className="theme-elevated group flex w-full items-center gap-2 rounded px-2.5 py-2 transition-all hover:bg-surface-2/30"
      style={{ borderLeft: `2px solid ${pc}` }}>
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded text-[9px] font-bold font-mono"
        style={{ background: `${pc}12`, color: pc, border: `1px solid ${pc}15` }}>{score}</span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-[10px] font-bold text-text group-hover:text-primary">Risk #{fa.id}</p>
        <p className="truncate text-[8px] text-text-muted font-mono">{(fa.triggered_rules ?? []).slice(0, 2).join(" · ") || "—"}</p>
      </div>
      <span className="shrink-0 text-[7px] font-bold font-mono uppercase tracking-wider" style={{ color: pc }}>{fa.priority ?? "low"}</span>
    </button>
  );
}

/* ================================================================== */
/*  RANK ROW                                                          */
/* ================================================================== */
export function RankRow({ rank, label, primary, secondary, accent = "cyan", loading = false }: {
  rank: number; label: string; primary?: string; secondary?: string;
  accent?: HudColor; loading?: boolean;
}) {
  const c = hex(accent);
  if (loading) return <div className="h-6 w-full rounded bg-surface-2/60 animate-pulse" />;
  return (
    <div className="theme-elevated group flex items-center gap-2 rounded px-2 py-1.5 transition-all hover:bg-surface-2/30"
      style={{ borderLeft: `1.5px solid ${c}30` }}>
      <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded text-[8px] font-bold font-mono"
        style={{ background: `${c}12`, color: c }}>{rank}</span>
      <span className="min-w-0 flex-1 truncate text-[10px] font-medium text-text group-hover:text-primary">{label}</span>
      {primary && <span className="shrink-0 text-[9px] font-bold font-mono tabular-nums" style={{ color: c }}>{primary}</span>}
      {secondary && <span className="shrink-0 text-[8px] text-text-muted font-mono">{secondary}</span>}
    </div>
  );
}

/* ================================================================== */
/*  ECO NODE                                                          */
/* ================================================================== */
export function EcoNode({ icon: Icon, label, value, accent = "cyan" }: {
  icon: IconType; label: string; value: number; accent?: HudColor;
}) {
  const c = hex(accent);
  return (
    <div className="theme-elevated flex items-center gap-2 rounded px-2.5 py-2" style={{ borderLeft: `2px solid ${c}` }}>
      <Icon className="h-3 w-3 shrink-0" style={{ color: c, filter: `drop-shadow(0 0 3px ${c})` }} />
      <div className="min-w-0">
        <p className="truncate text-[7px] font-bold font-mono uppercase tracking-[0.12em] text-text-faint">{label}</p>
        <p className="text-xs font-bold text-text tabular-nums" style={{ textShadow: `0 0 8px ${c}20` }}>{value.toLocaleString()}</p>
      </div>
    </div>
  );
}

export { useCountUp };
