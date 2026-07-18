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

export interface OffsetPageResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  hasMore: boolean;
}

export function normalizeCollectionResponse<T>(
  payload: CollectionEnvelope<T>,
  extraKeys: string[] = [],
): T[] {
  if (Array.isArray(payload)) {
    return payload;
  }

  if (!payload || typeof payload !== "object") {
    return [];
  }

  const envelope = payload as Record<string, unknown>;
  for (const key of [...extraKeys, "items", "data", "results"]) {
    const value = envelope[key];
    if (Array.isArray(value)) {
      return value as T[];
    }
  }

  return [];
}

function normalizeOffsetPageResponse<T>(
  payload: CollectionEnvelope<T>,
  limit: number,
  offset: number,
  extraKeys: string[] = [],
): OffsetPageResponse<T> {
  const items = normalizeCollectionResponse(payload, extraKeys);
  const envelope = payload && typeof payload === "object" && !Array.isArray(payload)
    ? payload as Record<string, unknown>
    : null;
  const total = typeof envelope?.total === "number" ? envelope.total : offset + items.length;

  return {
    items,
    total,
    limit,
    offset,
    hasMore: typeof envelope?.total === "number"
      ? offset + items.length < total
      : items.length >= limit,
  };
}

// ── Auth API ──────────────────────────────────────────────────────────────────

export interface LoginPayload {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token: string;
  user: {
    id: number;
    email: string;
    username: string;
    role: "customer" | "supplier" | "admin" | "logistics_partner" | "sub_admin" | "moderator" | "support" | "country_head" | "country_manager" | "employee";
    profile_image?: string;
    phone?: string;
    email_verified?: boolean;
    referral_code?: string;
    referral_points?: number;
    sharing_points?: number;
    total_points?: number;
  };
}

export interface AuthCapabilities {
  google: boolean;
  google_mode?: "gsi" | "redirect" | "disabled";
  google_client_id?: string | null;
  facebook: boolean;
  facebook_mode?: "redirect" | "disabled";
  customer_email_verification_required: boolean;
  email_delivery?: {
    available: boolean;
    live: boolean;
    preview_only: boolean;
    provider: string;
    from_address?: string | null;
  };
}

export async function login(payload: LoginPayload, remember = true): Promise<AuthResponse> {
  const res = await apiFetch<AuthResponse>("/auth/login/json", {
    method: "POST",
    body: JSON.stringify({ ...payload, remember }),
    skipAuth: true,
  });
  mobileAdapter.setAccessToken(res.access_token, res.expires_in);
  mobileAdapter.setRefreshToken(res.refresh_token);
  return res;
}

export async function register(payload: {
  email: string;
  password: string;
  username: string;
  role?: string;
  [key: string]: unknown;
}): Promise<AuthResponse> {
  const res = await apiFetch<AuthResponse>("/auth/register/json", {
    method: "POST",
    body: JSON.stringify(payload),
    skipAuth: true,
  });
  mobileAdapter.setAccessToken(res.access_token, res.expires_in);
  mobileAdapter.setRefreshToken(res.refresh_token);
  return res;
}

export async function logout(): Promise<void> {
  try {
    await apiFetch("/auth/logout", { method: "POST" });
  } finally {
    mobileAdapter.clearAccessToken();
    mobileAdapter.clearRefreshToken();
  }
}

export async function getMe(): Promise<AuthResponse["user"]> {
  return apiFetch("/auth/me");
}

export async function getAuthCapabilities(): Promise<AuthCapabilities> {
  return apiFetch("/auth/oauth/providers", {
    method: "GET",
    skipAuth: true,
  });
}

export async function forgotPassword(email: string): Promise<void> {
  await apiFetch("/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
    skipAuth: true,
  });
}

export async function resetPassword(token: string, password: string): Promise<void> {
  await apiFetch("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ token, new_password: password }),
    skipAuth: true,
  });
}

export async function verifyEmail(token: string): Promise<void> {
  await apiFetch(`/auth/verify-email?token=${encodeURIComponent(token)}`, {
    method: "GET",
    skipAuth: true,
  });
}

// ── Notifications API ─────────────────────────────────────────────────────────

export type Notification = SharedNotification;

export async function getNotifications(): Promise<Notification[]> {
  const payload = await apiFetch<CollectionEnvelope<Notification>>("/notifications");
  return normalizeCollectionResponse(payload, ["notifications"]);
}

export async function markNotificationRead(id: number): Promise<void> {
  await apiFetch(`/notifications/${id}/read`, { method: "PUT" });
}

export async function markAllNotificationsRead(): Promise<void> {
  await apiFetch("/notifications/read-all", { method: "PUT" });
}

export async function deleteNotification(id: number): Promise<void> {
  await apiFetch(`/notifications/${id}`, { method: "DELETE" });
}

// ── Coupons API ───────────────────────────────────────────────────────────────

export interface Coupon {
  id: number;
  code: string;
  discount_type: "percentage" | "fixed";
  discount_value: number;
  min_order_amount: number;
  max_uses: number;
  current_uses: number;
  expires_at: string | null;
  is_active: boolean;
}

/**
 * The backend returns coupon rows under several different field-name
 * conventions depending on the endpoint (raw ORM rows expose `minimum_order`,
 * `usage_limit`, `usage_count`; the admin list serializes aliases like
 * `min_order`, `max_uses`, `uses_count`). Normalize them all into the single
 * shape the UI expects so screens don't render `undefined`/`NaN`.
 */
export function normalizeCoupon(raw: Partial<Coupon> & Record<string, any>): Coupon {
  const num = (...vals: unknown[]): number => {
    for (const v of vals) {
      if (v === null || v === undefined || v === "") continue;
      const n = Number(v);
      if (!Number.isNaN(n)) return n;
    }
    return 0;
  };

  return {
    id: num(raw.id),
    code: String(raw.code ?? ""),
    discount_type: raw.discount_type === "fixed" ? "fixed" : "percentage",
    discount_value: num(raw.discount_value, raw.value),
    min_order_amount: num(raw.min_order_amount, raw.min_order, raw.minimum_order),
    max_uses: num(raw.max_uses, raw.usage_limit, raw.max_uses),
    current_uses: num(raw.current_uses, raw.uses_count, raw.used_count, raw.usage_count),
    expires_at: raw.expires_at ?? (raw.expires_at === undefined ? null : null),
    is_active: raw.is_active ?? true,
  };
}

export async function getPublicCoupons(): Promise<Coupon[]> {
  const payload = await apiFetch<CollectionEnvelope<Partial<Coupon> & Record<string, any>>>("/coupons");
  return normalizeCollectionResponse(payload, ["coupons"]).map(normalizeCoupon);
}

// ── Admin coupon management ─────────────────────────────────────────────────
// The admin list endpoint returns a paginated envelope with aliases; the create
// endpoint returns only {message, id, code}, so we re-fetch after creating.

export async function listAdminCoupons(search?: string): Promise<Coupon[]> {
  const qs = search ? `?search=${encodeURIComponent(search)}` : "";
  const payload = await apiFetch<CollectionEnvelope<Partial<Coupon> & Record<string, any>>>(`/admin/coupons${qs}`);
  return normalizeCollectionResponse(payload, ["coupons"]).map(normalizeCoupon);
}

export async function createAdminCoupon(input: {
  code: string;
  discount_type: "percentage" | "fixed";
  value: number;
  min_order: number;
  max_uses?: number | null;
  expires_at?: string | null;
  is_active?: boolean;
}): Promise<Coupon> {
  const body: Record<string, unknown> = {
    code: input.code.trim().toUpperCase(),
    discount_type: input.discount_type,
    value: input.value,
    min_order: input.min_order,
  };
  if (input.max_uses != null) body.max_uses = input.max_uses;
  if (input.expires_at) body.expires_at = input.expires_at;
  if (input.is_active != null) body.is_active = input.is_active;

  await apiFetch("/admin/coupons", { method: "POST", body: JSON.stringify(body) });
  // The endpoint only returns {message, id, code} — re-fetch the full list.
  const fresh = await listAdminCoupons();
  return fresh.find((c) => c.code === input.code.trim().toUpperCase()) ?? normalizeCoupon({ ...input, id: 0 } as any);
}

export async function getOrdersPage(limit = 20, offset = 0): Promise<OffsetPageResponse<Order>> {
  const payload = await apiFetch<CollectionEnvelope<Order>>(`/orders?skip=${offset}&limit=${limit}`);
  return normalizeOffsetPageResponse(payload, limit, offset, ["orders"]);
}

export async function validateCoupon(code: string, orderAmount: number): Promise<{ discount: number; message: string }> {
  return apiFetch("/coupons/validate", {
    method: "POST",
    body: JSON.stringify({ code, order_amount: orderAmount }),
  });
}

// ── Tickets (Support) API ─────────────────────────────────────────────────────

export interface Ticket {
  id: number;
  subject: string;
  status: string;
  priority: string;
  ticket_category?: "customer" | "supplier" | "logistics_partner";
  raised_by_role?: string | null;
  related_entity_type?: string | null;
  related_entity_id?: number | null;
  created_at: string;
  reply_count?: number;
  attachments?: TicketAttachment[];
  replies?: TicketReply[];
}

export interface TicketAttachment {
  id: number;
  original_name: string;
  file_path: string;
  mime_type?: string | null;
  file_size_bytes?: number | null;
  created_at: string;
}

export interface TicketReply {
  id: number;
  message: string;
  is_admin: boolean;
  created_at: string;
  attachments?: TicketAttachment[];
}

export async function getTickets(): Promise<Ticket[]> {
  return apiFetch("/tickets");
}

export async function getTicket(id: number): Promise<Ticket> {
  return apiFetch(`/tickets/${id}`);
}

export async function createTicket(data: {
  subject: string;
  message: string;
  priority?: string;
}): Promise<Ticket> {
  return apiFetch("/tickets", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function replyToTicket(id: number, message: string): Promise<TicketReply> {
  return apiFetch(`/tickets/${id}/reply`, {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export async function uploadTicketAttachment(id: number, file: {
  uri: string;
  name: string;
  mimeType?: string | null;
}): Promise<TicketAttachment> {
  const payload = new FormData();
  payload.append("file", {
    uri: file.uri,
    name: file.name,
    type: file.mimeType || "application/octet-stream",
  } as any);

  return apiFetch(`/tickets/${id}/attachments`, {
    method: "POST",
    body: payload,
  });
}

// ── Reviews API ───────────────────────────────────────────────────────────────

export interface Review {
  id: number;
  rating: number;
  comment: string;
  created_at: string;
  user?: { username: string; profile_image?: string };
}

export async function getProductReviews(productId: number): Promise<Review[]> {
  return apiFetch(`/reviews/product/${productId}`);
}

export async function createReview(data: {
  product_id: number;
  rating: number;
  comment: string;
}): Promise<Review> {
  return apiFetch("/reviews", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ── Newsletter API ────────────────────────────────────────────────────────────

export async function subscribeNewsletter(email: string): Promise<void> {
  await apiFetch("/email/newsletter/subscribe", {
    method: "POST",
    body: JSON.stringify({ email }),
    skipAuth: true,
  });
}

export async function unsubscribeNewsletter(email: string): Promise<void> {
  await apiFetch("/email/newsletter/unsubscribe", {
    method: "POST",
    body: JSON.stringify({ email }),
    skipAuth: true,
  });
}

export interface NewsletterPreferences {
  email: string;
  is_active: boolean;
  preferences?: Record<string, unknown> | string | null;
}

export async function getNewsletterPreferences(email?: string): Promise<NewsletterPreferences> {
  const suffix = email?.trim() ? `?email=${encodeURIComponent(email.trim())}` : "";
  return apiFetch(`/email/newsletter/preferences${suffix}`);
}

export interface ReferralActivityItem {
  id: number;
  event_type: string;
  points: number;
  channel?: string | null;
  description?: string | null;
  created_at: string;
  referred_user_id?: number | null;
  referred_username?: string | null;
}

export interface ReferralDashboard {
  referral_code: string;
  referral_link: string;
  total_points: number;
  referral_points: number;
  sharing_points: number;
  referred_count: number;
  recent_activity: ReferralActivityItem[];
}

export interface ReferralHistoryResponse {
  items: ReferralActivityItem[];
  total: number;
  limit: number;
  offset: number;
}

export function buildAppReferralLink(referralCode: string): string {
  const trimmed = referralCode.trim().toUpperCase();
  if (!trimmed) return "zozi://register";
  return `zozi://register?ref=${encodeURIComponent(trimmed)}`;
}

export async function getReferralDashboard(): Promise<ReferralDashboard> {
  return apiFetch("/auth/referrals/me");
}

export async function getReferralHistory(limit = 50, offset = 0): Promise<ReferralHistoryResponse> {
  return apiFetch(`/auth/referrals/history?limit=${limit}&offset=${offset}`);
}

export async function claimReferralShareBonus(channel = "mobile_app"): Promise<{
  awarded: boolean;
  points_awarded: number;
  message: string;
  channel: string;
  total_points: number;
  referral_points: number;
  sharing_points: number;
  next_eligible_at?: string;
}> {
  return apiFetch("/auth/referrals/share", {
    method: "POST",
    body: JSON.stringify({ channel }),
  });
}

// ── Search API ────────────────────────────────────────────────────────────────

export interface SearchProduct {
  id: number;
  name: string;
  price: number;
  image_url?: string;
  category?: { name: string } | string;
  rating_avg?: number;
}

function mapSearchProductRow(row: any): SearchProduct {
  const rawCategory = row?.category;
  let category: SearchProduct["category"] | undefined;
  if (typeof rawCategory === "string" && rawCategory.trim()) {
    category = { name: rawCategory.trim() };
  } else if (rawCategory && typeof rawCategory === "object" && typeof rawCategory.name === "string") {
    category = { name: rawCategory.name };
  }

  const rawRating = row?.rating_avg ?? row?.rating;
  const ratingAvg =
    rawRating != null && !Number.isNaN(Number(rawRating)) ? Number(rawRating) : undefined;

  return {
    id: Number(row?.id),
    name: String(row?.name ?? ""),
    price: Number(row?.price ?? 0),
    image_url: row?.image_url || undefined,
    category,
    rating_avg: ratingAvg,
  };
}

export async function searchProducts(params: {
  q?: string;
  category?: string;
  min_price?: string;
  max_price?: string;
  sort?: string;
  limit?: number;
  skip?: number;
  trending?: boolean;
  newArrivals?: boolean;
  bestSellers?: boolean;
  deals?: boolean;
  discountPct?: string;
  brand?: string;
  color?: string;
  minRating?: string;
  inStock?: boolean;
  tag?: string;
  supplier?: string;
}): Promise<SearchProduct[]> {
  const qs = buildProductQueryParams(params);
  const response = await apiFetch<{ products?: any[]; results?: any[] } | any[]>(
    `/products?${qs}`,
    { skipAuth: true } satisfies ApiFetchOptions
  );

  const rows = Array.isArray(response)
    ? response
    : Array.isArray(response?.products)
    ? response.products
    : Array.isArray(response?.results)
    ? response.results
    : [];

  return rows.map(mapSearchProductRow);
}

export interface SupplierSearchResponse {
  total: number;
  items: SupplierPublicSummary[];
}

export async function searchSuppliers(params: {
  q?: string;
  names?: string;
  limit?: number;
  offset?: number;
}): Promise<SupplierSearchResponse> {
  const qs = new URLSearchParams();
  if (params.q?.trim()) qs.set("q", params.q.trim());
  if (params.names?.trim()) qs.set("names", params.names.trim());
  qs.set("limit", String(params.limit ?? 6));
  qs.set("offset", String(params.offset ?? 0));

  const response = await apiFetch<SupplierSearchResponse>(`/suppliers?${qs.toString()}`, {
    skipAuth: true,
  } satisfies ApiFetchOptions);

  return {
    total: Number(response?.total ?? 0),
    items: Array.isArray(response?.items) ? response.items : [],
  };
}

export async function getRecommendations(params?: {
  limit?: number;
  recent_categories?: string[];
}): Promise<SearchProduct[]> {
  const query = new URLSearchParams();
  query.set("limit", String(params?.limit ?? 8));
  if (params?.recent_categories?.length) {
    query.set("recent_categories", params.recent_categories.join(","));
  }

  const response = await apiFetch<{ products?: any[]; results?: any[] } | any[]>(
    `/search/recommendations?${query.toString()}`,
    // Recommendations are a nice-to-have personalized widget. They must NOT trigger
    // the global auth-expiry redirect when the visitor is browsing unauthenticated.
    { skipAuth: true } satisfies ApiFetchOptions
  );
  const rows = Array.isArray(response)
    ? response
    : Array.isArray(response?.products)
    ? response.products
    : Array.isArray(response?.results)
    ? response.results
    : [];
  return rows.map(mapSearchProductRow);
}

export interface HierarchyPermissionsResponse {
  role: string;
  permissions: string[];
  matrix: Record<string, string[]>;
}

export async function getAdminHierarchyPermissions(): Promise<HierarchyPermissionsResponse> {
  return apiFetch("/admin/hierarchy/permissions");
}

// ── Supplier extended API ─────────────────────────────────────────────────────

export interface SupplierPayout {
  id: number;
  amount: number;
  status: string;
  method?: string | null;
  reference?: string | null;
  notes?: string | null;
  created_at: string;
  paid_at?: string;
  processed_at?: string | null;
}

export interface FinanceBankInstruction {
  configured: boolean;
  title: string;
  direction: string;
  account_label?: string | null;
  beneficiary_name?: string | null;
  bank_name?: string | null;
  branch_name?: string | null;
  account_number?: string | null;
  iban?: string | null;
  swift_code?: string | null;
  routing_number?: string | null;
  currency?: string | null;
  support_email?: string | null;
  support_phone?: string | null;
  remittance_reference_prefix?: string | null;
  reference_value?: string | null;
  reference_help?: string | null;
  instructions?: string | null;
  details_visible?: boolean;
}

export interface SupplierFinanceSummary {
  total_gross_revenue: number;
  total_commission_deducted: number;
  total_net_earnings: number;
  total_vat_on_orders: number;
  total_refund_reversals: number;
  pending_settlement: number;
  total_settled: number;
  total_orders: number;
  currency?: string;
  bank_instruction?: FinanceBankInstruction | null;
}

export interface SupplierFinanceSettlement {
  id: number;
  supplier_id: number;
  order_id: number;
  gross_amount: number;
  commission_rate: number;
  commission_deducted: number;
  vat_on_commission: number;
  net_amount: number;
  status: string;
  eligible_at?: string | null;
  settled_at?: string | null;
  currency: string;
  created_at: string;
  payment_method?: string | null;
  vat_amount?: number | null;
  delivery_total?: number | null;
  delivery_pickup_charge?: number | null;
  delivery_dropoff_charge?: number | null;
  destination_country?: string | null;
  destination_city?: string | null;
  partner_id?: number | null;
  partner_name?: string | null;
  partner_code?: string | null;
  service_area_label?: string | null;
  allocation_source?: string | null;
  refund_status?: string | null;
  supplier_reversal_amount?: number | null;
  customer_refund_amount?: number | null;
}

export interface SupplierShipment {
  id: number;
  order_id?: number;
  tracking_number?: string;
  carrier?: string;
  carrier_name?: string | null;
  status: string;
  distribution_channel?: string;
  current_hub?: string;
  scan_code?: string;
  shipping_address?: string | null;
  assigned_partner_id?: number | null;
  assigned_partner_name?: string | null;
  assigned_partner_code?: string | null;
  created_at: string;
  updated_at?: string;
}

export interface LogisticsPartnerOption {
  id: number;
  name: string;
  code: string;
  status: string;
  contact_name?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
  website?: string | null;
  coverage_regions?: string[];
  service_types?: string[];
  linked_username?: string | null;
  linked_user_email?: string | null;
}

export interface PublicLogisticsPartnerSummary {
  id: number;
  name: string;
  code: string;
  contact_name?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
  website?: string | null;
  coverage_regions?: string[];
  service_types?: string[];
  business_type?: string | null;
  country?: string | null;
  region?: string | null;
  city?: string | null;
  address?: string | null;
  postal_code?: string | null;
  bio?: string | null;
  about_us?: string | null;
  logo_url?: string | null;
  banner_url?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  verification_status?: string | null;
  verification_note?: string | null;
  status?: string | null;
  is_terms_accepted?: boolean | null;
  terms_version?: string | null;
  social_links?: Record<string, string> | null;
}

export interface PublicLogisticsPartnerServiceArea {
  id: number;
  partner_id: number;
  country_code: string;
  country_name: string;
  city_name?: string | null;
  origin_city?: string | null;
  zone_label?: string | null;
  charge_amount: number;
  minimum_charge?: number | null;
  per_kg_rate?: number | null;
  per_km_rate?: number | null;
  fuel_multiplier?: number | null;
  pickup_charge?: number | null;
  dropoff_charge?: number | null;
  currency: string;
  latitude?: number | null;
  longitude?: number | null;
  delivery_days_min?: number | null;
  delivery_days_max?: number | null;
  is_active: boolean;
  approval_status: string;
  review_note?: string | null;
  reviewed_by?: number | null;
  reviewed_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PublicLogisticsPartnerDetail extends PublicLogisticsPartnerSummary {
  service_areas?: PublicLogisticsPartnerServiceArea[];
}

export interface PublicLogisticsPartnerSearchResponse {
  total: number;
  items: PublicLogisticsPartnerSummary[];
}

export async function getSupplierPayouts(): Promise<SupplierPayout[]> {
  return apiFetch("/supplier/payouts");
}

export async function getSupplierFinanceSummary(): Promise<SupplierFinanceSummary> {
  return apiFetch("/cash-management/supplier/summary");
}

export async function getSupplierFinanceSettlements(): Promise<SupplierFinanceSettlement[]> {
  return apiFetch("/cash-management/supplier/settlements");
}

export async function getSupplierShipments(): Promise<SupplierShipment[]> {
  return apiFetch("/supplier/shipments");
}

export async function listLogisticsPartners(): Promise<LogisticsPartnerOption[]> {
  return apiFetch("/logistics-partners/");
}

export async function searchPublicLogisticsPartners(params: {
  q?: string;
  limit?: number;
} = {}): Promise<PublicLogisticsPartnerSearchResponse> {
  const search = new URLSearchParams();
  if (params.q?.trim()) search.set("q", params.q.trim());
  if (params.limit != null) search.set("limit", String(params.limit));
  return apiFetch(`/logistics-partners/public${search.toString() ? `?${search.toString()}` : ""}`, {
    skipAuth: true,
  });
}

export async function getPublicLogisticsPartner(partnerId: number | string): Promise<PublicLogisticsPartnerDetail> {
  return apiFetch(`/logistics-partners/public/${partnerId}`, {
    skipAuth: true,
  });
}

export interface LogisticsPartnerDashboardStats {
  total: number;
  active: number;
  delivered: number;
  pending: number;
  failed: number;
}

export interface LogisticsPartnerDashboardAnalytics {
  delivery_rate: number;
  average_transit_hours: number;
  scan_compliance_rate: number;
  sla_on_time_rate: number;
  shipments_with_events: number;
  sla_eligible_shipments: number;
  status_breakdown: Record<string, number>;
}

export interface LogisticsPartnerActiveShipment {
  id: number;
  order_id?: number;
  tracking_number?: string;
  carrier_name?: string;
  status: string;
  distribution_channel?: string;
  current_hub?: string;
  estimated_delivery?: string;
}

export interface LogisticsPartnerDashboardData {
  stats: LogisticsPartnerDashboardStats;
  analytics: LogisticsPartnerDashboardAnalytics;
  channel_breakdown: Record<string, number>;
  active_shipments: LogisticsPartnerActiveShipment[];
  live_locations: LogisticsPartnerLiveLocation[];
  route_plan: LogisticsPartnerRoutePlan;
  sla_alerts: LogisticsPartnerSlaAlert[];
  payout_summary: LogisticsPartnerPayoutSummary;
}

export interface LogisticsPartnerLiveLocation {
  shipment_id: number;
  order_id?: number;
  tracking_number?: string | null;
  status: string;
  current_hub?: string | null;
  location?: string | null;
  latitude: number;
  longitude: number;
  recorded_at?: string | null;
}

export interface LogisticsPartnerRouteStop extends LogisticsPartnerLiveLocation {
  stop_number: number;
  distance_from_previous_km: number;
}

export interface LogisticsPartnerRoutePlan {
  generated_at?: string | null;
  total_stops: number;
  estimated_distance_km: number;
  estimated_duration_hours: number;
  stops: LogisticsPartnerRouteStop[];
}

export interface LogisticsPartnerSlaAlert {
  shipment_id: number;
  order_id?: number;
  tracking_number?: string | null;
  status: string;
  current_hub?: string | null;
  estimated_delivery: string;
  overdue_hours: number;
}

export interface LogisticsPartnerPayout {
  id: number;
  partner_id: number;
  partner_name?: string | null;
  partner_code?: string | null;
  amount: number;
  status: string;
  method?: string | null;
  reference?: string | null;
  notes?: string | null;
  created_at?: string | null;
  processed_at?: string | null;
}

export interface LogisticsFinanceSummary {
  total_delivery_fees: number;
  total_pickup_fees: number;
  total_dropoff_fees: number;
  total_cod_collected: number;
  total_cod_remitted: number;
  total_refund_reversals: number;
  pending_cod_remittance: number;
  total_deliveries: number;
  currency?: string;
  bank_instruction?: FinanceBankInstruction | null;
}

export interface LogisticsFinanceAllocation {
  supplier_id: number;
  supplier_name?: string | null;
  shipping_amount: number;
  pickup_charge: number;
  dropoff_charge: number;
}

export interface LogisticsFinanceSettlement {
  id: number;
  partner_id: number;
  order_id: number;
  pickup_charge: number;
  dropoff_charge: number;
  total_delivery_fee: number;
  cod_collected?: number | null;
  cod_remitted?: number | null;
  cod_retained?: number | null;
  cod_remittance_status?: string | null;
  status: string;
  eligible_at?: string | null;
  settled_at?: string | null;
  currency: string;
  created_at: string;
  payment_method?: string | null;
  destination_country?: string | null;
  destination_city?: string | null;
  partner_name?: string | null;
  partner_code?: string | null;
  service_area_label?: string | null;
  allocation_source?: string | null;
  refund_status?: string | null;
  logistics_reversal_amount?: number | null;
  customer_refund_amount?: number | null;
  allocations?: LogisticsFinanceAllocation[];
}

export interface LogisticsPartnerPayoutSummary {
  total_earned: number;
  available_balance: number;
  pending_amount: number;
  completed_amount: number;
  payout_count: number;
  recent_payouts: LogisticsPartnerPayout[];
}

export interface LogisticsPartnerShipment {
  id: number;
  order_id?: number;
  supplier_id?: number;
  supplier_name?: string | null;
  supplier_phone?: string | null;
  supplier_pickup_address?: string | null;
  supplier_pickup_location?: string | null;
  assigned_partner_id?: number | null;
  assigned_partner_name?: string | null;
  assigned_partner_code?: string | null;
  customer_name?: string | null;
  customer_phone?: string | null;
  customer_dropoff_address?: string | null;
  customer_dropoff_location?: string | null;
  carrier_name?: string | null;
  tracking_number?: string | null;
  status: string;
  status_label?: string | null;
  distribution_channel?: string | null;
  current_hub?: string | null;
  scan_code?: string | null;
  shipping_address?: string | null;
  delivery_location?: string | null;
  package_count?: number | null;
  package_weight_kg?: number | null;
  package_dimensions?: string | null;
  packaged_at?: string | null;
  packaging_notes?: string | null;
  shipped_at?: string | null;
  estimated_delivery?: string | null;
  actual_delivery?: string | null;
  delivery_signature_name?: string | null;
  delivery_signature_data_url?: string | null;
  delivery_signature_captured_at?: string | null;
  active_confirmation_request?: ShipmentConfirmationRequest | null;
  estimated_partner_payout?: number | null;
  settlement_status?: string | null;
  order_payment_status?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface LogisticsPartnerShipmentsResponse {
  items: LogisticsPartnerShipment[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface LogisticsPartnerShipmentStatusUpdate {
  status?: string;
  release_assignment?: boolean;
  delivery_signature_name?: string;
  delivery_signature_data_url?: string;
  event_type?: string;
  current_hub?: string;
  tracking_number?: string;
  notes?: string;
  scan_code?: string;
}

export interface ShipmentConfirmationRequest {
  id: number;
  shipment_id: number;
  order_id: number;
  supplier_id: number;
  requester_user_id?: number | null;
  requester_role?: string | null;
  target_user_id?: number | null;
  target_role?: string | null;
  confirmation_type: "pickup" | "delivery";
  confirmation_type_label?: string | null;
  status: "pending" | "accepted" | "rejected" | "cancelled";
  requested_status: string;
  requested_event_type?: string | null;
  current_hub?: string | null;
  tracking_number?: string | null;
  delivery_signature_name?: string | null;
  delivery_signature_data_url?: string | null;
  notes?: string | null;
  response_notes?: string | null;
  created_at?: string | null;
  responded_at?: string | null;
}

export interface ShipmentConfirmationCreatePayload {
  requested_status: "shipped" | "delivered";
  current_hub?: string;
  tracking_number?: string;
  scan_code?: string;
  event_type?: string;
  notes?: string;
  delivery_signature_name?: string;
  delivery_signature_data_url?: string;
}

export interface ShipmentConfirmationRespondPayload {
  decision: "accepted" | "rejected";
  response_notes?: string;
}

export async function getLogisticsPartnerDashboard(): Promise<LogisticsPartnerDashboardData> {
  return apiFetch("/logistics-partners/dashboard");
}

// ── Logistics Partner Profile ────────────────────────────────────────────────

export interface LogisticsPartnerProfile {
  id: number;
  name: string;
  code: string;
  contact_name?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
  website?: string | null;
  business_type?: string | null;
  country?: string | null;
  region?: string | null;
  city?: string | null;
  address?: string | null;
  postal_code?: string | null;
  tax_id?: string | null;
  bio?: string | null;
  about_us?: string | null;
  logo_url?: string | null;
  banner_url?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  verification_status?: string | null;
  verification_note?: string | null;
  status?: string | null;
  is_terms_accepted?: boolean | null;
  terms_version?: string | null;
  service_types?: string[] | null;
  coverage_regions?: string[] | null;
  social_links?: Record<string, string> | null;
}

export interface LogisticsPartnerServiceArea {
  id: number;
  country: string;
  region?: string | null;
  city?: string | null;
  origin_city?: string | null;
  charge?: number | null;
  currency?: string | null;
}

function normalizeLogisticsPartnerServiceArea(area: any): LogisticsPartnerServiceArea {
  const rawCharge = area?.charge ?? area?.charge_amount;
  return {
    id: Number(area?.id ?? 0),
    country: String(area?.country ?? area?.country_name ?? area?.country_code ?? "").trim(),
    region: area?.region ?? area?.zone_label ?? null,
    city: area?.city ?? area?.city_name ?? null,
    origin_city: area?.origin_city ?? null,
    charge: rawCharge == null || rawCharge === "" ? null : Number(rawCharge),
    currency: area?.currency ?? null,
  };
}

export interface UploadableDocumentAsset {
  uri: string;
  name?: string | null;
  mimeType?: string | null;
}

export interface LogisticsPartnerDocument {
  id: number;
  partner_id: number;
  document_type: string;
  document_name: string;
  file_url: string;
  status: "pending" | "approved" | "rejected" | "under_review";
  expires_at?: string | null;
  review_note?: string | null;
  reviewed_by?: number | null;
  reviewed_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface LogisticsPartnerDocumentUpload {
  file: UploadableDocumentAsset;
  documentType: string;
  documentName?: string;
  expiresAt?: string | null;
}

export async function getLogisticsPartnerProfile(): Promise<LogisticsPartnerProfile> {
  return apiFetch("/logistics-partners/profile");
}

export async function updateLogisticsPartnerProfile(data: Partial<LogisticsPartnerProfile>): Promise<LogisticsPartnerProfile> {
  return apiFetch("/logistics-partners/profile", {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function getLogisticsPartnerServiceAreas(): Promise<LogisticsPartnerServiceArea[]> {
  const payload = await apiFetch<any>("/logistics-partners/service-areas");
  return normalizeCollectionResponse(payload).map((area) => normalizeLogisticsPartnerServiceArea(area));
}

export async function addLogisticsPartnerServiceArea(data: Omit<LogisticsPartnerServiceArea, "id">): Promise<LogisticsPartnerServiceArea> {
  const payload = await apiFetch<any>("/logistics-partners/service-areas", {
    method: "POST",
    body: JSON.stringify({
      country_name: data.country,
      city_name: data.city,
      origin_city: data.origin_city,
      charge_amount: data.charge,
      currency: data.currency,
      region: data.region,
    }),
  });
  return normalizeLogisticsPartnerServiceArea(payload);
}

export async function removeLogisticsPartnerServiceArea(id: number): Promise<void> {
  await apiFetch(`/logistics-partners/service-areas/${id}`, { method: "DELETE" });
}

export async function acceptLogisticsPartnerTerms(): Promise<void> {
  await apiFetch("/logistics-partners/profile/terms/accept", { method: "POST" });
}

export async function listLogisticsPartnerDocuments(): Promise<LogisticsPartnerDocument[]> {
  return apiFetch("/logistics-partners/me/docs");
}

export async function uploadLogisticsPartnerDocument(data: LogisticsPartnerDocumentUpload): Promise<LogisticsPartnerDocument> {
  const formData = new FormData();
  formData.append("file", {
    uri: data.file.uri,
    name: data.file.name || "document",
    type: data.file.mimeType || "application/octet-stream",
  } as any);
  formData.append("document_type", data.documentType);
  if (data.documentName?.trim()) {
    formData.append("document_name", data.documentName.trim());
  } else if (data.file.name) {
    formData.append("document_name", data.file.name.replace(/\.[^.]+$/, ""));
  }
  if (data.expiresAt?.trim()) {
    formData.append("expires_at", data.expiresAt.trim());
  }
  return apiFetch("/logistics-partners/me/docs/upload", {
    method: "POST",
    body: formData as never,
  } as never);
}

export async function deleteLogisticsPartnerDocument(id: number): Promise<{ detail: string }> {
  return apiFetch(`/logistics-partners/me/docs/${id}`, { method: "DELETE" });
}

export async function getLogisticsPartnerPayouts(): Promise<LogisticsPartnerPayout[]> {
  return apiFetch("/logistics-partners/payouts");
}

export async function getLogisticsFinanceSummary(): Promise<LogisticsFinanceSummary> {
  return apiFetch("/cash-management/logistics/summary");
}

export async function getLogisticsFinanceSettlements(): Promise<LogisticsFinanceSettlement[]> {
  return apiFetch("/cash-management/logistics/settlements");
}

// ── Recipient bank accounts ───────────────────────────────────────────────────

export interface RecipientBankAccount {
  configured: boolean;
  id?: number;
  beneficiary_name?: string | null;
  bank_name?: string | null;
  branch_name?: string | null;
  account_number?: string | null;
  iban?: string | null;
  swift_code?: string | null;
  routing_number?: string | null;
  currency?: string;
  bank_country?: string | null;
  verification_status?: "pending" | "verified" | "rejected";
  verification_note?: string | null;
  verified_at?: string | null;
}

export interface RecipientBankAccountUpsert {
  beneficiary_name?: string | null;
  bank_name?: string | null;
  branch_name?: string | null;
  account_number?: string | null;
  iban?: string | null;
  swift_code?: string | null;
  routing_number?: string | null;
  currency?: string;
  bank_country?: string | null;
}

export async function getSupplierBankAccount(): Promise<RecipientBankAccount> {
  return apiFetch("/supplier/bank-account");
}

export async function upsertSupplierBankAccount(data: RecipientBankAccountUpsert): Promise<{ ok: boolean; id: number; verification_status: string; message: string }> {
  return apiFetch("/supplier/bank-account", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function getPartnerBankAccount(): Promise<RecipientBankAccount> {
  return apiFetch("/logistics-partners/me/bank-account");
}

export async function upsertPartnerBankAccount(data: RecipientBankAccountUpsert): Promise<{ ok: boolean; id: number; verification_status: string; message: string }> {
  return apiFetch("/logistics-partners/me/bank-account", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function requestLogisticsPartnerPayout(data: {
  amount: number;
  method?: string;
  notes?: string;
}): Promise<LogisticsPartnerPayout> {
  return apiFetch("/logistics-partners/payouts/request", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function getLogisticsPartnerShipments(params: {
  page?: number;
  page_size?: number;
  status?: string;
} = {}): Promise<LogisticsPartnerShipmentsResponse> {
  const search = new URLSearchParams();
  if (params.page != null) search.set("page", String(params.page));
  if (params.page_size != null) search.set("page_size", String(params.page_size));
  if (params.status) search.set("status", params.status);
  const suffix = search.toString();
  return apiFetch(`/logistics-partners/shipments${suffix ? `?${suffix}` : ""}`);
}

export async function lookupLogisticsPartnerShipment(code: string): Promise<LogisticsPartnerShipment> {
  return apiFetch(`/logistics-partners/shipments/scan?code=${encodeURIComponent(code)}`);
}

export async function updateLogisticsPartnerShipmentStatus(
  shipmentId: number,
  data: LogisticsPartnerShipmentStatusUpdate,
): Promise<Pick<LogisticsPartnerShipment, "status" | "status_label" | "current_hub" | "tracking_number">> {
  return apiFetch(`/logistics-partners/shipments/${shipmentId}/status`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function createLogisticsPartnerShipmentConfirmationRequest(
  shipmentId: number,
  data: ShipmentConfirmationCreatePayload,
): Promise<{
  shipment_id: number;
  order_id: number;
  status: string;
  status_label?: string | null;
  request: ShipmentConfirmationRequest;
}> {
  return apiFetch(`/logistics-partners/shipments/${shipmentId}/confirmation-request`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export interface LogisticsSummary {
  awaiting_fulfilment: number;
  in_transit: number;
  delivered_total: number;
  total_shipments: number;
  pending_shipments: number;
  active_zones: number;
  distribution_channels?: {
    channel: string;
    total: number;
    delivered: number;
    in_transit: number;
    pending: number;
  }[];
}

export interface PendingFulfilmentOrder {
  order_id: number;
  order_status: string;
  total_amount: number;
  shipping_address?: string;
  created_at?: string;
  paid_at?: string | null;
  items: {
    product_id: number;
    product_name: string;
    quantity: number;
    price: number;
  }[];
}

export interface ShipmentEvent {
  id: number;
  shipment_id: number;
  order_id: number;
  actor_role: string;
  event_type: string;
  status_after?: string;
  distribution_channel?: string;
  location?: string;
  scan_code?: string;
  notes?: string;
  created_at: string;
}

export async function getLogisticsSummary(): Promise<LogisticsSummary> {
  return apiFetch("/logistics/summary");
}

export async function getPendingFulfilmentOrders(): Promise<PendingFulfilmentOrder[]> {
  return apiFetch("/logistics/orders/pending");
}

export async function getDistributionChannels(): Promise<
  {
    channel: string;
    total_shipments: number;
    in_transit: number;
    delivered: number;
    returned_or_failed: number;
  }[]
> {
  return apiFetch("/logistics/distribution/channels");
}

export async function createShipment(data: {
  order_id: number;
  assigned_partner_id?: number | null;
  carrier_id?: number;
  carrier_name?: string;
  tracking_number?: string;
  estimated_delivery?: string;
  notes?: string;
  distribution_channel?: string;
  current_hub?: string;
  package_count?: number;
  package_weight_kg?: number;
  package_dimensions?: string;
  packaging_notes?: string;
}): Promise<SupplierShipment> {
  return apiFetch("/logistics/shipments", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateShipmentStatus(
  shipmentId: number,
  data: {
    status?: string;
    assigned_partner_id?: number | null;
    tracking_number?: string;
    notes?: string;
    distribution_channel?: string;
    current_hub?: string;
  }
): Promise<SupplierShipment> {
  return apiFetch(`/logistics/shipments/${shipmentId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function getShipmentEvents(shipmentId: number): Promise<ShipmentEvent[]> {
  return apiFetch(`/logistics/shipments/${shipmentId}/events`);
}

export interface SupplierLabelPayload {
  order_id: number;
  shipment_id: number | null;
  has_shipment: boolean;
  sheet_mode: "packing" | "shipment";
  invoice_number: string;
  order_status: string;
  shipment_status: string;
  shipment_status_label?: string | null;
  customer_name: string;
  customer_email: string | null;
  customer_phone: string | null;
  shipping_address: string | null;
  delivery_location: string | null;
  delivery_note: string | null;
  carrier_name: string | null;
  tracking_number: string | null;
  scan_code: string;
  current_hub: string | null;
  package_count: number | null;
  package_weight_kg: number | null;
  package_dimensions: string | null;
  packaged_at: string | null;
  packaging_notes: string | null;
  subtotal: number;
  vat: number;
  shipping: number;
  total: number;
  items: {
    order_item_id?: number;
    product_id: number;
    product_name: string;
    quantity: number;
    unit_price: number;
    line_total: number;
  }[];
}

export async function getSupplierOrderLabel(orderId: number): Promise<SupplierLabelPayload> {
  return apiFetch(`/supplier/orders/${orderId}/label`);
}

export async function scanShipmentEvent(
  shipmentId: number,
  data: {
    scan_code: string;
    event_type:
      | "picked_from_supplier"
      | "logistics_received"
      | "distribution_checkpoint"
      | "out_for_delivery"
      | "customer_received"
      | "shipment_failed"
      | "shipment_returned";
    status_after?: string;
    distribution_channel?: string;
    location?: string;
    notes?: string;
  }
): Promise<{ shipment: SupplierShipment; event: ShipmentEvent }> {
  return apiFetch(`/logistics/shipments/${shipmentId}/scan`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export interface OrderInvoice {
  id: number;
  invoice_number: string;
  order_id: number;
  created_at: string;
  status: string;
  customer_name: string;
  customer_email: string;
  customer_address: string;
  supplier_name: string;
  supplier_email?: string;
  items: {
    product_id: number;
    product_name: string;
    quantity: number;
    unit_price: number;
    total: number;
    supplier_id?: number;
    supplier_name?: string;
  }[];
  subtotal: number;
  vat: number;
  shipping: number;
  total: number;
  logistics: {
    stage: "supplier" | "warehouse" | "in_transit" | "delivered";
    label: string;
    timestamp?: string | null;
    notes?: string | null;
    completed: boolean;
  }[];
  tracking_number?: string;
  carrier?: string;
  distribution_channels?: string[];
  scan_codes?: string[];
}

export interface OrderTrackingStep {
  key: "placed" | "preparing" | "picked_up" | "in_transit" | "delivered";
  label: string;
  completed: boolean;
  active: boolean;
  timestamp?: string | null;
  notes?: string | null;
}

export interface OrderTrackingEvent {
  id: number;
  shipment_id: number;
  order_id: number;
  supplier_id: number;
  actor_user_id?: number | null;
  actor_role: string;
  event_type: string;
  event_label?: string | null;
  status_after?: string | null;
  distribution_channel?: string | null;
  location?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  scan_code?: string | null;
  notes?: string | null;
  created_at?: string | null;
}

export interface OrderTrackingReturnSummary {
  id: number;
  intent: "return" | "replacement";
  status: string;
  reason: string;
  resolution_notes?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface OrderTrackingShipment {
  id: number;
  order_id: number;
  supplier_id: number;
  supplier_name?: string | null;
  assigned_partner_id?: number | null;
  assigned_partner_name?: string | null;
  assigned_partner_code?: string | null;
  carrier_id?: number | null;
  carrier_name?: string | null;
  tracking_number?: string | null;
  tracking_url?: string | null;
  status: string;
  status_label?: string | null;
  distribution_channel?: string | null;
  current_hub?: string | null;
  scan_code?: string | null;
  package_count?: number | null;
  package_weight_kg?: number | null;
  package_dimensions?: string | null;
  packaged_at?: string | null;
  packaged_by_user_id?: number | null;
  packaging_notes?: string | null;
  shipping_address?: string | null;
  shipped_at?: string | null;
  estimated_delivery?: string | null;
  actual_delivery?: string | null;
  delivery_signature_name?: string | null;
  delivery_signature_data_url?: string | null;
  delivery_signature_captured_at?: string | null;
  notes?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  active_confirmation_request?: ShipmentConfirmationRequest | null;
  recent_confirmation_requests?: ShipmentConfirmationRequest[] | null;
  events?: OrderTrackingEvent[] | null;
}

export interface OrderTrackingFinanceAllocation {
  supplier_id: number;
  supplier_name?: string | null;
  partner_id?: number | null;
  partner_name?: string | null;
  partner_code?: string | null;
  service_area_id?: number | null;
  service_area_label?: string | null;
  allocation_source?: string | null;
  destination_country?: string | null;
  destination_city?: string | null;
  shipping_amount: number;
  pickup_charge: number;
  dropoff_charge: number;
  estimated_delivery_min?: number | null;
  estimated_delivery_max?: number | null;
  currency: string;
}

export interface OrderTrackingFinanceRefund {
  id: number;
  status: string;
  refund_reason: string;
  refund_method: string;
  customer_refund_amount: number;
  supplier_reversal: number;
  logistics_reversal: number;
  commission_reversal: number;
  vat_adjustment: number;
  created_at?: string | null;
  processed_at?: string | null;
}

export interface OrderTrackingFinanceBreakdown {
  payment_method?: string | null;
  subtotal_amount: number;
  discount_amount: number;
  shipping_amount: number;
  vat_amount: number;
  service_fee_amount: number;
  total_amount: number;
  selected_partner_id?: number | null;
  selected_service_area_id?: number | null;
  estimated_delivery_min?: number | null;
  estimated_delivery_max?: number | null;
  allocations: OrderTrackingFinanceAllocation[];
  refund?: OrderTrackingFinanceRefund | null;
}

export interface OrderTracking {
  order_id: number;
  order_status: string;
  order_status_label?: string | null;
  subtotal_amount?: number;
  shipping_amount?: number;
  vat_amount?: number;
  total_amount?: number;
  payment_method?: string;
  shipment_count: number;
  delivered_shipments: number;
  pending_shipments: number;
  all_shipments_delivered: boolean;
  tracking_numbers: string[];
  available_scan_codes: string[];
  shipping_address?: string | null;
  customer_phone?: string | null;
  delivery_location?: string | null;
  delivery_note?: string | null;
  active_return_request?: OrderTrackingReturnSummary | null;
  finance_breakdown?: OrderTrackingFinanceBreakdown | null;
  items: {
    order_item_id?: number;
    product_id: number;
    product_name: string;
    quantity: number;
    price: number;
    supplier_id?: number | null;
  }[];
  timeline: OrderTrackingStep[];
  shipments: OrderTrackingShipment[];
}

export async function getOrderInvoice(orderId: number): Promise<OrderInvoice> {
  return apiFetch(`/orders/${orderId}/invoice`);
}

export async function getOrderTracking(orderId: number): Promise<OrderTracking> {
  return apiFetch(`/orders/${orderId}/tracking`);
}

export async function respondToShipmentConfirmation(
  orderId: number,
  confirmationId: number,
  data: ShipmentConfirmationRespondPayload,
): Promise<{
  id: number;
  status: string;
  responded_at?: string | null;
  response_notes?: string | null;
  shipment_id: number;
  order_id: number;
  requested_status: string;
}> {
  return apiFetch(`/orders/${orderId}/confirmation-requests/${confirmationId}/respond`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function confirmOrderReceiptByScan(
  orderId: number,
  scan_code: string,
  location?: string,
  notes?: string
): Promise<{ message: string; order_id: number; shipment_id: number; status: string }> {
  return apiFetch(`/orders/${orderId}/scan-receipt`, {
    method: "POST",
    body: JSON.stringify({ scan_code, location, notes }),
  });
}

// ───────── Returns ─────────────────────────────────────────────────────────
export interface ReturnRequestItem {
  product_id: number;
  product_name?: string;
  quantity: number;
  price?: number;
}

export interface ReturnRequest {
  id: number;
  order_id: number;
  reason: string;
  status: "pending" | "approved" | "rejected" | "completed" | "refunded";
  refund_amount?: number;
  notes?: string;
  items?: ReturnRequestItem[];
  created_at: string;
  updated_at?: string;
}

export interface SupplierReturnReview {
  decision: "pending" | "approved" | "rejected" | "restocked";
  notes?: string | null;
  updated_at?: string | null;
  restocked_at?: string | null;
  restock_applied: boolean;
}

export interface SupplierReturnQueueItem {
  id: number;
  order_id: number;
  user_id: number;
  customer_name?: string | null;
  customer_email?: string | null;
  intent: "return" | "replacement";
  reason: string;
  status: string;
  resolution_notes?: string | null;
  shipping_address?: string | null;
  supplier_owned_items: ReturnRequestItem[];
  supplier_review: SupplierReturnReview;
  created_at: string;
  updated_at?: string | null;
  resolved_at?: string | null;
}

export async function listReturns(): Promise<ReturnRequest[]> {
  return apiFetch("/returns");
}

export async function listSupplierReturns(): Promise<SupplierReturnQueueItem[]> {
  const payload = await apiFetch<any>("/supplier/returns");
  return normalizeCollectionResponse(payload);
}

export async function updateSupplierReturnReview(
  returnId: number,
  data: { supplier_decision: SupplierReturnReview["decision"]; supplier_notes?: string }
): Promise<SupplierReturnQueueItem> {
  return apiFetch(`/supplier/returns/${returnId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function getReturn(id: number): Promise<ReturnRequest> {
  return apiFetch(`/returns/${id}`);
}

export async function createReturn(data: {
  order_id: number;
  reason: string;
  items?: ReturnRequestItem[];
}): Promise<ReturnRequest> {
  return apiFetch("/returns", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ───────── Supplier Documents ────────────────────────────────────────────────
export interface SupplierDocument {
  id: number;
  document_type: string;
  file_url: string;
  file_name?: string;
  document_name?: string;
  status: "pending" | "approved" | "rejected";
  notes?: string;
  review_note?: string;
  expires_at?: string | null;
  uploaded_at: string;
}

function normalizeSupplierDocument(payload: any): SupplierDocument {
  return {
    id: Number(payload?.id ?? 0),
    document_type: String(payload?.document_type ?? "other"),
    file_url: String(payload?.file_url ?? ""),
    file_name: payload?.file_name ?? payload?.document_name ?? undefined,
    document_name: payload?.document_name ?? payload?.file_name ?? undefined,
    status: payload?.status ?? "pending",
    notes: payload?.notes ?? payload?.review_note ?? undefined,
    review_note: payload?.review_note ?? payload?.notes ?? undefined,
    expires_at: payload?.expires_at ?? null,
    uploaded_at: String(payload?.uploaded_at ?? payload?.created_at ?? new Date(0).toISOString()),
  };
}

export async function listSupplierDocuments(): Promise<SupplierDocument[]> {
  const payload = await apiFetch<any>("/supplier-documents/my");
  return normalizeCollectionResponse<any>(payload).map((item) => normalizeSupplierDocument(item));
}

export async function uploadSupplierDocument(data: {
  document_type: string;
  file_url: string;
  file_name?: string;
}): Promise<SupplierDocument> {
  const payload = await apiFetch("/supplier-documents/my", {
    method: "POST",
    body: JSON.stringify(data),
  });
  return normalizeSupplierDocument(payload);
}

// ───────── Product Verification ─────────────────────────────────────────────
export interface ProductVerificationResult {
  id: number;
  product_id: number;
  product_name?: string;
  barcode?: string;
  status: "pending" | "verified" | "failed";
  notes?: string;
  verified_at?: string;
  created_at: string;
}

export async function verifyProductBarcode(data: {
  barcode: string;
  product_id?: number;
  notes?: string;
}): Promise<ProductVerificationResult> {
  return apiFetch("/product-verifications", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ───────── Push Notifications ────────────────────────────────────────────────

export async function registerPushToken(data: {
  token: string;
  platform?: string;
  device_name?: string;
}): Promise<void> {
  await apiFetch("/push-notifications/register", {
    method: "POST",
    body: JSON.stringify({ platform: "expo", ...data }),
  });
}

export async function unregisterPushToken(token: string): Promise<void> {
  await apiFetch("/push-notifications/unregister", {
    method: "DELETE",
    body: JSON.stringify({ token, platform: "expo" }),
  });
}

// ── Social Auth API ───────────────────────────────────────────────────────────

export interface SocialAuthPayload {
  provider: "google" | "facebook";
  access_token: string;
  id_token?: string;
}

export async function socialLogin(payload: SocialAuthPayload): Promise<AuthResponse> {
  const res = await apiFetch<AuthResponse>(`/auth/social/json`, {
    method: "POST",
    body: JSON.stringify(payload),
    skipAuth: true,
  });
  mobileAdapter.setAccessToken(res.access_token, res.expires_in);
  mobileAdapter.setRefreshToken(res.refresh_token);
  return res;
}

export async function signInWithGoogle(): Promise<AuthResponse> {
  return socialSignIn("google");
}

export async function signInWithFacebook(): Promise<AuthResponse> {
  return socialSignIn("facebook");
}

export async function signInWithApple(): Promise<AuthResponse> {
  return socialSignIn("apple");
}

// ── Notification Preferences API ───────────────────────────────────────────────

export interface NotificationPreferences {
  order_status: boolean;
  promotions: boolean;
  newsletter: boolean;
  ai_assistant: boolean;
}

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
