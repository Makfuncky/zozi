/**
 * money.ts — shared currency formatting and arithmetic helpers.
 * Works in both web (Next.js) and mobile (Expo/React Native) environments.
 */

import { getLocaleTag } from "./localization";

/**
 * Round a number to 2 decimal places using ROUND_HALF_UP semantics.
 */
export function roundMoney(value: number): number {
  return Math.round((value + Number.EPSILON) * 100) / 100;
}

/**
 * Convert a decimal amount to minor units (e.g. cents).
 * @param value - The amount in major units (e.g. 9.99 USD)
 * @param factor - Minor unit factor; default 100 for most currencies
 */
export function toMinorUnits(value: number, factor = 100): number {
  return Math.round(roundMoney(value) * factor);
}

/**
 * Convert minor units back to major units (e.g. cents → dollars).
 */
export function fromMinorUnits(cents: number, factor = 100): number {
  return roundMoney(cents / factor);
}

/**
 * Format a number as a currency string using the browser/native Intl APIs.
 * Falls back to a simple string if Intl is unavailable.
 *
 * @param value   - Amount in major units
 * @param currency - ISO 4217 currency code (e.g. "USD", "KWD")
 * @param locale   - BCP 47 locale string (e.g. "en-US")
 */
export function formatMoney(
  value: number,
  currency = "USD",
  locale = "en-US"
): string {
  const intlLocale = getLocaleTag(locale);
  try {
    const fractionDigits = new Intl.NumberFormat(intlLocale, {
      style: "currency",
      currency,
    }).resolvedOptions().maximumFractionDigits;

    return new Intl.NumberFormat(intlLocale, {
      style: "currency",
      currency,
      minimumFractionDigits: fractionDigits,
      maximumFractionDigits: fractionDigits,
    }).format(value);
  } catch {
    return `${currency} ${roundMoney(value).toFixed(2)}`;
  }
}

/**
 * Add two monetary values safely (avoids floating-point drift).
 */
export function addMoney(a: number, b: number): number {
  return roundMoney(a + b);
}

/**
 * Subtract b from a safely.
 */
export function subtractMoney(a: number, b: number): number {
  return roundMoney(a - b);
}

/**
 * Multiply a monetary value by a quantity, rounded to 2dp.
 */
export function multiplyMoney(amount: number, qty: number): number {
  return roundMoney(amount * qty);
}

/**
 * Apply a percentage discount to an amount.
 * @param amount    - Original price
 * @param pctOff    - Discount percentage (0–100)
 */
export function applyPercentageDiscount(amount: number, pctOff: number): number {
  const discount = roundMoney((amount * pctOff) / 100);
  return Math.max(0, roundMoney(amount - discount));
}

/**
 * Apply a fixed discount, floor at 0.
 */
export function applyFixedDiscount(amount: number, fixedOff: number): number {
  return Math.max(0, roundMoney(amount - fixedOff));
}

/**
 * Calculate the total for a list of line items.
 */
export function calcTotal(items: { price: number; quantity: number }[]): number {
  return items.reduce((sum, item) => addMoney(sum, multiplyMoney(item.price, item.quantity)), 0);
}
