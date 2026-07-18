/**
 * Cross-border service for customer geo-detection and country-specific settings.
 * Handles IP-based country detection, currency/tax switching, and localization.
 */

import { apiFetch } from "@/lib/api";
import { setAutoDetectedCountry, getAutoDetectedCountry, STORAGE_KEY } from "@/lib/api";

export interface CountrySettings {
  code: string;
  name: string;
  currency: string;
  currency_symbol: string;
  tax_type: string;
  tax_rate: number;
  language: string;
  rtl_enabled: boolean;
}

/**
 * Get stored detected country from localStorage
 */
export function getStoredCountry(): string | null {
  if (typeof window === "undefined") return null;
  try {
    // First check the in-memory auto-detected country
    const autoDetected = getAutoDetectedCountry();
    if (autoDetected) return autoDetected;
    
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

/**
 * Store detected country in localStorage
 */
export function setStoredCountry(code: string): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, code);
  } catch {
    // ignore
  }
}

/**
 * Clear stored country
 */
export function clearStoredCountry(): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
}

/**
 * Initialize country detection from backend middleware headers
 * The backend adds X-Country-Code header to responses automatically
 */
export function initCountryDetection(): string | null {
  const detected = getAutoDetectedCountry();
  if (detected) {
    setStoredCountry(detected);
    return detected;
  }
  
  const stored = getStoredCountry();
  if (stored) {
    setAutoDetectedCountry(stored);
    return stored;
  }
  
  return null;
}

/**
 * Get country settings from the backend
 */
export async function getCountrySettings(countryCode: string): Promise<CountrySettings | null> {
  try {
    const response = await apiFetch(`/admin/countries/${countryCode}`);
    if (!response.ok) return null;
    
    const data = await response.json();
    return {
      code: data.code || countryCode,
      name: data.name || "",
      currency: data.currency || "USD",
      currency_symbol: data.currency_symbol || "$",
      tax_type: data.tax_type || "VAT",
      tax_rate: data.tax_rate || 0,
      language: data.language || "en",
      rtl_enabled: false, // Will be determined by language
    };
  } catch (error) {
    console.error("Failed to get country settings:", error);
    return null;
  }
}

/**
 * Get the effective country code for the current session
 * Priority: URL param > Stored > Detected > Default
 */
export function getEffectiveCountryCode(urlCountry?: string | null): string | null {
  // 1. URL parameter takes precedence
  if (urlCountry) {
    return urlCountry.toUpperCase();
  }

  // 2. Check stored country
  const stored = getStoredCountry();
  if (stored) {
    return stored;
  }

  // 3. Backend middleware will set X-Country-Code header
  // This is handled in api.ts and stored via getSelectedCountryCode()
  
  return null;
}

/**
 * Get currency symbol for a country
 */
export function getCurrencySymbol(currency: string): string {
  const symbols: Record<string, string> = {
    USD: "$",
    EUR: "€",
    GBP: "£",
    SAR: "SR",
    AED: "د.إ",
    OMR: "ر.ع.",
    KWD: "د.ك",
    BHD: "ب.ح.",
    QAR: "ق.ر",
    JOD: "د.ج",
    EGP: "ج.م",
  };
  return symbols[currency] || currency;
}

/**
 * Get tax calculation for an amount in a specific country
 */
export async function calculateTax(
  countryCode: string,
  amount: number,
  category?: string
): Promise<{
  tax_amount: number;
  tax_rate: number;
  tax_name: string;
  total_amount: number;
} | null> {
  try {
    const response = await apiFetch(`/admin/countries/${countryCode}/preview-tax`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount, category }),
    });
    
    if (!response.ok) return null;
    
    const data = await response.json();
    return {
      tax_amount: data.tax_amount || 0,
      tax_rate: data.tax_rate || 0,
      tax_name: data.tax_name || "Tax",
      total_amount: data.total_amount || amount,
    };
  } catch (error) {
    console.error("Tax calculation failed:", error);
    return null;
  }
}

/**
 * Get available payment gateways for a country
 */
export async function getAvailablePaymentGateways(countryCode: string): Promise<Array<{
  gateway_id: string;
  name: string;
  type: string;
  enabled: boolean;
  supports_cod: boolean;
}>> {
  try {
    const response = await apiFetch(`/admin/countries/${countryCode}/payment-gateways`);
    if (!response.ok) return [];
    
    const data = await response.json();
    return (data.gateways || [])
      .filter((g: any) => g.enabled)
      .map((g: any) => ({
        gateway_id: g.gateway_id,
        name: g.name,
        type: g.type,
        enabled: g.enabled,
        supports_cod: g.supports_cod || false,
      }));
  } catch (error) {
    console.error("Failed to get payment gateways:", error);
    return [];
  }
}

/**
 * Get available delivery partners for a country
 */
export async function getAvailableDeliveryPartners(countryCode: string): Promise<Array<{
  provider_id: string;
  name: string;
  enabled: boolean;
  sla_standard_days: string;
  sla_express_days: string;
}>> {
  try {
    const response = await apiFetch(`/admin/countries/${countryCode}/logistics-providers`);
    if (!response.ok) return [];
    
    const data = await response.json();
    return (data.providers || [])
      .filter((p: any) => p.enabled)
      .map((p: any) => ({
        provider_id: p.provider_id,
        name: p.name,
        enabled: p.enabled,
        sla_standard_days: p.sla_standard_days || "3-5",
        sla_express_days: p.sla_express_days || "1-2",
      }));
  } catch (error) {
    console.error("Failed to get delivery partners:", error);
    return [];
  }
}

/**
 * Format price with currency for a specific country
 */
export function formatPrice(amount: number, currency: string, symbol?: string): string {
  const currencySymbol = symbol || getCurrencySymbol(currency);
  return `${currencySymbol}${amount.toFixed(2)}`;
}

/**
 * Check if a category is tax-exempt in a country
 */
export function isCategoryTaxExempt(categorySlug: string, exemptCategories: string[]): boolean {
  return exemptCategories.some(
    (cat) => cat.toLowerCase() === categorySlug.toLowerCase()
  );
}
