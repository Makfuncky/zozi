import { motion } from "motion/react";
import type { CSSProperties } from "react";
import ZoziLogo, { type ZoziLogoVariant } from "./ZoziLogo";

export type ZoziLockupProps = {
  logoSize?: number;
  className?: string;
  textClassName?: string;
  animated?: boolean;
  variant?: ZoziLogoVariant;
  gap?: number;
};

const textPalettes: Record<ZoziLogoVariant, { color: string; shadow: string }> = {
  brand: {
    color: "#243454",
    shadow: "0px 4px 16px rgba(36, 52, 84, 0.12)",
  },
  black: {
    color: "#111111",
    shadow: "0px 4px 14px rgba(0, 0, 0, 0.08)",
  },
  white: {
    color: "#FFFFFF",
    shadow: "0px 4px 14px rgba(255, 255, 255, 0.12)",
  },
};

export default function ZoziLockup({
  logoSize = 190,
  className,
  textClassName,
  animated = true,
  variant = "brand",
  gap = 0,
}: ZoziLockupProps) {
  const textPalette = textPalettes[variant];
  const fontSize = (logoSize / 190) * 116;
  const wrapperStyle = {
    display: "inline-flex",
    alignItems: "center",
    gap: `${gap}px`,
    userSelect: "none",
  } satisfies CSSProperties;
  const textStyle = {
    fontFamily: '"Nunito", sans-serif',
    fontWeight: 900,
    fontSize: `${fontSize}px`,
    lineHeight: 0.95,
    letterSpacing: `${fontSize * -0.043}px`,
    color: textPalette.color,
    textShadow: textPalette.shadow,
  } satisfies CSSProperties;

  return (
    <div className={className} style={wrapperStyle}>
      <ZoziLogo size={logoSize} animated={animated} variant={variant} />
      <motion.span
        initial={animated ? { x: 30, opacity: 0 } : false}
        animate={{ x: 0, opacity: 1 }}
        transition={animated ? { delay: 0.5, duration: 0.7, ease: "easeOut" } : { duration: 0 }}
        className={textClassName}
        style={textStyle}
      >
        Zozi
      </motion.span>
    </div>
  );
}
