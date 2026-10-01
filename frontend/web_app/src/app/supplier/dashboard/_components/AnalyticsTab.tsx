"use client";

import { ArrowUpRight, ArrowDownRight, TrendingUp, Download } from "@/lib/icons";
import { useCurrencyStore } from "@/stores/currencyStore";
import {
  ANALYTICS_STATS,
  type DashboardPeriod,
  type GrowthData,
  type OverviewData,
  type RevenueTrendPoint,
  type TopProductData,
} from "@/lib/supplierDashboardConfig";
import { RevenueChart } from "./RevenueChart";
import { GrowthIndicator } from "./GrowthIndicator";
import { ExportButton } from "./ExportButton";

interface AnalyticsTabProps {
  overview: OverviewData;
  growth: GrowthData;
  revenueTrend: RevenueTrendPoint[];
  topProducts: TopProductData[];
  periodLabel: string;
  period: DashboardPeriod;
}

export function AnalyticsTab({
  overview,
  growth,
  revenueTrend,
  topProducts,
  periodLabel,
  period,
}: AnalyticsTabProps) {
  const formatMoney = useCurrencyStore((s) => s.format);
  const maxRevenue = Math.max(...revenueTrend.map((d) => d.amount), 1);
  const maxProductRevenue = Math.max(...topProducts.map((p) => p.revenue), 1);

  const renderStatValue = (key: string, format: "money" | "number" | "percent") => {
    const val = (overview as unknown as Record<string, number>)[key] ?? 0;
    if (format === "money") return formatMoney(val);
    if (format === "percent") return `${val.toFixed(1)}%`;
    return val.toLocaleString();
  };

  const getGrowth = (key: string): number | null => {
    if (key === "total_revenue") return growth.revenue_growth;
    if (key === "total_orders") return growth.order_growth;
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Header with Export */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-sm font-semibold text-text">Performance Analytics</h2>
          <p className="text-xs text-text-muted">Deep metrics for {periodLabel}</p>
        </div>
        <ExportButton period={period} label="Export Analytics" />
      </div>

      {/* Metric Cards with Growth */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {ANALYTICS_STATS.map((m) => {
          const growthValue = m.growth ? getGrowth(m.key) : null;
          return (
            <div key={m.key} className="p-4 rounded-xl border border-border bg-surface">
              <div className="flex items-center justify-between mb-2">
                <m.icon className="w-5 h-5 text-primary" />
                {growthValue !== null && (
                  <GrowthIndicator value={growthValue} size="sm" showLabel={false} />
                )}
              </div>
              <p className="text-xl font-bold text-text">{renderStatValue(m.key, m.format)}</p>
              <p className="text-xs text-text-faint">{m.label}</p>
            </div>
          );
        })}
      </div>

      {/* Period Comparison Summary */}
      <div className="rounded-xl border border-border bg-surface p-4">
        <h3 className="text-xs font-bold text-text mb-3 flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-primary" />
          vs Previous Period
        </h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-lg bg-surface-2 px-3 py-2">
            <p className="text-xs uppercase tracking-wide text-text-faint">Previous Revenue</p>
            <p className="text-sm font-bold text-text">{formatMoney(growth.previous_revenue)}</p>
            <p className="text-xs text-text-faint mt-1">
              <GrowthIndicator value={growth.revenue_growth} size="sm" />
            </p>
          </div>
          <div className="rounded-lg bg-surface-2 px-3 py-2">
            <p className="text-xs uppercase tracking-wide text-text-faint">Previous Orders</p>
            <p className="text-sm font-bold text-text">{growth.previous_orders.toLocaleString()}</p>
            <p className="text-xs text-text-faint mt-1">
              <GrowthIndicator value={growth.order_growth} size="sm" />
            </p>
          </div>
          <div className="rounded-lg bg-surface-2 px-3 py-2">
            <p className="text-xs uppercase tracking-wide text-text-faint">Current Revenue</p>
            <p className="text-sm font-bold text-success">{formatMoney(overview.recent_revenue)}</p>
          </div>
          <div className="rounded-lg bg-surface-2 px-3 py-2">
            <p className="text-xs uppercase tracking-wide text-text-faint">Current Orders</p>
            <p className="text-sm font-bold text-success">{overview.total_orders.toLocaleString()}</p>
          </div>
        </div>
      </div>

      {/* Revenue Bar Chart */}
      <RevenueChart data={revenueTrend} periodLabel={periodLabel} />

      {/* Top Products with Bars */}
      <div className="rounded-xl border border-border bg-surface p-5">
        <h3 className="text-xs font-bold text-text mb-4 flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-primary" />
          Top Products by Revenue
        </h3>
        {topProducts.length > 0 ? (
          <div className="space-y-3">
            {topProducts.slice(0, 6).map((p, i) => (
              <div key={p.id}>
                <div className="flex items-center justify-between text-xs mb-1">
                  <div className="flex items-center gap-2 min-w-0 flex-1">
                    <span className="w-5 h-5 rounded bg-surface-2 flex items-center justify-center text-xs font-bold text-text-muted shrink-0">
                      {i + 1}
                    </span>
                    <span className="text-text font-medium truncate">{p.name}</span>
                  </div>
                  <span className="text-text font-semibold ml-2 shrink-0">{formatMoney(p.revenue)}</span>
                </div>
                <div className="h-1.5 rounded-full bg-surface-3 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-primary transition-all"
                    style={{ width: `${(p.revenue / maxProductRevenue) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-text-faint py-6 text-center">No sales data yet</p>
        )}
      </div>
    </div>
  );
}
