"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  DollarSign, Package, RefreshCw, ShoppingCart, TrendingUp, Users,
} from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";
import { useAdminCountry } from "@/lib/useAdminCountry";
import { useAuth } from "@/lib/useAuth";
import { useCurrencyStore } from "@/stores/currencyStore";
import { useToastStore } from "@/stores/toastStore";
import { apiFetch } from "@/lib/api";

type CountryScope = "GLOBAL" | "AE" | "SA";
const COUNTRY_OPTIONS: CountryScope[] = ["GLOBAL", "AE", "SA"];

interface OverviewResponse {
  total_revenue?: number;
  total_orders?: number;
  total_users?: number;
  total_products?: number;
  total_suppliers?: number;
  revenue_growth?: number;
  orders_growth?: number;
  users_growth?: number;
  top_products?: Array<{ name: string; revenue?: number; units?: number }>;
  user_growth?: Array<{ period: string; users?: number }>;
  customer_insights?: Record<string, unknown>;
  by_country?: Record<string, unknown>;
}

function pickCountryParam(scope: CountryScope): string | null {
  if (scope === "GLOBAL") return null;
  return scope;
}

function AdminAnalyticsInner() {
  const router = useRouter();
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();
  const role = user?.role ?? null;
  const { assignedCountries } = useAdminCountry();
  const formatMoney = useCurrencyStore((s) => s.format);
  const addToast = useToastStore((s) => s.addToast);

  const [scope, setScope] = useState<CountryScope>("GLOBAL");
  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [timeseries, setTimeseries] = useState<any>(null);
  const [topProducts, setTopProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn || !["admin", "sub_admin"].includes(role || "")) {
      router.push("/admin/login");
    }
  }, [authLoading, isLoggedIn, role, router]);

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    try {
      const cc = pickCountryParam(scope);
      const baseQs = cc ? `?country_code=${cc}` : "";
      const assignedList = (assignedCountries || []).map((c: any) => c.code).filter(Boolean);

      const countriesToQuery: Array<string | null> = cc ? [cc] : (assignedList.length ? assignedList : [null]);

      const countryOverviews = await Promise.all(
        countriesToQuery.map(async (c) => {
          const qs = c ? `?country_code=${c}` : "";
          const res = await apiFetch(`/admin/analytics/overview${qs}`).catch(() => null);
          if (!res || !res.ok) return null;
          return res.json().catch(() => null);
        })
      );

      const merged: OverviewResponse = {};
      countryOverviews.forEach((entry) => {
        if (!entry || typeof entry !== "object") return;
        const e = entry as OverviewResponse;
        merged.total_revenue = (merged.total_revenue ?? 0) + Number(e.total_revenue ?? 0);
        merged.total_orders = (merged.total_orders ?? 0) + Number(e.total_orders ?? 0);
        merged.total_users = (merged.total_users ?? 0) + Number(e.total_users ?? 0);
        merged.total_products = (merged.total_products ?? 0) + Number(e.total_products ?? 0);
        merged.total_suppliers = (merged.total_suppliers ?? 0) + Number(e.total_suppliers ?? 0);
      });

      setOverview(merged);

      const tsRes = await apiFetch(`/admin/analytics/timeseries${baseQs}`);
      if (tsRes.ok) setTimeseries(await tsRes.json().catch(() => null));
      else setTimeseries(null);

      const tpRes = await apiFetch(`/admin/analytics/top-products${baseQs}`);
      if (tpRes.ok) {
        const tpJson = await tpRes.json().catch(() => null);
        setTopProducts(Array.isArray(tpJson) ? tpJson : (tpJson?.items ?? tpJson?.data ?? []));
      } else {
        setTopProducts([]);
      }
    } catch (e) {
      addToast(e instanceof Error ? e.message : "Failed to load analytics", "error");
    } finally {
      setLoading(false);
    }
  }, [scope, assignedCountries, addToast]);

  useEffect(() => {
    if (isLoggedIn) fetchAnalytics();
  }, [fetchAnalytics, isLoggedIn]);

  const stats = [
    { key: "revenue", label: "Revenue", value: formatMoney(overview?.total_revenue ?? 0), icon: DollarSign, bg: "theme-chip-success" },
    { key: "orders", label: "Orders", value: overview?.total_orders ?? 0, icon: ShoppingCart, bg: "theme-chip-warning" },
    { key: "users", label: "Users", value: overview?.total_users ?? 0, icon: Users, bg: "theme-chip-info" },
    { key: "products", label: "Products", value: overview?.total_products ?? 0, icon: Package, bg: "theme-chip-brand" },
    { key: "suppliers", label: "Suppliers", value: overview?.total_suppliers ?? 0, icon: TrendingUp, bg: "theme-chip-success" },
  ];

  const timeseriesPoints: Array<{ label: string; value: number }> = Array.isArray(timeseries)
    ? timeseries
    : (timeseries?.points ?? timeseries?.data ?? []);

  if (authLoading) {
    return (
      <AdminLayout title="Analytics">
        <PanelLoadingState count={3} />
      </AdminLayout>
    );
  }

  return (
    <AdminLayout title="Analytics" headerMode="compact">
      <PanelContent width="full" className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs text-text-muted">
              Consolidated KPIs across countries or scoped per-country. Country is the orthogonal scope axis.
            </p>
          </div>
          <div className="inline-flex overflow-hidden rounded-xl border border-border bg-surface-1 shadow-sm">
            {COUNTRY_OPTIONS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setScope(s)}
                aria-pressed={scope === s}
                className={`border-l border-border px-3 py-2 text-xs font-medium transition-colors first:border-l-0 ${
                  scope === s ? "bg-primary/10 text-primary" : "text-text-muted hover:bg-surface-2 hover:text-text"
                }`}
              >
                {s === "GLOBAL" ? "All Countries" : s}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={fetchAnalytics}
            disabled={loading}
            className="flex h-9 items-center justify-center rounded-lg border border-border bg-surface-1 px-3 text-xs text-text-muted transition-colors hover:bg-surface-2 disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>

        {loading ? (
          <PanelLoadingState count={5} blockClassName="h-20 rounded-xl bg-surface-2 animate-pulse" />
        ) : (
          <>
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
              {stats.map((s) => (
                <div key={s.key} className="theme-card theme-stat-card rounded-xl border p-3">
                  <div className={`mb-2 flex h-8 w-8 items-center justify-center rounded-xl ${s.bg}`}>
                    <s.icon className="h-3.5 w-3.5" />
                  </div>
                  <p className="text-base font-bold text-text">{s.value}</p>
                  <p className="text-xs text-text-muted">{s.label}</p>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <div className="theme-card rounded-xl border p-4">
                <h2 className="mb-3 text-xs font-bold text-text">Revenue Timeseries</h2>
                {Array.isArray(timeseriesPoints) && timeseriesPoints.length > 0 ? (
                  <div className="space-y-1">
                    {timeseriesPoints.slice(0, 12).map((pt, idx) => (
                      <div key={idx} className="flex items-center justify-between text-xs">
                        <span className="text-text-muted">{pt.label ?? `Point ${idx + 1}`}</span>
                        <span className="tabular-nums text-text">{formatMoney(Number(pt.value ?? 0))}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-text-faint">No timeseries data available.</p>
                )}
              </div>

              <div className="theme-card rounded-xl border p-4">
                <h2 className="mb-3 text-xs font-bold text-text">Top Products</h2>
                {topProducts.length > 0 ? (
                  <div className="space-y-1">
                    {topProducts.slice(0, 10).map((p: any, idx: number) => (
                      <div key={idx} className="flex items-center justify-between text-xs">
                        <span className="text-text">{p.name ?? p.product_name ?? `Product ${idx + 1}`}</span>
                        <span className="tabular-nums text-text-muted">{formatMoney(Number(p.revenue ?? p.total_revenue ?? 0))}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-text-faint">No top products available.</p>
                )}
              </div>
            </div>
          </>
        )}
      </PanelContent>
    </AdminLayout>
  );
}

export default function AdminAnalyticsPage() {
  return (
    <Suspense>
      <AdminAnalyticsInner />
    </Suspense>
  );
}