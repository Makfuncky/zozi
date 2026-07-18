"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Activity,
  CheckCircle,
  Clock,
  Navigation,
  Package,
  RefreshCw,
  Truck,
  XCircle,
} from "@/lib/icons";
import LogisticsPartnerLayout from "@/components/LogisticsPartnerLayout";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";
import { StatCard } from "@/components/ui/StatCard";
import { apiFetch } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { getStatusChip } from "@shared/statusColors";

interface DashboardStats {
  total: number;
  active: number;
  delivered: number;
  pending: number;
  failed: number;
}

interface PayoutSummary {
  total_earned: number;
  available_balance: number;
  pending_amount: number;
  completed_amount: number;
  payout_count: number;
}

interface ActiveShipment {
  id: number;
  order_id: number;
  tracking_number: string | null;
  carrier_name: string | null;
  status: string;
  distribution_channel: string | null;
  estimated_delivery: string | null;
}

interface DashboardAnalytics {
  delivery_rate?: number;
  average_transit_hours?: number;
  scan_compliance_rate?: number;
  sla_on_time_rate?: number;
  shipments_with_events?: number;
  sla_eligible_shipments?: number;
  status_breakdown?: Record<string, number>;
}

interface LiveLocation {
  id?: number;
  shipment_id?: number;
  latitude?: number;
  longitude?: number;
  updated_at?: string | null;
}

interface DashboardData {
  stats: DashboardStats;
  analytics?: DashboardAnalytics;
  channel_breakdown: Record<string, number>;
  active_shipments: ActiveShipment[];
  live_locations?: LiveLocation[];
  payout_summary: PayoutSummary | null;
  sla_alerts: { shipment_id: number; message: string }[];
}

export default function LogisticsPartnerDashboardPage() {
  const formatMoney = useCurrencyStore((s) => s.format);
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch("/logistics-partner/dashboard");
      if (res.ok) setData(await res.json());
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchDashboard(); }, [fetchDashboard]);

  const stats = data?.stats;
  const analytics = data?.analytics;
  const payouts = data?.payout_summary;
  const shipments = data?.active_shipments ?? [];
  const liveLocations = data?.live_locations ?? [];
  const channels = data?.channel_breakdown ?? {};

  return (
    <LogisticsPartnerLayout title="Dashboard">
      <PanelContent className="space-y-5">
        <div className="flex items-center justify-between">
          <p className="text-xs text-text-muted">Real-time logistics operations overview</p>
          <button onClick={fetchDashboard} disabled={loading}
            className="flex items-center gap-2 rounded-xl border border-border bg-surface-2 px-4 py-2 text-xs font-semibold text-text-muted hover:text-text disabled:opacity-50">
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        {loading ? (
          <PanelLoadingState
            count={5}
            className="!mt-0 grid grid-cols-2 gap-3 lg:grid-cols-5"
            blockClassName="h-28 rounded-xl bg-surface-2 animate-pulse"
          />
        ) : (
          <>
            {stats && (
              <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
                <StatCard label="Total" value={String(stats.total)} icon={Package} color="bg-primary/10 text-primary" />
                <StatCard label="Active" value={String(stats.active)} icon={Truck} color="bg-info/10 text-info" sub="In transit / processing" />
                <StatCard label="Delivered" value={String(stats.delivered)} icon={CheckCircle} color="bg-success/10 text-success" />
                <StatCard label="Pending" value={String(stats.pending)} icon={Clock} color="bg-warning/10 text-warning" />
                <StatCard label="Failed" value={String(stats.failed)} icon={XCircle} color="bg-danger/10 text-danger" />
              </div>
            )}

            {analytics && (
              <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                <StatCard label="Delivery Rate" value={`${(analytics.delivery_rate ?? 0).toFixed(1)}%`} icon={CheckCircle} color="bg-success/10 text-success" />
                <StatCard label="Avg Transit" value={`${(analytics.average_transit_hours ?? 0)}h`} icon={Clock} color="bg-info/10 text-info" />
                <StatCard label="Scan Compliance" value={`${(analytics.scan_compliance_rate ?? 0).toFixed(1)}%`} icon={Navigation} color="bg-primary/10 text-primary" />
                <StatCard label="SLA On-Time" value={`${(analytics.sla_on_time_rate ?? 0).toFixed(1)}%`} icon={Activity} color="bg-warning/10 text-warning" />
              </div>
            )}

            <div className="grid gap-4 lg:grid-cols-3">
              {payouts && (
                <div className="rounded-xl border border-border bg-surface p-4">
                  <h2 className="text-sm font-semibold text-text mb-3">Payout Summary</h2>
                  <div className="space-y-2.5">
                    <div className="flex justify-between text-xs">
                      <span className="text-text-muted">Total earned</span>
                      <span className="font-semibold text-text tabular-nums">{formatMoney(payouts.total_earned)}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-text-muted">Available</span>
                      <span className="font-semibold text-text tabular-nums">{formatMoney(payouts.available_balance)}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-text-muted">Pending</span>
                      <span className="font-semibold text-warning tabular-nums">{formatMoney(payouts.pending_amount)}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-text-muted">Completed</span>
                      <span className="font-semibold text-success tabular-nums">{formatMoney(payouts.completed_amount)}</span>
                    </div>
                    <div className="flex justify-between text-xs pt-1 border-t border-border">
                      <span className="text-text-muted">Payouts</span>
                      <span className="font-semibold text-text tabular-nums">{payouts.payout_count}</span>
                    </div>
                  </div>
                </div>
              )}

              {Object.keys(channels).length > 0 && (
                <div className="rounded-xl border border-border bg-surface p-4">
                  <h2 className="text-sm font-semibold text-text mb-3">Distribution Channels</h2>
                  <div className="space-y-2.5">
                    {Object.entries(channels).map(([channel, count]) => (
                      <div key={channel} className="flex items-center justify-between">
                        <span className="text-xs text-text-muted">{channel}</span>
                        <div className="flex items-center gap-2">
                          <div className="h-1.5 w-24 rounded-full bg-surface-2 overflow-hidden">
                            <div className="h-full rounded-full bg-primary"
                              style={{ width: `${stats ? (count / stats.total) * 100 : 0}%` }} />
                          </div>
                          <span className="text-xs font-semibold text-text tabular-nums w-8 text-right">{count}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {data?.sla_alerts && data.sla_alerts.length > 0 && (
                <div className="rounded-xl border border-border bg-surface p-4">
                  <h2 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
                    <Activity className="h-4 w-4 text-warning" />
                    SLA Alerts
                  </h2>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {data.sla_alerts.map((alert, i) => (
                      <div key={i} className="rounded-lg bg-warning/5 border border-warning/20 px-3 py-2 text-xs text-text-muted">
                        #{alert.shipment_id}: {alert.message}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="rounded-xl border border-border bg-surface p-4">
              <h2 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
                <Navigation className="h-4 w-4 text-primary" />
                Active Shipments
              </h2>
              {shipments.length === 0 ? (
                <div className="py-8 text-center">
                  <Truck className="mx-auto h-8 w-8 text-text-faint mb-2" />
                  <p className="text-sm text-text-muted">No active shipments</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-border text-left">
                        <th className="px-3 py-2 font-semibold text-text-faint">#</th>
                        <th className="px-3 py-2 font-semibold text-text-faint">Order</th>
                        <th className="px-3 py-2 font-semibold text-text-faint">Tracking</th>
                        <th className="px-3 py-2 font-semibold text-text-faint">Carrier</th>
                        <th className="px-3 py-2 font-semibold text-text-faint">Channel</th>
                        <th className="px-3 py-2 font-semibold text-text-faint">Status</th>
                        <th className="px-3 py-2 font-semibold text-text-faint">Est. Delivery</th>
                      </tr>
                    </thead>
                    <tbody>
                      {shipments.map((s) => (
                        <tr key={s.id} className="border-b border-border/50">
                          <td className="px-3 py-2.5 font-mono text-text-faint">#{s.id}</td>
                          <td className="px-3 py-2.5 text-text">#{s.order_id}</td>
                          <td className="px-3 py-2.5 font-mono text-text-muted">{s.tracking_number || "—"}</td>
                          <td className="px-3 py-2.5 text-text-muted">{s.carrier_name || "—"}</td>
                          <td className="px-3 py-2.5 text-text-faint">{s.distribution_channel || "—"}</td>
                          <td className="px-3 py-2.5">
                            <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${getStatusChip(s.status)}`}>{s.status}</span>
                          </td>
                          <td className="px-3 py-2.5 text-text-faint tabular-nums">
                            {s.estimated_delivery ? new Date(s.estimated_delivery).toLocaleDateString() : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="rounded-xl border border-border bg-surface p-4">
              <h2 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
                <Navigation className="h-4 w-4 text-primary" />
                Live GPS Pings
              </h2>
              {liveLocations.length === 0 ? (
                <div className="space-y-1 text-xs text-text-muted">
                  <p className="font-semibold text-text">{liveLocations.length} live pings</p>
                  <p>No GPS checkpoints have been received yet for active shipments.</p>
                </div>
              ) : (
                <div className="space-y-1 text-xs text-text-muted">
                  <p className="font-semibold text-text">{liveLocations.length} live pings</p>
                  <ul className="space-y-1">
                    {liveLocations.map((loc) => (
                      <li key={loc.id ?? loc.shipment_id} className="rounded-lg bg-surface-2 px-2 py-1.5">
                        Shipment #{loc.shipment_id}: {loc.latitude ?? "—"}, {loc.longitude ?? "—"}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </>
        )}
      </PanelContent>
    </LogisticsPartnerLayout>
  );
}
