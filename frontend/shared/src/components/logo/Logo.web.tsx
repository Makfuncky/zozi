"use client";

import { motion } from "framer-motion";
import type { LogoSize, LogoTheme } from "./types";
import ZoziLogo from "./ZoziLogo";

export interface LogoWebProps {
  size?: LogoSize;
  className?: string;
  animated?: boolean;
  theme?: LogoTheme;
  showWordmark?: boolean;
}

const SIZES = {
  sm: { symbol: 72, wordmark: 34, gap: 10 },
  md: { symbol: 96, wordmark: 46, gap: 12 },
  lg: { symbol: 126, wordmark: 58, gap: 14 },
} as const;

const WORDMARK_VARS = {
  light: { "--zozi-logo-wordmark": "#111111" },
  dark: { "--zozi-logo-wordmark": "#FFFFFF" },
} as const;

export default function LogoWeb({
  size = "md",
  className,
  animated = true,
  theme,
  showWordmark = true,
}: LogoWebProps) {
  const scale = SIZES[size];

  return (
    <div
      className={className}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: showWordmark ? scale.gap : 0,
        flexShrink: 0,
        ...(theme ? WORDMARK_VARS[theme] : null),
      }}
    >
      <ZoziLogo size={scale.symbol} animated={animated} theme={theme} />

      {showWordmark ? (
        <motion.span
          initial={animated ? { opacity: 0, x: 18, filter: "blur(6px)" } : false}
          animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
          transition={animated ? { delay: 0.95, duration: 0.55, ease: [0.16, 1, 0.3, 1] } : { duration: 0 }}
          style={{
            fontFamily: "var(--font-nunito, 'Nunito', var(--font-body, 'Sora', system-ui, sans-serif))",
            fontSize: scale.wordmark,
            fontWeight: 900,
            lineHeight: 1,
            letterSpacing: "-0.06em",
            color: "var(--zozi-logo-wordmark)",
          }}
        >
          Zozi
        </motion.span>
      ) : null}
    </div>
  );
}