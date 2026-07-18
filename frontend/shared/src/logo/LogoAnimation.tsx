"use client";

import { useCallback, useEffect, useState } from "react";
import { cn } from "../utils";
import { motion } from "./motion";
import ZoziLogo from "./ZoziLogo";

interface LogoAnimationProps {
  theme?: "dark" | "light";
  tagline?: string;
  onDone?: () => void;
  autoReplay?: boolean;
  className?: string;
}

const T = {
  bgGlow: 0.08,
  wordmark: 1.26,
  tagline: 1.72,
  totalMs: 4300,
};

export default function LogoAnimation({
  theme = "dark",
  tagline,
  onDone,
  autoReplay = false,
  className = "",
}: LogoAnimationProps) {
  const isDark = theme === "dark";
  const [key, setKey] = useState(0);

  const replay = useCallback(() => {
    setKey((value) => value + 1);
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      onDone?.();
      if (autoReplay) replay();
    }, T.totalMs);

    return () => clearTimeout(timer);
  }, [autoReplay, key, onDone, replay]);

  return (
    <div
      className={cn(
        "relative flex min-h-screen w-full items-center justify-center overflow-hidden",
        className,
      )}
    >
      <motion.div
        className="pointer-events-none absolute rounded-full"
        style={{
          width: 760,
          height: 520,
          background: isDark
            ? "radial-gradient(circle, rgba(205, 255, 92, 0.28) 0%, rgba(255, 212, 64, 0.18) 22%, rgba(61, 128, 24, 0.12) 48%, transparent 80%)"
            : "radial-gradient(circle, rgba(220, 246, 116, 0.22) 0%, rgba(255, 212, 64, 0.12) 22%, rgba(61, 128, 24, 0.08) 48%, transparent 80%)",
          top: "50%",
          left: "50%",
          translate: "-50% -50%",
        }}
        initial={{ opacity: 0, scale: 0.6 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1], delay: T.bgGlow }}
      />

      <motion.div
        key={`logo-animation-${key}`}
        className="relative z-10 flex flex-row items-center gap-4 md:gap-6"
      >
        <ZoziLogo size={240} animated theme={theme} />

        <div className="flex flex-col gap-3">
          <motion.span
            style={{
              fontFamily: "var(--font-nunito, 'Nunito', var(--font-body, 'Sora', system-ui, sans-serif))",
              fontWeight: 900,
              fontSize: "clamp(58px, 8.5vw, 96px)",
              letterSpacing: "-0.06em",
              lineHeight: 1,
              color: isDark ? "#314A73" : "#233A61",
            }}
            initial={{ opacity: 0, x: 36, filter: "blur(8px)" }}
            animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
            transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1], delay: T.wordmark }}
          >
            Zozi
          </motion.span>

          {tagline ? (
            <motion.span
              style={{
                fontFamily: "var(--font-body, 'Sora', system-ui, sans-serif)",
                fontWeight: 500,
                fontSize: "clamp(11px, 1.5vw, 15px)",
                letterSpacing: "0.28em",
                textTransform: "uppercase",
                color: isDark ? "rgba(93, 118, 160, 0.78)" : "rgba(35, 58, 97, 0.62)",
              }}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: "easeOut", delay: T.tagline }}
            >
              {tagline}
            </motion.span>
          ) : null}
        </div>
      </motion.div>

    </div>
  );
}