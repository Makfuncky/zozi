/**
 * Native theme tokens — explicit colors for React Native (RGBA)
 * These mirror `theme.ts` but use platform-friendly values (no CSS color-mix).
 */
import { Platform } from "react-native";

// Brand
export const brand = {
  primary: "#32CD32",
  primaryLight: "#7CFC00",
  primaryDark: "#228B22",
  accent: "#FFD700",
  accentLight: "#FFEA00",
} as const;

// Dark palette
export const dark = {
  surface0: "#000000",
  surface1: "#111111",
  surface2: "#1A1A1A",
  surface3: "#2A2A2A",
  success: "#22c55e",
  danger: "#ef4444",
  warning: "#f59e0b",
  info: "#38bdf8",
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

// Light palette
export const light = {
  surface0: "#FFFFFF",
  surface1: "#F5F5F5",
  surface2: "#EFEFEF",
  surface3: "#E5E5E5",
  success: "#22c55e",
  danger: "#ef4444",
  warning: "#f59e0b",
  info: "#38bdf8",
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
} as const;

// Glass tokens for light theme (explicit RGBA approximations)
// Unified glass tokens (identical for light and dark platforms)
export const glass = {
  base: "rgba(255,255,255,0.88)",
  mid: "rgba(255,255,255,0.90)",
  hi: "rgba(255,255,255,0.94)",
  solid: "rgba(255,255,255,0.95)",
  panel: "rgba(255,255,255,0.84)",
  faint: "rgba(255,255,255,0.65)",
  panelHover: "rgba(255,255,255,0.92)",
  border: "rgba(209,213,219,0.75)",
  borderMid: "rgba(209,213,219,0.65)",
  borderSoft: "rgba(209,213,219,0.55)",
} as const;

export const glassLight = glass;
export const glassDark = glass;

export function getGlass(mode: "light" | "dark" = "light") {
  return mode === "dark" ? glassDark : glassLight;
}

export const shadows = {
  soft: Platform.select({
    web: {
      boxShadow: "0px 4px 8px rgba(0,0,0,0.06)",
    },
    default: {
      shadowColor: "#000",
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.06,
      shadowRadius: 8,
      elevation: 3,
    },
  })!,
} as const;

export default {
  brand,
  dark,
  light,
  gradients,
  glassLight,
  glassDark,
  getGlass,
  shadows,
};
