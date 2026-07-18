"use client";

import { motion } from "framer-motion";
import { LogoSymbol } from "@shared/logo/web";

interface BrandLoadingProps {
  label?: string;
  size?: number;
  fullscreen?: boolean;
  className?: string;
}

export default function BrandLoading({
  label,
  size = 82,
  fullscreen = false,
  className = "",
}: BrandLoadingProps) {
  return (
    <div
      className={[
        "flex w-full flex-col items-center justify-center gap-4 text-center",
        fullscreen ? "min-h-screen" : "",
        className,
      ].filter(Boolean).join(" ")}
    >
      <motion.div
        animate={{ opacity: [0.82, 1, 0.82], scale: [0.985, 1, 0.985] }}
        transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
      >
        <LogoSymbol size={size} animated />
      </motion.div>

      {label ? <p className="text-sm text-text-muted">{label}</p> : null}
    </div>
  );
}


