import { useState, useEffect, useCallback } from "react";
import { apiFetch, getEffectiveCountryCode, getAutoDetectedCountry } from "@/lib/api";
import { parseJsonResponse } from "@/lib/api";

export interface CrossBorderConfig {
  country_code: string;
  currency: string;
  currency_symbol: string | null;
  tax_rate: number;
  tax_name: string;
  tax_inclusive: boolean;
  shipping_cost: number;
  delivery_estimate_days: string;
  is_cross_border: boolean;
}

interface UseCrossBorderResult {
  config: CrossBorderConfig | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * Hook for managing cross-border checkout logic.
 * Fetches country-specific configuration for tax, currency, and shipping.
 */
export function useCrossBorder(countryCode?: string | null): UseCrossBorderResult {
  const [config, setConfig] = useState<CrossBorderConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchConfig = useCallback(async (code: string) => {
    if (!code) {
      setConfig(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Use the public country endpoint for cross-border info
      const response = await apiFetch(`/countries/${code}`, {
        method: "GET",
      });

      const data = await parseJsonResponse(response);

      if (!response.ok) {
        throw new Error(data?.detail || "Failed to fetch country config");
      }

      const crossBorderConfig: CrossBorderConfig = {
        country_code: data.code || code,
        currency: data.currency || "USD",
        currency_symbol: data.currency_symbol || null,
        tax_rate: data.tax_rate ?? 0,
        tax_name: data.tax_name || "Tax",
        tax_inclusive: data.tax_inclusive ?? false,
        shipping_cost: data.shipping_cost ?? 0,
        delivery_estimate_days: data.delivery_estimate_days ?? "3-5",
        is_cross_border: data.is_cross_border ?? false,
      };

      setConfig(crossBorderConfig);
    } catch (err) {
      // Use fallback config on error
      setConfig(DEFAULT_CROSS_BORDER_CONFIG);
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, []);

  const refetch = useCallback(async () => {
    const code = countryCode || getEffectiveCountryCode();
    if (code) {
      await fetchConfig(code);
    }
  }, [countryCode, fetchConfig]);

  useEffect(() => {
    const code = countryCode || getEffectiveCountryCode();
    fetchConfig(code || "");
  }, [countryCode, fetchConfig]);

  return { config, loading, error, refetch };
}

/**
 * Calculate tax for a given amount and country.
 */
export function calculateTax(amount: number, taxRate: number, inclusive: boolean = false): {
  taxAmount: number;
  totalAmount: number;
  netAmount: number;
} {
  if (inclusive) {
    // Tax is included in the price
    const netAmount = amount / (1 + taxRate);
    const taxAmount = amount - netAmount;
    return { taxAmount, totalAmount: amount, netAmount };
  } else {
    // Tax is added to the price
    const taxAmount = amount * taxRate;
    return { taxAmount, totalAmount: amount + taxAmount, netAmount: amount };
  }
}

/**
 * Format a price with the appropriate currency symbol.
 */
export function formatPrice(amount: number, currency: string, symbol: string | null = null): string {
  const options: Intl.NumberFormatOptions = {
    style: "currency",
    currency: currency,
  };
  const formatter = new Intl.NumberFormat("en-US", options);
  const defaultFormatted = formatter.format(amount);
  if (symbol) {
    // Replace the default symbol with the provided one while keeping the numeric formatting.
    return defaultFormatted.replace(/^[^\d]*/, symbol);
  }
  return defaultFormatted;
}

/**
 * Get the currency symbol for a country code.
 */
export function getCurrencySymbol(currency: string): string {
  const symbols: Record<string, string> = {
    USD: "$",
    EUR: "€",
    GBP: "£",
    SAR: "SR",
    AED: "DH",
    KWD: "KD",
    BHD: "BD",
    OMR: "RO",
    QAR: "QR",
  };
  return symbols[currency] || currency;
}

/**
 * Default fallback configuration for cross-border when API fails.
 */
export const DEFAULT_CROSS_BORDER_CONFIG: CrossBorderConfig = {
  country_code: "US",
  currency: "USD",
  currency_symbol: "$",
  tax_rate: 0,
  tax_name: "Tax",
  tax_inclusive: false,
  shipping_cost: 0,
  delivery_estimate_days: "3-5",
  is_cross_border: true,
};

/**
 * Get the detected country for display purposes.
 */
export function getDisplayCountry(): string | null {
  return getAutoDetectedCountry();
}
