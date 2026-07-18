import React from "react";
import TestRenderer, { act } from "react-test-renderer";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

type CountryContextValue = {
  countryCode: string;
  isHydrated: boolean;
  setCountryCode: (countryCode: string) => Promise<void>;
  clearCountryCode: () => Promise<void>;
  refreshCountryCode: () => Promise<void>;
};

const mockSetCountry = jest.fn(() => Promise.resolve());
const mockDetectFromIP = jest.fn(() => Promise.resolve());

const mockCurrencyState = {
  selectedCountry: "PK",
  setCountry: mockSetCountry,
  detectFromIP: mockDetectFromIP,
};

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (selector: (state: typeof mockCurrencyState) => unknown) => selector(mockCurrencyState),
}));

import { CountryProvider, useCountry } from "@/lib/countryContext";

describe("countryContext", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("hydrates country ownership from the currency store on mount", async () => {
    const contextRef: { current: CountryContextValue | null } = { current: null };

    function Consumer() {
      contextRef.current = useCountry();
      return null;
    }

    await act(async () => {
      TestRenderer.create(
        <CountryProvider>
          <Consumer />
        </CountryProvider>,
      );
    });

    expect(mockDetectFromIP).toHaveBeenCalledTimes(1);
    expect(contextRef.current?.countryCode).toBe("PK");
    expect(contextRef.current?.isHydrated).toBe(true);
  });

  it("exposes a single setCountryCode action for callers", async () => {
    const contextRef: { current: CountryContextValue | null } = { current: null };

    function Consumer() {
      contextRef.current = useCountry();
      return null;
    }

    await act(async () => {
      TestRenderer.create(
        <CountryProvider>
          <Consumer />
        </CountryProvider>,
      );
    });

    await act(async () => {
      await contextRef.current?.setCountryCode("AE");
    });

    expect(mockSetCountry).toHaveBeenCalledWith("AE");
  });
});