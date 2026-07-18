"use client";

import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import {
  DollarSign,
  TrendingUp,
  BarChart3,
  ShoppingCart,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
} from "@/lib/icons";
import SupplierLayout from "@/components/SupplierLayout";
import { apiFetch } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";

type Period = "7d" | "30d" | "90d" | "1y";

interface AnalyticsData {
  overview: {
    totalRevenue: number;
    totalOrders: number;
    totalProducts: number;
    averageOrderValue: number;
    conversionRate: number;
  };
  revenue: {
    daily: { date: string; revenue: number }[];
  };
  products: {
    topSelling: { id: number; name: string; sales: number; revenue: number; image_url?: string }[];
  };
  trends: {
    revenueGrowth: number;
    orderGrowth: number;
    period: string;
  };
}

export default function SupplierAnalyticsPage() {
  const formatMoney = useCurrencyStore((s) => s.format);
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [period, setPeriod] = useState<Period>("30d");
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const res = await apiFetch(`/supplier/analytics?period=${period}`);
      if (res.ok) {
        setData(await res.json());
      } else {
        const text = await res.text();
        setLoadError(text || "Failed to load analytics");
      }
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Failed to load analytics");
    }
    setLoading(false);
  }, [period]);

  useEffect(() => { fetchAnalytics(); }, [fetchAnalytics]);

  const overview = data?.overview;
  const daily = data?.revenue?.daily ?? [];
  const topSelling = data?.products?.topSelling ?? [];
  const trends = data?.trends;

  const chartData = daily.slice(-14).map((d) => ({
    date: d.date.slice(5), // "MM-DD"
    revenue: d.revenue,
  }));
  const maxRevenue = Math.max(...chartData.map((d) => d.revenue), 1);

  const metrics = overview
    ? [
        {
          label: "Total Revenue",
          value: formatMoney(overview.totalRevenue),
          icon: DollarSign,
          growth: trends?.revenueGrowth ?? 0,
        },
        {
          label: "Total Orders",
          value: overview.totalOrders.toLocaleString(),
          icon: ShoppingCart,
          growth: trends?.orderGrowth ?? 0,
        },
        {
          label: "Avg Order Value",
          value: formatMoney(overview.averageOrderValue),
          icon: TrendingUp,
          growth: null,
        },
        {
          label: "Conversion Rate",
          value: `${overview.conversionRate.toFixed(1)}%`,
          icon: BarChart3,
          growth: null,
        },
      ]
    : [];

  return (
    <SupplierLayout title="Analytics">
      <div className="theme-card mb-6 rounded-2xl border p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-faint">Reporting Window</p>
            <p className="mt-1 text-xs text-text-muted">Adjust the sales window and refresh the supplier performance feed from the same control surface.</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {(["7d", "30d", "90d", "1y"] as Period[]).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                  period === p
                    ? "bg-primary text-on-brand"
                    : "bg-surface-2 text-text-muted hover:text-text"
                }`}
              >
                {p}
              </button>
            ))}
            <button
              onClick={fetchAnalytics}
              disabled={loading}
              className="rounded-lg bg-surface-2 p-2 text-text-muted transition-colors hover:text-text"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>
      </div>

      {loadError && !loading ? (
        <div className="theme-card rounded-2xl border border-danger/30 bg-danger/10 p-6 text-center">
          <p className="text-sm font-semibold text-text">Analytics could not be loaded</p>
          <p className="mt-1 text-xs text-text-muted">{loadError}</p>
          <button
            onClick={fetchAnalytics}
            className="theme-btn-primary mt-4 rounded-xl px-4 py-2 text-xs font-semibold"
          >
            Retry
          </button>
        </div>
      ) : null}

      {loading ? (
        <div className="space-y-4">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-24 rounded-xl bg-surface-2 animate-pulse" />
            ))}
          </div>
          <div className="h-48 rounded-xl bg-surface-2 animate-pulse" />
        </div>
      ) : (
        <>
          {/* Metrics */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {metrics.map((m, i) => (
              <motion.div
                key={m.label}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="p-4 rounded-xl theme-card border"
              >
                <div className="flex items-center justify-between mb-2">
                  <m.icon className="w-5 h-5 text-primary" />
                  {m.growth !== null ? (
                    <span
                      className={`text-xs font-semibold flex items-center gap-0.5 ${
                        m.growth >= 0 ? "text-success" : "text-danger"
                      }`}
                    >
                      {m.growth >= 0 ? (
                        <ArrowUpRight className="w-3 h-3" />
                      ) : (
                        <ArrowDownRight className="w-3 h-3" />
                      )}
                      {Math.abs(m.growth).toFixed(1)}%
                    </span>
                  ) : null}
                </div>
                <p className="text-xl font-bold text-text">{m.value}</p>
                <p className="text-xs text-text-faint">{m.label}</p>
              </motion.div>
            ))}
          </div>

          {/* Revenue Bar Chart */}
          <div className="rounded-xl theme-card border p-5 mb-6">
            <h3 className="text-xs font-bold text-text mb-4 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-primary" />
              Daily Revenue — last 14 days
            </h3>
            {chartData.length === 0 ? (
              <p className="text-xs text-text-faint">No revenue data for this period</p>
            ) : (
              <div className="overflow-x-auto">
                <div className="flex items-end gap-1 h-32 min-w-100">
                  {chartData.map((d, i) => (
                    <div key={i} className="flex-1 flex flex-col items-center gap-1">
                      <motion.div
                        initial={{ height: 0 }}
                        animate={{ height: `${(d.revenue / maxRevenue) * 100}%` }}
                        transition={{ delay: i * 0.03, duration: 0.5 }}
                        className="w-full rounded-t bg-primary min-h-0.5"
                        title={formatMoney(d.revenue)}
                      />
                      <span className="text-[9px] text-text-faint truncate w-full text-center">
                        {d.date}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Top Products by Revenue */}
            <div className="rounded-xl theme-card border p-5">
              <h3 className="text-xs font-bold text-text mb-4">
                Top Products by Revenue
              </h3>
              {topSelling.length === 0 ? (
                <p className="text-xs text-text-faint">No sales data yet</p>
              ) : (
                <div className="space-y-3">
                  {topSelling.slice(0, 6).map((p, i) => {
                    const maxRev = topSelling[0]?.revenue || 1;
                    return (
                      <div key={p.id}>
                        <div className="flex items-center justify-between text-xs mb-1">
                          <div className="flex items-center gap-2">
                            <span className="w-5 h-5 rounded bg-surface-2 flex items-center justify-center text-[10px] font-bold text-text-muted">
                              {i + 1}
                            </span>
                            <span className="text-text font-medium truncate max-w-40">
                              {p.name}
                            </span>
                          </div>
                          <span className="text-text font-semibold ml-2 shrink-0">
                            {formatMoney(p.revenue)}
                          </span>
                        </div>
                        <div className="h-1.5 rounded-full bg-surface-3 overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${(p.revenue / maxRev) * 100}%` }}
                            transition={{ delay: 0.3 + i * 0.05, duration: 0.6 }}
                            className="h-full rounded-full bg-primary"
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Growth Summary */}
            <div className="rounded-xl theme-card border p-5">
              <h3 className="text-xs font-bold text-text mb-4 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-primary" />
                Period Summary ({period})
              </h3>
              <div className="space-y-4">
                {[
                  { label: "Revenue Growth", value: trends?.revenueGrowth ?? 0, pct: true },
                  { label: "Order Growth", value: trends?.orderGrowth ?? 0, pct: true },
                  { label: "Total Products", value: overview?.totalProducts ?? 0, pct: false },
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between">
                    <span className="text-xs text-text-muted">{item.label}</span>
                    <span
                      className={`text-xs font-bold ${
                        item.pct && item.value >= 0
                          ? "text-success"
                          : item.pct && item.value < 0
                          ? "text-danger"
                          : "text-text"
                      }`}
                    >
                      {item.pct && item.value >= 0 ? "+" : ""}
                      {item.value.toFixed(item.pct ? 1 : 0)}
                      {item.pct ? "%" : ""}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </SupplierLayout>
  );
}
