/**
 * ZOZI Design Tokens — shared by web and mobile
 * Web: maps to CSS custom properties in globals.css
 * Mobile: maps to React Native StyleSheet / NativeWind
 */

// ── Brand ───────────────────────────────────────────────────────────────────
export const brand = {
  primary: "#32CD32",
  primaryLight: "#7CFC00",
  primaryDark: "#228B22",
  accent: "#FFD700",
  accentLight: "#FFEA00",
} as const;

// ── Dark theme palette ───────────────────────────────────────────────────────
export const dark = {
  surface0: "#000000",
  surface1: "#111111",
  surface2: "#1A1A1A",
  surface3: "#2A2A2A",
  border: "#333333",
  borderLight: "#4A4A4A",
  text: "#FFFFFF",
  textMuted: "#D1D5DB",
  textFaint: "#9CA3AF",
  onBrand: "#000000",
  onAccent: "#000000",
  onWarning: "#1c1917",
  gradientStart: "#000000",
  gradientEnd: "#1A1A1A",
} as const;
// ── Light theme palette ──────────────────────────────────────────────────────
export const light = {
  surface0: "#FFFFFF",
  surface1: "#F5F5F5",
  surface2: "#EFEFEF",
  surface3: "#E5E5E5",
  border: "#D1D5DB",
  borderLight: "#E5E7EB",
  text: "#111111",
  textMuted: "#4B5563",
  textFaint: "#6B7280",
  onBrand: "#000000",
  onAccent: "#000000",
  onWarning: "#1c1917",
  gradientStart: "#F0FDF4",
  gradientEnd: "#ECFCCB",
} as const;

export const gradients = {
  logo: ["#32CD32", "#7CFC00", "#FFD700"],
  card: ["#f8fafc", "#e8f5de"],
  button: ["#7CFC00", "#32CD32"],
  ice: ["#ffffff", "#f5f5f5"],
  hero: ["#7CFC00", "#32CD32", "#FFD700"],
  brandText: ["#32CD32", "#FFD700"],
  banner: ["#32CD32", "#7CFC00", "#FFD700"],
  bannerAlt: ["#FFD700", "#32CD32"],
  brandAlt: ["#7CFC00", "#FFD700"],
  bannerLuxe: ["#e6ffed", "#d4f7c7", "#fff8cc"],
  bannerFestive: ["#efffe0", "#f0fff4", "#fff8e5"],
  bannerNocturne: ["#0f0f0f", "#1a1a1a", "#222"],
  bannerRoyal: ["#123d28", "#2f7b42", "#ffd700"],
  bannerCoral: ["#fffaf0", "#fff0d1", "#ffd700"],
  bannerMidnight: ["#050505", "#0a0a0a", "#1a1a1a"],
  brandToSuccess: ["#32CD32", "#22c55e"],
  brandToBrandDark: ["#228B22", "#145a32"],
  brandToBrandLight: ["#7CFC00", "#adff2f"],
  shimmer: ["#f3f9ea", "#e5f3d0", "#f3f9ea"],
  logoText: ["#ffffff", "#7CFC00", "#ffffff"],
} as const;

// ── Glass / Frosted Layer Tokens ─────────────────────────────────────────────
export const glass = {
  base: "rgba(0, 0, 0, 0.40)",
  mid: "rgba(0, 0, 0, 0.46)",
  hi: "rgba(0, 0, 0, 0.52)",
  solid: "rgba(0, 0, 0, 0.65)",
  panel: "rgba(17, 17, 17, 0.84)",
  faint: "rgba(255, 255, 255, 0.08)",
  panelHover: "rgba(26, 26, 26, 0.92)",
  border: "rgba(255, 255, 255, 0.15)",
  borderMid: "rgba(255, 255, 255, 0.12)",
  borderSoft: "rgba(255, 255, 255, 0.08)",
} as const;

// ── Semantic / Status ────────────────────────────────────────────────────────
export const status = {
  success: "#22c55e",
  danger: "#ef4444",
  warning: "#f59e0b",
  info: "#38bdf8",
} as const;

// ── Spacing scale (rem → rn points: 1rem = 16pt) ────────────────────────────
export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  "2xl": 48,
  "3xl": 64,
} as const;

// ── Border radius ─────────────────────────────────────────────────────────────
export const radius = {
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
  "2xl": 24,
  full: 9999,
} as const;

// ── Font sizes (sp) ──────────────────────────────────────────────────────────
export const fontSize = {
  xs: 11,
  sm: 13,
  base: 15,
  md: 17,
  lg: 20,
  xl: 24,
  "2xl": 30,
  "3xl": 36,
} as const;

// ── Font weights ─────────────────────────────────────────────────────────────
export const fontWeight = {
  normal: "400" as const,
  medium: "500" as const,
  semibold: "600" as const,
  bold: "700" as const,
  extrabold: "800" as const,
} as const;

// ── Font families (used by web and mobile) ─────────────────────────────────
// Robust fallback stacks: the brand web fonts (Sora/Fraunces) are loaded on web;
// native and pre-load states gracefully fall back to high-quality system fonts.
// Font families (used by web and mobile).
// Web still loads Fraunces/Sora via globals.css and will use those when present.
// On native (RN) those families are NOT bundled, so a robust system stack is
// provided first — this keeps text readable and avoids silent fallbacks to a
// tiny default font. The web fallbacks remain for browsers without the webfonts.
export const fontFamily = {
    heading:
      'Fraunces, "Playfair Display", Georgia, "Times New Roman", serif',
    body:
      'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  } as const;
export type ColorTheme = "dark" | "light";

export function palette(theme: ColorTheme) {
  return theme === "light" ? light : dark;
}

// Set CSS variables for web theme usage
export function applyCssTheme(theme: ColorTheme) {
  const root = (globalThis as any).document?.documentElement;
  if (!root) return;
  const colors = palette(theme);

  root.style.setProperty("--color-brand", brand.primary);
  root.style.setProperty("--color-brand-light", brand.primaryLight);
  root.style.setProperty("--color-brand-dark", brand.primaryDark);
  root.style.setProperty("--color-accent", brand.accent);
  root.style.setProperty("--color-accent-light", brand.accentLight);

  root.style.setProperty("--color-surface-0", colors.surface0);
  root.style.setProperty("--color-surface-1", colors.surface1);
  root.style.setProperty("--color-surface-2", colors.surface2);
  root.style.setProperty("--color-surface-3", colors.surface3);
  root.style.setProperty("--color-border", colors.border);
  root.style.setProperty("--color-border-light", colors.borderLight);
  root.style.setProperty("--color-text", colors.text);
  root.style.setProperty("--color-text-muted", colors.textMuted);
  root.style.setProperty("--color-text-faint", colors.textFaint);
  root.style.setProperty("--color-on-brand", colors.onBrand ?? "#ffffff");
  root.style.setProperty("--color-on-accent", colors.onAccent ?? "#ffffff");
  root.style.setProperty("--color-on-warning", colors.onWarning ?? "#1c1917");

  root.classList.remove("light", "dark");
  root.classList.add(theme);
  root.style.colorScheme = theme;
}


