/**
 * Server-side helpers for reading country code and the inbound request cookies
 * from a Next.js Server Component.
 *
 * Mirrors the client-side `getEffectiveCountryCode()` in
 * `frontend/web_app/src/lib/api/country.ts`, but does NOT touch
 * `window` or `localStorage`.
 */
import { cookies, headers } from "next/headers";

const COOKIE_KEYS = [
  "zozi_selected_country",
  "zozi_admin_country",
  "zozi_country_code",
  "country_code",
];

/** Best-effort country-code resolution for RSC fetches. Returns `null` if unset. */
export function getServerCountryCode(): string | null {
  const cookieStore = cookies();

  for (const key of COOKIE_KEYS) {
    const raw = cookieStore.get(key)?.value;
    if (!raw) continue;
    const upper = raw.toUpperCase();
    if (/^[A-Z]{2}$/.test(upper)) return upper;
  }

  // Fall back to the currency store JSON cookie.
  const currency = cookieStore.get("zozi_currency")?.value;
  if (currency) {
    try {
      const parsed = JSON.parse(currency);
      const code = parsed?.state?.selectedCountry ?? parsed?.selectedCountry;
      if (typeof code === "string" && /^[A-Z]{2}$/i.test(code)) {
        return code.toUpperCase();
      }
    } catch {
      // ignore
    }
  }

  // Fall back to the delivery-details JSON cookie.
  const delivery = cookieStore.get("zozi_delivery_details")?.value;
  if (delivery) {
    try {
      const parsed = JSON.parse(delivery);
      if (typeof parsed?.country === "string" && /^[A-Z]{2}$/i.test(parsed.country)) {
        return parsed.country.toUpperCase();
      }
    } catch {
      // ignore
    }
  }

  return null;
}

/** Pass-through helper for cookie forwarding on RSC fetches (proxying auth cookies). */
export function getServerCookieHeader(): string {
  const cookieStore = cookies();
  return cookieStore
    .getAll()
    .map((c) => `${c.name}=${c.value}`)
    .join("; ");
}

/** Optional accept-language passthrough for downstream locale hints. */
export function getServerAcceptLanguage(): string | undefined {
  return headers().get("accept-language") ?? undefined;
}
