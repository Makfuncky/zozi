"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Activity,
  CheckCircle,
  Clock,
  Download,
  Loader2,
  Package,
  TrendingUp,
  Truck,
  XCircle,
} from "@/lib/icons";
import LogisticsPartnerLayout from "@/components/LogisticsPartnerLayout";
import { apiFetch } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";

// ── Types ─────────────────────────────────────────────────────────────────────

interface DeliveryKPI {
  delivery_rate: number;
  average_transit_hours: number;
  sla_on_time_rate: number;
  scan_compliance_rate: number;
  total_shipments: number;
  delivered: number;
  failed: number;
  in_transit: number;
}

interface PayoutSummary {
  id: number;
  amount: number;
  status: string;
  payout_date: string | null;
  period_start: string | null;
  period_end: string | null;
}

type Period = "7d" | "30d" | "90d";

// ── Helpers ───────────────────────────────────────────────────────────────────

function exportCSV(kpi: DeliveryKPI, period: string) {
  const rows = [
    ["Metric", "Value"],
    ["Period", period],
    ["Total Shipments", kpi.total_shipments],
    ["Delivered", kpi.delivered],
    ["In Transit", kpi.in_transit],
    ["Failed", kpi.failed],
    ["Delivery Rate %", (kpi.delivery_rate * 100).toFixed(1)],
    ["SLA On-Time Rate %", (kpi.sla_on_time_rate * 100).toFixed(1)],
    ["Avg Transit Hours", kpi.average_transit_hours.toFixed(1)],
    ["Scan Compliance %", (kpi.scan_compliance_rate * 100).toFixed(1)],
  ];
  const csv = rows.map((r) => r.join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `lp-analytics-${period}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

// ── KPI Card ─────────────────────────────────────────────────────────────────

function KPICard({
  label,
  value,
  sub,
  icon: Icon,
  color,
}: {
  label: string;
  value: string;
  sub?: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-border bg-surface p-4"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.15em] text-text-muted">{label}</p>
          <p className="mt-1.5 text-2xl font-bold text-text">{value}</p>
          {sub && <p className="mt-0.5 text-xs text-text-muted">{sub}</p>}
        </div>
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${color}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </motion.div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function LPAnalyticsPage() {
  const formatMoney = useCurrencyStore((s) => s.format);
  const [period, setPeriod] = useState<Period>("30d");
  const [kpi, setKPI] = useState<DeliveryKPI | null>(null);
  const [payouts, setPayouts] = useState<PayoutSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    Promise.all([
      apiFetch(`/logistics-partner/analytics?period=${period}`)
        .then((r) => (r.ok ? r.json() : null))
        .catch(() => null),
      apiFetch("/logistics-partner/payouts")
        .then((r) => (r.ok ? r.json() : []))
        .catch(() => []),
    ]).then(([analyticsData, payoutsData]) => {
      if (cancelled) return;
      if (analyticsData) setKPI(analyticsData);
      setPayouts(Array.isArray(payoutsData) ? payoutsData.slice(0, 10) : []);
      setLoading(false);
    });

    return () => { cancelled = true; };
  }, [period]);

  return (
    <LogisticsPartnerLayout title="Analytics">
      <div className="space-y-5">
        <div className="theme-card rounded-2xl border p-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-faint">Analytics Controls</p>
              <p className="mt-1 text-xs text-text-muted">Monitor delivery KPIs, SLA compliance, and export payout history from one workspace.</p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex w-full gap-1 overflow-x-auto rounded-xl bg-surface-2 p-1 sm:w-fit">
                {(["7d", "30d", "90d"] as Period[]).map((p) => (
                  <button
                    key={p}
                    onClick={() => setPeriod(p)}
                    className={`flex-1 whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors sm:flex-none ${
                      period === p ? "bg-surface text-text shadow-sm" : "text-text-muted hover:text-text"
                    }`}
                  >
                    {p === "7d" ? "7 days" : p === "30d" ? "30 days" : "90 days"}
                  </button>
                ))}
              </div>
              {kpi && (
                <button
                  onClick={() => exportCSV(kpi, period)}
                  className="flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-xs font-medium text-text-muted transition-colors hover:text-text"
                >
                  <Download className="w-3.5 h-3.5" />
                  Export CSV
                </button>
              )}
            </div>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-7 h-7 animate-spin text-primary" />
          </div>
        ) : (
          <>
            {/* KPI grid */}
            {kpi && (
              <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                <KPICard
                  label="Delivery Rate"
                  value={`${(kpi.delivery_rate * 100).toFixed(1)}%`}
                  sub={`${kpi.delivered} of ${kpi.total_shipments} delivered`}
                  icon={CheckCircle}
                  color="bg-success/10 text-success"
                />
                <KPICard
                  label="SLA On-Time"
                  value={`${(kpi.sla_on_time_rate * 100).toFixed(1)}%`}
                  sub="Orders delivered within SLA"
                  icon={TrendingUp}
                  color={kpi.sla_on_time_rate >= 0.9 ? "bg-success/10 text-success" : "bg-warning/10 text-warning"}
                />
                <KPICard
                  label="Avg Transit"
                  value={`${kpi.average_transit_hours.toFixed(1)}h`}
                  sub="Average delivery time"
                  icon={Clock}
                  color="bg-primary/10 text-primary"
                />
                <KPICard
                  label="Scan Compliance"
                  value={`${(kpi.scan_compliance_rate * 100).toFixed(1)}%`}
                  sub="Packages scanned at checkpoints"
                  icon={Activity}
                  color="bg-info/10 text-info"
                />
              </div>
            )}

            {/* Status breakdown */}
            {kpi && (
              <div className="rounded-xl border border-border bg-surface p-4">
                <h2 className="text-sm font-semibold text-text mb-3">Shipment Status Breakdown</h2>
                <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                  {[
                    { label: "In Transit", value: kpi.in_transit, icon: Truck, color: "text-primary" },
                    { label: "Delivered", value: kpi.delivered, icon: CheckCircle, color: "text-success" },
                    { label: "Failed", value: kpi.failed, icon: XCircle, color: "text-danger" },
                    { label: "Total", value: kpi.total_shipments, icon: Package, color: "text-text-muted" },
                  ].map((item) => (
                    <div key={item.label} className="rounded-lg bg-surface-2 p-3 flex items-center gap-3">
                      <item.icon className={`w-5 h-5 shrink-0 ${item.color}`} />
                      <div>
                        <p className="text-xs text-text-muted">{item.label}</p>
                        <p className="text-base font-bold text-text">{item.value}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Payout history */}
            <div className="rounded-xl border border-border bg-surface p-4">
              <h2 className="text-sm font-semibold text-text mb-3">Recent Payouts</h2>
              {payouts.length === 0 ? (
                <p className="text-sm text-text-muted py-4 text-center">No payout records found</p>
              ) : (
                <div className="divide-y divide-border">
                  {payouts.map((p) => (
                    <div key={p.id} className="flex items-center justify-between py-2.5 gap-3">
                      <div>
                        <p className="text-xs font-semibold text-text">{formatMoney(p.amount)}</p>
                        {p.period_start && p.period_end && (
                          <p className="text-[10px] text-text-muted">
                            {new Date(p.period_start).toLocaleDateString()} –{" "}
                            {new Date(p.period_end).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                      <div className="text-right">
                        <span
                          className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                            p.status === "paid"
                              ? "bg-success/10 text-success"
                              : p.status === "pending"
                              ? "bg-warning/10 text-warning"
                              : "bg-surface-2 text-text-muted"
                          }`}
                        >
                          {p.status}
                        </span>
                        {p.payout_date && (
                          <p className="text-[10px] text-text-muted mt-0.5">
                            {new Date(p.payout_date).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </LogisticsPartnerLayout>
  );
}


