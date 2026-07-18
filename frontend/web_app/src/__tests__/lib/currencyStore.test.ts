import { useCurrencyStore } from "@/lib/currencyStore";

const OMR_CONTEXT = {
  currency_code: "OMR",
  symbol: "OMR",
  name: "Omani Rial",
  locale: "en-OM",
  decimals: 3,
  rate_from_aed: 0.10489,
  source: "geo",
};

describe("currencyStore", () => {
  beforeEach(() => {
    localStorage.clear();
    useCurrencyStore.setState({
      currency: {
        code: "AED",
        symbol: "AED",
        name: "UAE Dirham",
        rateFromAED: 1,
        locale: "en-AE",
        decimals: 2,
        source: "persisted",
      },
      detected: true,
      selectedCountry: "AE",
      countryLocked: false,
    });

    global.fetch = jest.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/geo")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ country_code: "OM" }),
        } as Response);
      }

      if (url.includes("/api/currency/context")) {
        return Promise.resolve({
          ok: true,
          json: async () => OMR_CONTEXT,
        } as Response);
      }

      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    }) as typeof fetch;
  });

  it("refreshes geo detection even when a stale detected flag is persisted", async () => {
    await useCurrencyStore.getState().detectFromIP();

    expect(global.fetch).toHaveBeenCalledWith("/api/geo", expect.any(Object));
    expect(useCurrencyStore.getState().currency.code).toBe("OMR");
    expect(useCurrencyStore.getState().selectedCountry).toBe("OM");
    expect(useCurrencyStore.getState().countryLocked).toBe(false);
  });

  it("keeps a delivery-country selection authoritative", async () => {
    localStorage.setItem(
      "zozi_delivery_details",
      JSON.stringify({ country: "AE" })
    );
    useCurrencyStore.setState({
      currency: {
        code: "OMR",
        symbol: "OMR",
        name: "Omani Rial",
        rateFromAED: 0.10489,
        locale: "en-OM",
        decimals: 3,
        source: "fallback",
      },
      detected: true,
      selectedCountry: "OM",
      countryLocked: false,
    });

    await useCurrencyStore.getState().detectFromIP();

    expect(useCurrencyStore.getState().selectedCountry).toBe("AE");
    expect(useCurrencyStore.getState().countryLocked).toBe(true);
  });

  it("normalizes full country names to ISO country codes", async () => {
    await useCurrencyStore.getState().setCountry("Pakistan", { lock: true });

    expect(useCurrencyStore.getState().selectedCountry).toBe("PK");
    expect(localStorage.getItem("zozi_selected_country")).toBe("PK");
    expect(localStorage.getItem("zozi_country_code")).toBe("PK");
  });
});
