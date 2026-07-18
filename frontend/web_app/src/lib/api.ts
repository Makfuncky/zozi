/**
 * api.ts — thin wrapper around fetch for the ZOZI backend API.
 *
 * Auth token strategy (XSS hardening):
 *   - The ACCESS token is stored only in memory (module-level variable).
 *     It is NEVER written to localStorage or a non-httpOnly cookie, so it
 *     cannot be exfiltrated by injected scripts.
 *   - The REFRESH token lives in an httpOnly cookie set by the backend and
 *     is never readable from JavaScript.
 *   - `zozi_has_session` is a non-sensitive boolean flag in localStorage that
 *     tells the frontend whether to attempt a silent refresh on page load.
 *     It carries no secret material.
 */

import {
  buildShortGetCacheKey,
  createResponseRequestCache,
  DEFAULT_SHORT_GET_TTL_MS,
  shouldUseShortGetCache,
} from "@shared/requestCache";

// Default timeout for API requests (in milliseconds)
export const DEFAULT_API_TIMEOUT_MS = 30000;

// Use relative URL for same-origin requests to avoid CORS issues
// when frontend and API are on different hostnames (localhost vs 127.0.0.1).
// Local hosts always target 127.0.0.1:8000 (IPv4, matching the backend bind).
// LAN/remote hosts (e.g. 192.168.x.x:3000) target the SAME host on :8000 so the
// request stays same-origin and never hits a CORS preflight failure.
const _API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
const _IS_LOCAL = (h: string) => h === "localhost" || h === "127.0.0.1" || h === "[::1]";
export const API_URL = typeof window !== "undefined"
  ? (_IS_LOCAL(window.location.hostname)
      ? _API_URL
      : `${window.location.protocol}//${window.location.hostname}:8000`)
  : _API_URL;
const responseCache = createResponseRequestCache();

// Storage key for auto-detected country
export const STORAGE_KEY = "zozi_detected_country";

function resolveRequestUrl(path: string, body?: BodyInit | null): string {
  if (path.startsWith("http")) return path;
  // All requests (including FormData uploads) go through the same-origin
  // Next.js /__api proxy so the browser never makes a cross-origin,
  // credentialed fetch to 127.0.0.1:8000. This sidesteps CORS preflight
  // failures and the localhost→IPv6 / 127.0.0.1→IPv4 mismatch that blocks
  // direct uploads in some browsers. The proxy forwards server-side to the
  // backend (no browser CORS involved).
  if (!path.startsWith("/api") && !path.startsWith("/auth") && !path.startsWith("/admin")) return `/__api${path}`;
  return path;
}

// ── In-memory access token (not exposed to localStorage / sessionStorage) ────

let _accessToken: string | null = null;

/** Set the in-memory access token after a successful login or token refresh. */
export function setAccessToken(token: string | null): void {
  _accessToken = token;
  responseCache.invalidateAll();
}

/** Read the current in-memory access token. */
export function getAccessToken(): string | null {
  return _accessToken;
}

/** Clear the in-memory access token on logout / 401. */
export function clearAccessToken(): void {
  _accessToken = null;
  responseCache.invalidateAll();
}

// ── Error helpers ─────────────────────────────────────────────────────────────

/**
 * Extract a user-friendly error message from an API response body.
 */
export function getErrorMessage(data: any): string {
  if (typeof data.detail === "string") {
    return data.detail;
  }
  if (Array.isArray(data.detail) && data.detail.length > 0) {
    // Pydantic validation error: [{"loc": [...], "msg": "...", "type": "..."}]
    return data.detail[0].msg || "Validation error";
  }
  if (data.message) {
    return data.message;
  }
  // slowapi rate-limit responses use { "error": "N per 1 minute" }
  if (typeof data.error === "string") {
    return "Too many attempts. Please wait a moment and try again.";
  }
  return "An error occurred";
}

/**
 * Enhanced error handler that integrates with toast notifications
 */
export function handleApiError(error: any, context?: string): void {
  let message = "An unknown error occurred";

  if (error instanceof Response) {
    message = `HTTP ${error.status}: ${error.statusText || "Request failed"}`;
  } else if (error instanceof Error) {
    message = error.message;
  } else if (typeof error === "string") {
    message = error;
  } else if (error && typeof error === "object") {
    message = getErrorMessage(error);
  }

  // Log to console with context
  console.error(`[API Error${context ? ` - ${context}` : ""}]: ${message}`, error);

  // In production, you could send this to an error reporting service
  // if (process.env.NODE_ENV === 'production') {
  //   reportError(error, { context, message });
  // }
}

// ── apiFetch ──────────────────────────────────────────────────────────────────

/**
 * Read the `csrf_token` cookie value that the backend issues on first load.
 * Returns an empty string in SSR contexts (no document).
 */
function getCsrfToken(): string {
  if (typeof document === "undefined") return "";
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : "";
}

/** Methods that mutate server state and therefore need CSRF protection. */
const CSRF_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

// When using Next.js Fast Refresh, module-level state (like `_accessToken`) can be
// reset while React state (user logged-in) persists. In that case, we still have
// a valid session (refresh token cookie), so we attempt a silent refresh before
// making an authenticated request. We also reuse the same flow when a request
// returns 401 so background jobs and long-lived tabs can recover from expired
// access tokens without forcing an immediate logout.
let _refreshPromise: Promise<RefreshResult> | null = null;

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  const [, payloadSegment] = token.split(".");
  if (!payloadSegment) return null;

  try {
    const normalized = payloadSegment.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
    const decoded = atob(padded);
    const payload = JSON.parse(decoded);
    return payload && typeof payload === "object" ? (payload as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

function isAccessTokenExpiringSoon(token: string, skewSeconds = 30): boolean {
  const payload = decodeJwtPayload(token);
  const exp = payload?.exp;
  if (typeof exp !== "number") return false;
  return exp * 1000 <= Date.now() + skewSeconds * 1000;
}

function clearSessionState(): void {
  clearAccessToken();
  if (typeof window !== "undefined") {
    localStorage.removeItem("zozi_has_session");
  }
}

export { clearSessionState };

/**
 * Result of a silent refresh attempt.
 *  - "ok"        : a new access token was issued.
 *  - "no_session": there is no session flag, so no refresh should be attempted.
 *  - "rejected"  : the backend definitively rejected the refresh token
 *                  (expired / revoked / reuse detected). The session is gone.
 *  - "network"   : the request failed due to a transient network/abort error
 *                  (very common when a navigation cancels the in-flight request).
 *                  The session flag and local cart are intentionally preserved so
 *                  a later page load can retry — we never destroy a session on a
 *                  flaky request.
 */
export type RefreshResult =
  | { status: "ok"; accessToken: string }
  | { status: "no_session" }
  | { status: "rejected" }
  | { status: "network" };

const REFRESH_NETWORK_RETRIES = 2;
const REFRESH_RETRY_DELAY_MS = 300;

async function silentlyRefreshAccessToken(): Promise<RefreshResult> {
  if (typeof window === "undefined") return { status: "network" };
  if (localStorage.getItem("zozi_has_session") !== "1") return { status: "no_session" };

  if (_refreshPromise) {
    return _refreshPromise;
  }

  const attempt = async (triesLeft: number): Promise<RefreshResult> => {
    try {
      const res = await fetch("/auth/refresh", {
        method: "POST",
        credentials: "include",
      });
      if (!res.ok) {
        clearSessionState();
        return { status: "rejected" };
      }
      const data = await res.json();
      if (!data?.access_token) {
        clearSessionState();
        return { status: "rejected" };
      }
      setAccessToken(data.access_token);
      localStorage.setItem("zozi_has_session", "1");
      return { status: "ok", accessToken: data.access_token };
    } catch {
      // A navigation can cancel the request (ERR_ABORTED). Retry a bounded
      // number of times so that transient failures during page transitions
      // do not wipe the user's session or cart.
      if (triesLeft > 0) {
        await new Promise((resolve) => setTimeout(resolve, REFRESH_RETRY_DELAY_MS));
        return attempt(triesLeft - 1);
      }
      // Out of retries — keep the session flag and local cart intact so a
      // subsequent page load will retry the refresh.
      return { status: "network" };
    }
  };

  _refreshPromise = attempt(REFRESH_NETWORK_RETRIES);
  try {
    return await _refreshPromise;
  } finally {
    _refreshPromise = null;
  }
}

export { silentlyRefreshAccessToken };

async function ensureAccessToken(): Promise<void> {
  if (_accessToken && !isAccessTokenExpiringSoon(_accessToken)) return;
  await silentlyRefreshAccessToken();
}

/**
 * Thin wrapper around fetch that:
 *  1. Prefixes relative paths with the API base URL.
 *  2. Attaches the in-memory Bearer token when available.
 *  3. Echoes the CSRF cookie as `X-CSRF-Token` on mutating requests.
 *  4. Clears the token and dispatches a session-expired event on 401.
 *
 * Pass `skipAuthRedirect: true` in options to suppress the 401 redirect
 * (e.g. when handling auth yourself, such as in an inline sign-in modal).
 */
export async function parseJsonResponse(response: Response): Promise<any> {
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    return null;
  }

  try {
    return await response.json();
  } catch {
    return null;
  }
}

export function isUrlSameOrigin(url: string, currentOrigin?: string): boolean {
  if (typeof window === "undefined" && !currentOrigin) return false;

  const origin = currentOrigin ?? window.location.origin;
  try {
    return new URL(url).origin === origin;
  } catch {
    return false;
  }
}

// ── Country Detection ───────────────────────────────────────────────────────────

/**
 * Detect the user's country from their IP address via backend middleware headers.
 * The backend sets X-Country-Code header after geo-detection.
 */
export async function detectCountryFromIP(): Promise<string | null> {
  if (typeof window === "undefined") return null;
  
  // Check if we already have a detected country
  const existing = getAutoDetectedCountry();
  if (existing) return existing;
  
  // The backend already sets X-Country-Code in the response headers
  // via CountryDetectionMiddleware. We just need to make a request to trigger it.
  try {
    const res = await fetch("/api/health", {
      method: "GET",
      credentials: "include",
      headers: { "Accept": "application/json" },
    });
    
    // The middleware sets the header on any response
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
  // 1. Check URL parameter first
  if (typeof window !== "undefined") {
    const urlParams = new URLSearchParams(window.location.search);
    const countryParam = urlParams.get("country");
    if (countryParam) {
      const normalized = countryParam.toUpperCase();
      if (/^[A-Z]{2}$/.test(normalized)) return normalized;
    }
  }
  
  // 2. Check localStorage/session
  const selectedCountry = getSelectedCountryCode();
  if (selectedCountry) return selectedCountry;
  
  // 3. Check auto-detected country
  const autoDetected = getAutoDetectedCountry();
  if (autoDetected) return autoDetected;
  
  return null;
}

function getSelectedCountryCode(): string | null {
  if (typeof window === "undefined") return null;

  const countryAliases: Record<string, string> = {
    AE: "AE",
    UAE: "AE",
    UNITEDARABEMIRATES: "AE",
    EMIRATES: "AE",
    PK: "PK",
    PAKISTAN: "PK",
    OM: "OM",
    OMAN: "OM",
    SA: "SA",
    KSA: "SA",
    SAUDIARABIA: "SA",
    IN: "IN",
    INDIA: "IN",
    US: "US",
    USA: "US",
    UNITEDSTATES: "US",
    UNITEDSTATESOFAMERICA: "US",
    GB: "GB",
    UK: "GB",
    UNITEDKINGDOM: "GB",
    QA: "QA",
    QATAR: "QA",
    KW: "KW",
    KUWAIT: "KW",
    BH: "BH",
    BAHRAIN: "BH",
  };

  const normalizeCountryCode = (raw: string | null | undefined): string => {
    const lettersOnly = String(raw || "").toUpperCase().replace(/[^A-Z]/g, "");
    if (!lettersOnly) return "";
    const aliased = countryAliases[lettersOnly];
    if (aliased) return aliased;
    if (lettersOnly.length === 2) return lettersOnly;
    return "";
  };

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

// ── Auto-detected country from backend middleware headers ──
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

export async function apiFetch(
  path: string,
  options: RequestInit & { skipAuthRedirect?: boolean; disableCache?: boolean; cacheTtlMs?: number; timeoutMs?: number } = {}
): Promise<Response> {
  const {
    skipAuthRedirect,
    disableCache = false,
    cacheTtlMs = DEFAULT_SHORT_GET_TTL_MS,
    timeoutMs = DEFAULT_API_TIMEOUT_MS,
    ...fetchOptions
  } = options;
  const url = resolveRequestUrl(path, fetchOptions.body);

  const headers = new Headers(fetchOptions.headers);
  const method = (fetchOptions.method || "GET").toUpperCase();
  const useGetCache = shouldUseShortGetCache(path, method, disableCache);

  // If we might have a valid session but no in-memory access token (common during
  // Fast Refresh or after a hard reload), try to refresh the token before calling.
  await ensureAccessToken();

  const attachAccessToken = () => {
    if (fetchOptions.headers && new Headers(fetchOptions.headers).has("Authorization")) {
      return;
    }
    if (_accessToken) {
      headers.set("Authorization", `Bearer ${_accessToken}`);
    } else {
      headers.delete("Authorization");
    }
  };

  // Auto-attach auth token from memory (never from localStorage)
  attachAccessToken();

  if (!headers.has("X-Country-Code")) {
    const selectedCountry = getSelectedCountryCode();
    if (selectedCountry) {
      headers.set("X-Country-Code", selectedCountry);
    }
  }

  // Echo CSRF token on every state-changing request
  if (CSRF_METHODS.has(method) && !headers.has("X-CSRF-Token")) {
    const csrf = getCsrfToken();
    if (csrf) headers.set("X-CSRF-Token", csrf);
  }

  // Create abort controller for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const doFetch = (sig: AbortSignal) =>
    fetch(url, { credentials: "include", ...fetchOptions, headers, signal: sig });

  const executeRequest = async (): Promise<Response> => {
    try {
      return await doFetch(controller.signal);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      console.error(`[API] Fetch failed for ${url}: ${errorMessage}`);

      // Retry against the current origin for relative non-auth URLs.
      // Use a FRESH AbortController so a previous timeout abort doesn't
      // poison the retry.
      const canRetryRelative =
        typeof window !== "undefined" &&
        !path.startsWith("http") &&
        !path.startsWith("/auth/") &&
        isUrlSameOrigin(url);

      if (canRetryRelative) {
        const retryController = new AbortController();
        const retryTimeout = setTimeout(() => retryController.abort(), timeoutMs);
        try {
          const r = await fetch(path, { credentials: "include", ...fetchOptions, headers, signal: retryController.signal });
          return r;
        } finally {
          clearTimeout(retryTimeout);
        }
      } else {
        throw new TypeError(`Failed to fetch: ${url}. ${errorMessage}`);
      }
    }
  };

  const performRequest = async (): Promise<Response> => {
    let res = await executeRequest();

    clearTimeout(timeoutId);

    // Capture auto-detected country from backend middleware response header
    const detectedCountry = res.headers.get("X-Country-Code");
    if (detectedCountry) {
      setAutoDetectedCountry(detectedCountry);
    }

    // Retry on transient failures (429 Too Many Requests, 503 Service Unavailable)
    // with exponential backoff, respecting Retry-After header when present.
    const maxRetries = 2;
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      if (res.status !== 429 && res.status !== 503) break;

      const retryAfterHeader = res.headers.get("Retry-After");
      let waitMs = 500 * Math.pow(2, attempt);
      if (retryAfterHeader) {
        const parsed = parseInt(retryAfterHeader, 10);
        if (!Number.isNaN(parsed) && parsed > 0) {
          waitMs = Math.max(waitMs, parsed * 1000);
        }
      }

      await new Promise((resolve) => setTimeout(resolve, waitMs));
      res = await executeRequest();
    }

    // If the access token expired mid-session, try one silent refresh and retry.
    if (res.status === 401 && !skipAuthRedirect && typeof window !== "undefined") {
      const refreshResult = await silentlyRefreshAccessToken();
      if (refreshResult.status === "ok") {
        attachAccessToken();
        res = await executeRequest();
      }
    }

    // Auto-logout on unrecoverable 401 (skip when caller handles auth themselves)
    if (res.status === 401 && !skipAuthRedirect && typeof window !== "undefined") {
      clearSessionState();
      window.dispatchEvent(new Event("zozi:auth-expired"));
    }

    if (CSRF_METHODS.has(method) && res.ok) {
      responseCache.invalidateAll();
    }

    return res;
  };

  if (useGetCache) {
    const cacheKey = buildShortGetCacheKey({ url, authToken: _accessToken, extraKey: fetchOptions.cache });
    return responseCache.getOrSet(
      cacheKey,
      async () => {
        const response = await performRequest();
        return response;
      },
      cacheTtlMs,
      (response) => response.ok,
    );
  }

  return performRequest();
}
