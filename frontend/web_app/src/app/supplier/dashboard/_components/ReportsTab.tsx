"use client";

import { ArrowRight, FileText, Package, Sparkles, TrendingUp } from "@/lib/icons";
import { useCurrencyStore } from "@/stores/currencyStore";
import { StatCard } from "@/components/ui/StatCard";
import { useRouter } from "next/navigation";
import {
  OVERVIEW_STATS,
  REPORT_NAV_LINKS,
  AUDIT_METRICS,
  type AiAuditData,
  type OverviewData,
  type RevenueTrendPoint,
  type TopProductData,
  type DashboardPeriod,
} from "@/lib/supplierDashboardConfig";
import { RevenueChart } from "./RevenueChart";
import { ExportButton } from "./ExportButton";

interface ReportsTabProps {
  overview: OverviewData;
  revenueTrend: RevenueTrendPoint[];
  topProducts: TopProductData[];
  periodLabel: string;
  aiAudit: AiAuditData | null;
  onRunAudit: () => Promise<void>;
  auditLoading: boolean;
  period: DashboardPeriod;
}

export function ReportsTab({
  overview,
  revenueTrend,
  topProducts,
  periodLabel,
  aiAudit,
  onRunAudit,
  auditLoading,
  period,
}: ReportsTabProps) {
  const formatMoney = useCurrencyStore((s) => s.format);
  const router = useRouter();

  const renderStatValue = (config: typeof OVERVIEW_STATS[number], value: number) => {
    if (config.format === "money") return formatMoney(value);
    return String(value);
  };

  const handleNav = (route: string) => {
    router.push(route);
  };

  return (
    <div className="space-y-6">
      {/* Header with Export */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-sm font-semibold text-text">Performance Report</h2>
          <p className="text-xs text-text-muted">Export-ready summary for {periodLabel}</p>
        </div>
        <ExportButton period={period} variant="primary" />
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {OVERVIEW_STATS.map((stat) => (
          <StatCard
            key={stat.key}
            label={stat.label}
            value={renderStatValue(stat, (overview[stat.key as keyof OverviewData] as number) ?? 0)}
            icon={stat.icon}
            color={stat.color}
            subtitle={stat.subtitle}
          />
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Revenue Summary */}
        <div className="rounded-xl border border-border bg-surface p-4">
          <h2 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-primary" />
            Revenue Summary
          </h2>
          <RevenueChart data={revenueTrend} periodLabel={periodLabel} height={120} />
        </div>

        {/* AI Credibility Audit */}
        <div className="rounded-xl border border-border bg-surface p-4">
          <h2 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            AI Credibility Audit
          </h2>
          <p className="text-xs text-text-muted mb-4">
            Run an AI audit to scan your product media for compliance and quality issues.
          </p>
          {aiAudit ? (
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-5 mb-4">
              {AUDIT_METRICS.map((m) => (
                <div key={m.key} className="rounded-lg bg-surface-2 px-3 py-2">
                  <p className="text-xs uppercase tracking-wide text-text-faint">{m.label}</p>
                  <p className={`text-lg font-bold ${m.tone}`}>
                    {String((aiAudit as unknown as Record<string, number>)[m.key] ?? 0)}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-text-muted py-4 text-center">No audit has been run yet.</p>
          )}
          <button
            onClick={() => { void onRunAudit(); }}
            disabled={auditLoading}
            className="theme-btn-primary inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold disabled:opacity-60"
          >
            <Sparkles className="h-4 w-4" />
            {auditLoading ? "Running..." : "Run AI Audit"}
          </button>
        </div>
      </div>

      {/* Top Products */}
      <div className="rounded-xl border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
          <Package className="h-4 w-4 text-primary" />
          Top Selling Products
        </h2>
        {topProducts.length > 0 ? (
          <div className="divide-y divide-border">
            {topProducts.slice(0, 8).map((product, i) => (
              <div key={product.id} className="flex items-center gap-3 py-2.5">
                <span className="w-5 text-xs font-bold text-text-faint tabular-nums">#{i + 1}</span>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-medium text-text truncate">{product.name}</p>
                  <p className="text-xs text-text-muted">{product.sales} sales</p>
                </div>
                <span className="text-xs font-semibold text-text tabular-nums">
                  {formatMoney(product.revenue)}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-text-muted py-6 text-center">No sales in this period yet.</p>
        )}
      </div>

      {/* Navigation Links */}
      <div className="flex flex-wrap items-center gap-3">
        {REPORT_NAV_LINKS.map((link) =>
          "isExport" in link && link.isExport ? (
            <ExportButton key={link.route} period={period} />
          ) : (
            <button
              key={link.route}
              onClick={() => { handleNav(link.route); }}
              className="theme-btn-secondary inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold"
            >
              {link.icon && <link.icon className="h-3.5 w-3.5" />}
              {link.label}
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          )
        )}
      </div>
    </div>
  );
}
