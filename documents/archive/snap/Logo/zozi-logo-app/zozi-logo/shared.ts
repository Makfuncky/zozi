export type ZoziTheme = "light" | "dark";

export type ZoziBaseProps = {
  size?: number;
  className?: string;
  animated?: boolean;
  /** "light" = for white/light backgrounds (default). "dark" = for black/dark backgrounds. */
  theme?: ZoziTheme;
};

export const tokens = {
  light: {
    zTop: "#E2FF70",
    zMid1: "#C8EC22",
    zMid2: "#86BE12",
    zMid3: "#409808",
    zBot: "#1A5204",
    shadowOpacity: "0.18",
    pinShadowFill: "black",
    pinShadowOpacity: "0.06",
    pinShadowLoop: [0.06, 0.01, 0.06, 0.01, 0.06] as number[],
    pinHoleStroke: "rgba(0,0,0,0.08)",
    flareColor: "#F8C400",
    flareOpacity: 0.7,
    pinReflStart: "#E8A000",
    wordmarkText: "#163905",
    wordmarkShadow: "rgba(26, 82, 4, 0.18)",
  },
  dark: {
    zTop: "#EEFF99",
    zMid1: "#CCEE38",
    zMid2: "#97D01A",
    zMid3: "#55B010",
    zBot: "#2A7006",
    shadowOpacity: "0.45",
    pinShadowFill: "white",
    pinShadowOpacity: "0.14",
    pinShadowLoop: [0.14, 0.04, 0.14, 0.04, 0.14] as number[],
    pinHoleStroke: "rgba(255,255,255,0.15)",
    flareColor: "#FFD740",
    flareOpacity: 0.85,
    pinReflStart: "#FFCC22",
    wordmarkText: "#F4FFD0",
    wordmarkShadow: "rgba(0, 0, 0, 0.28)",
  },
} as const;