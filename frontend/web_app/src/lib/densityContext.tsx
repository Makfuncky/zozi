"use client";

import { createContext, useContext, useState, useEffect, type ReactNode } from "react";

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export type Density = "compact" | "normal" | "expanded";

interface DensityContextType {
  density: Density;
  setDensity: (d: Density) => void;
}

// ─────────────────────────────────────────────────────────────────────────────
// Context
// ─────────────────────────────────────────────────────────────────────────────

const DensityContext = createContext<DensityContextType>({
  density: "compact",
  setDensity: () => {},
});

const STORAGE_KEY = "admin-density";
const VALID = new Set<Density>(["compact", "normal", "expanded"]);

export function DensityProvider({ children }: { children: ReactNode }) {
  const [density, setDensityState] = useState<Density>("compact");

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY) as Density | null;
      if (stored && VALID.has(stored)) setDensityState(stored);
    } catch {}
  }, []);

  const setDensity = (d: Density) => {
    setDensityState(d);
    try { localStorage.setItem(STORAGE_KEY, d); } catch {}
  };

  return (
    <DensityContext.Provider value={{ density, setDensity }}>
      {children}
    </DensityContext.Provider>
  );
}

export function useDensity() {
  return useContext(DensityContext);
}

// ─────────────────────────────────────────────────────────────────────────────
// Utility: pick value by density mode
// Usage: dc(density, "compact-class", "normal-class", "expanded-class")
// ─────────────────────────────────────────────────────────────────────────────

export function dc(density: Density, compact: string, normal: string, expanded: string): string {
  if (density === "compact") return compact;
  if (density === "expanded") return expanded;
  return normal;
}


