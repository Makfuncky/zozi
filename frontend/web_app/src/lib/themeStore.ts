"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { applyCssTheme } from "@shared/theme";

type Theme = "light" | "dark";

interface ThemeStore {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

function parseStoredTheme(value: string | null): Theme | null {
  if (!value) return null;
  try {
    const parsed = JSON.parse(value);
    const theme = parsed?.state?.theme;
    return theme === "light" || theme === "dark" ? theme : null;
  } catch {
    return null;
  }
}

function detectPreferredTheme(): Theme {
  if (typeof window === "undefined") return "dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(theme: Theme) {
  if (typeof window === "undefined") return;
  applyCssTheme(theme);
}

/** Reads persisted preference, falling back to OS preference, then dark. */
function getInitialTheme(): Theme {
  if (typeof window === "undefined") return "dark";
  return parseStoredTheme(localStorage.getItem("zozi-theme")) ?? detectPreferredTheme();
}

export const useThemeStore = create<ThemeStore>()(
  persist(
    (set, get) => ({
      theme: getInitialTheme(),
      setTheme: (theme: Theme) => {
        set({ theme });
        applyTheme(theme);
      },
      toggleTheme: () => {
        const currentTheme = get().theme;
        const newTheme = currentTheme === "dark" ? "light" : "dark";
        get().setTheme(newTheme);
      },
    }),
    {
      name: "zozi-theme",
    }
  )
);

// Initialize theme on client side — runs before React hydrates to minimise flash
if (typeof window !== "undefined") {
  applyTheme(parseStoredTheme(localStorage.getItem("zozi-theme")) ?? detectPreferredTheme());
}
