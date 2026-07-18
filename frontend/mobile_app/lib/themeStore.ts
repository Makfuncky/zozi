import * as SecureStore from "expo-secure-store";
import { Appearance, Platform } from "react-native";
import { create } from "zustand";
import { darkTheme, lightTheme, AppTheme } from "@/theme";

const THEME_KEY = "zozi-theme";

type ThemeMode = "dark" | "light";

interface ThemeState {
  mode: ThemeMode;
  theme: AppTheme;
  initialized: boolean;
  toggle: () => void;
  setMode: (mode: ThemeMode) => Promise<void>;
  initTheme: () => Promise<void>;
}

async function saveTheme(mode: ThemeMode) {
  try {
    if (Platform.OS === "web" && typeof window !== "undefined") {
      window.localStorage.setItem(THEME_KEY, mode);
      return;
    }
    await SecureStore.setItemAsync(THEME_KEY, mode);
  } catch {
    // ignore non-critical failure; continue with in-memory state
  }
}

function readSavedThemeSync(): ThemeMode | null {
  if (Platform.OS === "web" && typeof window !== "undefined") {
    const value = window.localStorage.getItem(THEME_KEY);
    if (value === "dark" || value === "light") {
      return value;
    }
    return null;
  }
  return null;
}

async function readSavedThemeAsync(): Promise<ThemeMode | null> {
  try {
    if (Platform.OS === "web" && typeof window !== "undefined") {
      return window.localStorage.getItem(THEME_KEY) as ThemeMode | null;
    }
    const value = await SecureStore.getItemAsync(THEME_KEY);
    if (value === "dark" || value === "light") {
      return value;
    }
  } catch {
    // fallback to system preference
  }
  return null;
}

export const useThemeStore = create<ThemeState>((set, get) => ({
  mode: "dark",
  theme: darkTheme,
  initialized: false,
  toggle: () => {
    set((s) => {
      const mode: ThemeMode = s.mode === "dark" ? "light" : "dark";
      void saveTheme(mode);
      return { mode, theme: mode === "dark" ? darkTheme : lightTheme };
    });
  },
  setMode: async (mode) => {
    set({ mode, theme: mode === "dark" ? darkTheme : lightTheme });
    await saveTheme(mode);
  },
  initTheme: async () => {
    // On web, initialize synchronously to prevent blank screen
    if (Platform.OS === "web" && typeof window !== "undefined") {
      const storedMode = readSavedThemeSync();
      const systemMode = Appearance.getColorScheme() === "light" ? "light" : "dark";
      const mode = storedMode || systemMode;
      set({ mode, theme: mode === "dark" ? darkTheme : lightTheme, initialized: true });
      if (!storedMode) {
        await saveTheme(mode);
      }
      return;
    }

    // On mobile, use async storage
    try {
      const storedMode = (await readSavedThemeAsync()) as ThemeMode | null;
      const systemMode = Appearance.getColorScheme() === "light" ? "light" : "dark";
      const mode = storedMode || systemMode;
      set({ mode, theme: mode === "dark" ? darkTheme : lightTheme, initialized: true });
      if (!storedMode) {
        await saveTheme(mode);
      }
    } catch {
      // Fallback to dark theme on error
      set({ mode: "dark", theme: darkTheme, initialized: true });
    }
  },
}));
