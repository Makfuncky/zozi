/**
 * Core API fetch wrapper — handles auth, CSRF, retries, caching, and timeouts.
 */

import {
  buildShortGetCacheKey,
  createResponseRequestCache,
  DEFAULT_SHORT_GET_TTL_MS,
  shouldUseShortGetCache,
} from "@shared/requestCache";

import {
  ensureAccessToken,
  getAccessToken,
  silentlyRefreshAccessToken,
  clearSessionState,
  _getTraceIdStore,
} from "./auth";
import { getSelectedCountryCode, setAutoDetectedCountry } from "./country";

// Default timeout for API requests (in milliseconds)
export const DEFAULT_API_TIMEOUT_MS = 30000;

// Use relative URL for same-origin requests to avoid CORS issues
const _API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
const _API_HOST = process.env.NEXT_PUBLIC_API_HOST || "";
const _API_PORT = process.env.NEXT_PUBLIC_API_PORT || "8000";
const _IS_LOCAL = (h: string) => h === "localhost" || h === "127.0.0.1" || h === "[::1]"
export const API_URL = typeof window !== "undefined"
  ? (_IS_LOCAL(window.location.hostname)
      ? (_API_HOST ? `${_API_HOST.startsWith("http") ? _API_HOST : "http://" + _API_HOST}:${_API_PORT}` : _API_URL)
      : `${window.location.protocol}//${window.location.hostname}${window.location.port ? ':' + window.location.port : ''}`)
  : _API_URL;

/** Shared response cache — also used by auth.ts to invalidate on token change. */
export const responseCache = createResponseRequestCache();

function resolveRequestUrl(path: string, _body?: BodyInit | null): string {
  if (path.startsWith("http")) return path;
  if (!path.startsWith("/api") && !path.startsWith("/auth") && !path.startsWith("/admin")) return `/__api${path}`;
  return path;
}

// ── CSRF ────────────────────────────────────────────────────────────────

function getCsrfToken(): string {
  if (typeof document === "undefined") return "";
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : "";
}

const CSRF_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

// ── Trace context ───────────────────────────────────────────────────────

function getTraceparent(): string | null {
  const store = _getTraceIdStore();
  if (!store.traceId) {
    store.traceId = crypto.randomUUID().replace(/-/g, "").slice(0, 32);
  }
  const spanId = crypto.randomUUID().replace(/-/g, "").slice(0, 16);
  return `00-${store.traceId}-${spanId}-01`;
}

// ── Response helpers ────────────────────────────────────────────────────

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

// ── apiFetch ────────────────────────────────────────────────────────────

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

  await ensureAccessToken();

  const attachAccessToken = () => {
    if (fetchOptions.headers && new Headers(fetchOptions.headers).has("Authorization")) {
      return;
    }
    const token = getAccessToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    } else {
      headers.delete("Authorization");
    }
  };

  attachAccessToken();

  if (!headers.has("X-Country-Code")) {
    const selectedCountry = getSelectedCountryCode();
    if (selectedCountry) {
      headers.set("X-Country-Code", selectedCountry);
    }
  }

  if (CSRF_METHODS.has(method) && !headers.has("X-CSRF-Token")) {
    const csrf = getCsrfToken();
    if (csrf) headers.set("X-CSRF-Token", csrf);
  }

  const traceparent = getTraceparent();
  if (traceparent) {
    headers.set("traceparent", traceparent);
  }

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
        throw new TypeError(`Failed to fetch: ${url}. ${errorMessage}`, { cause: err });
      }
    }
  };

  const performRequest = async (): Promise<Response> => {
    let res = await executeRequest();
    clearTimeout(timeoutId);

    const detectedCountry = res.headers.get("X-Country-Code");
    if (detectedCountry) {
      setAutoDetectedCountry(detectedCountry);
    }

    // Retry on transient failures (429, 503) with exponential backoff
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

    // Silent refresh on 401
    if (res.status === 401 && !skipAuthRedirect && typeof window !== "undefined") {
      const refreshResult = await silentlyRefreshAccessToken();
      if (refreshResult.status === "ok") {
        attachAccessToken();
        res = await executeRequest();
      }
    }

    // Auto-logout on unrecoverable 401
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
    const cacheKey = buildShortGetCacheKey({ url, authToken: getAccessToken(), extraKey: fetchOptions.cache });
    return responseCache.getOrSet(
      cacheKey,
      async () => performRequest(),
      cacheTtlMs,
      (response) => response.ok,
    );
  }

  return performRequest();
}
