import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Locale } from "./i18n";
import { t, type TranslationKey } from "./i18n";
import { apiFetch } from "./api";
import { getLocaleTag, isRtlLocale, normalizeLocale } from "@shared/localization";

function createTranslator(locale: Locale) {
  return (key: TranslationKey) => t(locale, key);
}

interface LocaleStore {
  locale: Locale;
  hasHydrated: boolean;
  setLocale: (locale: Locale) => void;
  hydrateLocale: () => void;
  /** Persist preference to the server when the user is logged in. */
  syncLocaleToServer: () => Promise<void>;
  t: (key: TranslationKey) => string;
}

function getPreferredLocale(): Locale {
  if (typeof window === "undefined") return "en";
  try {
    const stored = localStorage.getItem("zozi_locale");
    const persistedLocale = stored ? JSON.parse(stored)?.state?.locale : null;
    if (typeof persistedLocale === "string") return normalizeLocale(persistedLocale) as Locale;
  } catch {}
  return normalizeLocale(navigator.language) as Locale;
}

function applyLocaleToDocument(locale: Locale) {
  if (typeof document === "undefined") return;
  document.documentElement.dir = isRtlLocale(locale) ? "rtl" : "ltr";
  document.documentElement.lang = getLocaleTag(locale);
}

export const useLocaleStore = create<LocaleStore>()(
  persist(
    (set, get) => ({
      locale: "en",
      hasHydrated: false,
      setLocale: (locale) => {
        set({ locale, t: createTranslator(locale) });
        applyLocaleToDocument(locale);
      },
      hydrateLocale: () => {
        if (get().hasHydrated) return;
        const locale = getPreferredLocale();
        set({ locale, t: createTranslator(locale), hasHydrated: true });
        applyLocaleToDocument(locale);
      },
      syncLocaleToServer: async () => {
        const locale = get().locale;
        try {
          await apiFetch("/auth/me/preferences", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ preferred_language: locale }),
          });
        } catch {
          // best-effort — we don't block on network failure
        }
      },
      t: createTranslator("en"),
    }),
    {
      name: "zozi_locale",
      skipHydration: true,
      partialize: (state) => ({ locale: state.locale }),
    }
  )
);
