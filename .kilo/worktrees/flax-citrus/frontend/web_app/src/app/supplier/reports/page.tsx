"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import SupplierLayout from "@/components/SupplierLayout";
import { PanelContent, PanelHero } from "@/components/PanelPage";
import { StatCard } from "@/components/ui/StatCard";
import { apiFetch, getErrorMessage, parseJsonResponse } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useToastStore } from "@/lib/toastStore";
import {
  FileText,
  ArrowRight,
  BarChart3,
  TrendingUp,
  Package,
  ShoppingCart,
  DollarSign,
  Sparkles,
  Loader2,
  RefreshCw,
} from "@/lib/icons";

const PERIODS = [
  { value: "7d", label: "7 days" },
  { value: "30d", label: "30 days" },
  { value: "90d", label: "90 days" },
  { value: "1y", label: "1 year" },
];

type ReportOverview = {
  totalRevenue: number;
  totalOrders: number;
  totalProducts: number;
  averageOrderValue: number;
  conversionRate: number;
};

type ReportTrends = {
  revenueGrowth: number;
  orderGrowth: number;
  customerGrowth: number;
  period: string;
};

type TopProduct = {
  id: number;
  name: string;
  sales: number;
  revenue: number;
  image_url?: string;
};

type AiAuditSummary = {
  generatedAt?: string | null;
  groupCount?: number;
  curatedGroupCount?: number;
  errorCount?: number;
  warningCount?: number;
  attentionCount?: number;
  attentionGroups?: Array<{ id?: string; label?: string; status?: string }>;
};

type ReportsResponse = {
  overview: ReportOverview;
  revenue: { daily: Array<{ date: string; revenue: number }> };
  products: { topSelling: TopProduct[] };
  trends: ReportTrends;
  aiAudit?: AiAuditSummary | null;
};

export default function SupplierReportsPage() {
  const router = useRouter();
  const formatMoney = useCurrencyStore((s) => s.format);
  const addToast = useToastStore((state) => state.addToast);
  const [period, setPeriod] = useState("30d");
  const [data, setData] = useState<ReportsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [runningAudit, setRunningAudit] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const res = await apiFetch(`/supplier/reports?period=${period}`);
      const json = (await parseJsonResponse(res)) as ReportsResponse;
      if (!res.ok) {
        throw new Error(getErrorMessage(json || {}));
      }
      setData(json);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Failed to load reports");
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => {
    void load();
  }, [load]);

  const runAudit = useCallback(async () => {
    setRunningAudit(true);
    try {
      const res = await apiFetch("/supplier/reports/ai-audit/run", { method: "POST" });
      const json = (await parseJsonResponse(res)) as { aiAudit?: AiAuditSummary };
      if (!res.ok) {
        throw new Error(getErrorMessage(json || {}));
      }
      addToast("AI audit started. Refresh after it completes.", "success");
      void load();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Failed to run AI audit", "error");
    } finally {
      setRunningAudit(false);
    }
  }, [addToast, load]);

  const overview = data?.overview;
  const trends = data?.trends;
  const topSelling = data?.products?.topSelling ?? [];
  const revenueSpark = useMemo(() => {
    const daily = data?.revenue?.daily ?? [];
    if (daily.length === 0) return null;
    const values = daily.map((d) => d.revenue);
    const max = Math.max(...values, 1);
    return daily.map((d) => ({ ...d, pct: Math.max(2, (d.revenue / max) * 100) }));
  }, [data]);
  const audit = data?.aiAudit ?? null;

  return (
    <SupplierLayout title="Reports">
      <PanelContent width="wide">
        <PanelHero
          eyebrow="Overview"
          title="Reports & Exports"
          description="Periodic performance summaries for your storefront, plus an on-demand AI credibility audit of your product media."
          icon={<FileText className="h-5 w-5" />}
          actions={
            <div className="flex items-center gap-2">
              <select
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
                className="rounded-xl border border-border bg-surface-2 px-3 py-2 text-xs font-semibold text-text-muted focus:outline-none"
              >
                {PERIODS.map((p) => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
              <button
                onClick={() => void load()}
                disabled={loading}
                className="flex items-center gap-2 rounded-xl border border-border bg-surface-2 px-3 py-2 text-xs font-semibold text-text-muted hover:text-text disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                Refresh
              </button>
            </div>
          }
        />

        {loadError ? (
          <div className="theme-card rounded-xl border border-danger/30 bg-danger/10 p-6 text-center">
            <p className="text-sm font-semibold text-text">{loadError}</p>
            <button
              onClick={() => void load()}
              className="theme-btn-primary mt-4 rounded-xl px-4 py-2 text-xs font-semibold"
            >
              Retry
            </button>
          </div>
        ) : loading ? (
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-28 animate-pulse rounded-xl bg-surface-2" />
            ))}
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              <StatCard label="Revenue" value={formatMoney(overview?.totalRevenue ?? 0)} icon={DollarSign}
                color="bg-primary/10 text-primary"
                trend={trends ? { value: trends.revenueGrowth, positive: trends.revenueGrowth >= 0 } : undefined} />
              <StatCard label="Orders" value={String(overview?.totalOrders ?? 0)} icon={ShoppingCart}
                color="bg-info/10 text-info"
                trend={trends ? { value: trends.orderGrowth, positive: trends.orderGrowth >= 0 } : undefined} />
              <StatCard label="Products" value={String(overview?.totalProducts ?? 0)} icon={Package}
                color="bg-success/10 text-success" />
              <StatCard label="Avg Order" value={formatMoney(overview?.averageOrderValue ?? 0)} icon={TrendingUp}
                color="bg-warning/10 text-warning" />
            </div>

            <div className="grid gap-4 lg:grid-cols-3">
              <div className="rounded-xl border border-border bg-surface p-4">
                <h2 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-primary" />
                  Revenue Trend
                </h2>
                {revenueSpark ? (
                  <div className="flex h-32 items-end gap-1">
                    {revenueSpark.map((point, idx) => (
                      <div key={idx} className="flex-1 rounded-t bg-primary/70" style={{ height: `${point.pct}%` }}
                        title={`${point.date}: ${formatMoney(point.revenue)}`} />
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-text-muted">No revenue recorded in this period.</p>
                )}
              </div>

              <div className="lg:col-span-2 rounded-xl border border-border bg-surface p-4">
                <h2 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-primary" />
                  AI Credibility Audit
                </h2>
                {audit ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                      <div className="rounded-lg bg-surface-2 px-3 py-2">
                        <p className="text-[10px] uppercase tracking-wide text-text-faint">Groups</p>
                        <p className="text-lg font-bold text-text">{audit.curatedGroupCount ?? audit.groupCount ?? 0}</p>
                      </div>
                      <div className="rounded-lg bg-surface-2 px-3 py-2">
                        <p className="text-[10px] uppercase tracking-wide text-text-faint">Need attention</p>
                        <p className="text-lg font-bold text-text">{audit.attentionCount ?? 0}</p>
                      </div>
                      <div className="rounded-lg bg-surface-2 px-3 py-2">
                        <p className="text-[10px] uppercase tracking-wide text-text-faint">Errors</p>
                        <p className="text-lg font-bold text-danger">{audit.errorCount ?? 0}</p>
                      </div>
                      <div className="rounded-lg bg-surface-2 px-3 py-2">
                        <p className="text-[10px] uppercase tracking-wide text-text-faint">Warnings</p>
                        <p className="text-lg font-bold text-warning">{audit.warningCount ?? 0}</p>
                      </div>
                    </div>
                    {(audit.attentionGroups ?? []).length > 0 && (
                      <ul className="space-y-1 text-xs text-text-muted">
                        {(audit.attentionGroups ?? []).slice(0, 4).map((g, i) => (
                          <li key={i} className="truncate">
                            <span className={`font-semibold ${(g.status || "").toUpperCase() === "FAIL" ? "text-danger" : "text-warning"}`}>
                              {g.status}
                            </span>{" "}
                            — {g.label}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                ) : (
                  <p className="text-xs text-text-muted">No audit has been run yet. Trigger one to scan your product media.</p>
                )}
                <button
                  onClick={() => void runAudit()}
                  disabled={runningAudit}
                  className="theme-btn-primary mt-4 inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold disabled:opacity-60"
                >
                  {runningAudit ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                  Run AI Audit
                </button>
              </div>
            </div>

            <div className="rounded-xl border border-border bg-surface p-4">
              <h2 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
                <Package className="h-4 w-4 text-primary" />
                Top Selling Products
              </h2>
              {topSelling.length > 0 ? (
                <div className="divide-y divide-border">
                  {topSelling.slice(0, 8).map((product, i) => (
                    <div key={product.id} className="flex items-center gap-3 py-2.5">
                      <span className="w-5 text-xs font-bold text-text-faint tabular-nums">#{i + 1}</span>
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-medium text-text truncate">{product.name}</p>
                        <p className="text-[10px] text-text-muted">{product.sales} sales</p>
                      </div>
                      <span className="text-xs font-semibold text-text tabular-nums">{formatMoney(product.revenue)}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-text-muted">No sales in this period yet.</p>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={() => router.push("/supplier/analytics")}
                className="theme-btn-secondary inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold"
              >
                Open Analytics
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => router.push("/supplier/payouts")}
                className="theme-btn-secondary inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold"
              >
                Open Payouts
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </>
        )}
      </PanelContent>
    </SupplierLayout>
  );
}
