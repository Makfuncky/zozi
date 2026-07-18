import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { useCurrencyStore } from "@/lib/currencyStore";

interface CountryContextValue {
  countryCode: string;
  isHydrated: boolean;
  setCountryCode: (countryCode: string) => Promise<void>;
  clearCountryCode: () => Promise<void>;
  refreshCountryCode: () => Promise<void>;
}

const CountryContext = createContext<CountryContextValue | null>(null);

export function CountryProvider({ children }: { children: React.ReactNode }) {
  const countryCode = useCurrencyStore((state) => state.selectedCountry);
  const setCountry = useCurrencyStore((state) => state.setCountry);
  const detectFromIP = useCurrencyStore((state) => state.detectFromIP);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    let active = true;

    detectFromIP().finally(() => {
      if (active) {
        setIsHydrated(true);
      }
    });

    return () => {
      active = false;
    };
  }, [detectFromIP]);

  const value = useMemo<CountryContextValue>(
    () => ({
      countryCode,
      isHydrated,
      setCountryCode: (nextCountryCode: string) => setCountry(nextCountryCode),
      clearCountryCode: () => setCountry(""),
      refreshCountryCode: () => detectFromIP(),
    }),
    [countryCode, detectFromIP, isHydrated, setCountry],
  );

  return <CountryContext.Provider value={value}>{children}</CountryContext.Provider>;
}

export function useCountry() {
  const context = useContext(CountryContext);
  if (!context) {
    throw new Error("useCountry must be used within CountryProvider");
  }
  return context;
}