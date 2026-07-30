"use client";

import { motion } from "framer-motion";
import { useComm } from "./CommShell";

const LENSES = [
  { key: "all", label: "All" },
  { key: "unread", label: "Unread" },
  { key: "mentions", label: "@Me" },
  { key: "starred", label: "★" },
] as const;

export default function LensChips() {
  const { lens, setLens } = useComm();

  return (
    <div className="flex items-center gap-1">
      {LENSES.map((l) => (
        <button
          key={l.key}
          onClick={() => setLens(l.key)}
          data-active={lens === l.key}
          className="relative px-2.5 py-1 rounded-lg text-[10px] font-semibold transition-colors data-[active=true]:text-primary data-[active=true]:bg-primary/10 text-text-muted hover:text-text hover:bg-surface-2"
        >
          {l.label}
          {lens === l.key && (
            <motion.div
              layoutId="lens-chip"
              className="absolute inset-0 rounded-lg border border-primary/30"
              transition={{ duration: 0.18 }}
            />
          )}
        </button>
      ))}
    </div>
  );
}
