import { apiFetch } from "./api";

export type CheckoutConfig = {
  vatRate: number;
  shippingFlatRate: number;
  freeShippingThreshold: number;
};

export const DEFAULT_CHECKOUT_CONFIG: CheckoutConfig = {
  vatRate: 0.05,
  shippingFlatRate: 2,
  freeShippingThreshold: 0,
};

function normalizeNumber(value: unknown, fallback: number): number {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

export async function fetchCheckoutConfig(): Promise<CheckoutConfig> {
  try {
    const response = await apiFetch("/config/checkout");
    if (!response.ok) {
      return DEFAULT_CHECKOUT_CONFIG;
    }

    const payload = await response.json();
    return {
      vatRate: normalizeNumber(payload?.vat_rate, DEFAULT_CHECKOUT_CONFIG.vatRate),
      shippingFlatRate: normalizeNumber(payload?.shipping_flat_rate, DEFAULT_CHECKOUT_CONFIG.shippingFlatRate),
      freeShippingThreshold: normalizeNumber(payload?.free_shipping_threshold, DEFAULT_CHECKOUT_CONFIG.freeShippingThreshold),
    };
  } catch {
    return DEFAULT_CHECKOUT_CONFIG;
  }
}
