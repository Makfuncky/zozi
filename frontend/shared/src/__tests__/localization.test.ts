import {
  COUNTRY_OPTIONS,
  CURRENCY_OPTIONS,
  LANGUAGE_OPTIONS,
  formatLocalizedDate,
  getDefaultCurrencyForCountry,
  getLocaleTag,
  isRtlLocale,
  normalizeLocale,
} from "../localization";

describe("localization constants", () => {
  it("contains at least english and arabic language options", () => {
    expect(LANGUAGE_OPTIONS.some((lang) => lang.code === "en")).toBe(true);
    expect(LANGUAGE_OPTIONS.some((lang) => lang.code === "ar")).toBe(true);
  });

  it("supports an expanded language set for web and mobile pickers", () => {
    const codes = LANGUAGE_OPTIONS.map((language) => language.code);
    expect(codes).toEqual(expect.arrayContaining(["fr", "de", "es", "hi", "ur", "tr", "fa"]));
  });

  it("contains core GCC currencies", () => {
    const codes = CURRENCY_OPTIONS.map((currency) => currency.code);
    expect(codes).toEqual(expect.arrayContaining(["OMR", "AED", "SAR", "KWD", "BHD", "QAR"]));
  });

  it("maps country code to default currency", () => {
    expect(getDefaultCurrencyForCountry("AE")).toBe("AED");
    expect(getDefaultCurrencyForCountry("om")).toBe("OMR");
    expect(getDefaultCurrencyForCountry("")).toBeNull();
    expect(getDefaultCurrencyForCountry("ZZ")).toBeNull();
  });

  it("keeps country definitions available for UI country pickers", () => {
    expect(COUNTRY_OPTIONS.length).toBeGreaterThan(5);
  });

  it("normalizes locale tags and detects rtl languages", () => {
    expect(normalizeLocale("fr-FR")).toBe("fr");
    expect(normalizeLocale("ur_PK")).toBe("ur");
    expect(getLocaleTag("fa")).toBe("fa-IR");
    expect(isRtlLocale("ar")).toBe(true);
    expect(isRtlLocale("ur")).toBe(true);
    expect(isRtlLocale("de")).toBe(false);
  });

  it("formats dates with the resolved locale tag", () => {
    expect(formatLocalizedDate("2025-03-01T00:00:00Z", "en")).toBeTruthy();
    expect(formatLocalizedDate("2025-03-01T00:00:00Z", "ar")).toBeTruthy();
  });
});