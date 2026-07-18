export const SUPPORTED_LOCALES = ["en", "ar", "fr", "de", "es", "hi", "ur", "tr", "fa"] as const;

export type Locale = (typeof SUPPORTED_LOCALES)[number];

export interface LanguageOption {
  code: Locale;
  name: string;
  nativeName: string;
  direction: "LTR" | "RTL";
  tag: string;
}

export interface CurrencyOption {
  code: string;
  name: string;
  symbol: string;
}

export interface CountryOption {
  code: string;
  name: string;
  currency: string;
}

const LOCALE_TAGS: Record<Locale, string> = {
  en: "en-US",
  ar: "ar-OM",
  fr: "fr-FR",
  de: "de-DE",
  es: "es-ES",
  hi: "hi-IN",
  ur: "ur-PK",
  tr: "tr-TR",
  fa: "fa-IR",
};

const RTL_LOCALES = new Set<Locale>(["ar", "ur", "fa"]);

const LOCALE_ALIASES: Record<string, Locale> = {
  en: "en",
  "en-us": "en",
  "en-gb": "en",
  ar: "ar",
  "ar-om": "ar",
  "ar-ae": "ar",
  "ar-sa": "ar",
  fr: "fr",
  "fr-fr": "fr",
  de: "de",
  "de-de": "de",
  es: "es",
  "es-es": "es",
  hi: "hi",
  "hi-in": "hi",
  ur: "ur",
  "ur-pk": "ur",
  tr: "tr",
  "tr-tr": "tr",
  fa: "fa",
  "fa-ir": "fa",
};

export const LANGUAGE_OPTIONS: readonly LanguageOption[] = [
  { code: "en", name: "English", nativeName: "English", direction: "LTR", tag: LOCALE_TAGS.en },
  { code: "ar", name: "Arabic", nativeName: "العربية", direction: "RTL", tag: LOCALE_TAGS.ar },
  { code: "fr", name: "French", nativeName: "Français", direction: "LTR", tag: LOCALE_TAGS.fr },
  { code: "de", name: "German", nativeName: "Deutsch", direction: "LTR", tag: LOCALE_TAGS.de },
  { code: "es", name: "Spanish", nativeName: "Español", direction: "LTR", tag: LOCALE_TAGS.es },
  { code: "hi", name: "Hindi", nativeName: "हिन्दी", direction: "LTR", tag: LOCALE_TAGS.hi },
  { code: "ur", name: "Urdu", nativeName: "اردو", direction: "RTL", tag: LOCALE_TAGS.ur },
  { code: "tr", name: "Turkish", nativeName: "Türkçe", direction: "LTR", tag: LOCALE_TAGS.tr },
  { code: "fa", name: "Persian", nativeName: "فارسی", direction: "RTL", tag: LOCALE_TAGS.fa },
] as const;

export const CURRENCY_OPTIONS: readonly CurrencyOption[] = [
  { code: "OMR", name: "Omani Rial", symbol: "OMR" },
  { code: "AED", name: "UAE Dirham", symbol: "AED" },
  { code: "SAR", name: "Saudi Riyal", symbol: "SAR" },
  { code: "KWD", name: "Kuwaiti Dinar", symbol: "KWD" },
  { code: "BHD", name: "Bahraini Dinar", symbol: "BHD" },
  { code: "QAR", name: "Qatari Riyal", symbol: "QAR" },
  { code: "USD", name: "US Dollar", symbol: "$" },
  { code: "EUR", name: "Euro", symbol: "EUR" },
  { code: "GBP", name: "British Pound", symbol: "GBP" },
  { code: "INR", name: "Indian Rupee", symbol: "INR" },
  { code: "PKR", name: "Pakistani Rupee", symbol: "PKR" },
] as const;

export const COUNTRY_OPTIONS: readonly CountryOption[] = [
  { code: "OM", name: "Oman", currency: "OMR" },
  { code: "AE", name: "United Arab Emirates", currency: "AED" },
  { code: "SA", name: "Saudi Arabia", currency: "SAR" },
  { code: "KW", name: "Kuwait", currency: "KWD" },
  { code: "BH", name: "Bahrain", currency: "BHD" },
  { code: "QA", name: "Qatar", currency: "QAR" },
  { code: "US", name: "United States", currency: "USD" },
  { code: "GB", name: "United Kingdom", currency: "GBP" },
  { code: "DE", name: "Germany", currency: "EUR" },
  { code: "IN", name: "India", currency: "INR" },
  { code: "PK", name: "Pakistan", currency: "PKR" },
] as const;

export function isLocale(value: string | null | undefined): value is Locale {
  return SUPPORTED_LOCALES.includes((value ?? "") as Locale);
}

export function normalizeLocale(value: string | null | undefined, fallback: Locale = "en"): Locale {
  const normalized = (value ?? "").trim().toLowerCase().replace(/_/g, "-");
  if (!normalized) return fallback;
  const alias = LOCALE_ALIASES[normalized];
  if (alias) return alias;

  const base = normalized.split("-")[0];
  return isLocale(base) ? base : fallback;
}

export function getLocaleTag(locale: string | Locale): string {
  return LOCALE_TAGS[normalizeLocale(locale)];
}

export function isRtlLocale(locale: string | Locale): boolean {
  return RTL_LOCALES.has(normalizeLocale(locale));
}

function toDate(value: string | number | Date): Date {
  return value instanceof Date ? value : new Date(value);
}

export function formatLocalizedDate(
  value: string | number | Date,
  locale: string | Locale,
  options: Intl.DateTimeFormatOptions = {}
): string {
  const date = toDate(value);
  if (Number.isNaN(date.getTime())) return "";

  try {
    return new Intl.DateTimeFormat(getLocaleTag(locale), options).format(date);
  } catch {
    return date.toLocaleDateString(undefined, options);
  }
}

export function formatLocalizedDateTime(
  value: string | number | Date,
  locale: string | Locale,
  options: Intl.DateTimeFormatOptions = {}
): string {
  return formatLocalizedDate(value, locale, options);
}

export function getDefaultCurrencyForCountry(countryCode: string): string | null {
  const normalized = (countryCode || "").trim().toUpperCase();
  if (!normalized) return null;
  return COUNTRY_OPTIONS.find((country) => country.code === normalized)?.currency ?? null;
}
