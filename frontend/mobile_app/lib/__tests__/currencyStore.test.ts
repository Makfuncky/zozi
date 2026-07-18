/**
 * currencyStore.test.ts
 * Tests currency normalisation, conversion helpers, format utilities,
 * and the Zustand store actions (setCurrency, setCountry).
 */

const mockApiFetch = jest.fn();
const mockGetItemAsync = jest.fn();
const mockSetItemAsync = jest.fn();
const mockDeleteItemAsync = jest.fn();

jest.mock("react-native", () => ({ Platform: { OS: "android" } }));
jest.mock("expo-secure-store", () => ({
  getItemAsync: (...args: unknown[]) => mockGetItemAsync(...args),
  setItemAsync: (...args: unknown[]) => mockSetItemAsync(...args),
  deleteItemAsync: (...args: unknown[]) => mockDeleteItemAsync(...args),
}));
jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
  login: jest.fn(),
  logout: jest.fn(),
  getMe: jest.fn(),
  register: jest.fn(),
  restoreTokens: jest.fn().mockResolvedValue(false),
  getStoredRefreshToken: jest.fn().mockResolvedValue(null),
  refreshAccessToken: jest.fn(),
  tokenAdapter: { clearAccessToken: jest.fn(), clearRefreshToken: jest.fn() },
}));

// Mock global fetch used by detectCountryFromIP
global.fetch = jest.fn().mockRejectedValue(new Error("network unavailable"));

import { useCurrencyStore } from "@/lib/currencyStore";
import { __resetCountrySelectionState } from "@/lib/countrySelection";

const OMR_DEFAULTS = {
  code: "OMR",
  symbol: "OMR",
  rateFromAED: 0.10489,
  decimals: 3,
};

beforeEach(() => {
  jest.clearAllMocks();
  __resetCountrySelectionState();
  // Reset store to defaults
  useCurrencyStore.setState({
    currency: { ...OMR_DEFAULTS, name: "Omani Rial", locale: "en-OM", source: "fallback" },
    detected: false,
    selectedCountry: "",
  });
});

// ── Default currency ──────────────────────────────────────────────────────────

describe("currencyStore — defaults", () => {
  it("starts with OMR as default currency", () => {
    const { currency } = useCurrencyStore.getState();
    expect(currency.code).toBe("OMR");
    expect(currency.decimals).toBe(3);
  });

  it("convert() multiplies AED amount by rateFromAED", () => {
    const { convert } = useCurrencyStore.getState();
    // 100 AED × 0.10489 = ~10.489 OMR
    expect(convert(100)).toBeCloseTo(10.489, 2);
  });

  it("convert(0) returns 0", () => {
    expect(useCurrencyStore.getState().convert(0)).toBe(0);
  });

  it("toAED() is the inverse of convert()", () => {
    const { convert, toAED } = useCurrencyStore.getState();
    const aed = 150;
    const converted = convert(aed);
    const backToAED = toAED(converted);
    expect(backToAED).toBeCloseTo(aed, 0);
  });

  it("toAED() accepts string amounts", () => {
    const amount = useCurrencyStore.getState().toAED("10.489");
    expect(amount).toBeGreaterThan(90);
  });
});

// ── formatCurrent ─────────────────────────────────────────────────────────────

describe("currencyStore — formatCurrent", () => {
  it("formats a numeric amount using defaults without throwing", () => {
    const result = useCurrencyStore.getState().formatCurrent(9.999);
    expect(typeof result).toBe("string");
    expect(result.length).toBeGreaterThan(0);
  });

  it("formatCurrent handles string input", () => {
    const result = useCurrencyStore.getState().formatCurrent("25.5");
    expect(typeof result).toBe("string");
  });

  it("formatCurrent('') returns formatted 0", () => {
    const result = useCurrencyStore.getState().formatCurrent("");
    expect(typeof result).toBe("string");
  });
});

// ── setCurrency ────────────────────────────────────────────────────────────────

describe("currencyStore — setCurrency", () => {
  it("updates currency from API response on success", async () => {
    mockApiFetch.mockResolvedValueOnce({
      currency_code: "USD",
      symbol: "$",
      name: "US Dollar",
      locale: "en-US",
      decimals: 2,
      rate_from_aed: 0.2723,
      source: "api",
    });

    await useCurrencyStore.getState().setCurrency("USD");

    const { currency } = useCurrencyStore.getState();
    expect(currency.code).toBe("USD");
    expect(currency.symbol).toBe("$");
    expect(currency.decimals).toBe(2);
  });

  it("falls back to OMR defaults if API throws", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("Network error"));

    await useCurrencyStore.getState().setCurrency("XYZ");

    const { currency, detected } = useCurrencyStore.getState();
    expect(currency.code).toBe("OMR");
    expect(detected).toBe(true);
  });
});

// ── setCountry ────────────────────────────────────────────────────────────────

describe("currencyStore — setCountry", () => {
  it("sets selectedCountry and fetches matching currency", async () => {
    mockApiFetch.mockResolvedValueOnce({
      currency_code: "SAR",
      symbol: "SAR",
      name: "Saudi Riyal",
      locale: "ar-SA",
      decimals: 2,
      rate_from_aed: 0.9838,
      source: "api",
    });

    await useCurrencyStore.getState().setCountry("SA");

    const { selectedCountry, currency } = useCurrencyStore.getState();
    expect(selectedCountry).toBe("SA");
    expect(currency.code).toBe("SAR");
    expect(mockSetItemAsync).toHaveBeenCalledWith("zozi_selected_country", "SA");
  });

  it("ignores blank country input without calling API", async () => {
    await useCurrencyStore.getState().setCountry("   ");

    expect(mockApiFetch).not.toHaveBeenCalled();
    expect(useCurrencyStore.getState().selectedCountry).toBe("");
    expect(mockDeleteItemAsync).toHaveBeenCalledWith("zozi_selected_country");
  });

  it("uses OMR fallback when API fails for setCountry", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("timeout"));

    await useCurrencyStore.getState().setCountry("AE");

    expect(useCurrencyStore.getState().currency.code).toBe("OMR");
    expect(useCurrencyStore.getState().detected).toBe(true);
  });
});

// ── KWD / BHD 3-decimal handling ─────────────────────────────────────────────

describe("currencyStore — 3-decimal currencies", () => {
  it("KWD gets 3 decimals when API omits decimals field", async () => {
    mockApiFetch.mockResolvedValueOnce({
      currency_code: "KWD",
      symbol: "KD",
      name: "Kuwaiti Dinar",
      locale: "ar-KW",
      rate_from_aed: 0.083,
      source: "api",
      // NOTE: decimals intentionally omitted — should default to 3
    });

    await useCurrencyStore.getState().setCurrency("KWD");
    expect(useCurrencyStore.getState().currency.decimals).toBe(3);
  });
});
