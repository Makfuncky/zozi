export const LOGO_VIEW_BOX = "0 0 72 72";

export const Z_LAYERS = {
  // Render: diagonal first (back), arms on top — arms overlap diagonal at both junctions
  diagonal: {
    // Central Z diagonal: upper-right (near top arm's inner right end) → lower-left (near bottom arm's left end)
    body: "M59 16C47 26 31 39 14 52L18 57C35 44 51 31 63 21Z",
    highlight: "M59 16C47 26 32 38 16 51L14 52C31 39 47 26 59 17Z",
  },
  top: {
    // Top arm: sickle ribbon from lower-left tail to upper-right spike, ~7 units wide
    body: "M8 33C9 27 26 18 44 12C56 8 62 8 67 10L66 17C61 15 55 15 44 18C26 24 10 34 9 37Z",
    highlight: "M8 33C9 27 26 18 44 12C56 8 62 8 67 10L67 11C62 8 55 9 44 13C26 19 10 28 9 34Z",
  },
  bottom: {
    // Bottom arm: sickle ribbon from lower-left hook to right spike, ~7 units wide
    body: "M8 55C9 51 28 48 47 47C60 47 63 47 67 50L66 57C63 55 58 54 47 54C28 55 10 60 9 62Z",
    highlight: "M8 55C9 51 28 48 47 47C60 47 63 47 67 50L67 51C63 48 57 48 47 48C28 49 10 54 9 56Z",
  },
} as const;

export const PIN_PATH =
  "M47.5 23.5C44.8 23.5 42.8 25.1 41.7 27.3C40.6 29.5 41 32.1 42.8 34.5L50 45.5L57.2 34.5C59 32.1 59.4 29.5 58.3 27.3C57.2 25.1 55.2 23.5 52.5 23.5H47.5Z";

export const PIN_INNER_CIRCLE = {
  cx: 50,
  cy: 31,
  r: 4,
} as const;

export const PIN_GLEAM = {
  cx: 46.3,
  cy: 27.2,
  rx: 1.6,
  ry: 1.0,
  rotation: -25,
} as const;

export const PIN_GROUND = {
  cx: 50,
  cy: 46.5,
  rx: 4.8,
  ry: 1.1,
} as const;

export const PIN_IMPACT = {
  cx: 50,
  cy: 45.5,
} as const;

export const WORDMARK_COLOR = "#102643";

// Gradient used per-arm with a vertical gradient matching each arm's y-range
export const Z_GRADIENT_STOPS = [
  { offset: "0%", color: "#D8F500" },   // Very bright lime at outer/upper edge
  { offset: "20%", color: "#9ADB00" },  // Main lime-green
  { offset: "62%", color: "#46A800" },  // Medium forest green
  { offset: "100%", color: "#104808" }, // Dark forest green at inner/lower edge
] as const;

// Diagonal: dark forest green throughout (no navy — keeps the Z looking all-green)
export const Z_CORE_GRADIENT_STOPS = [
  { offset: "0%", color: "#142A08" },
  { offset: "50%", color: "#1D3C10" },
  { offset: "100%", color: "#2A5A0A" },
] as const;

export const PIN_GRADIENT_STOPS = [
  { offset: "0%", color: "#FFF27A" },
  { offset: "40%", color: "#FFE100" },
  { offset: "78%", color: "#FFC400" },
  { offset: "100%", color: "#FFAC00" },
] as const;

// Shadow disabled – offset shadow path was the primary cause of the 3D/cartoon look
export const SHADOW_FILL = "none";
export const HIGHLIGHT_FILL = "rgba(235, 255, 100, 0.18)";
export const DIAGONAL_HIGHLIGHT_FILL = "rgba(150, 210, 100, 0.14)";
// Pin center hole: dark ring matching the reference
export const PIN_INNER_FILL = "#1A2E45";

export const WORDMARK_TRACKING_WEB = "-0.048em";
export const WORDMARK_TRACKING_ANIMATION = "-0.055em";

export const PIN_SPARKS: ReadonlyArray<{ angle: number; dist: number; delay: number }> = [
  { angle: -82, dist: 24, delay: 0.00 },
  { angle: -42, dist: 28, delay: 0.04 },
  { angle: -10, dist: 24, delay: 0.08 },
  { angle: 22, dist: 29, delay: 0.02 },
  { angle: 54, dist: 25, delay: 0.06 },
  { angle: 95, dist: 22, delay: 0.10 },
] as const;

// Render diagonal first (back), then top arm and bottom arm over it
export const SEGMENT_ORDER = ["diagonal", "top", "bottom"] as const;

export type LogoSegmentName = (typeof SEGMENT_ORDER)[number];