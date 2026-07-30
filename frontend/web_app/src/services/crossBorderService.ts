import { apiFetch, parseJsonResponse } from "@/lib/api";

export interface CrossBorderSession {
  sessionId: string;
  customerId: number;
  originalCountryCode: string;
  currentCountryCode: string;
  shoppingHistory: Array<{
    countryCode: string;
    currency: string;
    totalSpent: number;
    orderCount: number;
  }>;
}

export interface CurrencyConversion {
  fromCurrency: string;
  toCurrency: string;
  amount: number;
  convertedAmount: number;
  rate: number;
}

/**
 * Service for cross-border customer detection and currency/tax handling
 */
export const crossBorderService = {
  /**
   * Get customer's cross-border shopping history
   */
  getCustomerSession: async (customerId: number): Promise<CrossBorderSession | null> => {
    const response = await apiFetch(`/cross-border/session/${customerId}`);
    if (!response.ok) return null;
    return parseJsonResponse(response);
  },

  /**
   * Convert amount between currencies
   */
  convertCurrency: async (
    fromCurrency: string,
    toCurrency: string,
    amount: number
  ): Promise<CurrencyConversion | null> => {
    const response = await apiFetch(
      `/cross-border/convert?from=${fromCurrency}&to=${toCurrency}&amount=${amount}`
    );
    if (!response.ok) return null;
    return parseJsonResponse(response);
  },

  /**
   * Get tax calculation for a specific country
   */
  calculateTax: async (
    countryCode: string,
    amount: number,
    categoryId?: number
  ): Promise<{ taxAmount: number; taxRate: number; taxName: string } | null> => {
    const params = new URLSearchParams({ country_code: countryCode, amount: String(amount) });
    if (categoryId) params.append("category_id", String(categoryId));

    const response = await apiFetch(`/cross-border/tax/calculate?${params.toString()}`);
    if (!response.ok) return null;
    return parseJsonResponse(response);
  },
};
