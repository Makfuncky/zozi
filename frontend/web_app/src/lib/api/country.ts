/**
 * Country detection and resolution for multi-country storefronts.
 */

import { normalizeCountryCode } from "@shared/localization";
import { apiFetch } from "./client";

export const STORAGE_KEY = "zozi_detected_country";

// ── Auto-detected country from backend middleware headers ────────────────

let _autoDetectedCountry: string | null = null;

export function setAutoDetectedCountry(code: string | null): void {
  _autoDetectedCountry = code;
  if (code && typeof window !== "undefined") {
    try {
      localStorage.setItem(STORAGE_KEY, code);
    } catch {
      // ignore
    }
  }
}

export function getAutoDetectedCountry(): string | null {
  return _autoDetectedCountry;
}

// ── Country code normalization and selection ─────────────────────────────

export function getSelectedCountryCode(): string | null {
  if (typeof window === "undefined") return null;

  const persistedCurrencyCountry = (() => {
    try {
      const raw = window.localStorage.getItem("zozi_currency");
      if (!raw) return "";
      const parsed = JSON.parse(raw);
      const selectedCountry = parsed?.state?.selectedCountry ?? parsed?.selectedCountry;
      return normalizeCountryCode(selectedCountry);
    } catch {
      return "";
    }
  })();

  const persistedDeliveryCountry = (() => {
    try {
      const raw = window.localStorage.getItem("zozi_delivery_details");
      if (!raw) return "";
      const parsed = JSON.parse(raw);
      return normalizeCountryCode(parsed?.country);
    } catch {
      return "";
    }
  })();

  const keys = [
    "zozi_selected_country",
    "zozi_admin_country",
    "zozi_country_code",
    "country_code",
  ];

  for (const key of keys) {
    const value = normalizeCountryCode(window.localStorage.getItem(key));
    if (value) return value;
  }

  if (persistedCurrencyCountry) return persistedCurrencyCountry;
  if (persistedDeliveryCountry) return persistedDeliveryCountry;

  return null;
}

// ── Public API ──────────────────────────────────────────────────────────

/**
 * Detect the user's country from their IP address via backend middleware headers.
 */
export async function detectCountryFromIP(): Promise<string | null> {
  if (typeof window === "undefined") return null;

  const existing = getAutoDetectedCountry();
  if (existing) return existing;

  try {
    const res = await apiFetch("/api/health", {
      method: "GET",
      headers: { "Accept": "application/json" },
    });

    const detectedCountry = res.headers.get("X-Country-Code");
    if (detectedCountry) {
      setAutoDetectedCountry(detectedCountry);
      return detectedCountry;
    }
  } catch (error) {
    console.debug("Geo-detection failed:", error);
  }

  return null;
}

/**
 * Get the effective country code for the current session.
 * Priority: URL param > localStorage > auto-detected > null
 */
export function getEffectiveCountryCode(): string | null {
  if (typeof window !== "undefined") {
    const urlParams = new URLSearchParams(window.location.search);
    const countryParam = urlParams.get("country");
    if (countryParam) {
      const normalized = countryParam.toUpperCase();
      if (/^[A-Z]{2}$/.test(normalized)) return normalized;
    }
  }

  const selectedCountry = getSelectedCountryCode();
  if (selectedCountry) return selectedCountry;

  const autoDetected = getAutoDetectedCountry();
  if (autoDetected) return autoDetected;

  return null;
}
