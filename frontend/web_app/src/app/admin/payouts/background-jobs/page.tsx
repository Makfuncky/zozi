"use client";

import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Play,
  Square,
  RefreshCw,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Loader2,
  FileText,
  TrendingUp,
  Activity,
  Wifi,
  WifiOff,
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";
import { useLocaleStore } from "@/lib/localeStore";
import { isRtlLocale } from "@shared/localization";
import {
  connectBackgroundJobSocket,
  type BackgroundJobWSMessage,
  type RealtimeStatus,
} from "@/lib/backgroundJobRealtime";

// ── Types ───────────────────────────────────────────────────────────────────

interface BackgroundJobStatus {
  is_running: boolean;
  is_thread_alive: boolean;
  last_run_at: string | null;
  last_run_status: string | null;
  last_error: string | null;
  total_sweep_count: number;
  total_settlements_processed: number;
  last_supplier_result: Record<string, unknown> | null;
  last_logistics_result: Record<string, unknown> | null;
  thread_started_at: string | null;
  thread_stopped_at: string | null;
}

interface AutomationLogEntry {
  id: number;
  kind: string;
  records_processed: number;
  records_changed: number;
  detail: Record<string, unknown> | null;
  created_at: string | null;
}

interface DashboardData {
  status: BackgroundJobStatus;
  history: AutomationLogEntry[];
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return "—";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

function statusLabel(status: string | null): string {
  if (!status) return "Unknown";
  return status.charAt(0).toUpperCase() + status.slice(1).replace(/_/g, " ");
}

// ── Component ───────────────────────────────────────────────────────────────

export default function BackgroundJobsPage() {
  const addToast = useToastStore((s) => s.addToast);
  const locale = useLocaleStore((s) => s.locale);
  const isRtl = isRtlLocale(locale);

  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [wsStatus, setWsStatus] = useState<RealtimeStatus>("connecting");
  const [rowActionLoadingKey, setRowActionLoadingKey] = useState<
    number | null
  >(null);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await apiFetch("/admin/background-job-status");
      if (res.ok) {
        const d = (await res.json()) as DashboardData;
        setData(d);
      }
    } catch {
      // Silent failure on background refresh
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // WebSocket: receive real-time push when a background sweep completes.
  // Replaces the 15-second polling interval — the server pushes updates
  // immediately after each sweep via ``broadcast_background_job_update``.
  useEffect(() => {
    const handle = connectBackgroundJobSocket(
      (status: RealtimeStatus) => {
        setWsStatus(status);
      },
      (payload: BackgroundJobWSMessage | null) => {
        if (payload?.event === "sweep_completed") {
          // Sweep finished — refresh the full status from the REST endpoint
          fetchStatus();
        }
      },
    );
    return () => {
      handle.close();
    };
  }, [fetchStatus]);

  const runSingleSweep = async (
    kind: "supplier" | "logistics",
    logEntryId: number,
  ) => {
    setRowActionLoadingKey(logEntryId);
    try {
      const res = await apiFetch(`/admin/background-job/trigger/${kind}`, {
        method: "POST",
      });
      if (res.ok) {
        const data = await res.json();
        addToast(
          `${
            kind === "supplier" ? "Supplier" : "Logistics"
          } sweep complete: ${data.processed ?? 0} processed`,
          "success",
        );
        await fetchStatus();
      } else {
        const err = await res.json().catch(() => ({ detail: "Sweep failed" }));
        addToast(err.detail || `Failed to run ${kind} sweep`, "error");
      }
    } catch {
      addToast(`Network error running ${kind} sweep`, "error");
    } finally {
      setRowActionLoadingKey(null);
    }
  };

  const performAction = async (action: "start" | "stop" | "trigger") => {
    setActionLoading(action);
    try {
      const res = await apiFetch(`/admin/background-job/${action}`, {
        method: "POST",
      });
      if (res.ok) {
        addToast(
          action === "start"
            ? "Background job started"
            : action === "stop"
              ? "Background job stopping"
              : "Sweep triggered successfully",
          "success",
        );
        // Refresh to show updated state
        await fetchStatus();
      } else {
        const err = await res.json().catch(() => ({ detail: "Action failed" }));
        addToast(err.detail || `Failed to ${action}`, "error");
      }
    } catch {
      addToast(`Network error during ${action}`, "error");
    } finally {
      setActionLoading(null);
    }
  };

  const s = data?.status;

  // ── Stats cards ─────────────────────────────────────────────────────────

  const stats = [
    {
      label: "Status",
      value: s?.is_running ? "Running" : "Stopped",
      icon: Activity,
      color: s?.is_running ? "text-emerald-600" : "text-text-muted",
      bg: s?.is_running ? "bg-emerald-50" : "bg-surface-2",
    },
    {
      label: "Last Run",
      value: s?.last_run_at ? timeAgo(s.last_run_at) : "Never",
      icon: Clock,
      color: "text-blue-600",
      bg: "bg-blue-50",
    },
    {
      label: "Settlements Processed",
      value: String(s?.total_settlements_processed ?? 0),
      icon: FileText,
      color: "text-purple-600",
      bg: "bg-purple-50",
    },
    {
      label: "Total Sweeps",
      value: String(s?.total_sweep_count ?? 0),
      icon: TrendingUp,
      color: "text-amber-600",
      bg: "bg-amber-50",
    },
  ];

  const lastResult = s?.last_supplier_result;
  const lastStatus: string | null = s?.last_run_status ?? null;

  return (
    <main className="min-h-screen" dir={isRtl ? "rtl" : "ltr"}>
      <div className="mx-auto max-w-7xl px-4 sm:px-6 py-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-text">Background Jobs</h1>
            <p className="text-sm text-text-faint mt-1">
              Auto-payout scheduler status and control panel
            </p>
          </div>
          <div className="flex items-center gap-3">
            {/* WebSocket live indicator */}
            <div
              className="flex items-center gap-1.5 text-xs"
              title={
                wsStatus === "live"
                  ? "Connected — updates pushed in real-time"
                  : wsStatus === "connecting"
                    ? "Connecting to real-time feed..."
                    : wsStatus === "offline"
                      ? "Disconnected — falling back to manual refresh"
                      : "Idle"
              }
            >
              {wsStatus === "live" ? (
                <>
                  <Wifi className="w-3.5 h-3.5 text-emerald-500" />
                  <span className="text-text-faint hidden sm:inline">
                    Live
                  </span>
                </>
              ) : wsStatus === "connecting" ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 text-amber-500 animate-spin" />
                  <span className="text-text-faint hidden sm:inline">
                    Connecting
                  </span>
                </>
              ) : (
                <>
                  <WifiOff className="w-3.5 h-3.5 text-text-faint" />
                  <span className="text-text-faint hidden sm:inline">
                    Offline
                  </span>
                </>
              )}
            </div>

            <button
              onClick={fetchStatus}
              disabled={loading}
              className="theme-btn-outline rounded-xl px-4 py-2 text-xs font-semibold flex items-center gap-2"
            >
              {loading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <RefreshCw className="w-3.5 h-3.5" />
              )}
              Refresh
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {stats.map((stat) => {
            const Icon = stat.icon;
            return (
              <div
                key={stat.label}
                className="theme-card rounded-xl border border-border p-4"
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-10 h-10 rounded-lg ${stat.bg} flex items-center justify-center ${stat.color}`}
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-xs text-text-faint">{stat.label}</p>
                    <p className="text-lg font-bold text-text">{stat.value}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Action Buttons */}
        <div className="theme-card rounded-xl border border-border p-4">
          <h3 className="text-sm font-semibold text-text mb-3">
            Scheduler Controls
          </h3>
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => performAction("start")}
              disabled={actionLoading === "start" || s?.is_running}
              className={`rounded-xl px-4 py-2 text-xs font-semibold flex items-center gap-2 ${
                s?.is_running
                  ? "bg-surface-1 text-text-faint cursor-not-allowed"
                  : "theme-btn-primary"
              }`}
            >
              {actionLoading === "start" ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Play className="w-3.5 h-3.5" />
              )}
              Start Scheduler
            </button>

            <button
              onClick={() => performAction("stop")}
              disabled={actionLoading === "stop" || !s?.is_running}
              className={`rounded-xl px-4 py-2 text-xs font-semibold flex items-center gap-2 ${
                !s?.is_running
                  ? "bg-surface-1 text-text-faint cursor-not-allowed"
                  : "theme-action-danger"
              }`}
            >
              {actionLoading === "stop" ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Square className="w-3.5 h-3.5" />
              )}
              Stop Scheduler
            </button>

            <button
              onClick={() => performAction("trigger")}
              disabled={actionLoading === "trigger"}
              className={`rounded-xl px-4 py-2 text-xs font-semibold flex items-center gap-2 ${
                actionLoading === "trigger"
                  ? "bg-surface-1 text-text-faint cursor-not-allowed"
                  : "theme-btn-outline"
              }`}
            >
              {actionLoading === "trigger" ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <RefreshCw className="w-3.5 h-3.5" />
              )}
              Trigger Sweep Now
            </button>
          </div>
        </div>

        {/* Last Run Details */}
        {lastResult && (
          <div className="theme-card rounded-xl border border-border p-4">
            <h3 className="text-sm font-semibold text-text mb-3">
              Last Sweep Result
            </h3>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <div className="bg-surface-1 rounded-lg p-3">
                <p className="text-[10px] text-text-faint uppercase tracking-wider">
                  Status
                </p>
                <div className="flex items-center gap-1.5 mt-1">
                  {lastStatus === "ok" ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  ) : lastStatus === "error" ? (
                    <XCircle className="w-4 h-4 text-red-500" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-amber-500" />
                  )}
                  <span className="text-sm font-semibold text-text">
                    {statusLabel(lastStatus)}
                  </span>
                </div>
              </div>
              <div className="bg-surface-1 rounded-lg p-3">
                <p className="text-[10px] text-text-faint uppercase tracking-wider">
                  Supplier Settlements
                </p>
                <p className="text-sm font-bold text-text mt-1">
                  {Number(s?.last_supplier_result?.processed ?? 0)}
                </p>
              </div>
              <div className="bg-surface-1 rounded-lg p-3">
                <p className="text-[10px] text-text-faint uppercase tracking-wider">
                  Logistics Settlements
                </p>
                <p className="text-sm font-bold text-text mt-1">
                  {Number(s?.last_logistics_result?.processed ?? 0)}
                </p>
              </div>
              <div className="bg-surface-1 rounded-lg p-3">
                <p className="text-[10px] text-text-faint uppercase tracking-wider">
                  Suppliers Paid
                </p>
                <p className="text-sm font-bold text-text mt-1">
                  {Number(s?.last_supplier_result?.supplier_count ?? 0)}
                </p>
              </div>
            </div>

            {s?.last_error && (
              <div className="mt-3 bg-red-50 border border-red-200 rounded-lg p-3">
                <div className="flex items-center gap-2">
                  <XCircle className="w-4 h-4 text-red-500 shrink-0" />
                  <p className="text-xs text-red-700 font-medium">
                    Last Error
                  </p>
                </div>
                <p className="text-xs text-red-600 mt-1 font-mono">
                  {s.last_error}
                </p>
              </div>
            )}

            {s?.last_run_at && (
              <p className="text-[10px] text-text-faint mt-2">
                Last run: {new Date(s.last_run_at).toLocaleString()}
              </p>
            )}
          </div>
        )}

        {/* History Table */}
        <div className="theme-card rounded-xl border border-border p-4">
          <h3 className="text-sm font-semibold text-text mb-3">
            Recent Automation History
          </h3>

          {!data || data.history.length === 0 ? (
            <div className="py-8 text-center">
              <Clock className="w-8 h-8 text-text-faint mx-auto mb-2" />
              <p className="text-xs text-text-faint">
                No automation runs recorded yet.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-surface-1 text-text-faint text-[10px] uppercase tracking-wider">
                    <th className="text-left px-3 py-2 font-medium">Time</th>
                    <th className="text-left px-3 py-2 font-medium">Kind</th>
                    <th className="text-right px-3 py-2 font-medium">
                      Processed
                    </th>
                    <th className="text-right px-3 py-2 font-medium">
                      Changed
                    </th>
                    <th className="text-left px-3 py-2 font-medium">Batch</th>
                    <th className="text-right px-3 py-2 font-medium">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {data.history.map((entry) => {
                    // Only show Run Now for known sweep kinds
                    if (
                      entry.kind !== "auto_payout" &&
                      entry.kind !== "auto_logistics_payout"
                    ) {
                      return (
                        <tr
                          key={entry.id}
                          className="border-t border-border/50 hover:bg-surface-1/30"
                        >
                          <td className="px-3 py-2.5 text-text-muted whitespace-nowrap">
                            {timeAgo(entry.created_at)}
                          </td>
                          <td className="px-3 py-2.5">
                            <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-gray-50 text-gray-700">
                              {entry.kind}
                            </span>
                          </td>
                          <td className="px-3 py-2.5 text-right font-semibold text-text">
                            {entry.records_processed}
                          </td>
                          <td className="px-3 py-2.5 text-right font-semibold text-text">
                            {entry.records_changed}
                          </td>
                          <td className="px-3 py-2.5 text-text-faint max-w-[160px] truncate">
                            {String(entry.detail?.batch_number ?? "—")}
                          </td>
                          <td className="px-3 py-2.5 text-right">
                            <span className="text-[10px] text-text-faint">
                              —
                            </span>
                          </td>
                        </tr>
                      );
                    }
                    const sweepKind =
                      entry.kind === "auto_payout" ? "supplier" : "logistics";
                    const rowActionLoading =
                      rowActionLoadingKey === entry.id;
                    return (
                      <tr
                        key={entry.id}
                        className="border-t border-border/50 hover:bg-surface-1/30"
                      >
                        <td className="px-3 py-2.5 text-text-muted whitespace-nowrap">
                          {timeAgo(entry.created_at)}
                        </td>
                        <td className="px-3 py-2.5">
                          <span
                            className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
                              entry.kind === "auto_payout"
                                ? "bg-blue-50 text-blue-700"
                                : "bg-purple-50 text-purple-700"
                            }`}
                          >
                            {entry.kind === "auto_payout"
                              ? "Supplier"
                              : "Logistics"}
                          </span>
                        </td>
                        <td className="px-3 py-2.5 text-right font-semibold text-text">
                          {entry.records_processed}
                        </td>
                        <td className="px-3 py-2.5 text-right font-semibold text-text">
                          {entry.records_changed}
                        </td>
                        <td className="px-3 py-2.5 text-text-faint max-w-[160px] truncate">
                          {String(entry.detail?.batch_number ?? "—")}
                        </td>
                        <td className="px-3 py-2.5 text-right">
                          <button
                            onClick={() =>
                              runSingleSweep(
                                sweepKind as "supplier" | "logistics",
                                entry.id,
                              )
                            }
                            disabled={rowActionLoading}
                            className={`rounded-lg px-2.5 py-1 text-[10px] font-semibold flex items-center gap-1 ml-auto ${
                              rowActionLoading
                                ? "bg-surface-1 text-text-faint cursor-not-allowed"
                                : sweepKind === "supplier"
                                  ? "bg-blue-50 text-blue-700 hover:bg-blue-100"
                                  : "bg-purple-50 text-purple-700 hover:bg-purple-100"
                            }`}
                          >
                            {rowActionLoading ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                              <Play className="w-3 h-3" />
                            )}
                            Run Now
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
