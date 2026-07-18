import { create } from "zustand";
import { Locale, t as translate } from "@shared/i18n";

export type TranslationKey = keyof typeof import("@shared/i18n").translations.en;

interface LocaleStore {
  locale: Locale;
  t: (key: TranslationKey) => string;
  setLocale: (locale: Locale) => void;
}

const makeTranslator = (locale: Locale) => (key: TranslationKey) => translate(locale, key);

export const useLocaleStore = create<LocaleStore>()((set) => ({
  locale: "en",
  t: makeTranslator("en"),
  setLocale: (locale) => {
    set({ locale, t: makeTranslator(locale) });
  },
}));
