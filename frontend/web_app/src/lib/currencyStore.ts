/**
 * Currency Store — resolves currency from the customer's selected country
 * first, then geo detection, and converts all storefront prices from AED.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";
import { apiFetch } from "./api";
import { normalizeCountryCode } from "@shared/localization";

export interface CurrencyInfo {
  code: string;
  symbol: string;
  name: string;
  rateFromAED: number;
  locale: string;
  decimals: number;
  source?: string;
}

const DEFAULT_CURRENCY: CurrencyInfo = {
  code: "OMR",
  symbol: "OMR",
  name: "Omani Rial",
  rateFromAED: 0.10489,
  locale: "en-OM",
  decimals: 3,
  source: "fallback",
};

const THREE_DECIMAL_CURRENCIES = new Set(["OMR", "KWD", "BHD"]);

const CURRENCY_LOCALE_BY_CODE: Record<string, string> = {
  AED: "en-AE",
  BHD: "en-BH",
  EUR: "en-IE",
  GBP: "en-GB",
  INR: "en-IN",
  KWD: "en-KW",
  OMR: "en-OM",
  PKR: "en-PK",
  QAR: "en-QA",
  SAR: "en-SA",
  USD: "en-US",
};

function persistCountryContext(countryCode: string) {
  if (typeof window === "undefined") return;
  const code = normalizeCountryCode(countryCode);
  if (!code) {
    localStorage.removeItem("zozi_selected_country");
    localStorage.removeItem("zozi_country_code");
    localStorage.removeItem("country_code");
    return;
  }
  localStorage.setItem("zozi_selected_country", code);
  localStorage.setItem("zozi_country_code", code);
  localStorage.setItem("country_code", code);
}

function resolveCurrencyCode(value?: string | null): string {
  return (value || DEFAULT_CURRENCY.code).toUpperCase();
}

function resolveCurrencyLocale(code: string, fallback?: string): string {
  return fallback || CURRENCY_LOCALE_BY_CODE[code] || DEFAULT_CURRENCY.locale;
}

function resolveCurrencyDecimals(code: string, fallback?: number): number {
  if (typeof fallback === "number") return fallback;
  return THREE_DECIMAL_CURRENCIES.has(code) ? 3 : 2;
}

function normalizeCurrencyInfo(value?: Partial<CurrencyInfo> | null): CurrencyInfo {
  if (!value) return DEFAULT_CURRENCY;
  const code = resolveCurrencyCode(value.code);
  return {
    code,
    symbol: value.symbol || code,
    name: value.name || code,
    rateFromAED: typeof value.rateFromAED === "number" ? value.rateFromAED : DEFAULT_CURRENCY.rateFromAED,
    locale: resolveCurrencyLocale(code, value.locale),
    decimals: resolveCurrencyDecimals(code, value.decimals),
    source: value.source || DEFAULT_CURRENCY.source,
  };
}

export function formatCurrencyAmount(
  amount: number | string | null | undefined,
  currencyOrCode?: Partial<CurrencyInfo> | string | null
): string {
  const normalizedAmount = typeof amount === "number" ? amount : Number(amount || 0);
  const currency = typeof currencyOrCode === "string"
    ? normalizeCurrencyInfo({ code: currencyOrCode })
    : normalizeCurrencyInfo(currencyOrCode || DEFAULT_CURRENCY);

  try {
    return new Intl.NumberFormat(currency.locale, {
      style: "currency",
      currency: currency.code,
      minimumFractionDigits: currency.decimals,
      maximumFractionDigits: currency.decimals,
    }).format(normalizedAmount);
  } catch {
    return `${currency.symbol} ${normalizedAmount.toFixed(currency.decimals)}`;
  }
}

function getPersistedDeliveryCountry(): string {
  if (typeof window === "undefined") return "";
  try {
    const raw = localStorage.getItem("zozi_delivery_details");
    if (!raw) return "";
    const parsed = JSON.parse(raw);
    return typeof parsed?.country === "string" ? parsed.country : "";
  } catch {
    return "";
  }
}

function inferCountryFromRuntimeHints(): string {
  if (typeof window === "undefined") return "";
  try {
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone?.toLowerCase() || "";
    if (timezone.includes("muscat")) return "OM";
    if (timezone.includes("karachi") || timezone.includes("islamabad")) return "PK";
  } catch {}

  const language = navigator.language?.toLowerCase() || "";
  if (language.includes("-pk") || language.includes("ur-pk")) return "PK";
  if (language.includes("-om") || language.includes("ar-om")) return "OM";
  return "";
}

async function fetchCurrencyContext(params: { country?: string; currency?: string }): Promise<CurrencyInfo> {
  const search = new URLSearchParams();
  if (params.country?.trim()) search.set("country", params.country.trim());
  if (params.currency?.trim()) search.set("currency", params.currency.trim().toUpperCase());

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 5000);

  try {
    const response = await apiFetch(`/currency/context?${search.toString()}`, {
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) return DEFAULT_CURRENCY;
    const data = await response.json();
    return normalizeCurrencyInfo({
      code: data.currency_code,
      symbol: data.symbol,
      name: data.name,
      rateFromAED: data.rate_from_aed,
      locale: data.locale,
      decimals: data.decimals,
      source: data.source,
    });
  } catch {
    clearTimeout(timeoutId);
    return DEFAULT_CURRENCY;
  }
}

interface CurrencyState {
  currency: CurrencyInfo;
  detected: boolean;
  selectedCountry: string;
  countryLocked: boolean;
  setCurrency: (code: string) => Promise<void>;
  setCountry: (country: string, options?: { lock?: boolean }) => Promise<void>;
  detectFromIP: () => Promise<void>;
  format: (aedAmount: number) => string;
  formatCurrent: (amount: number | string) => string;
  convert: (aedAmount: number) => number;
  toAED: (amount: number | string) => number;
}

export const useCurrencyStore = create<CurrencyState>()(
  persist(
    (set, get) => ({
      currency: DEFAULT_CURRENCY,
      detected: false,
      selectedCountry: "",
      countryLocked: false,

      setCurrency: async (code: string) => {
        try {
          const currency = await fetchCurrencyContext({ currency: code });
          set({ currency, detected: true });
        } catch {
          set({ currency: DEFAULT_CURRENCY, detected: true });
        }
      },

      setCountry: async (country: string, options?: { lock?: boolean }) => {
        const selectedCountry = normalizeCountryCode(country);
        const countryLocked = options?.lock ?? true;
        if (!selectedCountry) {
          persistCountryContext("");
          set({ selectedCountry: "", countryLocked: false });
          return;
        }

        try {
          const currency = await fetchCurrencyContext({ country: selectedCountry });
          persistCountryContext(selectedCountry);
          set({ currency, detected: true, selectedCountry, countryLocked });
        } catch {
          persistCountryContext(selectedCountry);
          set({ currency: DEFAULT_CURRENCY, detected: true, selectedCountry, countryLocked });
        }
      },

      detectFromIP: async () => {
        const persistedDeliveryCountry = getPersistedDeliveryCountry();
        if (persistedDeliveryCountry) {
          await get().setCountry(persistedDeliveryCountry, { lock: true });
          return;
        }

        const { countryLocked } = get();
        if (countryLocked) {
          set({ selectedCountry: "", countryLocked: false });
        }

        try {
          const response = await apiFetch("/api/geo", { signal: AbortSignal.timeout(4000) });
          if (!response.ok) {
            set({ currency: DEFAULT_CURRENCY, detected: true });
            return;
          }

          const data = await response.json();
          const countryCode = typeof data.country_code === "string" ? data.country_code : "";
          if (countryCode) {
            await get().setCountry(countryCode, { lock: false });
            return;
          }

          const runtimeCountry = inferCountryFromRuntimeHints();
          if (runtimeCountry) {
            await get().setCountry(runtimeCountry, { lock: false });
            return;
          }

          set({ currency: DEFAULT_CURRENCY, detected: true, selectedCountry: "", countryLocked: false });
        } catch {
          const runtimeCountry = inferCountryFromRuntimeHints();
          if (runtimeCountry) {
            await get().setCountry(runtimeCountry, { lock: false });
            return;
          }
          set({ currency: DEFAULT_CURRENCY, detected: true, selectedCountry: "", countryLocked: false });
        }
      },

      format: (aedAmount: number) => get().formatCurrent(get().convert(aedAmount)),

      formatCurrent: (amount: number | string) => formatCurrencyAmount(amount, get().currency),

      convert: (aedAmount: number) => {
        const { currency } = get();
        return Number((aedAmount * currency.rateFromAED).toFixed(currency.decimals));
      },

      toAED: (amount: number | string) => {
        const { currency } = get();
        const normalizedAmount = typeof amount === "number" ? amount : Number(amount || 0);
        if (!normalizedAmount || !currency.rateFromAED) return 0;
        return Number((normalizedAmount / currency.rateFromAED).toFixed(2));
      },
    }),
    {
      name: "zozi_currency",
      partialize: (state) => ({
        currency: state.currency,
        detected: state.detected,
        selectedCountry: state.selectedCountry,
        countryLocked: state.countryLocked,
      }),
      merge: (persisted, current) => {
        const saved = persisted as Partial<CurrencyState> | undefined;
        const normalizedSavedCountry = normalizeCountryCode(saved?.selectedCountry || "");
        if (normalizedSavedCountry) {
          persistCountryContext(normalizedSavedCountry);
        }
        return {
          ...current,
          ...saved,
          currency: normalizeCurrencyInfo(saved?.currency),
          selectedCountry: normalizedSavedCountry,
          countryLocked: saved?.countryLocked ?? false,
        };
      },
    }
  )
);
