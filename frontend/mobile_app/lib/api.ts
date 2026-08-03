/**
 * Mobile API client — uses expo-secure-store for token storage.
 * Implements the TokenAdapter interface from @shared/api-core.
 */
import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";
import { createApiClient, TokenAdapter } from "@shared/api-core";
import { buildProductQueryParams } from "@shared/productQuery";
import type { Notification as SharedNotification, Order, SupplierPublicSummary } from "@shared/types";
import { getPersistedSelectedCountryCode } from "@/lib/countrySelection";
import { socialSignIn } from "@/lib/socialAuth";

type LegacySecureStore = typeof SecureStore & {
  getValueWithKeyAsync?: (key: string) => Promise<string | null>;
  setValueWithKeyAsync?: (key: string, value: string) => Promise<void>;
  deleteValueWithKeyAsync?: (key: string) => Promise<void>;
};

type ApiFetchOptions = RequestInit & { skipAuth?: boolean };

const KEYS = {
  ACCESS: "zozi_access_token",
  REFRESH: "zozi_refresh_token",
  ACCESS_EXPIRY: "zozi_access_expiry",
} as const;

const legacySecureStore = SecureStore as LegacySecureStore;

const secureStoreAdapter = {
  async getItemAsync(key: string): Promise<string | null> {
    if (Platform.OS === "web" && typeof window !== "undefined") {
      return window.localStorage.getItem(key);
    }
    try {
      if (typeof SecureStore.getItemAsync === "function") {
        return await SecureStore.getItemAsync(key);
      }
      if (typeof legacySecureStore.getValueWithKeyAsync === "function") {
        return await legacySecureStore.getValueWithKeyAsync(key);
      }
    } catch (err) {
      console.warn("SecureStore.getItemAsync failed", key, err);
    }
    return null;
  },

  async setItemAsync(key: string, value: string): Promise<void> {
    if (Platform.OS === "web" && typeof window !== "undefined") {
      try {
        window.localStorage.setItem(key, value);
        return;
      } catch (err) {
        console.warn("localStorage setItem failed", key, err);
        // Try clearing a stale key and retry once
        try {
          window.localStorage.removeItem(key);
          window.localStorage.setItem(key, value);
          return;
        } catch (_err) {
          console.warn("localStorage fallback write failed", key, _err);
        }
      }
      return;
    }
    try {
      if (typeof SecureStore.setItemAsync === "function") {
        await SecureStore.setItemAsync(key, value);
        return;
      }
      if (typeof legacySecureStore.setValueWithKeyAsync === "function") {
        await legacySecureStore.setValueWithKeyAsync(key, value);
        return;
      }
    } catch (err) {
      console.warn("SecureStore.setItemAsync failed", key, err);
      if (Platform.OS === "web") {
        window.localStorage.removeItem(key);
      }
    }
  },

  async deleteItemAsync(key: string): Promise<void> {
    if (Platform.OS === "web" && typeof window !== "undefined") {
      window.localStorage.removeItem(key);
      return;
    }
    try {
      if (typeof SecureStore.deleteItemAsync === "function") {
        await SecureStore.deleteItemAsync(key);
        return;
      }
      if (typeof legacySecureStore.deleteValueWithKeyAsync === "function") {
        await legacySecureStore.deleteValueWithKeyAsync(key);
        return;
      }
    } catch (err) {
      console.warn("SecureStore.deleteItemAsync failed", key, err);
    }
  },
};

// In-memory access token for perf (avoid disk reads per request)
let _inMemoryAccessToken: string | null = null;
let _accessExpiry: number | null = null;
let _refreshToken: string | null = null;

const mobileAdapter: TokenAdapter = {
  getAccessToken() {
    if (_inMemoryAccessToken && _accessExpiry && Date.now() < _accessExpiry) {
      return _inMemoryAccessToken;
    }
    _inMemoryAccessToken = null;
    return null;
  },

  setAccessToken(token: string, expiresIn = 900) {
    _inMemoryAccessToken = token;
    _accessExpiry = Date.now() + expiresIn * 1000;
    // Also persist to secure store (async — best effort)
    secureStoreAdapter.setItemAsync(KEYS.ACCESS, token);
    secureStoreAdapter.setItemAsync(KEYS.ACCESS_EXPIRY, String(_accessExpiry));
  },

  clearAccessToken() {
    _inMemoryAccessToken = null;
    _accessExpiry = null;
    secureStoreAdapter.deleteItemAsync(KEYS.ACCESS);
    secureStoreAdapter.deleteItemAsync(KEYS.ACCESS_EXPIRY);
  },

  getRefreshToken() {
    return _refreshToken;
  },

  setRefreshToken(token: string) {
    _refreshToken = token;
    secureStoreAdapter.setItemAsync(KEYS.REFRESH, token).catch((err) => {
      console.warn("Failed to persist refresh token", err);
    });
  },

  clearRefreshToken() {
    _refreshToken = null;
    secureStoreAdapter.deleteItemAsync(KEYS.REFRESH).catch((err) => {
      console.warn("Failed to clear refresh token", err);
    });
  },

  getCSRFHeader() {
    // Mobile uses Bearer token — no CSRF cookie needed
    return {};
  },
};

// ── Async helpers (used during app startup) ───────────────────────────────────

export async function restoreTokens(): Promise<boolean> {
  try {
    const [token, expiry, refresh] = await Promise.all([
      secureStoreAdapter.getItemAsync(KEYS.ACCESS),
      secureStoreAdapter.getItemAsync(KEYS.ACCESS_EXPIRY),
      secureStoreAdapter.getItemAsync(KEYS.REFRESH),
    ]);

    if (token && expiry && Date.now() < Number(expiry)) {
      _inMemoryAccessToken = token;
      _accessExpiry = Number(expiry);
      return true;
    }

    // Access token expired — try refresh
    if (refresh) {
      _refreshToken = refresh;
      return false; // Will be refreshed by authStore
    }

    return false;
  } catch {
    return false;
  }
}

export async function getStoredRefreshToken(): Promise<string | null> {
  return secureStoreAdapter.getItemAsync(KEYS.REFRESH);
}

export function getCurrentAccessToken(): string | null {
  return mobileAdapter.getAccessToken();
}

export function __resetTokenAdapterState() {
  _inMemoryAccessToken = null;
  _accessExpiry = null;
  _refreshToken = null;
}

// ── Create the client ─────────────────────────────────────────────────────────

const DEFAULT_API_HOST = (() => {
  if (Platform.OS === "android") return "10.0.2.2"; // Android emulator host
  if (Platform.OS === "ios") return "localhost"; // iOS simulator host
  return "localhost"; // web / other
})();

const DEFAULT_API_BASE = `http://${DEFAULT_API_HOST}:8000`;
export const API_BASE = (process.env.EXPO_PUBLIC_API_URL && process.env.EXPO_PUBLIC_API_URL.trim()) || DEFAULT_API_BASE;

export function resolveApiAssetUrl(path?: string | null): string | null {
  if (!path) return null;
  if (/^https?:\/\//i.test(path)) return path;
  return `${API_BASE.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;
}

let _onAuthExpiredCb: (() => void) | undefined;

export function setAuthExpiredCallback(cb: () => void) {
  _onAuthExpiredCb = cb;
}

const apiClient = createApiClient({
  baseUrl: API_BASE,
  adapter: mobileAdapter,
  onAuthExpired: () => _onAuthExpiredCb?.(),
});

// ── Lightweight in-memory GET cache ────────────────────────────────────────────
// Deduplicates identical GET requests across the app (e.g. /banners + /flash-sales
// would otherwise refetch on every screen mount) and caches successful GET responses
// for a short TTL so navigation between tabs is instant. Mutations (POST/PUT/DELETE/
// PATCH) always bypass the cache and optionally invalidate matching entries.

interface CachedEntry<T> {
  ts: number;
  promise: Promise<T>;
  data?: T;
}

const GET_CACHE_TTL_MS = 60_000;
const _getCache = new Map<string, CachedEntry<unknown>>();

function cacheKey(path: string, headers: Record<string, string>): string {
  const country = headers["X-Country-Code"] || headers["x-country-code"] || "";
  return `${country}|${path}`;
}

function invalidateCache(prefix?: string) {
  if (!prefix) {
    _getCache.clear();
    return;
  }
  for (const key of _getCache.keys()) {
    if (key.includes(`|${prefix}`) || key.endsWith(`|${prefix}`)) {
      _getCache.delete(key);
    }
  }
}

async function apiFetch<T = unknown>(
  path: string,
  options?: RequestInit & { skipAuth?: boolean }
): Promise<T> {
  if (!mobileAdapter.getRefreshToken()) {
    const rt = await getStoredRefreshToken();
    if (rt) mobileAdapter.setRefreshToken(rt);
  }

  const nextOptions = { ...(options || {}) };
  const existingHeaders = new Headers(nextOptions.headers || {});

  if (!existingHeaders.has("X-Country-Code")) {
    const selectedCountryCode = await getPersistedSelectedCountryCode();
    if (selectedCountryCode) {
      existingHeaders.set("X-Country-Code", selectedCountryCode);
    }
  }

  const normalizedHeaders: Record<string, string> = {};
  existingHeaders.forEach((value, key) => {
    normalizedHeaders[key] = value;
  });

  const method = (nextOptions.method || "GET").toUpperCase();

  // Mutations bypass the cache and invalidate related GET entries.
  if (method !== "GET") {
    if (typeof path === "string") invalidateCache(path.split("?")[0]);
    return apiClient.apiFetch<T>(path, {
      ...nextOptions,
      headers: normalizedHeaders,
    });
  }

  // GET: serve from cache when fresh, deduping in-flight requests.
  const key = cacheKey(path, normalizedHeaders);
  const cached = _getCache.get(key) as CachedEntry<T> | undefined;
  const now = Date.now();
  if (cached && (cached.data !== undefined || now - cached.ts < GET_CACHE_TTL_MS)) {
    if (cached.data !== undefined) {
      return cached.data;
    }
    return cached.promise;
  }

  const promise = apiClient.apiFetch<T>(path, {
    ...nextOptions,
    headers: normalizedHeaders,
  });
  const entry: CachedEntry<T> = {
    ts: now,
    promise: promise
      .then((data) => {
        _getCache.set(key, { ts: Date.now(), promise, data });
        return data;
      })
      .catch((err) => {
        _getCache.delete(key);
        throw err;
      }),
  };
  _getCache.set(key, entry);
  return entry.promise;
}

export async function refreshAccessToken(): Promise<boolean> {
  return apiClient.refreshAccessToken();
}

export {
  apiFetch,
  mobileAdapter as tokenAdapter,
};

type CollectionEnvelope<T> = T[] | {
  items?: T[];
  data?: T[];
  results?: T[];
  notifications?: T[];
  coupons?: T[];
  orders?: T[];
  products?: T[];
  users?: T[];
  total?: number;
};

export * from './apiTypes';
export async function getNotificationPreferences(): Promise<NotificationPreferences> {
  return apiFetch("/notifications/preferences");
}

export async function updateNotificationPreferences(
  prefs: Partial<NotificationPreferences>
): Promise<NotificationPreferences> {
  return apiFetch("/notifications/preferences", {
    method: "PUT",
    body: JSON.stringify(prefs),
  });
}
