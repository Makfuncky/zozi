"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  Users, Activity, TrendingUp, AlertCircle, CheckCircle2,
  Clock, ArrowRight, Loader2, RefreshCw, Calendar,
  UserPlus, UserX, BarChart3, Star, Award, Zap,
} from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent } from "@/components/PanelPage";
import { StatCard } from "@/components/ui/StatCard";
import { apiFetch, getAccessToken } from "@/lib/api";
import { useAdminCountry } from "@/lib/useAdminCountry";
import { useAuth } from "@/lib/useAuth";
import { isAdminStaffRole } from "@shared/adminPermissions";

/* ── WebSocket helpers ───────────────────────────────────── */

const WS_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/^http/, "ws");
const WS_RECONNECT_DELAY = 3000;

/* ════════════════════════ Types ════════════════════════ */

interface OnboardingData {
  stats: { active: number; overdue: number; completed: number; cancelled: number };
  overdue_items: Array<{
    id: number; employee_id: number; current_step: string;
    total_steps: number; completed_steps: number; due_date: string;
    employee_code: string | null; department: string | null; position: string | null;
  }>;
}

interface PerfStats {
  green: number; amber: number; red: number; not_scored: number; avg_score: number | null;
}

interface Performer {
  id: number; employee_code: string; department: string | null;
  position: string | null; performance_score: number | null;
}

interface PerformanceData {
  stats: PerfStats;
  top_performers: Performer[];
  bottom_performers: Performer[];
}

interface ActivityEvent {
  id: number; actor_employee_id: number; actor_code: string | null;
  action: string; entity_type: string | null; target_code: string | null;
  timestamp: string | null;
}

interface ActivityData {
  total_events: number;
  action_breakdown: Record<string, number>;
  events: ActivityEvent[];
}

interface HrDashboardData {
  onboarding: OnboardingData;
  performance: PerformanceData;
  activity: ActivityData;
  employees: { total: number; active: number; terminating: number; terminated: number };
}

/* ════════════════════════ Helpers ════════════════════════ */

const ACTION_LABELS: Record<string, string> = {
  login: "Logged In", logout: "Logged Out", attendance_scan: "Attendance Scan",
  chat_sent: "Sent Chat", email_sent: "Sent Email", channel_sent: "Channel Message",
  submitted_review: "Submitted Review", approved_leave: "Approved Leave",
  handover: "Shift Handover", document_share: "Shared Document",
};

function formatAction(action: string): string {
  return ACTION_LABELS[action] || action.replace(/_/g, " ");
}

const ACTION_ICONS: Record<string, any> = {
  login: Clock, logout: UserX, attendance_scan: Clock,
  chat_sent: Activity, email_sent: Activity,
  submitted_review: Star, approved_leave: CheckCircle2,
  handover: RefreshCw, document_share: Activity,
};

function getActionIcon(action: string) {
  return ACTION_ICONS[action] || Activity;
}

function getScoreColor(score: number | null): string {
  if (score === null) return "text-text-faint";
  if (score >= 4.0) return "text-success";
  if (score >= 2.5) return "text-warning";
  return "text-danger";
}

function getScoreBg(score: number | null): string {
  if (score === null) return "bg-surface-2";
  if (score >= 4.0) return "bg-success/10";
  if (score >= 2.5) return "bg-warning/10";
  return "bg-danger/10";
}

/* ════════════════════════ Component ════════════════════════ */

export default function HrDashboardPage() {
  const { user, isLoggedIn, isLoading } = useAuth();
  const { selectedCountry } = useAdminCountry();
  const role = user?.role ?? null;

  const [data, setData] = useState<HrDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [liveEvents, setLiveEvents] = useState<ActivityEvent[]>([]);
  const [wsConnected, setWsConnected] = useState(false);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams({ days: "7" });
      if (selectedCountry?.code && selectedCountry.code !== "*") {
        params.set("country_code", selectedCountry.code);
      }
      const res = await apiFetch(`/hr/dashboard?${params.toString()}`);
      if (res.ok) {
        const json = await res.json();
        setData(json);
      } else {
        setError("Failed to load HR dashboard");
      }
    } catch (e: any) {
      setError(e?.message || "Network error");
    } finally {
      setLoading(false);
    }
  }, [selectedCountry]);

  useEffect(() => {
    if (isLoading) return;
    if (!isLoggedIn || !isAdminStaffRole(role)) return;
    loadDashboard();
  }, [isLoading, isLoggedIn, role, loadDashboard]);

  // ── WebSocket Connection ──
  useEffect(() => {
    if (!isLoggedIn || !isAdminStaffRole(role)) return;

    const token = getAccessToken();
    if (!token) return;

    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout>;

    function connect() {
      ws = new WebSocket(`${WS_BASE}/ws/hr/activity?token=${encodeURIComponent(token!)}`);

      ws.onopen = () => {
        setWsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === "activity.new") {
            const newEvent: ActivityEvent = {
              id: msg.id,
              actor_employee_id: msg.actor_employee_id,
              actor_code: null, // Will be filled on next dashboard refresh
              action: msg.action,
              entity_type: msg.entity_type || null,
              target_code: null,
              timestamp: msg.timestamp || new Date().toISOString(),
            };
            setLiveEvents((prev) => [newEvent, ...prev].slice(0, 20));
          }
        } catch (e) {
          // Ignore malformed messages
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
        reconnectTimer = setTimeout(connect, WS_RECONNECT_DELAY);
      };

      ws.onerror = () => {
        ws?.close();
      };
    }

    connect();

    return () => {
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (ws) {
        ws.onclose = null; // prevent reconnect on intentional close
        ws.close();
      }
      setWsConnected(false);
    };
  }, [isLoggedIn, role]);

  // Clear live events when manually refreshing
  const handleRefresh = useCallback(() => {
    setLiveEvents([]);
    loadDashboard();
  }, [loadDashboard]);

  // Merge live events into the activity feed display
  const mergedActivityEvents = useMemo(() => {
    if (!data) return [];
    const existingIds = new Set(data.activity.events.map((e) => e.id));
    const fresh = liveEvents.filter((e) => !existingIds.has(e.id));
    return [...fresh, ...data.activity.events].slice(0, 50);
  }, [data, liveEvents]);

  if (isLoading || !isLoggedIn || !isAdminStaffRole(role)) {
    return (
      <AdminLayout title="HR Dashboard" headerMode="compact">
        <PanelContent className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 text-primary animate-spin" />
        </PanelContent>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout title="HR Dashboard" headerMode="compact">
      <PanelContent className="space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-text">HR Dashboard</h1>
            <p className="text-xs text-text-muted">
              Onboarding pipeline, performance health, and recent activity
              {selectedCountry?.code && selectedCountry.code !== "*" && (
                <span className="ml-1">· {selectedCountry.name || selectedCountry.code}</span>
              )}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {/* Live indicator */}
            <div className="flex items-center gap-1.5 rounded-full border border-border bg-surface-2 px-3 py-1.5">
              <span
                className={`h-2 w-2 rounded-full ${wsConnected ? "bg-success animate-pulse" : "bg-text-faint"}`}
              />
              <span className="text-[10px] font-medium text-text-muted">
                {wsConnected ? "Live" : "Offline"}
              </span>
            </div>
            <button
              onClick={handleRefresh}
              disabled={loading}
              className="flex items-center gap-1.5 rounded-xl border border-border bg-surface-2 px-3.5 py-2 text-xs font-semibold text-text-muted hover:text-text transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="flex items-center gap-2 rounded-xl border border-danger/20 bg-danger/5 px-4 py-3">
            <AlertCircle className="h-4 w-4 shrink-0 text-danger" />
            <p className="text-xs text-danger">{error}</p>
          </div>
        )}

        {loading && !data && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-28 rounded-xl bg-surface-2 animate-pulse" />
            ))}
          </div>
        )}

        {data && (
          <>
            {/* ═══ Stats Row ═══ */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3"
            >
              <StatCard
                label="Total Employees"
                value={String(data.employees.total)}
                sub={`${data.employees.active} active`}
                icon={Users}
                color="bg-primary/10 text-primary"
              />
              <StatCard
                label="Active Pipeline"
                value={String(data.onboarding.stats.active + data.onboarding.stats.overdue)}
                sub={`${data.onboarding.stats.overdue} overdue`}
                icon={UserPlus}
                color={data.onboarding.stats.overdue > 0 ? "bg-danger/10 text-danger" : "bg-success/10 text-success"}
              />
              <StatCard
                label="Performance Score"
                value={data.performance.stats.avg_score !== null ? String(data.performance.stats.avg_score) : "—"}
                sub={`${data.performance.stats.green} green · ${data.performance.stats.amber} amber · ${data.performance.stats.red} red`}
                icon={Star}
                color="bg-warning/10 text-warning"
              />
              <StatCard
                label="Green Performers"
                value={String(data.performance.stats.green)}
                sub={`${data.performance.stats.not_scored} not scored`}
                icon={TrendingUp}
                color="bg-success/10 text-success"
              />
              <StatCard
                label="Activity (7d)"
                value={String(data.activity.total_events)}
                sub={`${Object.keys(data.activity.action_breakdown).length} action types`}
                icon={Activity}
                color="bg-info/10 text-info"
              />
              <StatCard
                label="Terminating"
                value={String(data.employees.terminating)}
                sub={`${data.employees.terminated} terminated`}
                icon={UserX}
                color={data.employees.terminating > 0 ? "bg-warning/10 text-warning" : "bg-surface-2 text-text-muted"}
              />
            </motion.div>

            {/* ═══ Main Grid ═══ */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

              {/* ─── Onboarding Pipeline ─── */}
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="lg:col-span-2 rounded-xl border border-border bg-surface overflow-hidden"
              >
                <div className="flex items-center justify-between border-b border-border px-4 py-3">
                  <div className="flex items-center gap-2">
                    <UserPlus className="h-4 w-4 text-primary" />
                    <h2 className="text-sm font-semibold text-text">Onboarding Pipeline</h2>
                  </div>
                  <div className="flex items-center gap-2 text-[10px]">
                    <span className="rounded-full bg-success/10 px-2 py-0.5 text-success font-medium">
                      {data.onboarding.stats.completed} completed
                    </span>
                    {data.onboarding.stats.overdue > 0 && (
                      <span className="rounded-full bg-danger/10 px-2 py-0.5 text-danger font-medium">
                        {data.onboarding.stats.overdue} overdue
                      </span>
                    )}
                  </div>
                </div>

                {/* Pipeline progress bar */}
                {data.onboarding.stats.active + data.onboarding.stats.completed > 0 && (
                  <div className="px-4 pt-3">
                    <div className="flex items-center gap-2 text-[10px] text-text-muted mb-1">
                      <span>Pipeline completion</span>
                      <span className="ml-auto tabular-nums">
                        {data.onboarding.stats.completed} / {data.onboarding.stats.active + data.onboarding.stats.completed}
                      </span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-surface-2 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-success transition-all"
                        style={{
                          width: `${
                            data.onboarding.stats.active + data.onboarding.stats.completed > 0
                              ? (data.onboarding.stats.completed / (data.onboarding.stats.active + data.onboarding.stats.completed)) * 100
                              : 0
                          }%`,
                        }}
                      />
                    </div>
                  </div>
                )}

                {/* Overdue items */}
                <div className="p-4 space-y-2 max-h-[360px] overflow-y-auto">
                  {data.onboarding.overdue_items.length === 0 && data.onboarding.stats.active === 0 ? (
                    <div className="flex flex-col items-center justify-center py-8 text-center">
                      <CheckCircle2 className="h-8 w-8 text-success/40 mb-2" />
                      <p className="text-xs text-text-muted">No active onboarding pipelines</p>
                    </div>
                  ) : data.onboarding.overdue_items.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-6 text-center">
                      <CheckCircle2 className="h-8 w-8 text-success/40 mb-2" />
                      <p className="text-xs text-text-muted">All pipelines on track</p>
                      <p className="text-[10px] text-text-faint mt-0.5">
                        {data.onboarding.stats.active} active · {data.onboarding.stats.completed} completed
                      </p>
                    </div>
                  ) : (
                    data.onboarding.overdue_items.map((item) => (
                      <div
                        key={item.id}
                        className="flex items-center justify-between rounded-lg border border-danger/20 bg-danger/[0.03] px-3 py-2"
                      >
                        <div className="min-w-0">
                          <p className="text-xs font-medium text-text truncate">
                            {item.employee_code || `Employee #${item.employee_id}`}
                          </p>
                          <p className="text-[10px] text-text-muted mt-0.5">
                            {item.current_step?.replace(/_/g, " ") || "Starting"} · {item.completed_steps}/{item.total_steps} steps
                          </p>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <span className="text-[9px] text-danger font-semibold whitespace-nowrap">
                            OVERDUE
                          </span>
                          <ArrowRight className="h-3 w-3 text-text-faint" />
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </motion.div>

              {/* ─── Performance Health ─── */}
              <motion.div
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                className="rounded-xl border border-border bg-surface overflow-hidden"
              >
                <div className="flex items-center justify-between border-b border-border px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Star className="h-4 w-4 text-warning" />
                    <h2 className="text-sm font-semibold text-text">Performance Health</h2>
                  </div>
                </div>
                <div className="p-4 space-y-3">
                  {/* Color distribution */}
                  <div className="space-y-2">
                    <HealthBar
                      label="Green (≥ 4.0)"
                      count={data.performance.stats.green}
                      total={data.performance.stats.green + data.performance.stats.amber + data.performance.stats.red}
                      color="bg-success"
                    />
                    <HealthBar
                      label="Amber (2.5–4.0)"
                      count={data.performance.stats.amber}
                      total={data.performance.stats.green + data.performance.stats.amber + data.performance.stats.red}
                      color="bg-warning"
                    />
                    <HealthBar
                      label="Red (&lt; 2.5)"
                      count={data.performance.stats.red}
                      total={data.performance.stats.green + data.performance.stats.amber + data.performance.stats.red}
                      color="bg-danger"
                    />
                  </div>

                  {data.performance.stats.not_scored > 0 && (
                    <p className="text-[10px] text-text-faint text-center">
                      {data.performance.stats.not_scored} employees not yet scored
                    </p>
                  )}

                  {/* Top Performers */}
                  {data.performance.top_performers.length > 0 && (
                    <div>
                      <div className="flex items-center gap-1.5 mb-2">
                        <Award className="h-3 w-3 text-success" />
                        <span className="text-[10px] font-semibold text-text-muted uppercase tracking-wider">Top Performers</span>
                      </div>
                      <div className="space-y-1">
                        {data.performance.top_performers.slice(0, 5).map((p) => (
                          <div key={p.id} className="flex items-center justify-between rounded-lg bg-surface-2 px-2.5 py-1.5">
                            <div className="min-w-0">
                              <p className="text-[11px] font-medium text-text truncate">{p.employee_code}</p>
                              <p className="text-[9px] text-text-faint truncate">{p.department || p.position || "—"}</p>
                            </div>
                            <span className={`text-[11px] font-bold font-mono ${getScoreColor(p.performance_score)}`}>
                              {p.performance_score?.toFixed(2)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Bottom Performers */}
                  {data.performance.bottom_performers.length > 0 && (
                    <div>
                      <div className="flex items-center gap-1.5 mb-2">
                        <AlertCircle className="h-3 w-3 text-danger" />
                        <span className="text-[10px] font-semibold text-text-muted uppercase tracking-wider">Needs Attention</span>
                      </div>
                      <div className="space-y-1">
                        {data.performance.bottom_performers.map((p) => (
                          <div key={p.id} className="flex items-center justify-between rounded-lg bg-surface-2 px-2.5 py-1.5">
                            <div className="min-w-0">
                              <p className="text-[11px] font-medium text-text truncate">{p.employee_code}</p>
                              <p className="text-[9px] text-text-faint truncate">{p.department || p.position || "—"}</p>
                            </div>
                            <span className="text-[11px] font-bold font-mono text-danger">
                              {p.performance_score?.toFixed(2)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {data.performance.stats.green + data.performance.stats.amber + data.performance.stats.red === 0 && (
                    <div className="flex flex-col items-center justify-center py-6 text-center">
                      <BarChart3 className="h-8 w-8 text-text-faint/40 mb-2" />
                      <p className="text-xs text-text-muted">No performance data yet</p>
                      <p className="text-[10px] text-text-faint mt-0.5">
                        Scores appear after 360° reviews are submitted
                      </p>
                    </div>
                  )}
                </div>
              </motion.div>
            </div>

            {/* ═══ Activity Feed ═══ */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-xl border border-border bg-surface overflow-hidden"
            >
              <div className="flex items-center justify-between border-b border-border px-4 py-3">
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-info" />
                  <h2 className="text-sm font-semibold text-text">
                    Recent Activity (7 days)
                  </h2>
                  {liveEvents.length > 0 && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-info/10 px-2 py-0.5 text-[9px] font-semibold text-info animate-pulse">
                      <Zap className="h-2.5 w-2.5" />
                      +{liveEvents.length} new
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2 text-[10px]">
                  {Object.entries(data.activity.action_breakdown).slice(0, 4).map(([action, count]) => (
                    <span key={action} className="rounded-full bg-surface-2 px-2 py-0.5 text-text-muted font-medium">
                      {formatAction(action)} {count}
                    </span>
                  ))}
                </div>
              </div>

              {mergedActivityEvents.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <Activity className="h-8 w-8 text-text-faint/40 mb-2" />
                  <p className="text-xs text-text-muted">No recent activity</p>
                  <p className="text-[10px] text-text-faint mt-0.5">Activity appears once employees log in and perform actions</p>
                </div>
              ) : (
                <div className="max-h-[400px] overflow-y-auto">
                  {mergedActivityEvents.map((event, idx) => {
                    const Icon = getActionIcon(event.action);
                    return (
                      <div
                        key={event.id}
                        className="flex items-center gap-3 border-b border-border/50 px-4 py-2.5 last:border-0 hover:bg-surface-2/50 transition-colors"
                      >
                        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-info/10">
                          <Icon className="h-3.5 w-3.5 text-info" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs text-text">
                            <span className="font-semibold">{event.actor_code || `#${event.actor_employee_id}`}</span>
                            {" "}{formatAction(event.action)}{" "}
                            {event.entity_type && <span className="text-text-muted">· {event.entity_type}</span>}
                            {event.target_code && (
                              <span className="text-text-muted"> → {event.target_code}</span>
                            )}
                          </p>
                        </div>
                        <span className="text-[9px] text-text-faint tabular-nums shrink-0">
                          {event.timestamp ? new Date(event.timestamp).toLocaleDateString("en-US", {
                            month: "short", day: "numeric", hour: "2-digit", minute: "2-digit"
                          }) : "—"}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </motion.div>
          </>
        )}
      </PanelContent>
    </AdminLayout>
  );
}

/* ════════════════════════ Sub-Components ════════════════════════ */

function HealthBar({ label, count, total, color }: {
  label: string; count: number; total: number; color: string;
}) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <div>
      <div className="flex items-center justify-between text-[10px] mb-0.5">
        <span className="font-medium text-text-muted">{label}</span>
        <span className="font-semibold tabular-nums text-text">{count}</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-surface-2 overflow-hidden">
        <div className={`h-full rounded-full ${color} transition-all`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
