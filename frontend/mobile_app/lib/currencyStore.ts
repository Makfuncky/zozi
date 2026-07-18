import { create } from "zustand";
import { Platform } from "react-native";
import { apiFetch } from "@/lib/api";
import { getPersistedSelectedCountryCode, normalizeCountryCode, persistSelectedCountryCode, setInMemorySelectedCountryCode } from "@/lib/countrySelection";

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

function normalizeCurrencyInfo(value?: Partial<CurrencyInfo> | null): CurrencyInfo {
  if (!value) return DEFAULT_CURRENCY;
  const code = (value.code || DEFAULT_CURRENCY.code).toUpperCase();
  return {
    code,
    symbol: value.symbol || code,
    name: value.name || code,
    rateFromAED: typeof value.rateFromAED === "number" ? value.rateFromAED : DEFAULT_CURRENCY.rateFromAED,
    locale: value.locale || DEFAULT_CURRENCY.locale,
    decimals:
      typeof value.decimals === "number"
        ? value.decimals
        : code === "OMR" || code === "KWD" || code === "BHD"
        ? 3
        : 2,
    source: value.source || DEFAULT_CURRENCY.source,
  };
}

async function fetchCurrencyContext(params: { country?: string; currency?: string }): Promise<CurrencyInfo> {
  try {
    const search = new URLSearchParams();
    if (params.country?.trim()) search.set("country", params.country.trim());
    if (params.currency?.trim()) search.set("currency", params.currency.trim().toUpperCase());
    const query = search.toString();

    const response = await apiFetch<{ currency_code: string; symbol: string; name: string; locale: string; decimals: number; rate_from_aed: number; source: string }>(
      `/currency/context${query ? `?${query}` : ""}`,
      {
        method: "GET",
        skipAuth: true,
      }
    );

    return normalizeCurrencyInfo({
      code: response.currency_code,
      symbol: response.symbol,
      name: response.name,
      locale: response.locale,
      decimals: response.decimals,
      rateFromAED: response.rate_from_aed,
      source: response.source,
    });
  } catch {
    return DEFAULT_CURRENCY;
  }
}

async function detectCountryFromIP(): Promise<string | null> {
  if (Platform.OS === "web") {
    try {
      const locale = Intl.DateTimeFormat().resolvedOptions().locale || globalThis.navigator?.language || "";
      const match = locale.match(/[-_]([A-Za-z]{2})\b/);
      if (match?.[1]) {
        return match[1].toUpperCase();
      }
    } catch {
      return null;
    }

    return null;
  }

  try {
    const response = await fetch("https://ipapi.co/json/", { cache: "no-store" });
    if (!response.ok) return null;
    const data = await response.json();
    if (typeof data.country_code === "string" && data.country_code.trim()) {
      return data.country_code.trim();
    }
    return null;
  } catch {
    return null;
  }
}

interface CurrencyState {
  currency: CurrencyInfo;
  detected: boolean;
  selectedCountry: string;
  setCurrency: (code: string) => Promise<void>;
  setCountry: (country: string) => Promise<void>;
  detectFromIP: () => Promise<void>;
  format: (aedAmount: number) => string;
  formatCurrent: (amount: number | string) => string;
  convert: (aedAmount: number) => number;
  toAED: (amount: number | string) => number;
}

export const useCurrencyStore = create<CurrencyState>((set, get) => ({
  currency: DEFAULT_CURRENCY,
  detected: false,
  selectedCountry: "",

  setCurrency: async (code: string) => {
    try {
      const currency = await fetchCurrencyContext({ currency: code });
      set({ currency, detected: true });
    } catch {
      set({ currency: DEFAULT_CURRENCY, detected: true });
    }
  },

  setCountry: async (country: string) => {
    const selectedCountry = normalizeCountryCode(country);
    if (!selectedCountry) {
      setInMemorySelectedCountryCode(null);
      await persistSelectedCountryCode(null);
      set({ selectedCountry: "" });
      return;
    }

    try {
      const currency = await fetchCurrencyContext({ country: selectedCountry });
      setInMemorySelectedCountryCode(selectedCountry);
      await persistSelectedCountryCode(selectedCountry);
      set({ currency, detected: true, selectedCountry });
    } catch {
      setInMemorySelectedCountryCode(selectedCountry);
      await persistSelectedCountryCode(selectedCountry);
      set({ currency: DEFAULT_CURRENCY, detected: true, selectedCountry });
    }
  },

  detectFromIP: async () => {
    if (get().detected) return;

    const persistedCountry = get().selectedCountry || await getPersistedSelectedCountryCode();
    if (persistedCountry) {
      await get().setCountry(persistedCountry);
      return;
    }

    const countryCode = await detectCountryFromIP();
    if (countryCode) {
      await get().setCountry(countryCode);
      return;
    }

    const currency = await fetchCurrencyContext({});
    set({ currency, detected: true });
  },

  format: (aedAmount: number) => get().formatCurrent(get().convert(aedAmount)),

  formatCurrent: (amount: number | string) => {
    const { currency } = get();
    const normalizedAmount = typeof amount === "number" ? amount : Number(amount || 0);
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
  },

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
}));
