"use client";

import React, {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  Fragment,
  type CSSProperties,
  type PointerEvent as ReactPointerEvent,
  type ReactNode,
} from "react";
import {
  Trash2,
  Square,
  Circle,
  Type,
  Image as ImageIcon,
  MousePointerClick,
  Film,
  ArrowUp,
  ArrowDown,
  Plus,
  Copy,
  Undo2,
  Redo2,
  Grid3x3,
  Magnet,
  AlignLeft,
  AlignCenter,
  AlignRight,
  AlignVerticalJustifyStart,
  AlignVerticalJustifyCenter,
  AlignVerticalJustifyEnd,
  Triangle,
  Minus,
  Star,
  Hexagon,
  Sparkles,
  Eye,
  EyeOff,
  Lock,
  Unlock,
  LayoutTemplate,
  ZoomIn,
  ZoomOut,
  BringToFront,
  SendToBack,
  Group,
  Ungroup,
  FlipHorizontal2,
  FlipVertical2,
  FileJson,
  Download,
  Upload,
  Layers,
  Smile,
  // icon element set
  Heart,
  Gift,
  ShoppingBag,
  ShoppingCart,
  Tag,
  Percent,
  Crown,
  Rocket,
  Flame,
  Snowflake,
  Leaf,
  Sun,
  Moon,
  Zap,
  Bell,
  Trophy,
  Coffee,
  Music,
  Camera,
  Plane,
  Umbrella,
  Flower2,
  Diamond,
  type LucideIcon,
} from "lucide-react";

/* ──────────────────────────────────────────────────────────────────────────
   Advanced Banner Canvas Editor
   A complete free-form design surface for admins/employees to build ANY kind
   of banner: shapes (rect, ellipse, triangle, line, star, polygon), text,
   emoji, images, video, buttons (with CTA) and icons — placed anywhere inside
   or outside the banner. Advanced tooling: Layers panel, multi-select with
   alignment + distribute, smart snap guides + grid, undo/redo history,
   keyboard shortcuts, zoom, ready-made templates, gradient fills, rich text
   (font family / alignment / spacing / italic / underline / shadow / outline),
   per-element shadows, blend modes, image filters, entrance animations,
   flip/mirror, grouping, full z-order, copy/paste and JSON export/import —
   plus a celebration / season BACKGROUND EFFECT layer (balloons, poppers,
   ramadan, eid, christmas, diwali, new year, aurora) that is actually rendered.
   Everything serializes to `layout_json`.
   ──────────────────────────────────────────────────────────────────────── */

export type CanvasEffect =
  | ""
  | "balloons"
  | "poppers"
  | "ramadan"
  | "eid"
  | "christmas"
  | "diwali"
  | "newyear"
  | "aurora";

export type CanvasElementType =
  | "rect"
  | "ellipse"
  | "text"
  | "image"
  | "button"
  | "video"
  | "triangle"
  | "line"
  | "star"
  | "polygon"
  | "icon"
  | "emoji";

export type CanvasAnimation = "none" | "float" | "pulse" | "bounce" | "fade";

export interface CanvasElement {
  id: string;
  type: CanvasElementType;
  name?: string;
  visible?: boolean;
  locked?: boolean;
  x: number; // % top-left
  y: number; // % top-left
  w: number; // % width
  h: number; // % height
  rotation: number; // deg
  z: number;
  fill: string;
  stroke: string;
  strokeWidth: number;
  borderRadius: number;
  opacity: number;
  // gradient fill (rect / ellipse / button)
  gradientFrom?: string;
  gradientVia?: string;
  gradientTo?: string;
  gradientAngle?: number;
  gradientType?: "linear" | "radial";
  // effects
  shadow?: { x: number; y: number; blur: number; color: string };
  blend?: string; // normal | multiply | screen | overlay | lighten | darken
  // text / button / emoji
  content?: string;
  textColor?: string;
  fontSize?: number;
  fontWeight?: number;
  fontFamily?: string;
  textAlign?: "left" | "center" | "right";
  letterSpacing?: number;
  lineHeight?: number;
  italic?: boolean;
  underline?: boolean;
  textShadow?: boolean;
  textTransform?: "none" | "uppercase" | "capitalize";
  // image / video
  src?: string;
  objectFit?: "cover" | "contain" | "fill";
  imgFilter?: { brightness: number; contrast: number; saturate: number; blur: number; grayscale: number };
  // button
  ctaUrl?: string;
  // shape specifics
  points?: number; // star points / polygon sides
  icon?: string; // icon element key
  // grouping
  groupId?: string;
  // flip / mirror
  flipX?: boolean;
  flipY?: boolean;
  // text outline (text / button)
  textStroke?: string;
  textStrokeWidth?: number;
  // entrance animation (used in preview / public view)
  animation?: CanvasAnimation;
}

export interface BannerLayout {
  bg: {
    color: string;
    gradientFrom: string;
    gradientVia: string;
    gradientTo: string;
    gradientType?: "linear" | "radial";
    gradientAngle?: number;
    imageUrl: string;
    videoUrl: string;
    bgImageFit?: "cover" | "contain";
    bgImageOpacity?: number;
    overlayColor?: string;
    overlayOpacity?: number;
  };
  effect: CanvasEffect;
  elements: CanvasElement[];
  ratio?: number; // canvas height / width (display only)
}

export const DEFAULT_LAYOUT: BannerLayout = {
  bg: {
    color: "#0f172a",
    gradientFrom: "",
    gradientVia: "",
    gradientTo: "",
    gradientType: "linear",
    gradientAngle: 120,
    imageUrl: "",
    videoUrl: "",
    bgImageFit: "cover",
    bgImageOpacity: 0.3,
    overlayColor: "",
    overlayOpacity: 0.3,
  },
  effect: "balloons",
  elements: [],
  ratio: 0.3,
};

const EFFECT_OPTIONS: { value: CanvasEffect; label: string }[] = [
  { value: "", label: "None" },
  { value: "balloons", label: "Balloons" },
  { value: "poppers", label: "Poppers / Confetti" },
  { value: "ramadan", label: "Ramadan" },
  { value: "eid", label: "Eid" },
  { value: "christmas", label: "Christmas" },
  { value: "diwali", label: "Diwali" },
  { value: "newyear", label: "New Year" },
  { value: "aurora", label: "Aurora" },
];

const ASPECT_OPTIONS: { value: string; label: string; ratio: number }[] = [
  { value: "banner", label: "Banner (wide)", ratio: 0.3 },
  { value: "wide", label: "Ultra-wide", ratio: 0.2 },
  { value: "square", label: "Square", ratio: 1 },
  { value: "story", label: "Story (tall)", ratio: 1.3 },
  { value: "card", label: "Card", ratio: 0.5 },
  { value: "mobile", label: "Mobile strip", ratio: 0.18 },
];

const FONT_OPTIONS: { value: string; label: string }[] = [
  { value: "Inter, system-ui, sans-serif", label: "Inter" },
  { value: "Arial, Helvetica, sans-serif", label: "Arial" },
  { value: "Georgia, 'Times New Roman', serif", label: "Georgia" },
  { value: "Impact, sans-serif", label: "Impact" },
  { value: "'Courier New', monospace", label: "Courier" },
  { value: "'Trebuchet MS', sans-serif", label: "Trebuchet" },
  { value: "Verdana, sans-serif", label: "Verdana" },
  { value: "'Comic Sans MS', cursive", label: "Comic Sans" },
  { value: "'Times New Roman', serif", label: "Times" },
];

const ANIMATION_OPTIONS: { value: CanvasAnimation; label: string }[] = [
  { value: "none", label: "None" },
  { value: "float", label: "Float" },
  { value: "pulse", label: "Pulse" },
  { value: "bounce", label: "Bounce" },
  { value: "fade", label: "Fade in" },
];

const ICON_SET: Record<string, LucideIcon> = {
  Star,
  Heart,
  Gift,
  ShoppingBag,
  ShoppingCart,
  Tag,
  Percent,
  Crown,
  Rocket,
  Flame,
  Snowflake,
  Leaf,
  Sun,
  Moon,
  Zap,
  Bell,
  Trophy,
  Coffee,
  Music,
  Camera,
  Plane,
  Umbrella,
  Flower2,
  Diamond,
  Sparkles,
};
const ICON_NAMES = Object.keys(ICON_SET);

let _seq = 0;
const uid = () => `el-${Date.now().toString(36)}-${(_seq++).toString(36)}`;

const SVG_SHAPES: CanvasElementType[] = ["triangle", "line", "star", "polygon"];

const makeElement = (type: CanvasElementType, z: number): CanvasElement => {
  const base: CanvasElement = {
    id: uid(),
    type,
    name: type.charAt(0).toUpperCase() + type.slice(1),
    visible: true,
    locked: false,
    x: 12,
    y: 22,
    w: 30,
    h: 26,
    rotation: 0,
    z,
    fill: "#ffffff",
    stroke: "transparent",
    strokeWidth: 0,
    borderRadius: type === "rect" ? 12 : 0,
    opacity: 1,
    animation: "none",
  };
  switch (type) {
    case "text":
      return { ...base, fill: "transparent", content: "Your text here", textColor: "#ffffff", fontSize: 24, fontWeight: 800, fontFamily: FONT_OPTIONS[0].value, textAlign: "left", letterSpacing: 0, lineHeight: 1.1 };
    case "emoji":
      return { ...base, fill: "transparent", stroke: "transparent", strokeWidth: 0, content: "🎉", fontSize: 48, fontWeight: 400, fontFamily: FONT_OPTIONS[0].value, textAlign: "center", letterSpacing: 0, lineHeight: 1, name: "Emoji" };
    case "image":
      return { ...base, fill: "transparent", src: "", borderRadius: 12, objectFit: "cover", imgFilter: { brightness: 100, contrast: 100, saturate: 100, blur: 0, grayscale: 0 } };
    case "button":
      return { ...base, fill: "#ffd400", content: "Shop Now", textColor: "#111111", fontSize: 15, fontWeight: 700, fontFamily: FONT_OPTIONS[0].value, borderRadius: 999, ctaUrl: "/products" };
    case "video":
      return { ...base, fill: "#000000", src: "", borderRadius: 12, objectFit: "cover", imgFilter: { brightness: 100, contrast: 100, saturate: 100, blur: 0, grayscale: 0 } };
    case "triangle":
      return { ...base, fill: "#fbbf24", stroke: "transparent", strokeWidth: 0, w: 26, h: 24, borderRadius: 0, name: "Triangle" };
    case "line":
      return { ...base, fill: "transparent", stroke: "#ffffff", strokeWidth: 4, w: 34, h: 3, borderRadius: 0, name: "Line" };
    case "star":
      return { ...base, fill: "#fbbf24", stroke: "transparent", strokeWidth: 0, w: 26, h: 26, points: 5, borderRadius: 0, name: "Star" };
    case "polygon":
      return { ...base, fill: "#60a5fa", stroke: "transparent", strokeWidth: 0, w: 26, h: 26, points: 6, borderRadius: 0, name: "Polygon" };
    case "icon":
      return { ...base, fill: "#f472b6", stroke: "transparent", strokeWidth: 0, w: 18, h: 18, icon: "Star", borderRadius: 0, name: "Icon" };
    default:
      return base;
  }
};

const cloneEl = (el: CanvasElement, z: number): CanvasElement => ({
  ...structuredClone(el),
  id: uid(),
  z,
  name: el.name ? `${el.name} copy` : undefined,
});

const gradientCss = (g: { gradientFrom?: string; gradientVia?: string; gradientTo?: string; gradientAngle?: number; gradientType?: "linear" | "radial" }): string => {
  if (!g.gradientFrom) return "";
  const stops = [g.gradientFrom, g.gradientVia, g.gradientTo].filter(Boolean).join(", ");
  return g.gradientType === "radial"
    ? `radial-gradient(circle, ${stops})`
    : `linear-gradient(${g.gradientAngle ?? 120}deg, ${stops})`;
};

/* color alpha helpers (so fills/text/strokes can be translucent) */
const hexToRgb = (c: string): [number, number, number] | null => {
  let h = c.replace("#", "");
  if (h.length === 3) h = h.split("").map((x) => x + x).join("");
  if (h.length !== 6) return null;
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
};
const toRgba = (color: string, alpha: number): string => {
  const m = color.match(/rgba?\(([^)]+)\)/);
  if (m) {
    const parts = m[1].split(",").map((s) => s.trim());
    const rgb = parts.slice(0, 3).join(", ");
    return `rgba(${rgb}, ${alpha})`;
  }
  const rgb = hexToRgb(color);
  if (rgb) return `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, ${alpha})`;
  return color;
};
const readAlpha = (color: string): number => {
  const m = color.match(/rgba?\([^)]*,\s*([\d.]+)\s*\)/);
  return m ? parseFloat(m[1]) : 1;
};
const solidHex = (color: string): string => {
  const m = color.match(/rgba?\(([^)]+)\)/);
  if (!m) return color.startsWith("#") ? color : "#ffffff";
  const p = m[1].split(",").map((s) => s.trim());
  const toHex = (n: number) => Math.max(0, Math.min(255, Math.round(n))).toString(16).padStart(2, "0");
  return `#${toHex(Number(p[0]))}${toHex(Number(p[1]))}${toHex(Number(p[2]))}`;
};

/* merge a parsed layout with defaults (for JSON import) */
const mergeLayout = (raw: any): BannerLayout => {
  const base = structuredClone(DEFAULT_LAYOUT);
  if (!raw || typeof raw !== "object") return base;
  const bg = { ...base.bg, ...(raw.bg || {}) };
  const elements = Array.isArray(raw.elements)
    ? raw.elements.map((e: any, i: number) => ({ ...makeElement("rect", i + 1), ...e }))
    : base.elements;
  return { ...base, bg, elements, effect: raw.effect ?? base.effect, ratio: raw.ratio ?? base.ratio };
};

/* SVG path generation for polygon-based shapes (viewBox 0..100) */
const shapeSvg = (el: CanvasElement): ReactNode => {
  if (el.type === "triangle") {
    return <polygon points="50,6 94,94 6,94" fill={el.fill} stroke={el.stroke} strokeWidth={el.strokeWidth} vectorEffect="non-scaling-stroke" />;
  }
  if (el.type === "line") {
    return <line x1="4" y1="50" x2="96" y2="50" stroke={el.stroke} strokeWidth={el.strokeWidth || 2} vectorEffect="non-scaling-stroke" strokeLinecap="round" />;
  }
  if (el.type === "star") {
    const n = el.points ?? 5;
    const pts: string[] = [];
    for (let i = 0; i < n * 2; i++) {
      const r = i % 2 === 0 ? 48 : 20;
      const a = (Math.PI / n) * i - Math.PI / 2;
      pts.push(`${50 + r * Math.cos(a)},${50 + r * Math.sin(a)}`);
    }
    return <polygon points={pts.join(" ")} fill={el.fill} stroke={el.stroke} strokeWidth={el.strokeWidth} vectorEffect="non-scaling-stroke" />;
  }
  // polygon
  const n = el.points ?? 6;
  const pts: string[] = [];
  for (let i = 0; i < n; i++) {
    const a = (2 * Math.PI / n) * i - Math.PI / 2;
    pts.push(`${50 + 46 * Math.cos(a)},${50 + 46 * Math.sin(a)}`);
  }
  return <polygon points={pts.join(" ")} fill={el.fill} stroke={el.stroke} strokeWidth={el.strokeWidth} vectorEffect="non-scaling-stroke" />;
};

/* ── Celebration / season background effect layer ──────────────────────────
   These are generated once (module scope) so they stay stable across renders.
   Pure CSS animations + a single injected <style> block. ─────────────────── */

type Deco = { left: number; delay: number; dur: number; color: string; size: number; rot?: number };

const rnd = (seed: number) => {
  let s = seed;
  return () => {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  };
};

const buildDeco = (count: number, colors: string[], seed: number, opts?: { sizeMin?: number; sizeMax?: number; rot?: boolean }): Deco[] => {
  const r = rnd(seed);
  const sizeMin = opts?.sizeMin ?? 6;
  const sizeMax = opts?.sizeMax ?? 12;
  return Array.from({ length: count }, () => ({
    left: +(r() * 100).toFixed(1),
    delay: +(r() * 4).toFixed(2),
    dur: +(2.5 + r() * 3).toFixed(2),
    color: colors[Math.floor(r() * colors.length)],
    size: +(sizeMin + r() * (sizeMax - sizeMin)).toFixed(1),
    rot: opts?.rot ? Math.floor(r() * 360) : 0,
  }));
};

const CONFETTI = buildDeco(56, ["#ef4444", "#f59e0b", "#22c55e", "#3b82f6", "#a855f7", "#ec4899", "#ffffff", "#fde68a"], 11, { sizeMin: 5, sizeMax: 11, rot: true });
const SNOW = buildDeco(50, ["#ffffff", "#e0f2fe", "#f1f5f9"], 23, { sizeMin: 4, sizeMax: 9 });
const SPARKLES = buildDeco(40, ["#fde68a", "#fef08a", "#fbbf24", "#ffffff"], 37, { sizeMin: 3, sizeMax: 7 });
const FIREWORKS = [
  { left: 20, top: 30, color: "#f472b6", delay: 0 },
  { left: 50, top: 22, color: "#60a5fa", delay: 1.3 },
  { left: 78, top: 34, color: "#fde68a", delay: 0.6 },
  { left: 35, top: 46, color: "#34d399", delay: 2.1 },
  { left: 65, top: 50, color: "#a78bfa", delay: 1.7 },
];
const BALLOONS = [
  { left: 10, color: "#ef4444", delay: 0 },
  { left: 26, color: "#f59e0b", delay: 0.8 },
  { left: 44, color: "#22c55e", delay: 0.4 },
  { left: 62, color: "#3b82f6", delay: 1.2 },
  { left: 80, color: "#a855f7", delay: 0.6 },
  { left: 92, color: "#ec4899", delay: 1.0 },
];
const LANTERNS = [
  { left: 14, delay: 0 },
  { left: 38, delay: 0.6 },
  { left: 62, delay: 0.3 },
  { left: 86, delay: 0.9 },
];

const EFFECT_CSS = `
@keyframes bcu-fall { 0%{ transform: translateY(-12%) rotate(0deg); opacity:0 } 8%{opacity:1} 100%{ transform: translateY(112%) rotate(360deg); opacity:.9 } }
@keyframes bcu-snow { 0%{ transform: translateY(-12%); opacity:0 } 10%{opacity:1} 100%{ transform: translateY(112%); opacity:.8 } }
@keyframes bcu-twinkle { 0%,100%{ transform: scale(.4); opacity:.2 } 50%{ transform: scale(1); opacity:1 } }
@keyframes bcu-balloon { 0%{ transform: translateY(8%) rotate(-4deg); opacity:0 } 12%{opacity:1} 50%{ transform: translateY(-30%) rotate(4deg) } 100%{ transform: translateY(-118%) rotate(-3deg); opacity:.95 } }
@keyframes bcu-fw { 0%{ transform: scale(0); opacity:0 } 16%{ transform: scale(1.15); opacity:1 } 55%{ transform: scale(1); opacity:.9 } 100%{ transform: scale(1.25); opacity:0 } }
@keyframes bcu-aurora { 0%{ transform: translateX(-12%) skewX(8deg); opacity:.5 } 50%{ transform: translateX(12%) skewX(-8deg); opacity:.85 } 100%{ transform: translateX(-12%) skewX(8deg); opacity:.5 } }
@keyframes bcu-glow { 0%,100%{ filter: drop-shadow(0 0 4px rgba(253,224,71,.5)) } 50%{ filter: drop-shadow(0 0 14px rgba(253,224,71,.95)) } }
@keyframes bcu-anim-float { 0%,100%{ transform: translateY(0) } 50%{ transform: translateY(-8px) } }
@keyframes bcu-anim-pulse { 0%,100%{ transform: scale(1) } 50%{ transform: scale(1.05) } }
@keyframes bcu-anim-bounce { 0%,100%{ transform: translateY(0) } 40%{ transform: translateY(-10px) } 60%{ transform: translateY(0) } 80%{ transform: translateY(-4px) } }
@keyframes bcu-anim-fade { 0%{ opacity:0 } 100%{ opacity:1 } }
.bcu-confetti{ position:absolute; top:0; border-radius:1px; animation: bcu-fall linear infinite; }
.bcu-snow{ position:absolute; top:0; border-radius:999px; animation: bcu-snow linear infinite; }
.bcu-spark{ position:absolute; border-radius:999px; animation: bcu-twinkle ease-in-out infinite; }
.bcu-balloon{ position:absolute; bottom:0; width:42px; height:54px; border-radius:50% 50% 48% 48%; animation: bcu-balloon ease-in infinite; box-shadow: inset -6px -8px 12px rgba(0,0,0,.18); }
.bcu-balloon::after{ content:""; position:absolute; left:50%; top:100%; width:1px; height:26px; background: rgba(255,255,255,.5); transform: translateX(-50%); }
.bcu-fw{ position:absolute; border-radius:999px; animation: bcu-fw ease-out infinite; }
.bcu-aurora{ position:absolute; top:-20%; height:140%; width:60%; filter: blur(26px); opacity:.7; animation: bcu-aurora ease-in-out infinite; mix-blend-mode: screen; }
.bcu-lantern{ position:absolute; top:8%; width:26px; height:34px; border-radius:40% 40% 46% 46%; background: linear-gradient(#f59e0b,#b45309); box-shadow:0 0 18px rgba(245,158,11,.8); animation: bcu-glow ease-in-out infinite; }
.bcu-lantern::before{ content:""; position:absolute; left:50%; top:-22%; width:2px; height:30%; background:#92400e; transform: translateX(-50%); }
.bcu-crescent{ position:absolute; border-radius:999px; background: radial-gradient(circle at 35% 35%, #fff7d6, #fde68a); box-shadow:0 0 30px rgba(253,230,138,.9); }
`;

function BannerEffectLayer({ effect }: { effect: CanvasEffect }) {
  if (!effect) return null;
  if (effect === "balloons") {
    return (
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        {BALLOONS.map((b, i) => (
          <span key={i} className="bcu-balloon" style={{ left: `${b.left}%`, background: b.color, animationDelay: `${b.delay}s`, animationDuration: "7s" }} />
        ))}
      </div>
    );
  }
  if (effect === "poppers" || effect === "ramadan" || effect === "eid" || effect === "diwali") {
    const items = effect === "poppers" ? CONFETTI : SPARKLES;
    return (
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        {items.map((c, i) => (
          <span key={i} className={effect === "poppers" ? "bcu-confetti" : "bcu-spark"} style={{ left: `${c.left}%`, width: c.size, height: effect === "poppers" ? c.size * 0.6 : c.size, background: c.color, animationDelay: `${c.delay}s`, animationDuration: effect === "poppers" ? `${c.dur}s` : `${2 + (c.delay % 2)}s` }} />
        ))}
        {effect === "ramadan" &&
          LANTERNS.map((l, i) => <span key={`l${i}`} className="bcu-lantern" style={{ left: `${l.left}%`, animationDelay: `${l.delay}s` }} />)}
        {effect === "ramadan" && <span className="bcu-crescent" style={{ right: "8%", top: "12%", width: 54, height: 54 }} />}
        {effect === "eid" && <span className="bcu-crescent" style={{ left: "8%", top: "14%", width: 50, height: 50 }} />}
        {effect === "diwali" && <span className="bcu-crescent" style={{ right: "10%", top: "14%", width: 30, height: 30, opacity: 0.6 }} />}
      </div>
    );
  }
  if (effect === "christmas") {
    return (
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        {SNOW.map((c, i) => (
          <span key={i} className="bcu-snow" style={{ left: `${c.left}%`, width: c.size, height: c.size, background: c.color, animationDelay: `${c.delay}s`, animationDuration: `${c.dur + 1.5}s` }} />
        ))}
      </div>
    );
  }
  if (effect === "newyear") {
    return (
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        {FIREWORKS.map((f, i) => (
          <span key={i} className="bcu-fw" style={{ left: `${f.left}%`, top: `${f.top}%`, width: 90, height: 90, background: `radial-gradient(circle, ${f.color} 0%, transparent 60%)`, animationDelay: `${f.delay}s`, animationDuration: "3s" }} />
        ))}
        {SPARKLES.slice(0, 18).map((c, i) => (
          <span key={`s${i}`} className="bcu-spark" style={{ left: `${c.left}%`, top: `${c.delay * 12}%`, width: c.size, height: c.size, background: c.color, animationDelay: `${c.delay}s` }} />
        ))}
      </div>
    );
  }
  if (effect === "aurora") {
    return (
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <span className="bcu-aurora" style={{ left: "0%", background: "linear-gradient(90deg,#22d3ee,#34d399)", animationDuration: "9s" }} />
        <span className="bcu-aurora" style={{ left: "30%", background: "linear-gradient(90deg,#a78bfa,#60a5fa)", animationDuration: "11s", animationDelay: "1s" }} />
        <span className="bcu-aurora" style={{ left: "55%", background: "linear-gradient(90deg,#f472b6,#f59e0b)", animationDuration: "13s", animationDelay: "2s" }} />
      </div>
    );
  }
  return null;
}

/* Presentational render of one element — shared by editor + read-only view */
export function renderCanvasElement(
  el: CanvasElement,
  opts: { interactive?: boolean; onPointerDown?: (e: ReactPointerEvent, el: CanvasElement) => void; resolve?: (s: string) => string; animate?: boolean }
): ReactNode {
  const base: CSSProperties = {
    position: "absolute",
    left: `${el.x}%`,
    top: `${el.y}%`,
    width: `${el.w}%`,
    height: `${el.h}%`,
    transform: `rotate(${el.rotation}deg) scaleX(${el.flipX ? -1 : 1}) scaleY(${el.flipY ? -1 : 1})`,
    opacity: el.opacity ?? 1,
    zIndex: el.z,
    transformOrigin: "center",
    boxSizing: "border-box",
    borderRadius: el.type === "ellipse" ? "50%" : `${el.borderRadius || 0}px`,
    overflow: "hidden",
    cursor: opts.interactive ? "move" : "default",
  };
  if (opts.animate && el.animation && el.animation !== "none") base.animation = `bcu-anim-${el.animation} 2.4s ease-in-out infinite`;
  if (SVG_SHAPES.includes(el.type)) {
    return (
      <div key={el.id} style={base} onPointerDown={opts.onPointerDown ? (e) => opts.onPointerDown!(e, el) : undefined}>
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ width: "100%", height: "100%", display: "block", overflow: "visible" }}>
          {shapeSvg(el)}
        </svg>
      </div>
    );
  }
  if (el.type === "rect" || el.type === "ellipse" || el.type === "button") {
    base.background = gradientCss(el) || el.fill;
  }
  if ((el.strokeWidth || 0) > 0 && !SVG_SHAPES.includes(el.type)) {
    base.border = `${el.strokeWidth}px solid ${el.stroke || "transparent"}`;
  }
  if (el.shadow) {
    base.boxShadow = `${el.shadow.x}px ${el.shadow.y}px ${el.shadow.blur}px ${el.shadow.color}`;
  }
  if (el.blend && el.blend !== "normal") {
    base.mixBlendMode = el.blend as CSSProperties["mixBlendMode"];
  }

  if (el.type === "text" || el.type === "emoji") {
    return (
      <div
        key={el.id}
        style={{ ...base, background: el.fill, display: "flex", alignItems: "center", justifyContent: el.textAlign === "center" ? "center" : el.textAlign === "right" ? "flex-end" : "flex-start", padding: "0 3%" }}
        onPointerDown={opts.onPointerDown ? (e) => opts.onPointerDown!(e, el) : undefined}
      >
        <span
          style={{
            color: el.textColor,
            fontSize: `${el.fontSize}px`,
            fontWeight: el.fontWeight,
            fontFamily: el.fontFamily,
            letterSpacing: `${el.letterSpacing ?? 0}px`,
            lineHeight: el.lineHeight ?? 1.1,
            fontStyle: el.italic ? "italic" : "normal",
            textDecoration: el.underline ? "underline" : "none",
            textTransform: el.textTransform || "none",
            textShadow: el.textShadow ? "0 2px 8px rgba(0,0,0,0.55)" : undefined,
            WebkitTextStroke: el.textStrokeWidth ? `${el.textStrokeWidth}px ${el.textStroke || "#000000"}` : undefined,
            width: "100%",
            wordBreak: "break-word",
          }}
        >
          {el.content}
        </span>
      </div>
    );
  }
  if (el.type === "button") {
    return (
      <div
        key={el.id}
        style={{ ...base, background: gradientCss(el) || el.fill, display: "flex", alignItems: "center", justifyContent: "center" }}
        onPointerDown={opts.onPointerDown ? (e) => opts.onPointerDown!(e, el) : undefined}
      >
        <span style={{ color: el.textColor, fontSize: `${el.fontSize}px`, fontWeight: el.fontWeight, fontFamily: el.fontFamily }}>{el.content}</span>
      </div>
    );
  }
  if (el.type === "icon") {
    const Icon = el.icon ? ICON_SET[el.icon] : Star;
    return (
      <div key={el.id} style={base} onPointerDown={opts.onPointerDown ? (e) => opts.onPointerDown!(e, el) : undefined}>
        <div style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center" }}>
          {Icon ? <Icon style={{ width: "100%", height: "100%" }} color={el.fill} strokeWidth={el.strokeWidth || 2} /> : null}
        </div>
      </div>
    );
  }
  const filterCss = el.imgFilter
    ? `brightness(${el.imgFilter.brightness ?? 100}%) contrast(${el.imgFilter.contrast ?? 100}%) saturate(${el.imgFilter.saturate ?? 100}%) blur(${el.imgFilter.blur ?? 0}px) grayscale(${el.imgFilter.grayscale ?? 0}%)`
    : undefined;
  if (el.type === "image") {
    const src = el.src ? (opts.resolve ? opts.resolve(el.src) : el.src) : "";
    return (
      <div key={el.id} style={base} onPointerDown={opts.onPointerDown ? (e) => opts.onPointerDown!(e, el) : undefined}>
        {src ? (
          <img src={src} alt={el.content || "banner image"} style={{ width: "100%", height: "100%", objectFit: el.objectFit || "cover", display: "block", filter: filterCss }} />
        ) : (
          <div style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", background: "#1e293b", color: "#94a3b8", fontSize: 12 }}>Image URL</div>
        )}
      </div>
    );
  }
  // video
  const src = el.src ? (opts.resolve ? opts.resolve(el.src) : el.src) : "";
  return (
    <div key={el.id} style={base} onPointerDown={opts.onPointerDown ? (e) => opts.onPointerDown!(e, el) : undefined}>
      {src ? (
        <video src={src} autoPlay muted loop playsInline style={{ width: "100%", height: "100%", objectFit: el.objectFit || "cover", display: "block", filter: filterCss }} />
      ) : (
        <div style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", background: "#000", color: "#fff", fontSize: 12 }}>Video URL</div>
      )}
    </div>
  );
}

/* Read-only renderer used by BannerCarousel */
export function BannerCanvasView({ layout, resolve }: { layout: BannerLayout; resolve?: (s: string) => string }) {
  const bg = layout.bg;
  const bgStyle: CSSProperties = {
    background: gradientCss(bg) || bg.color || "#0f172a",
  };
  const els = [...layout.elements].sort((a, b) => a.z - b.z);
  return (
    <div className="absolute inset-0" style={bgStyle}>
      <style>{EFFECT_CSS}</style>
      {bg.videoUrl && (
        <video className="absolute inset-0 h-full w-full object-cover" autoPlay muted loop playsInline src={resolve ? resolve(bg.videoUrl) : bg.videoUrl} />
      )}
      {bg.imageUrl && (
        <img src={resolve ? resolve(bg.imageUrl) : bg.imageUrl} alt="" className="absolute inset-0 h-full w-full" style={{ objectFit: bg.bgImageFit || "cover", opacity: bg.bgImageOpacity ?? 0.3 }} />
      )}
      {bg.overlayColor && (
        <div className="absolute inset-0" style={{ background: bg.overlayColor, opacity: bg.overlayOpacity ?? 0.3 }} />
      )}
      <BannerEffectLayer effect={layout.effect} />
      {els.filter((e) => e.visible !== false).map((el) => renderCanvasElement(el, { interactive: false, resolve, animate: true }))}
    </div>
  );
}

/* ── Interactive editor ──────────────────────────────────────────────────── */

const HANDLES = ["nw", "n", "ne", "e", "se", "s", "sw", "w"] as const;
type Handle = (typeof HANDLES)[number];

const handlePos = (h: Handle): CSSProperties => {
  const map: Record<Handle, CSSProperties> = {
    nw: { left: -6, top: -6 },
    n: { left: "calc(50% - 6px)", top: -6 },
    ne: { right: -6, top: -6 },
    e: { right: -6, top: "calc(50% - 6px)" },
    se: { right: -6, bottom: -6 },
    s: { left: "calc(50% - 6px)", bottom: -6 },
    sw: { left: -6, bottom: -6 },
    w: { left: -6, top: "calc(50% - 6px)" },
  };
  return map[h];
};

const SNAP = 1.4; // % threshold for smart guides

interface DragState {
  mode: "move" | "resize";
  handle?: Handle;
  startX: number;
  startY: number;
  origPos: Record<string, { x: number; y: number; w: number; h: number }>;
  selIds: string[];
}

/* Templates -------------------------------------------------------------- */
const buildTemplate = (key: string, nextZ: () => number): BannerLayout => {
  const el = (type: CanvasElementType, patch: Partial<CanvasElement>): CanvasElement => ({ ...makeElement(type, nextZ()), ...patch });
  switch (key) {
    case "flash":
      return {
        ...DEFAULT_LAYOUT,
        ratio: 0.3,
        effect: "poppers",
        bg: { ...DEFAULT_LAYOUT.bg, color: "#7f1d1d", gradientFrom: "#ef4444", gradientTo: "#7f1d1d" },
        elements: [
          el("text", { name: "Headline", x: 6, y: 26, w: 60, h: 26, content: "FLASH SALE", textColor: "#fff", fontSize: 34, fontWeight: 900, letterSpacing: 1 }),
          el("text", { name: "Sub", x: 6, y: 54, w: 50, h: 16, content: "Up to 70% OFF", textColor: "#fde68a", fontSize: 16, fontWeight: 600 }),
          el("button", { name: "CTA", x: 62, y: 40, w: 30, h: 18, content: "Grab Now", fill: "#fde68a", textColor: "#7f1d1d", ctaUrl: "/products" }),
          el("star", { name: "Deco", x: 80, y: 10, w: 14, h: 14, fill: "#fde68a", rotation: 15 }),
        ],
      };
    case "eid":
      return {
        ...DEFAULT_LAYOUT,
        ratio: 0.34,
        effect: "eid",
        bg: { ...DEFAULT_LAYOUT.bg, color: "#064e3b", gradientFrom: "#065f46", gradientVia: "#0d9488", gradientTo: "#064e3b" },
        elements: [
          el("icon", { name: "Moon", x: 8, y: 30, w: 16, h: 16, icon: "Moon", fill: "#fde68a" }),
          el("text", { name: "Headline", x: 26, y: 30, w: 64, h: 22, content: "Eid Mubarak", textColor: "#fff", fontSize: 30, fontWeight: 800 }),
          el("text", { name: "Sub", x: 26, y: 56, w: 60, h: 14, content: "Festive offers inside", textColor: "#bbf7d0", fontSize: 14 }),
          el("button", { name: "CTA", x: 36, y: 72, w: 28, h: 16, content: "Shop Eid", fill: "#fde68a", textColor: "#064e3b", ctaUrl: "/products" }),
        ],
      };
    case "newyear":
      return {
        ...DEFAULT_LAYOUT,
        ratio: 0.34,
        effect: "newyear",
        bg: { ...DEFAULT_LAYOUT.bg, color: "#1e1b4b", gradientFrom: "#4f46e5", gradientVia: "#9333ea", gradientTo: "#0f172a" },
        elements: [
          el("text", { name: "Headline", x: 8, y: 24, w: 84, h: 24, content: "Happy New Year", textColor: "#fff", fontSize: 32, fontWeight: 900, textAlign: "center" }),
          el("star", { name: "Star1", x: 12, y: 12, w: 12, h: 12, fill: "#fde68a" }),
          el("star", { name: "Star2", x: 76, y: 14, w: 16, h: 16, fill: "#fbbf24", points: 6 }),
          el("button", { name: "CTA", x: 34, y: 64, w: 32, h: 18, content: "Celebrate", fill: "#fde68a", textColor: "#1e1b4b", ctaUrl: "/products" }),
        ],
      };
    case "diwali":
      return {
        ...DEFAULT_LAYOUT,
        ratio: 0.34,
        effect: "diwali",
        bg: { ...DEFAULT_LAYOUT.bg, color: "#451a03", gradientFrom: "#ea580c", gradientVia: "#f59e0b", gradientTo: "#7c2d12" },
        elements: [
          el("icon", { name: "Lamp", x: 8, y: 34, w: 16, h: 16, icon: "Flame", fill: "#fff7ed" }),
          el("text", { name: "Headline", x: 26, y: 28, w: 66, h: 22, content: "Happy Diwali", textColor: "#fffbeb", fontSize: 30, fontWeight: 800 }),
          el("text", { name: "Sub", x: 26, y: 56, w: 60, h: 14, content: "Festival of lights", textColor: "#fed7aa", fontSize: 14 }),
          el("button", { name: "CTA", x: 36, y: 74, w: 28, h: 15, content: "Shop Now", fill: "#fffbeb", textColor: "#7c2d12", ctaUrl: "/products" }),
        ],
      };
    case "ramadan":
      return {
        ...DEFAULT_LAYOUT,
        ratio: 0.34,
        effect: "ramadan",
        bg: { ...DEFAULT_LAYOUT.bg, color: "#1e1b4b", gradientFrom: "#312e81", gradientVia: "#4c1d95", gradientTo: "#0f172a" },
        elements: [
          el("text", { name: "Headline", x: 10, y: 30, w: 60, h: 22, content: "Ramadan Kareem", textColor: "#fff7d6", fontSize: 28, fontWeight: 800 }),
          el("text", { name: "Sub", x: 10, y: 56, w: 56, h: 14, content: "Blessed savings await", textColor: "#ddd6fe", fontSize: 14 }),
          el("button", { name: "CTA", x: 10, y: 72, w: 28, h: 15, content: "Explore", fill: "#fde68a", textColor: "#1e1b4b", ctaUrl: "/products" }),
        ],
      };
    case "christmas":
      return {
        ...DEFAULT_LAYOUT,
        ratio: 0.34,
        effect: "christmas",
        bg: { ...DEFAULT_LAYOUT.bg, color: "#0c4a6e", gradientFrom: "#0369a1", gradientVia: "#0e7490", gradientTo: "#082f49" },
        elements: [
          el("text", { name: "Headline", x: 8, y: 28, w: 64, h: 22, content: "Merry Christmas", textColor: "#fff", fontSize: 28, fontWeight: 800 }),
          el("text", { name: "Sub", x: 8, y: 56, w: 60, h: 14, content: "Joyful season offers", textColor: "#bae6fd", fontSize: 14 }),
          el("icon", { name: "Gift", x: 80, y: 18, w: 16, h: 16, icon: "Gift", fill: "#fca5a5" }),
          el("button", { name: "CTA", x: 8, y: 72, w: 28, h: 15, content: "Shop Gifts", fill: "#ef4444", textColor: "#fff", ctaUrl: "/products" }),
        ],
      };
    default: // promo
      return {
        ...DEFAULT_LAYOUT,
        ratio: 0.3,
        effect: "balloons",
        bg: { ...DEFAULT_LAYOUT.bg, color: "#0f172a", gradientFrom: "#0ea5e9", gradientTo: "#8b5cf6" },
        elements: [
          el("text", { name: "Headline", x: 8, y: 30, w: 56, h: 22, content: "Big Promotion", textColor: "#fff", fontSize: 28, fontWeight: 800 }),
          el("button", { name: "CTA", x: 64, y: 38, w: 28, h: 18, content: "Explore", fill: "#ffd400", textColor: "#111", ctaUrl: "/products" }),
          el("rect", { name: "Accent", x: 8, y: 60, w: 24, h: 4, fill: "#ffd400", borderRadius: 2 }),
        ],
      };
  }
};
const TEMPLATE_KEYS = [
  { key: "promo", label: "Promo" },
  { key: "flash", label: "Flash Sale" },
  { key: "eid", label: "Eid" },
  { key: "ramadan", label: "Ramadan" },
  { key: "diwali", label: "Diwali" },
  { key: "christmas", label: "Christmas" },
  { key: "newyear", label: "New Year" },
];

export default function BannerCanvasEditor({
  value,
  onChange,
}: {
  value: BannerLayout | null;
  onChange: (layout: BannerLayout) => void;
}) {
  const layout = value ?? DEFAULT_LAYOUT;
  const layoutRef = useRef(layout);
  layoutRef.current = layout;

  const canvasRef = useRef<HTMLDivElement>(null);
  const wrapRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragRef = useRef<DragState | null>(null);
  const editSnapRef = useRef<BannerLayout | null>(null);

  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const selectedIdsRef = useRef<string[]>([]);
  selectedIdsRef.current = selectedIds;
  const [showGrid, setShowGrid] = useState(false);
  const [snap, setSnap] = useState(true);
  const [gridSize, setGridSize] = useState(5);
  const [zoom, setZoom] = useState(1);
  const [canvasW, setCanvasW] = useState(600);
  const [guides, setGuides] = useState<{ x?: number; y?: number }>({});
  const [preview, setPreview] = useState(false);
  const clipRef = useRef<CanvasElement[] | null>(null);

  const [past, setPast] = useState<BannerLayout[]>([]);
  const [future, setFuture] = useState<BannerLayout[]>([]);

  const commit = useCallback(
    (next: BannerLayout, record = false) => {
      if (record) setPast((p) => [...p.slice(-59), structuredClone(layoutRef.current)]);
      if (record) setFuture([]);
      onChange(next);
    },
    [onChange]
  );
  const update = useCallback((patch: Partial<BannerLayout>) => commit({ ...layoutRef.current, ...patch }), [commit]);
  const updateBg = useCallback((patch: Partial<BannerLayout["bg"]>) => update({ bg: { ...layoutRef.current.bg, ...patch } }), [update]);
  const updateElements = useCallback((els: CanvasElement[]) => update({ elements: els }), [update]);

  /* live (no-history) update during interactions/typing */
  const live = useCallback((next: BannerLayout) => onChange(next), [onChange]);
  const liveUpdate = useCallback((patch: Partial<BannerLayout>) => live({ ...layoutRef.current, ...patch }), [live]);
  const liveUpdateElements = useCallback((els: CanvasElement[]) => live({ ...layoutRef.current, elements: els }), [live]);

  const selectedEls = useMemo(() => layout.elements.filter((e) => selectedIds.includes(e.id)), [layout.elements, selectedIds]);
  const single = selectedEls.length === 1 ? selectedEls[0] : null;
  const nextZ = layout.elements.reduce((m, e) => Math.max(m, e.z), 0) + 1;

  /* editing-session history (one entry per focus session) */
  const beginEdit = () => { if (!editSnapRef.current) editSnapRef.current = structuredClone(layoutRef.current); };
  const endEdit = () => {
    if (editSnapRef.current) {
      setPast((p) => [...p.slice(-59), editSnapRef.current!]);
      setFuture([]);
      editSnapRef.current = null;
    }
  };
  const liveUpdateElement = useCallback(
    (id: string, patch: Partial<CanvasElement>) => liveUpdateElements(layoutRef.current.elements.map((e) => (e.id === id ? { ...e, ...patch } : e))),
    [liveUpdateElements]
  );

  /* selection helpers */
  const setSingle = (id: string) => setSelectedIds([id]);
  const toggle = (id: string) =>
    setSelectedIds((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));

  const addElement = (type: CanvasElementType) => {
    const el = makeElement(type, nextZ);
    commit({ ...layout, elements: [...layout.elements, el] }, true);
    setSelectedIds([el.id]);
  };

  const removeSelected = () => {
    if (!selectedIds.length) return;
    commit({ ...layout, elements: layout.elements.filter((e) => !selectedIds.includes(e.id)) }, true);
    setSelectedIds([]);
  };

  const duplicateSelected = () => {
    if (!selectedIds.length) return;
    let z = nextZ;
    const copies = layout.elements
      .filter((e) => selectedIds.includes(e.id))
      .map((e) => {
        const c = cloneEl(e, z++);
        c.x = Math.min(100 - c.w, c.x + 3);
        c.y = Math.min(100 - c.h, c.y + 3);
        return c;
      });
    const next = { ...layout, elements: [...layout.elements, ...copies] };
    commit(next, true);
    setSelectedIds(copies.map((c) => c.id));
  };

  /* z-order: front / back / forward / backward */
  const reorderZ = (mode: "front" | "back" | "forward" | "backward") => {
    if (!selectedIds.length) return;
    const sel = new Set(selectedIds);
    const sorted = [...layout.elements].sort((a, b) => a.z - b.z);
    let result: CanvasElement[];
    if (mode === "front") {
      const others = sorted.filter((e) => !sel.has(e.id));
      const picked = sorted.filter((e) => sel.has(e.id));
      result = [...others, ...picked];
    } else if (mode === "back") {
      const picked = sorted.filter((e) => sel.has(e.id));
      const others = sorted.filter((e) => !sel.has(e.id));
      result = [...picked, ...others];
    } else if (mode === "forward") {
      result = [...sorted];
      for (let i = result.length - 2; i >= 0; i--) {
        if (sel.has(result[i].id) && !sel.has(result[i + 1].id)) {
          [result[i], result[i + 1]] = [result[i + 1], result[i]];
        }
      }
    } else {
      result = [...sorted];
      for (let i = 1; i < result.length; i++) {
        if (sel.has(result[i].id) && !sel.has(result[i - 1].id)) {
          [result[i], result[i - 1]] = [result[i - 1], result[i]];
        }
      }
    }
    commit({ ...layout, elements: result.map((e, i) => ({ ...e, z: i + 1 })) }, true);
  };

  /* grouping */
  const groupSelected = () => {
    if (selectedIds.length < 2) return;
    const gid = `g-${uid()}`;
    commit({ ...layout, elements: layout.elements.map((e) => (selectedIds.includes(e.id) ? { ...e, groupId: gid } : e)) }, true);
  };
  const ungroupSelected = () => {
    if (!selectedIds.length) return;
    commit({ ...layout, elements: layout.elements.map((e) => (selectedIds.includes(e.id) ? { ...e, groupId: undefined } : e)) }, true);
  };

  /* flip / mirror */
  const flip = (axis: "x" | "y") => {
    if (!single) return;
    liveUpdateElement(single.id, axis === "x" ? { flipX: !single.flipX } : { flipY: !single.flipY });
  };

  /* copy / paste */
  const copySelected = () => {
    const sel = layout.elements.filter((e) => selectedIds.includes(e.id));
    if (!sel.length) return;
    clipRef.current = sel;
  };
  const pasteSelected = () => {
    if (!clipRef.current || !clipRef.current.length) return;
    let z = nextZ;
    const copies = clipRef.current.map((c) => {
      const cc = cloneEl(c, z++);
      cc.x = Math.min(100 - cc.w, cc.x + 3);
      cc.y = Math.min(100 - cc.h, cc.y + 3);
      return cc;
    });
    const next = { ...layout, elements: [...layout.elements, ...copies] };
    commit(next, true);
    setSelectedIds(copies.map((c) => c.id));
  };

  /* JSON export / import */
  const copyJSON = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(layout, null, 2));
    } catch {
      /* clipboard may be unavailable */
    }
  };
  const downloadJSON = () => {
    const blob = new Blob([JSON.stringify(layout, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "banner-layout.json";
    a.click();
    URL.revokeObjectURL(url);
  };
  const importJSON = (file: File) => {
    const r = new FileReader();
    r.onload = () => {
      try {
        const obj = JSON.parse(String(r.result));
        if (obj && Array.isArray(obj.elements)) {
          commit(mergeLayout(obj), true);
          setSelectedIds([]);
        }
      } catch {
        /* ignore malformed file */
      }
    };
    r.readAsText(file);
  };

  const toggleVisible = (id: string) =>
    commit({ ...layout, elements: layout.elements.map((e) => (e.id === id ? { ...e, visible: !(e.visible !== false) } : e)) }, true);
  const toggleLock = (id: string) =>
    commit({ ...layout, elements: layout.elements.map((e) => (e.id === id ? { ...e, locked: !e.locked } : e)) }, true);

  /* alignment */
  const align = (axis: "left" | "centerX" | "right" | "top" | "middleY" | "bottom") => {
    const sel = layout.elements.filter((e) => selectedIds.includes(e.id));
    if (!sel.length) return;
    const minX = Math.min(...sel.map((e) => e.x));
    const maxX = Math.max(...sel.map((e) => e.x + e.w));
    const minY = Math.min(...sel.map((e) => e.y));
    const maxY = Math.max(...sel.map((e) => e.y + e.h));
    const cX = (minX + maxX) / 2;
    const cY = (minY + maxY) / 2;
    const toCanvas = sel.length === 1;
    const bx0 = toCanvas ? 0 : minX;
    const bx1 = toCanvas ? 100 : maxX;
    const by0 = toCanvas ? 0 : minY;
    const by1 = toCanvas ? 100 : maxY;
    const bcX = toCanvas ? 50 : cX;
    const bcY = toCanvas ? 50 : cY;
    const updated = layout.elements.map((e) => {
      if (!selectedIds.includes(e.id)) return e;
      let x = e.x;
      let y = e.y;
      if (axis === "left") x = bx0;
      else if (axis === "centerX") x = bcX - e.w / 2;
      else if (axis === "right") x = bx1 - e.w;
      else if (axis === "top") y = by0;
      else if (axis === "middleY") y = bcY - e.h / 2;
      else if (axis === "bottom") y = by1 - e.h;
      return { ...e, x, y };
    });
    commit({ ...layout, elements: updated }, true);
  };

  const distribute = (axis: "x" | "y") => {
    const sel = layout.elements.filter((e) => selectedIds.includes(e.id));
    if (sel.length < 3) return;
    const sorted = [...sel].sort((a, b) =>
      axis === "x" ? a.x + a.w / 2 - (b.x + b.w / 2) : a.y + a.h / 2 - (b.y + b.h / 2)
    );
    const first = sorted[0];
    const last = sorted[sorted.length - 1];
    const startC = axis === "x" ? first.x + first.w / 2 : first.y + first.h / 2;
    const endC = axis === "x" ? last.x + last.w / 2 : last.y + last.h / 2;
    const step = (endC - startC) / (sorted.length - 1);
    const idMap = new Map(sorted.map((e, i) => [e.id, i]));
    const updated = layout.elements.map((e) => {
      if (!idMap.has(e.id)) return e;
      const i = idMap.get(e.id)!;
      const center = startC + step * i;
      return axis === "x" ? { ...e, x: center - e.w / 2 } : { ...e, y: center - e.h / 2 };
    });
    commit({ ...layout, elements: updated }, true);
  };

  /* undo / redo */
  const undo = () => {
    if (!past.length) return;
    const prev = past[past.length - 1];
    setPast(past.slice(0, -1));
    setFuture([structuredClone(layoutRef.current), ...future]);
    onChange(prev);
  };
  const redo = () => {
    if (!future.length) return;
    const nxt = future[0];
    setFuture(future.slice(1));
    setPast([...past, structuredClone(layoutRef.current)]);
    onChange(nxt);
  };

  /* templates */
  const applyTemplate = (key: string) => {
    let z = 1;
    const t = buildTemplate(key, () => z++);
    commit(t, true);
    setSelectedIds([]);
  };

  /* pointer interactions */
  const snapValue = (v: number) => Math.round(v / gridSize) * gridSize;

  const smartSnap = (x: number, y: number, w: number, h: number) => {
    const targetsX = [0, 50, 100];
    const targetsY = [0, 50, 100];
    layout.elements.forEach((e) => {
      if (selectedIdsRef.current.includes(e.id)) return;
      targetsX.push(e.x, e.x + e.w / 2, e.x + e.w);
      targetsY.push(e.y, e.y + e.h / 2, e.y + e.h);
    });
    let gx: number | undefined;
    let gy: number | undefined;
    const tryX = (val: number) => {
      for (const t of targetsX) {
        if (Math.abs(val - t) < SNAP) {
          x += t - val;
          gx = t;
          return true;
        }
      }
      return false;
    };
    const tryY = (val: number) => {
      for (const t of targetsY) {
        if (Math.abs(val - t) < SNAP) {
          y += t - val;
          gy = t;
          return true;
        }
      }
      return false;
    };
    if (!tryX(x)) tryX(x + w / 2);
    if (!tryX(x + w)) tryX(x);
    if (!tryY(y)) tryY(y + h / 2);
    if (!tryY(y + h)) tryY(y);
    return { x, y, gx, gy };
  };

  const onPointerDownElement = (e: ReactPointerEvent, el: CanvasElement) => {
    if (el.locked) return;
    e.stopPropagation();
    (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
    const cur = selectedIdsRef.current;
    let nextSel: string[];
    if (e.ctrlKey || e.metaKey || e.shiftKey) {
      nextSel = cur.includes(el.id) ? cur.filter((x) => x !== el.id) : [...cur, el.id];
    } else if (!cur.includes(el.id)) {
      nextSel = el.groupId ? layout.elements.filter((x) => x.groupId === el.groupId).map((x) => x.id) : [el.id];
    } else {
      nextSel = cur;
    }
    setSelectedIds(nextSel);
    const origPos: Record<string, { x: number; y: number; w: number; h: number }> = {};
    layout.elements.forEach((x) => {
      if (nextSel.includes(x.id)) origPos[x.id] = { x: x.x, y: x.y, w: x.w, h: x.h };
    });
    dragRef.current = { mode: "move", startX: e.clientX, startY: e.clientY, origPos, selIds: [...nextSel] };
  };

  const onPointerDownHandle = (e: ReactPointerEvent, el: CanvasElement, handle: Handle) => {
    if (el.locked) return;
    e.stopPropagation();
    (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
    setSingle(el.id);
    const origPos: Record<string, { x: number; y: number; w: number; h: number }> = {
      [el.id]: { x: el.x, y: el.y, w: el.w, h: el.h },
    };
    dragRef.current = { mode: "resize", handle, startX: e.clientX, startY: e.clientY, origPos, selIds: [el.id] };
  };

  const onCanvasMove = (e: ReactPointerEvent) => {
    const drag = dragRef.current;
    const box = canvasRef.current?.getBoundingClientRect();
    if (!drag || !box) return;
    const dxPct = ((e.clientX - drag.startX) / box.width) * 100;
    const dyPct = ((e.clientY - drag.startY) / box.height) * 100;

    if (drag.mode === "move") {
      let els = layout.elements.map((el) => {
        const o = drag.origPos[el.id];
        if (!o) return el;
        let x = o.x + dxPct;
        let y = o.y + dyPct;
        if (snap && drag.selIds.length === 1) {
          const r = smartSnap(x, y, o.w, o.h);
          x = r.x;
          y = r.y;
          setGuides({ x: r.gx, y: r.gy });
        } else if (snap) {
          x = snapValue(x);
          y = snapValue(y);
        }
        x = Math.min(100, Math.max(-o.w, x));
        y = Math.min(100, Math.max(-o.h, y));
        return { ...el, x, y };
      });
      liveUpdateElements(els);
      return;
    }

    // resize (single)
    const h = drag.handle!;
    const id = drag.selIds[0];
    const o = drag.origPos[id];
    if (!o) return;
    let { x, y, w, h: hh } = o;
    if (h.includes("e")) w = o.w + dxPct;
    if (h.includes("s")) hh = o.h + dyPct;
    if (h.includes("w")) {
      w = o.w - dxPct;
      x = o.x + dxPct;
    }
    if (h.includes("n")) {
      hh = o.h - dyPct;
      y = o.y + dyPct;
    }
    if (snap) {
      w = snapValue(w);
      hh = snapValue(hh);
      if (h.includes("w")) x = o.x + (o.w - w);
      if (h.includes("n")) y = o.y + (o.h - hh);
    }
    if (w < 3) {
      if (h.includes("w")) x = o.x + o.w - 3;
      w = 3;
    }
    if (hh < 3) {
      if (h.includes("n")) y = o.y + o.h - 3;
      hh = 3;
    }
    liveUpdateElements(layout.elements.map((el) => (el.id === id ? { ...el, x, y, w, h: hh } : el)));
  };

  const onCanvasUp = () => {
    if (dragRef.current) {
      const moved = dragRef.current;
      const changed = layout.elements.some((e) => {
        const o = moved.origPos[e.id];
        return o && (o.x !== e.x || o.y !== e.y || o.w !== e.w || o.h !== e.h);
      });
      if (changed) commit(structuredClone(layoutRef.current), true);
      dragRef.current = null;
      setGuides({});
    }
  };

  /* keyboard shortcuts */
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement;
      if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.tagName === "SELECT" || t.isContentEditable)) return;
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
        e.preventDefault();
        if (e.shiftKey) redo();
        else undo();
        return;
      }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "y") {
        e.preventDefault();
        redo();
        return;
      }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "d") {
        e.preventDefault();
        duplicateSelected();
        return;
      }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "c") {
        e.preventDefault();
        copySelected();
        return;
      }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "v") {
        e.preventDefault();
        pasteSelected();
        return;
      }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "g") {
        e.preventDefault();
        if (e.shiftKey) ungroupSelected();
        else groupSelected();
        return;
      }
      if (e.key === "Delete" || e.key === "Backspace") {
        e.preventDefault();
        removeSelected();
        return;
      }
      if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(e.key) && selectedIds.length) {
        e.preventDefault();
        const step = e.shiftKey ? 2 : 0.5;
        const dx = e.key === "ArrowLeft" ? -step : e.key === "ArrowRight" ? step : 0;
        const dy = e.key === "ArrowUp" ? -step : e.key === "ArrowDown" ? step : 0;
        const sel = new Set(selectedIds);
        commit(
          { ...layout, elements: layout.elements.map((el) => (sel.has(el.id) ? { ...el, x: el.x + dx, y: el.y + dy } : el)) },
          true
        );
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedIds, layout, past.length, future.length]);

  /* measure canvas width for zoom/aspect */
  useLayoutEffect(() => {
    const measure = () => {
      if (wrapRef.current) setCanvasW(wrapRef.current.clientWidth);
    };
    measure();
    const ro = new ResizeObserver(measure);
    if (wrapRef.current) ro.observe(wrapRef.current);
    return () => ro.disconnect();
  }, []);

  const ratio = layout.ratio ?? 0.3;
  const canvasHeight = Math.max(160, Math.round(canvasW * ratio * zoom));

  const bgStyle: CSSProperties = {
    background: gradientCss(layout.bg) || layout.bg.color || "#0f172a",
    height: canvasHeight,
    backgroundSize: "cover",
  };

  const sortedEls = [...layout.elements].sort((a, b) => a.z - b.z);

  /* multi-select bounding box for outline */
  const bbox = useMemo(() => {
    if (selectedEls.length < 2) return null;
    const minX = Math.min(...selectedEls.map((e) => e.x));
    const maxX = Math.max(...selectedEls.map((e) => e.x + e.w));
    const minY = Math.min(...selectedEls.map((e) => e.y));
    const maxY = Math.max(...selectedEls.map((e) => e.y + e.h));
    return { x: minX, y: minY, w: maxX - minX, h: maxY - minY };
  }, [selectedEls]);

  return (
    <div className="space-y-3">
      <style>{EFFECT_CSS}</style>
      {/* Add toolbar */}
      <div className="flex flex-wrap items-center gap-1.5">
        <button type="button" onClick={() => addElement("rect")} className="theme-btn-secondary rounded-lg px-2 py-1.5 text-[11px] font-semibold flex items-center gap-1"><Square className="w-3.5 h-3.5" /> Shape</button>
        <button type="button" onClick={() => addElement("ellipse")} className="theme-btn-secondary rounded-lg px-2 py-1.5 text-[11px] font-semibold flex items-center gap-1"><Circle className="w-3.5 h-3.5" /> Circle</button>
        <button type="button" onClick={() => addElement("triangle")} className="theme-btn-secondary rounded-lg px-2 py-1.5 text-[11px] font-semibold flex items-center gap-1"><Triangle className="w-3.5 h-3.5" /> Tri</button>
        <button type="button" onClick={() => addElement("line")} className="theme-btn-secondary rounded-lg px-2 py-1.5 text-[11px] font-semibold flex items-center gap-1"><Minus className="w-3.5 h-3.5" /> Line</button>
        <button type="button" onClick={() => addElement("star")} className="theme-btn-secondary rounded-lg px-2 py-1.5 text-[11px] font-semibold flex items-center gap-1"><Star className="w-3.5 h-3.5" /> Star</button>
        <button type="button" onClick={() => addElement("polygon")} className="theme-btn-secondary rounded-lg px-2 py-1.5 text-[11px] font-semibold flex items-center gap-1"><Hexagon className="w-3.5 h-3.5" /> Poly</button>
        <button type="button" onClick={() => addElement("text")} className="theme-btn-secondary rounded-lg px-2 py-1.5 text-[11px] font-semibold flex items-center gap-1"><Type className="w-3.5 h-3.5" /> Text</button>
        <button type="button" onClick={() => addElement("emoji")} className="theme-btn-secondary rounded-lg px-2 py-1.5 text-[11px] font-semibold flex items-center gap-1"><Smile className="w-3.5 h-3.5" /> Emoji</button>
        <button type="button" onClick={() => addElement("image")} className="theme-btn-secondary rounded-lg px-2 py-1.5 text-[11px] font-semibold flex items-center gap-1"><ImageIcon className="w-3.5 h-3.5" /> Image</button>
        <button type="button" onClick={() => addElement("button")} className="theme-btn-secondary rounded-lg px-2 py-1.5 text-[11px] font-semibold flex items-center gap-1"><MousePointerClick className="w-3.5 h-3.5" /> Button</button>
        <button type="button" onClick={() => addElement("video")} className="theme-btn-secondary rounded-lg px-2 py-1.5 text-[11px] font-semibold flex items-center gap-1"><Film className="w-3.5 h-3.5" /> Video</button>
        <button type="button" onClick={() => addElement("icon")} className="theme-btn-secondary rounded-lg px-2 py-1.5 text-[11px] font-semibold flex items-center gap-1"><Sparkles className="w-3.5 h-3.5" /> Icon</button>
      </div>

      {/* Action toolbar */}
      <div className="flex flex-wrap items-center gap-1.5">
        <button type="button" onClick={undo} disabled={!past.length} title="Undo (Ctrl+Z)" className="theme-btn-secondary rounded-lg px-2 py-1.5 text-[11px] font-semibold disabled:opacity-40 flex items-center gap-1"><Undo2 className="w-3.5 h-3.5" /> Undo</button>
        <button type="button" onClick={redo} disabled={!future.length} title="Redo (Ctrl+Shift+Z)" className="theme-btn-secondary rounded-lg px-2 py-1.5 text-[11px] font-semibold disabled:opacity-40 flex items-center gap-1"><Redo2 className="w-3.5 h-3.5" /> Redo</button>
        <button type="button" onClick={duplicateSelected} disabled={!selectedIds.length} title="Duplicate (Ctrl+D)" className="theme-btn-secondary rounded-lg px-2 py-1.5 text-[11px] font-semibold disabled:opacity-40 flex items-center gap-1"><Copy className="w-3.5 h-3.5" /> Copy</button>
        <button type="button" onClick={removeSelected} disabled={!selectedIds.length} title="Delete (Del)" className="theme-action-danger rounded-lg px-2 py-1.5 text-[11px] font-semibold disabled:opacity-40 flex items-center gap-1"><Trash2 className="w-3.5 h-3.5" /> Delete</button>
        <div className="w-px h-5 bg-border mx-1" />
        <button type="button" onClick={() => align("left")} disabled={!selectedIds.length} title="Align left" className="theme-btn-secondary rounded-lg p-1.5 disabled:opacity-40"><AlignLeft className="w-3.5 h-3.5" /></button>
        <button type="button" onClick={() => align("centerX")} disabled={!selectedIds.length} title="Align center" className="theme-btn-secondary rounded-lg p-1.5 disabled:opacity-40"><AlignCenter className="w-3.5 h-3.5" /></button>
        <button type="button" onClick={() => align("right")} disabled={!selectedIds.length} title="Align right" className="theme-btn-secondary rounded-lg p-1.5 disabled:opacity-40"><AlignRight className="w-3.5 h-3.5" /></button>
        <button type="button" onClick={() => align("top")} disabled={!selectedIds.length} title="Align top" className="theme-btn-secondary rounded-lg p-1.5 disabled:opacity-40"><AlignVerticalJustifyStart className="w-3.5 h-3.5" /></button>
        <button type="button" onClick={() => align("middleY")} disabled={!selectedIds.length} title="Align middle" className="theme-btn-secondary rounded-lg p-1.5 disabled:opacity-40"><AlignVerticalJustifyCenter className="w-3.5 h-3.5" /></button>
        <button type="button" onClick={() => align("bottom")} disabled={!selectedIds.length} title="Align bottom" className="theme-btn-secondary rounded-lg p-1.5 disabled:opacity-40"><AlignVerticalJustifyEnd className="w-3.5 h-3.5" /></button>
        <button type="button" onClick={() => distribute("x")} disabled={selectedIds.length < 3} title="Distribute horizontally" className="theme-btn-secondary rounded-lg p-1.5 disabled:opacity-40"><AlignLeft className="w-3.5 h-3.5 opacity-40" /></button>
        <button type="button" onClick={() => distribute("y")} disabled={selectedIds.length < 3} title="Distribute vertically" className="theme-btn-secondary rounded-lg p-1.5 disabled:opacity-40"><AlignVerticalJustifyStart className="w-3.5 h-3.5 opacity-40" /></button>
        <div className="w-px h-5 bg-border mx-1" />
        <button type="button" onClick={() => setShowGrid((v) => !v)} className={`rounded-lg p-1.5 ${showGrid ? "theme-status-warning" : "theme-btn-secondary"}`} title="Toggle grid"><Grid3x3 className="w-3.5 h-3.5" /></button>
        <button type="button" onClick={() => setSnap((v) => !v)} className={`rounded-lg p-1.5 ${snap ? "theme-status-warning" : "theme-btn-secondary"}`} title="Toggle snap"><Magnet className="w-3.5 h-3.5" /></button>
        <div className="flex items-center gap-1 text-[11px] text-text-muted">
          <span>Grid</span>
          <input type="range" min={2} max={20} value={gridSize} onChange={(e) => setGridSize(Number(e.target.value))} className="w-16 theme-range" />
          <span>{gridSize}%</span>
        </div>
        <div className="flex-1" />
        <div className="flex items-center gap-1 text-[11px] text-text-muted">
          <button type="button" onClick={() => setZoom((z) => Math.max(0.5, +(z - 0.1).toFixed(2)))} className="theme-btn-secondary rounded p-1"><ZoomOut className="w-3 h-3" /></button>
          <span className="w-9 text-center">{Math.round(zoom * 100)}%</span>
          <button type="button" onClick={() => setZoom((z) => Math.min(1.8, +(z + 0.1).toFixed(2)))} className="theme-btn-secondary rounded p-1"><ZoomIn className="w-3 h-3" /></button>
        </div>
      </div>

      {/* Arrange toolbar */}
      <div className="flex flex-wrap items-center gap-1.5">
        <button type="button" onClick={() => reorderZ("front")} disabled={!selectedIds.length} title="Bring to front" className="theme-btn-secondary rounded-lg p-1.5 disabled:opacity-40"><BringToFront className="w-3.5 h-3.5" /></button>
        <button type="button" onClick={() => reorderZ("forward")} disabled={!selectedIds.length} title="Bring forward" className="theme-btn-secondary rounded-lg p-1.5 disabled:opacity-40"><ArrowUp className="w-3.5 h-3.5" /></button>
        <button type="button" onClick={() => reorderZ("backward")} disabled={!selectedIds.length} title="Send backward" className="theme-btn-secondary rounded-lg p-1.5 disabled:opacity-40"><ArrowDown className="w-3.5 h-3.5" /></button>
        <button type="button" onClick={() => reorderZ("back")} disabled={!selectedIds.length} title="Send to back" className="theme-btn-secondary rounded-lg p-1.5 disabled:opacity-40"><SendToBack className="w-3.5 h-3.5" /></button>
        <div className="w-px h-5 bg-border mx-1" />
        <button type="button" onClick={groupSelected} disabled={selectedIds.length < 2} title="Group (Ctrl+G)" className="theme-btn-secondary rounded-lg p-1.5 disabled:opacity-40"><Group className="w-3.5 h-3.5" /></button>
        <button type="button" onClick={ungroupSelected} disabled={!selectedIds.length} title="Ungroup (Ctrl+Shift+G)" className="theme-btn-secondary rounded-lg p-1.5 disabled:opacity-40"><Ungroup className="w-3.5 h-3.5" /></button>
        <div className="w-px h-5 bg-border mx-1" />
        <button type="button" onClick={copySelected} disabled={!selectedIds.length} title="Copy (Ctrl+C)" className="theme-btn-secondary rounded-lg p-1.5 disabled:opacity-40"><Copy className="w-3.5 h-3.5" /></button>
        <button type="button" onClick={pasteSelected} title="Paste (Ctrl+V)" className="theme-btn-secondary rounded-lg p-1.5"><Copy className="w-3.5 h-3.5 opacity-40" /></button>
        <button type="button" onClick={() => setPreview((v) => !v)} className={`rounded-lg p-1.5 ${preview ? "theme-status-warning" : "theme-btn-secondary"}`} title="Toggle preview (hide handles + play animations)"><Eye className="w-3.5 h-3.5" /></button>
      </div>

      {/* Export toolbar */}
      <div className="flex flex-wrap items-center gap-1.5">
        <button type="button" onClick={copyJSON} title="Copy layout JSON" className="theme-btn-secondary rounded-lg px-2 py-1.5 text-[11px] font-semibold flex items-center gap-1"><FileJson className="w-3.5 h-3.5" /> Copy JSON</button>
        <button type="button" onClick={downloadJSON} title="Download layout JSON" className="theme-btn-secondary rounded-lg px-2 py-1.5 text-[11px] font-semibold flex items-center gap-1"><Download className="w-3.5 h-3.5" /> Download</button>
        <button type="button" onClick={() => fileInputRef.current?.click()} title="Import layout JSON" className="theme-btn-secondary rounded-lg px-2 py-1.5 text-[11px] font-semibold flex items-center gap-1"><Upload className="w-3.5 h-3.5" /> Import</button>
        <input ref={fileInputRef} type="file" accept="application/json,.json" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) importJSON(f); e.target.value = ""; }} />
        <div className="flex-1" />
        <span className="text-[10px] text-text-faint">Shortcuts: Ctrl+Z/Y undo/redo · Ctrl+D dup · Ctrl+C/V copy · Ctrl+G group · Del remove · ←↑↓→ nudge</span>
      </div>

      {/* Templates */}
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="text-[11px] text-text-muted flex items-center gap-1"><LayoutTemplate className="w-3.5 h-3.5" /> Templates:</span>
        {TEMPLATE_KEYS.map((t) => (
          <button key={t.key} type="button" onClick={() => applyTemplate(t.key)} className="theme-btn-secondary rounded-lg px-2 py-1 text-[11px] font-medium">{t.label}</button>
        ))}
      </div>

      {/* Layers + Canvas */}
      <div className="flex gap-3">
        {/* Layers panel */}
        <div className="w-36 shrink-0 rounded-xl border border-border p-2 space-y-1 max-h-[460px] overflow-y-auto">
          <div className="text-[10px] font-bold uppercase tracking-wide text-text-faint px-1">Layers</div>
          {layout.elements.length === 0 && <div className="text-[10px] text-text-faint px-1 py-2">No elements yet</div>}
          {[...layout.elements].sort((a, b) => b.z - a.z).map((el) => {
            const isSel = selectedIds.includes(el.id);
            return (
              <div
                key={el.id}
                onClick={(e) => { e.stopPropagation(); if (e.ctrlKey || e.metaKey || e.shiftKey) toggle(el.id); else setSingle(el.id); }}
                className={`group flex items-center gap-1 rounded-lg px-1.5 py-1 cursor-pointer text-[11px] ${isSel ? "bg-primary/15 text-primary" : "hover:bg-surface-2 text-text-muted"} ${el.visible === false ? "opacity-50" : ""}`}
              >
                <button type="button" onClick={(e) => { e.stopPropagation(); toggleVisible(el.id); }} className="shrink-0">{el.visible === false ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}</button>
                {el.groupId && <Layers className="w-3 h-3 text-primary shrink-0" />}
                <span className="truncate flex-1" title={el.name || el.type}>{el.name || el.type}</span>
                <button type="button" onClick={(e) => { e.stopPropagation(); toggleLock(el.id); }} className="shrink-0 opacity-0 group-hover:opacity-100">{el.locked ? <Lock className="w-3 h-3" /> : <Unlock className="w-3 h-3" />}</button>
              </div>
            );
          })}
        </div>

        {/* Canvas area */}
        <div className="flex-1 min-w-0">
          <div ref={wrapRef} className="w-full">
            <div
              ref={canvasRef}
              onPointerMove={onCanvasMove}
              onPointerUp={onCanvasUp}
              onPointerLeave={onCanvasUp}
              onClick={() => setSelectedIds([])}
              className={`relative w-full overflow-hidden rounded-xl select-none touch-none ${preview ? "border border-solid border-border" : "border border-dashed border-border"}`}
              style={bgStyle}
            >
              {showGrid && (
                <div
                  className="pointer-events-none absolute inset-0"
                  style={{
                    backgroundImage:
                      "linear-gradient(to right, rgba(255,255,255,0.12) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.12) 1px, transparent 1px)",
                    backgroundSize: `${gridSize}% ${gridSize}%`,
                  }}
                />
              )}
              {layout.bg.videoUrl && (
                <video className="pointer-events-none absolute inset-0 h-full w-full object-cover" autoPlay muted loop playsInline src={layout.bg.videoUrl} />
              )}
              {layout.bg.imageUrl && (
                <img src={layout.bg.imageUrl} alt="" className="pointer-events-none absolute inset-0 h-full w-full" style={{ objectFit: layout.bg.bgImageFit || "cover", opacity: layout.bg.bgImageOpacity ?? 0.3 }} />
              )}
              {layout.bg.overlayColor && (
                <div className="pointer-events-none absolute inset-0" style={{ background: layout.bg.overlayColor, opacity: layout.bg.overlayOpacity ?? 0.3 }} />
              )}
              {/* celebration / season effect layer (now actually rendered) */}
              <BannerEffectLayer effect={layout.effect} />

              {/* elements — rendered directly for correct stacking + z-index */}
              {sortedEls.map((el) =>
                el.visible === false ? null : (
                  <Fragment key={el.id}>
                    {renderCanvasElement(el, { interactive: !preview, onPointerDown: onPointerDownElement, animate: preview })}
                    {!preview && selectedIds.includes(el.id) && selectedEls.length === 1 && (
                      <div
                        className="pointer-events-none absolute"
                        style={{ left: `${el.x}%`, top: `${el.y}%`, width: `${el.w}%`, height: `${el.h}%`, zIndex: 1000 }}
                      >
                        {HANDLES.map((h) => (
                          <span
                            key={h}
                            onPointerDown={(e) => onPointerDownHandle(e, el, h)}
                            className="absolute z-[1001] h-3 w-3 rounded-full border border-primary bg-white shadow"
                            style={{ ...handlePos(h), pointerEvents: "auto", cursor: h.includes("n") && h.includes("w") ? "nwse-resize" : h.includes("n") && h.includes("e") ? "nesw-resize" : h === "n" || h === "s" ? "ns-resize" : h === "e" || h === "w" ? "ew-resize" : "nwse-resize" }}
                          />
                        ))}
                        <span className="pointer-events-none absolute -top-5 left-0 rounded bg-primary px-1.5 py-0.5 text-[9px] font-bold text-white">{el.name || el.type}</span>
                      </div>
                    )}
                  </Fragment>
                )
              )}

              {/* multi-select outline */}
              {!preview && bbox && (
                <div className="pointer-events-none absolute border-2 border-primary/70 rounded-sm" style={{ left: `${bbox.x}%`, top: `${bbox.y}%`, width: `${bbox.w}%`, height: `${bbox.h}%` }} />
              )}

              {/* snap guides */}
              {!preview && guides.x !== undefined && <div className="pointer-events-none absolute top-0 bottom-0 w-px bg-pink-400 z-[998]" style={{ left: `${guides.x}%` }} />}
              {!preview && guides.y !== undefined && <div className="pointer-events-none absolute left-0 right-0 h-px bg-pink-400 z-[998]" style={{ top: `${guides.y}%` }} />}

              {!preview && layout.elements.length === 0 && (
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center text-white/80 px-4 gap-2">
                  <Sparkles className="w-7 h-7 opacity-80" />
                  <p className="text-[12px] font-semibold">Your canvas is empty</p>
                  <p className="text-[11px] text-white/60">Add elements from the toolbar, pick a celebration effect above, or start from a template. The selected effect is shown live on this canvas.</p>
                </div>
              )}
            </div>
          </div>
          <div className="mt-1 flex items-center justify-between text-[10px] text-text-faint">
            <span>Drag to move · handles to resize · shift/ctrl-click to multi-select</span>
            <select
              value={ASPECT_OPTIONS.find((a) => a.ratio === ratio)?.value || "banner"}
              onChange={(e) => { const a = ASPECT_OPTIONS.find((x) => x.value === e.target.value); if (a) commit({ ...layout, ratio: a.ratio }, true); }}
              className="theme-input rounded border px-1 py-0.5 text-[10px]"
            >
              {ASPECT_OPTIONS.map((a) => (<option key={a.value} value={a.value}>{a.label}</option>))}
            </select>
          </div>
        </div>
      </div>

      {/* Background section */}
      <div className="rounded-xl border border-border p-3 space-y-3">
        <div className="text-xs font-bold text-text flex items-center gap-1.5"><Plus className="w-3.5 h-3.5 theme-status-warning" /> Background & Effect</div>
        <div className="grid grid-cols-2 gap-3">
          <ColorField label="Background color" value={layout.bg.color} onChange={(v) => updateBg({ color: v, gradientFrom: "" })} />
          <div>
            <label className="block text-[11px] text-text-muted mb-1">Background Effect (celebration / season)</label>
            <select value={layout.effect} onChange={(e) => update({ effect: e.target.value as CanvasEffect })} className="theme-input w-full rounded-lg border px-2 py-1.5 text-xs focus:border-accent focus:outline-none">
              {EFFECT_OPTIONS.map((o) => (<option key={o.value} value={o.value}>{o.label}</option>))}
            </select>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <SelectField label="Gradient type" value={layout.bg.gradientType || "linear"} options={[{ value: "linear", label: "Linear" }, { value: "radial", label: "Radial" }]} onChange={(v) => updateBg({ gradientType: v as "linear" | "radial" })} />
          <NumberField label="Gradient angle" value={layout.bg.gradientAngle ?? 120} min={0} max={360} onChange={(v) => updateBg({ gradientAngle: v })} />
        </div>
        <div className="grid grid-cols-3 gap-2">
          <ColorField label="Gradient from" value={layout.bg.gradientFrom || "#0ea5e9"} onChange={(v) => updateBg({ gradientFrom: v })} />
          <ColorField label="Gradient via" value={layout.bg.gradientVia || "#8b5cf6"} onChange={(v) => updateBg({ gradientVia: v })} />
          <ColorField label="Gradient to" value={layout.bg.gradientTo || "#ec4899"} onChange={(v) => updateBg({ gradientTo: v })} />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <TextField label="Background image URL" value={layout.bg.imageUrl} placeholder="https://..." onChange={(v) => updateBg({ imageUrl: v })} />
          <TextField label="Background video URL" value={layout.bg.videoUrl} placeholder="https://...mp4" onChange={(v) => updateBg({ videoUrl: v })} />
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <SelectField label="Image fit" value={layout.bg.bgImageFit || "cover"} options={[{ value: "cover", label: "Cover" }, { value: "contain", label: "Contain" }]} onChange={(v) => updateBg({ bgImageFit: v as "cover" | "contain" })} />
          <NumberField label="Image opacity %" value={Math.round((layout.bg.bgImageOpacity ?? 0.3) * 100)} min={0} max={100} onChange={(v) => updateBg({ bgImageOpacity: Math.min(1, Math.max(0, v / 100)) })} />
          <ColorField label="Overlay color" value={layout.bg.overlayColor || "#000000"} onChange={(v) => updateBg({ overlayColor: v })} />
          <NumberField label="Overlay opacity %" value={Math.round((layout.bg.overlayOpacity ?? 0.3) * 100)} min={0} max={100} onChange={(v) => updateBg({ overlayOpacity: Math.min(1, Math.max(0, v / 100)) })} />
        </div>
      </div>

      {/* Selected element properties */}
      {selectedEls.length > 1 && (
        <div className="rounded-xl border border-border p-3 text-xs text-text-muted">
          <span className="font-bold text-text">{selectedEls.length} elements selected.</span> Use alignment &amp; distribute tools above. Drag together to move as a group.
        </div>
      )}
      {single && (
        <div className="rounded-xl border border-border p-3 space-y-3">
          <div className="text-xs font-bold text-text capitalize flex items-center gap-1.5"><Plus className="w-3.5 h-3.5 theme-status-warning" /> {single.name || single.type} properties</div>

          <TextField label="Layer name" value={single.name || ""} onChange={(v) => liveUpdateElement(single.id, { name: v })} onFocus={beginEdit} onBlur={endEdit} />

          {/* position */}
          <div className="grid grid-cols-4 gap-2">
            <NumberField label="X %" value={Math.round(single.x)} onChange={(v) => liveUpdateElement(single.id, { x: v })} onFocus={beginEdit} onBlur={endEdit} />
            <NumberField label="Y %" value={Math.round(single.y)} onChange={(v) => liveUpdateElement(single.id, { y: v })} onFocus={beginEdit} onBlur={endEdit} />
            <NumberField label="W %" value={Math.round(single.w)} onChange={(v) => liveUpdateElement(single.id, { w: Math.max(2, v) })} onFocus={beginEdit} onBlur={endEdit} />
            <NumberField label="H %" value={Math.round(single.h)} onChange={(v) => liveUpdateElement(single.id, { h: Math.max(2, v) })} onFocus={beginEdit} onBlur={endEdit} />
          </div>

          {(single.type === "text" || single.type === "button" || single.type === "emoji") && (
            <TextField label="Text content" value={single.content || ""} onChange={(v) => liveUpdateElement(single.id, { content: v })} onFocus={beginEdit} onBlur={endEdit} />
          )}
          {(single.type === "image" || single.type === "video") && (
            <TextField label={single.type === "video" ? "Video URL" : "Image URL"} value={single.src || ""} placeholder="https://..." onChange={(v) => liveUpdateElement(single.id, { src: v })} onFocus={beginEdit} onBlur={endEdit} />
          )}
          {single.type === "button" && (
            <TextField label="Button link (CTA URL)" value={single.ctaUrl || ""} placeholder="/products" onChange={(v) => liveUpdateElement(single.id, { ctaUrl: v })} onFocus={beginEdit} onBlur={endEdit} />
          )}

          {/* fill / gradient */}
          {(single.type === "rect" || single.type === "ellipse" || single.type === "button" || single.type === "triangle" || single.type === "star" || single.type === "polygon" || single.type === "icon") && (
            <div className="grid grid-cols-3 gap-2">
              <ColorField label="Fill" value={single.fill === "transparent" ? "#ffffff" : solidHex(single.fill)} onChange={(v) => liveUpdateElement(single.id, { fill: v, gradientFrom: "" })} />
              <ColorField label="Gradient from" value={single.gradientFrom || "#0ea5e9"} onChange={(v) => liveUpdateElement(single.id, { gradientFrom: v })} />
              <ColorField label="Gradient to" value={single.gradientTo || "#ec4899"} onChange={(v) => liveUpdateElement(single.id, { gradientTo: v })} />
            </div>
          )}

          {/* flip + fill alpha + group */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] text-text-muted">Flip:</span>
            <button type="button" onClick={() => flip("x")} className={`theme-btn-secondary rounded-lg p-1.5 ${single.flipX ? "theme-status-warning" : ""}`} title="Flip horizontal"><FlipHorizontal2 className="w-3.5 h-3.5" /></button>
            <button type="button" onClick={() => flip("y")} className={`theme-btn-secondary rounded-lg p-1.5 ${single.flipY ? "theme-status-warning" : ""}`} title="Flip vertical"><FlipVertical2 className="w-3.5 h-3.5" /></button>
            {(single.type === "rect" || single.type === "ellipse" || single.type === "button" || single.type === "triangle" || single.type === "star" || single.type === "polygon" || single.type === "icon") && (
              <div className="flex items-center gap-1 text-[11px] text-text-muted">
                <span>Fill alpha</span>
                <input type="range" min={0} max={100} value={Math.round(readAlpha(single.fill) * 100)} onChange={(e) => liveUpdateElement(single.id, { fill: toRgba(single.fill, Number(e.target.value) / 100) })} className="w-20 theme-range" />
                <span>{Math.round(readAlpha(single.fill) * 100)}%</span>
              </div>
            )}
            {single.groupId && (
              <span className="rounded bg-primary/15 px-1.5 py-0.5 text-[10px] font-semibold text-primary">Grouped</span>
            )}
          </div>

          {(single.type === "text" || single.type === "button" || single.type === "emoji") && (
            <div className="grid grid-cols-2 gap-2">
              <ColorField label="Text color" value={single.textColor || "#ffffff"} onChange={(v) => liveUpdateElement(single.id, { textColor: v })} />
              <SelectField label="Text align" value={single.textAlign || "left"} options={[{ value: "left", label: "Left" }, { value: "center", label: "Center" }, { value: "right", label: "Right" }]} onChange={(v) => liveUpdateElement(single.id, { textAlign: v as "left" | "center" | "right" })} />
            </div>
          )}

          {(single.type === "text" || single.type === "button" || single.type === "emoji") && (
            <div className="grid grid-cols-2 gap-2">
              <SelectField label="Font" value={single.fontFamily || FONT_OPTIONS[0].value} options={FONT_OPTIONS} onChange={(v) => liveUpdateElement(single.id, { fontFamily: v })} />
              <div className="flex gap-2">
                <NumberField label="Size" value={single.fontSize || 16} min={8} max={120} onChange={(v) => liveUpdateElement(single.id, { fontSize: v })} onFocus={beginEdit} onBlur={endEdit} />
                <NumberField label="Weight" value={single.fontWeight || 400} min={100} max={900} step={100} onChange={(v) => liveUpdateElement(single.id, { fontWeight: v })} onFocus={beginEdit} onBlur={endEdit} />
              </div>
            </div>
          )}

          {(single.type === "text" || single.type === "button" || single.type === "emoji") && (
            <div className="grid grid-cols-2 gap-2">
              <NumberField label="Letter spacing" value={single.letterSpacing ?? 0} min={-5} max={20} step={0.5} onChange={(v) => liveUpdateElement(single.id, { letterSpacing: v })} onFocus={beginEdit} onBlur={endEdit} />
              <NumberField label="Line height" value={single.lineHeight ?? 1.1} min={0.8} max={3} step={0.1} onChange={(v) => liveUpdateElement(single.id, { lineHeight: v })} onFocus={beginEdit} onBlur={endEdit} />
            </div>
          )}

          {(single.type === "text" || single.type === "button" || single.type === "emoji") && (
            <div className="flex gap-3 flex-wrap">
              <label className="flex items-center gap-1 text-[11px] text-text-muted"><input type="checkbox" checked={!!single.italic} onChange={(e) => liveUpdateElement(single.id, { italic: e.target.checked })} /> Italic</label>
              <label className="flex items-center gap-1 text-[11px] text-text-muted"><input type="checkbox" checked={!!single.underline} onChange={(e) => liveUpdateElement(single.id, { underline: e.target.checked })} /> Underline</label>
              <label className="flex items-center gap-1 text-[11px] text-text-muted"><input type="checkbox" checked={!!single.textShadow} onChange={(e) => liveUpdateElement(single.id, { textShadow: e.target.checked })} /> Text shadow</label>
              <SelectField label="Case" value={single.textTransform || "none"} options={[{ value: "none", label: "Normal" }, { value: "uppercase", label: "UPPER" }, { value: "capitalize", label: "Title" }]} onChange={(v) => liveUpdateElement(single.id, { textTransform: v as "none" | "uppercase" | "capitalize" })} />
            </div>
          )}

          {(single.type === "text" || single.type === "button" || single.type === "emoji") && (
            <div className="grid grid-cols-3 gap-2">
              <ColorField label="Text outline" value={single.textStroke || "#000000"} onChange={(v) => liveUpdateElement(single.id, { textStroke: v })} />
              <NumberField label="Outline width" value={single.textStrokeWidth ?? 0} min={0} max={12} step={0.5} onChange={(v) => liveUpdateElement(single.id, { textStrokeWidth: v })} onFocus={beginEdit} onBlur={endEdit} />
              <div className="flex items-end pb-1 text-[10px] text-text-faint">0 = no outline</div>
            </div>
          )}

          {(single.type === "star" || single.type === "polygon") && (
            <NumberField label={single.type === "star" ? "Star points" : "Polygon sides"} value={single.points ?? (single.type === "star" ? 5 : 6)} min={3} max={12} onChange={(v) => liveUpdateElement(single.id, { points: v })} onFocus={beginEdit} onBlur={endEdit} />
          )}

          {single.type === "icon" && (
            <SelectField label="Icon" value={single.icon || "Star"} options={ICON_NAMES.map((n) => ({ value: n, label: n }))} onChange={(v) => liveUpdateElement(single.id, { icon: v })} />
          )}

          {(single.type === "image" || single.type === "video") && (
            <>
              <SelectField label="Fit" value={single.objectFit || "cover"} options={[{ value: "cover", label: "Cover" }, { value: "contain", label: "Contain" }, { value: "fill", label: "Fill" }]} onChange={(v) => liveUpdateElement(single.id, { objectFit: v as "cover" | "contain" | "fill" })} />
              <div className="grid grid-cols-5 gap-2">
                <NumberField label="Bright" value={single.imgFilter?.brightness ?? 100} min={0} max={200} onChange={(v) => liveUpdateElement(single.id, { imgFilter: { ...(single.imgFilter || { brightness: 100, contrast: 100, saturate: 100, blur: 0, grayscale: 0 }), brightness: v } })} onFocus={beginEdit} onBlur={endEdit} />
                <NumberField label="Contrast" value={single.imgFilter?.contrast ?? 100} min={0} max={200} onChange={(v) => liveUpdateElement(single.id, { imgFilter: { ...(single.imgFilter || { brightness: 100, contrast: 100, saturate: 100, blur: 0, grayscale: 0 }), contrast: v } })} onFocus={beginEdit} onBlur={endEdit} />
                <NumberField label="Saturate" value={single.imgFilter?.saturate ?? 100} min={0} max={200} onChange={(v) => liveUpdateElement(single.id, { imgFilter: { ...(single.imgFilter || { brightness: 100, contrast: 100, saturate: 100, blur: 0, grayscale: 0 }), saturate: v } })} onFocus={beginEdit} onBlur={endEdit} />
                <NumberField label="Blur px" value={single.imgFilter?.blur ?? 0} min={0} max={20} onChange={(v) => liveUpdateElement(single.id, { imgFilter: { ...(single.imgFilter || { brightness: 100, contrast: 100, saturate: 100, blur: 0, grayscale: 0 }), blur: v } })} onFocus={beginEdit} onBlur={endEdit} />
                <NumberField label="Gray %" value={single.imgFilter?.grayscale ?? 0} min={0} max={100} onChange={(v) => liveUpdateElement(single.id, { imgFilter: { ...(single.imgFilter || { brightness: 100, contrast: 100, saturate: 100, blur: 0, grayscale: 0 }), grayscale: v } })} onFocus={beginEdit} onBlur={endEdit} />
              </div>
            </>
          )}

          {/* border + opacity + radius + rotation */}
          <div className="grid grid-cols-2 gap-2">
            <ColorField label="Border" value={single.stroke === "transparent" ? "#000000" : single.stroke} onChange={(v) => liveUpdateElement(single.id, { stroke: v, strokeWidth: v === "#000000" && single.strokeWidth === 0 ? 2 : single.strokeWidth })} />
            <NumberField label="Border width" value={single.strokeWidth} min={0} max={40} onChange={(v) => liveUpdateElement(single.id, { strokeWidth: v })} onFocus={beginEdit} onBlur={endEdit} />
          </div>

          <div className="grid grid-cols-3 gap-2">
            <NumberField label="Opacity %" value={Math.round((single.opacity ?? 1) * 100)} min={0} max={100} onChange={(v) => liveUpdateElement(single.id, { opacity: Math.min(1, Math.max(0, v / 100)) })} onFocus={beginEdit} onBlur={endEdit} />
            <NumberField label="Corner radius" value={single.borderRadius} min={0} max={400} onChange={(v) => liveUpdateElement(single.id, { borderRadius: v })} onFocus={beginEdit} onBlur={endEdit} />
            <NumberField label="Rotation °" value={single.rotation} min={-180} max={180} onChange={(v) => liveUpdateElement(single.id, { rotation: v })} onFocus={beginEdit} onBlur={endEdit} />
          </div>

          {/* shadow */}
          <div className="grid grid-cols-4 gap-2">
            <NumberField label="Shadow X" value={single.shadow?.x ?? 0} min={-40} max={40} onChange={(v) => liveUpdateElement(single.id, { shadow: { x: v, y: single.shadow?.y ?? 0, blur: single.shadow?.blur ?? 12, color: single.shadow?.color ?? "rgba(0,0,0,0.4)" } })} onFocus={beginEdit} onBlur={endEdit} />
            <NumberField label="Shadow Y" value={single.shadow?.y ?? 0} min={-40} max={40} onChange={(v) => liveUpdateElement(single.id, { shadow: { x: single.shadow?.x ?? 0, y: v, blur: single.shadow?.blur ?? 12, color: single.shadow?.color ?? "rgba(0,0,0,0.4)" } })} onFocus={beginEdit} onBlur={endEdit} />
            <NumberField label="Blur" value={single.shadow?.blur ?? 0} min={0} max={80} onChange={(v) => liveUpdateElement(single.id, { shadow: { x: single.shadow?.x ?? 0, y: single.shadow?.y ?? 0, blur: v, color: single.shadow?.color ?? "rgba(0,0,0,0.4)" } })} onFocus={beginEdit} onBlur={endEdit} />
            <ColorField label="Shadow" value={single.shadow?.color ?? "rgba(0,0,0,0.4)"} onChange={(v) => liveUpdateElement(single.id, { shadow: { x: single.shadow?.x ?? 0, y: single.shadow?.y ?? 0, blur: single.shadow?.blur ?? 12, color: v } })} />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <SelectField label="Blend mode" value={single.blend || "normal"} options={[{ value: "normal", label: "Normal" }, { value: "multiply", label: "Multiply" }, { value: "screen", label: "Screen" }, { value: "overlay", label: "Overlay" }, { value: "lighten", label: "Lighten" }, { value: "darken", label: "Darken" }]} onChange={(v) => liveUpdateElement(single.id, { blend: v })} />
            <SelectField label="Animation" value={single.animation || "none"} options={ANIMATION_OPTIONS} onChange={(v) => liveUpdateElement(single.id, { animation: v as CanvasAnimation })} />
          </div>
        </div>
      )}
    </div>
  );
}

/* Small form field helpers */
function ColorField({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <label className="block text-[11px] text-text-muted mb-1">{label}</label>
      <div className="flex items-center gap-2">
        <input type="color" value={value || "#ffffff"} onChange={(e) => onChange(e.target.value)} className="h-8 w-9 rounded border border-border bg-transparent" />
        <input value={value} onChange={(e) => onChange(e.target.value)} className="theme-input w-full rounded-lg border px-2 py-1.5 text-xs focus:border-accent focus:outline-none" />
      </div>
    </div>
  );
}

function TextField({ label, value, placeholder, onChange, onFocus, onBlur }: { label: string; value: string; placeholder?: string; onChange: (v: string) => void; onFocus?: () => void; onBlur?: () => void }) {
  return (
    <div>
      <label className="block text-[11px] text-text-muted mb-1">{label}</label>
      <input value={value} placeholder={placeholder} onFocus={onFocus} onBlur={onBlur} onChange={(e) => onChange(e.target.value)} className="theme-input w-full rounded-lg border px-2 py-1.5 text-xs focus:border-accent focus:outline-none" />
    </div>
  );
}

function NumberField({ label, value, min, max, step = 1, onChange, onFocus, onBlur }: { label: string; value: number; min?: number; max?: number; step?: number; onChange: (v: number) => void; onFocus?: () => void; onBlur?: () => void }) {
  return (
    <div>
      <label className="block text-[11px] text-text-muted mb-1">{label}</label>
      <input type="number" value={value} min={min} max={max} step={step} onFocus={onFocus} onBlur={onBlur} onChange={(e) => onChange(Number(e.target.value))} className="theme-input w-full rounded-lg border px-2 py-1.5 text-xs focus:border-accent focus:outline-none" />
    </div>
  );
}

function SelectField({ label, value, options, onChange }: { label: string; value: string; options: { value: string; label: string }[]; onChange: (v: string) => void }) {
  return (
    <div>
      <label className="block text-[11px] text-text-muted mb-1">{label}</label>
      <select value={value} onChange={(e) => onChange(e.target.value)} className="theme-input w-full rounded-lg border px-2 py-1.5 text-xs focus:border-accent focus:outline-none">
        {options.map((o) => (<option key={o.value} value={o.value}>{o.label}</option>))}
      </select>
    </div>
  );
}
