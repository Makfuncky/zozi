/**
 * Platform-agnostic API core for ZOZI.
 *
 * Platform adapters must provide:
 *   • getAccessToken() / setAccessToken() / clearAccessToken()
 *   • getRefreshToken() / setRefreshToken() / clearRefreshToken()
 *   • getCSRFHeader() — returns object with X-CSRF-Token (or empty {})
 *
 * The web adapter handles httpOnly cookies + in-memory access token.
 * The mobile adapter uses expo-secure-store.
 */

import {
  buildShortGetCacheKey,
  createTimedRequestCache,
  DEFAULT_SHORT_GET_TTL_MS,
  shouldUseShortGetCache,
} from "./requestCache";

export interface TokenAdapter {
  getAccessToken(): string | null;
  setAccessToken(token: string, expiresIn?: number): void;
  clearAccessToken(): void;
  getRefreshToken(): string | null;
  setRefreshToken(token: string): void;
  clearRefreshToken(): void;
  getCSRFHeader(): Record<string, string>;
}

export interface ApiCoreConfig {
  baseUrl: string;
  adapter: TokenAdapter;
  /** Called when a non-recoverable 401 occurs (session expired) */
  onAuthExpired?: () => void;
  defaultGetCacheTtlMs?: number;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly body: unknown,
    message?: string
  ) {
    super(message ?? `API error ${status}`);
    this.name = "ApiError";
  }
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function isAuthEndpoint(path: string): boolean {
  return path.includes("/auth/");
}

function buildUrl(baseUrl: string, path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  const base = baseUrl.replace(/\/$/, "");
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${base}${p}`;
}

// ── Core Fetch ───────────────────────────────────────────────────────────────

export function createApiClient(config: ApiCoreConfig) {
  const { baseUrl, adapter, onAuthExpired, defaultGetCacheTtlMs = DEFAULT_SHORT_GET_TTL_MS } = config;
  const getCache = createTimedRequestCache<unknown>();

  async function refreshAccessToken(): Promise<boolean> {
    const refreshToken = adapter.getRefreshToken();
    if (!refreshToken) return false;

    try {
      const res = await fetch(buildUrl(baseUrl, "/auth/refresh"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...adapter.getCSRFHeader(),
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!res.ok) {
        adapter.clearRefreshToken();
        adapter.clearAccessToken();
        return false;
      }

      const data = (await res.json()) as {
        access_token?: string;
        expires_in?: number;
      };
      if (data.access_token) {
        adapter.setAccessToken(data.access_token, data.expires_in);
        return true;
      }
    } catch {
      // network fail — stay logged out
    }
    return false;
  }

  async function apiFetch<T = unknown>(
    path: string,
    options: RequestInit & { skipAuth?: boolean; disableCache?: boolean; cacheTtlMs?: number } = {}
  ): Promise<T> {
    const { skipAuth = false, disableCache = false, cacheTtlMs = defaultGetCacheTtlMs, ...fetchOptions } = options;
    const url = buildUrl(baseUrl, path);

    const method = (fetchOptions.method ?? "GET").toUpperCase();
    const mutating = ["POST", "PUT", "PATCH", "DELETE"].includes(method);
    const isFormDataBody = typeof FormData !== "undefined" && fetchOptions.body instanceof FormData;

    // Build headers
    const headers: Record<string, string> = {
      ...(fetchOptions.headers as Record<string, string>),
    };
    const hasExplicitContentType = Object.keys(headers).some((key) => key.toLowerCase() === "content-type");
    if (!isFormDataBody && fetchOptions.body != null && !hasExplicitContentType) {
      headers["Content-Type"] = "application/json";
    }

    // Attach access token
    if (!skipAuth) {
      const token = adapter.getAccessToken();
      if (token) headers["Authorization"] = `Bearer ${token}`;
    }

    // Attach CSRF on mutating requests
    if (mutating && !isAuthEndpoint(path)) {
      Object.assign(headers, adapter.getCSRFHeader());
    }

    const authToken = skipAuth ? null : adapter.getAccessToken();
    const useGetCache = shouldUseShortGetCache(path, method, disableCache);
    const cacheKey = useGetCache
      ? buildShortGetCacheKey({ url, authToken, extraKey: fetchOptions.cache })
      : null;

    const performRequest = async (): Promise<T> => {
      let res = await fetch(url, { ...fetchOptions, headers });

      // Auto-refresh on 401
      if (res.status === 401 && !skipAuth && !isAuthEndpoint(path)) {
        const ok = await refreshAccessToken();
        if (ok) {
          const token = adapter.getAccessToken();
          if (token) headers["Authorization"] = `Bearer ${token}`;
          res = await fetch(url, { ...fetchOptions, headers });
        } else {
          adapter.clearAccessToken();
          getCache.invalidateAll();
          onAuthExpired?.();
          throw new ApiError(401, null, "Session expired");
        }
      }

      if (!res.ok) {
        let body: unknown = null;
        try {
          body = await res.json();
        } catch {
          body = await res.text().catch(() => null);
        }
        throw new ApiError(res.status, body);
      }

      if (mutating) {
        getCache.invalidateAll();
      }

      // 204 No Content
      if (res.status === 204) return undefined as T;

      return res.json() as Promise<T>;
    };

    if (cacheKey) {
      return getCache.getOrSet(cacheKey, performRequest, cacheTtlMs) as Promise<T>;
    }

    return performRequest();
  }

  return {
    apiFetch,
    refreshAccessToken,
    clearCache: () => getCache.invalidateAll(),
  };
}
