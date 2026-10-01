"use client";

import { useCallback, useMemo } from "react";
import { apiFetch, parseJsonResponse, getErrorMessage } from "@/lib/api";
import { useAdminCountry } from "@/lib/useAdminCountry";
import { normalizeListPage, type ListPage } from "@/lib/listResponse";

export interface AdminApiResult<T = unknown> {
  data: T | null;
  error: string | null;
  ok: boolean;
  status: number;
}

/**
 * Canonical admin resource base paths.
 *
 * Global (all-countries) view uses the base path directly (served by admin.py):
 *   GET /admin/products, /admin/orders, /admin/users, ...
 * Country-scoped view appends the ISO country code (re-prefixed routers):
 *   GET /admin/products/OM, /admin/orders/OM, ...
 */
export const ADMIN_RESOURCES = {
  products: "/admin/products",
  orders: "/admin/orders",
  users: "/admin/users",
  categories: "/admin/categories",
  banners: "/admin/banners",
  payouts: "/admin/payouts",
  campaigns: "/admin/campaigns",
  coupons: "/admin/coupons",
  "flash-sales": "/admin/flash-sales",
} as const;

export type AdminResource = keyof typeof ADMIN_RESOURCES | (string & {});

export interface UseAdminApiOptions {
  /**
   * - "auto" (default): global when "All Countries" (*) is selected, else country-scoped.
   * - "global": always hit the base /admin/{resource} endpoint (admin.py).
   * - "country": always append the country code (falls back to global when * selected).
   */
  countryMode?: "auto" | "global" | "country";
}

function resolveBase(resource?: AdminResource): string {
  if (!resource) return "";
  const known = (ADMIN_RESOURCES as Record<string, string>)[resource];
  if (known) return known;
  // Allow passing a raw base path like "/admin/tickets".
  if (resource.startsWith("/admin")) return resource;
  return `/admin/${resource.replace(/^\/+/, "")}`;
}

/**
 * useAdminApi — single wiring helper for admin pages.
 *
 * Usage:
 *   const { adminFetch, list, isGlobalView, countryCode } = useAdminApi("products");
 *   const page = await list({ page: 1, size: 50 });   // GET /admin/products[/{cc}]?page=1&size=50
 *   await adminFetch(`/${id}/approve`, { method: "PUT" });
 *
 * Legacy (no resource): adminFetch passes the full /admin/... path through unchanged.
 */
export function useAdminApi(resource?: AdminResource, options: UseAdminApiOptions = {}) {
  const { selectedCountry, isGlobalView } = useAdminCountry();
  const countryCode = selectedCountry?.code || "*";
  const mode = options.countryMode ?? "auto";

  const useGlobal = useMemo(() => {
    if (mode === "global") return true;
    if (mode === "country") return countryCode === "*";
    return isGlobalView || countryCode === "*";
  }, [mode, isGlobalView, countryCode]);

  const base = useMemo(() => resolveBase(resource), [resource]);

  const buildUrl = useCallback(
    (path = "") => {
      const clean = path ? (path.startsWith("/") ? path : "/" + path) : "";
      if (!base) {
        // Legacy mode: caller supplies the entire path.
        return clean || "/";
      }
      return useGlobal ? `${base}${clean}` : `${base}/${countryCode}${clean}`;
    },
    [base, useGlobal, countryCode],
  );

  const adminFetch = useCallback(
    async <T = unknown>(
      path = "",
      opts: Parameters<typeof apiFetch>[1] = {},
    ): Promise<AdminApiResult<T>> => {
      const url = buildUrl(path);
      try {
        const res = await apiFetch(url, opts);
        const data = await parseJsonResponse(res);
        if (res.ok) {
          return { data: data as T | null, error: null, ok: true, status: res.status };
        }
        return { data: null, error: getErrorMessage(data), ok: false, status: res.status };
      } catch (err) {
        return {
          data: null,
          error: err instanceof Error ? err.message : "Request failed",
          ok: false,
          status: 0,
        };
      }
    },
    [buildUrl],
  );

  const list = useCallback(
    async <T = unknown>(
      params: Record<string, string | number | boolean | undefined | null> = {},
      opts: Parameters<typeof apiFetch>[1] = {},
    ): Promise<{ page: ListPage<T>; error: string | null; ok: boolean; status: number }> => {
      const qs = new URLSearchParams();
      for (const [k, v] of Object.entries(params)) {
        if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
      }
      const suffix = qs.toString() ? `?${qs.toString()}` : "";
      const res = await adminFetch<unknown>(suffix, opts);
      return {
        page: normalizeListPage<T>(res.data),
        error: res.error,
        ok: res.ok,
        status: res.status,
      };
    },
    [adminFetch],
  );

  return { adminFetch, list, buildUrl, countryCode, isGlobalView: useGlobal };
}
