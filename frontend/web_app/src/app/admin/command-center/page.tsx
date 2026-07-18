"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Activity, AlertCircle, ArrowUpRight, Banknote, Bell, Box, Building2, Clock, Cpu,
  DollarSign, Globe2, LayoutGrid, Lock, Package, RefreshCw, Rows3,
  Search, Shield, ShieldAlert, ShoppingCart, Store, TrendingUp, Truck,
  UserCheck, UserX, Users, Wallet, Wifi, Zap,
} from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent } from "@/components/PanelPage";
import {
  HudBackground, Section, Stat, AreaChart, DonutChart, Bars,
  Gauge, Meter, Ticker, AlertRow, FraudRow, RankRow, MicroChart,
  HUD, HudColor,
} from "@/components/admin/commandCenter/hud";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { hasAdminPermission, isAdminStaffRole } from "@shared/adminPermissions";
import { useAdminCountry } from "@/lib/useAdminCountry";
import { cn } from "@/lib/utils";

/* ================================================================== */
/*  Types                                                              */
/* ================================================================== */
type DensityMode = "compact" | "balanced" | "expanded";

interface HeartbeatMetrics {
  today_orders: number; today_revenue: number; today_gmv: number;
  delayed_orders: number; failed_deliveries: number;
  active_customers_buying: number; active_customers_window_shopping: number;
  employees_working: number; system_issues: number;
  active_logistics_partners: number; logistics_issues: number;
}
interface TreasuryMetrics {
  available_cash: number; locked_cash: number; operating_cash: number;
  commission_reserve: number; vat_liability: number; pending_payouts: number;
  supplier_payables: number; logistics_payables: number; refund_reserve: number;
  refunds_today: number; active_disputes: number;
}
interface OperationsMetrics {
  stuck_orders: number; failed_deliveries: number; late_deliveries: number;
  kyc_pending: number; supplier_issues: number; logistics_issues: number;
  product_moderation: number; return_requests: number; open_tickets: number;
}
interface EcosystemMetrics {
  users: { customers: number; suppliers: number; employees: number; logistics_companies: number; logistics_individuals: number; };
  total_products: number; active_suppliers: number; supplier_issues: number;
  gender_stats: { gender: string; count: number }[];
}
interface GrowthMetrics {
  revenue_trend: { date: string; revenue: number }[];
  country_sales: { country: string; orders: number; revenue: number }[];
  category_trends: { category: string; items_sold: number; revenue: number }[];
  top_products: { product_id: number; product_name: string; units_sold: number; revenue: number }[];
  top_searches: { query: string; count: number; zero_results: number }[];
}
interface WorkforceMetrics {
  employees_by_department: { department: string; count: number }[];
  recent_hires_30d: number; total_employees: number;
  tickets_resolved_today: number; moderation_approval_rate: number;
  moderation_pending: number; employees_logged_today: number; avg_hours_logged_today: number;
}
interface SystemMetrics {
  active_sessions: number; api_latency: number; error_rate: number;
  cpu_usage: number; memory_usage: number; db_connections: number; redis_hit_ratio: number;
}
interface AlertItem { id: number; type: string; severity: string; title: string; message: string; country_code: string | null; created_at: string | null; }
interface FraudAlertItem { id: number; score: number; triggered_rules: string[]; status: string; priority: string; created_at: string | null; }
interface HeadlineItem { id: number; title: string; summary: string; category: string; sentiment: string; published_at: string | null; }
interface ComprehensiveData {
  timestamp: string; heartbeat: HeartbeatMetrics; treasury: TreasuryMetrics;
  operations: OperationsMetrics; ecosystem: EcosystemMetrics; growth: GrowthMetrics;
  workforce: WorkforceMetrics; system: SystemMetrics;
  alerts: AlertItem[]; fraud_alerts: FraudAlertItem[]; headlines: HeadlineItem[];
}

const DENSITY_KEY = "admin-cc-density";

function loadDensity(): DensityMode {
  if (typeof window === "undefined") return "balanced";
  try {
    const v = localStorage.getItem(DENSITY_KEY) as DensityMode | null;
    if (v === "compact" || v === "balanced" || v === "expanded") return v;
  } catch { }
  return "balanced";
}

function useClock(): string {
  const [t, setT] = useState("--:--:--");
  useEffect(() => {
    const tick = () => setT(new Date().toLocaleTimeString("en-GB"));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);
  return t;
}

function compactMoney(n: number): string {
  if (Math.abs(n) >= 1e6) return `${(n / 1e6).toFixed(2)}M`;
  if (Math.abs(n) >= 1e3) return `${(n / 1e3).toFixed(1)}K`;
  return Math.round(n).toLocaleString();
}

/* ================================================================== */
/*  MAIN PAGE — Single-Screen Iron-Man Mission Control                */
/* ================================================================== */
export default function AdminCommandCenterPage() {
  const router = useRouter();
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();
  const { selectedCountry, loading: countryLoading } = useAdminCountry();
  const clock = useClock();

  const role = user?.role ?? null;
  const canView = hasAdminPermission(role, "analytics.view");

  const [data, setData] = useState<ComprehensiveData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [wsStatus, setWsStatus] = useState<"connecting" | "connected" | "disconnected">("disconnected");
  const [density, setDensity] = useState<DensityMode>("balanced");
  const [alertFilter, setAlertFilter] = useState("");

  useEffect(() => { setDensity(loadDensity()); }, []);

  const updateDensity = (next: DensityMode) => {
    setDensity(next);
    try { localStorage.setItem(DENSITY_KEY, next); } catch { }
  };

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const res = await apiFetch("/admin/command-center/comprehensive", { disableCache: true });
      if (res.ok) {
        const json = (await res.json()) as ComprehensiveData;
        setData(json);
        setLastUpdated(new Date(json.timestamp).toLocaleTimeString());
      } else setError(true);
    } catch { setError(true); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn) { router.push("/admin/login"); return; }
    if (!isAdminStaffRole(role)) { router.push("/admin/dashboard"); return; }
    if (!canView) { router.push("/admin/dashboard"); return; }
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [authLoading, isLoggedIn, role, canView, router, fetchData]);

  useEffect(() => {
    if (!isLoggedIn) return;
    let ws: WebSocket | null = null;
    let rt: ReturnType<typeof setTimeout>;
    let attempts = 0;
    const connect = () => {
      if (attempts >= 3) { setWsStatus("disconnected"); return; }
      attempts++;
      setWsStatus("connecting");
      const p = window.location.protocol === "https:" ? "wss:" : "ws:";
      ws = new WebSocket(`${p}//${window.location.host}/admin/command-center/ws`);
      ws.onopen = () => setWsStatus("connected");
      ws.onclose = () => { setWsStatus("disconnected"); if (attempts < 3) rt = setTimeout(connect, 5000); };
      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);
          if (msg.type === "heartbeat" && msg.data) {
            setData((prev) => (prev ? { ...prev, heartbeat: msg.data, timestamp: msg.timestamp } : prev));
            setLastUpdated(new Date(msg.timestamp).toLocaleTimeString());
          }
        } catch { }
      };
    };
    connect();
    return () => { ws?.close(); clearTimeout(rt); };
  }, [isLoggedIn]);

  const revenueSpark = useMemo(() => data?.growth.revenue_trend.map((d) => d.revenue) ?? [], [data]);
  const filteredAlerts = useMemo(() => {
    const all = data?.alerts ?? [];
    if (!alertFilter.trim()) return all;
    const q = alertFilter.toLowerCase();
    return all.filter((a) => a.title.toLowerCase().includes(q) || a.message.toLowerCase().includes(q));
  }, [data, alertFilter]);

  const wsColor: keyof typeof HUD = wsStatus === "connected" || data ? "green" : wsStatus === "connecting" ? "amber" : "slate";

  const revenueTrend = data?.growth.revenue_trend ?? [];
  const pieSegments = (data?.growth.category_trends ?? []).slice(0, 6).map((c, i) => ({
    label: c.category, value: c.revenue,
    color: [HUD.green, HUD.blue, HUD.amber, HUD.red, HUD.purple, HUD.cyan][i % 6] as HudColor,
  }));
  const countryBars = (data?.growth.country_sales ?? []).slice(0, 7).map((c) => ({
    label: c.country, value: c.revenue, color: HUD.cyan as HudColor,
  }));

  const isCpt = density === "compact";
  const isExp = density === "expanded";
  const gap = isCpt ? "gap-1.5" : isExp ? "gap-3" : "gap-2";
  const pad = isCpt ? "p-2" : isExp ? "p-4" : "p-3";

  return (
    <AdminLayout title="Command Center" headerMode="compact">
      <HudBackground />
      <PanelContent className={cn("relative", gap, "pb-6")}>
        {/* ── Error ── */}
        {error && !loading && (
          <div className="theme-elevated flex items-center gap-3 rounded-xl border border-danger/20 p-2.5">
            <AlertCircle className="h-4 w-4 shrink-0 text-danger" />
            <p className="flex-1 text-[10px] font-bold text-text">TELEMETRY LINK LOST — Retry or check backend.</p>
            <button onClick={fetchData} className="theme-btn-primary rounded-lg px-3 py-1 text-[10px] font-semibold">Reconnect</button>
          </div>
        )}

        {/* ── TOP BAR ── */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-xl theme-elevated"
              style={{ border: `1px solid ${HUD.cyan}25`, boxShadow: `0 0 16px ${HUD.cyan}15` }}>
              <Zap className="h-3.5 w-3.5" style={{ color: HUD.cyan, filter: `drop-shadow(0 0 4px ${HUD.cyan})` }} />
            </div>
            <div>
              <h1 className="text-xs font-bold tracking-tight text-text">COMMAND CENTER</h1>
              <p className="font-mono text-[8px] uppercase tracking-[0.2em] text-text-faint">MISSION CONTROL · {clock}</p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-1.5">
            {selectedCountry && !countryLoading && (
              <span className="theme-elevated inline-flex items-center gap-1 rounded-lg px-2 py-1 text-[8px] font-semibold text-text-muted">
                <Globe2 className="h-2.5 w-2.5" style={{ color: HUD.cyan }} />
                {selectedCountry.code}
              </span>
            )}
            <span className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-[8px] font-semibold backdrop-blur-sm"
              style={{ color: HUD[wsColor], background: `color-mix(in srgb, ${HUD[wsColor]} 8%, var(--color-glass-mid))`, border: `1px solid color-mix(in srgb, ${HUD[wsColor]} 25%, transparent)` }}>
              <span className="relative flex h-1.5 w-1.5">
                {wsStatus === "connected" && <span className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-70" style={{ background: HUD[wsColor] }} />}
                <span className="relative inline-flex h-1.5 w-1.5 rounded-full" style={{ background: HUD[wsColor], boxShadow: `0 0 6px ${HUD[wsColor]}` }} />
              </span>
              {wsStatus === "connected" || data ? "LIVE" : wsStatus === "connecting" ? "SYNC" : "OFF"}
            </span>
            <div className="theme-elevated inline-flex rounded-lg overflow-hidden">
              {([
                { key: "compact" as DensityMode, icon: Rows3 },
                { key: "balanced" as DensityMode, icon: LayoutGrid },
                { key: "expanded" as DensityMode, icon: Activity },
              ]).map((opt) => (
                <button key={opt.key} onClick={() => updateDensity(opt.key)} aria-pressed={density === opt.key}
                  className={cn("px-1.5 py-1 transition-all", density === opt.key ? "text-text" : "text-text-faint hover:text-text-muted")}
                  style={density === opt.key ? { background: `color-mix(in srgb, var(--color-surface-2) 60%, transparent)` } : {}}>
                  <opt.icon className="h-2.5 w-2.5" />
                </button>
              ))}
            </div>
            <button onClick={fetchData} disabled={loading}
              className="theme-elevated inline-flex items-center gap-1 rounded-lg px-2 py-1 text-[8px] font-semibold text-text-muted hover:text-text disabled:opacity-50">
              <RefreshCw className={cn("h-2.5 w-2.5", loading && "animate-spin")} />
            </button>
          </div>
        </div>

        {/* ── ROW 1: OPERATIONAL HEARTBEAT ── */}
        <Section title="Operational Overview" subtitle="Today's commercial pulse" icon={ShoppingCart} accent="cyan" status={wsStatus === "connected" ? "live" : "idle"}>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-1.5">
            <Stat label="Orders" value={data?.heartbeat.today_orders ?? 0} icon={ShoppingCart} accent="cyan" loading={loading} />
            <Stat label="Revenue" value={data?.heartbeat.today_revenue ?? 0} format={compactMoney} icon={DollarSign} accent="green" loading={loading} sparkline={revenueSpark} />
            <Stat label="GMV" value={data?.heartbeat.today_gmv ?? 0} format={compactMoney} icon={TrendingUp} accent="blue" loading={loading} />
            <Stat label="Buying" value={data?.heartbeat.active_customers_buying ?? 0} icon={UserCheck} accent="green" trend={(data?.heartbeat.active_customers_buying ?? 0) > 0 ? "up" : "neutral"} loading={loading} />
            <Stat label="Employees" value={data?.heartbeat.employees_working ?? 0} icon={Building2} accent="purple" loading={loading} />
          </div>
        </Section>

        {/* ── ROW 2: CHARTS — Revenue Trend / Category Split / Country Sales ── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-1.5">
          <Section title="Revenue Trend" subtitle="30-day rolling" icon={TrendingUp} accent="green">
            <div className={cn(pad, "pt-0")}>
              <AreaChart data={revenueTrend.map((d) => ({ label: d.date, value: d.revenue }))} color="green" height={isCpt ? 60 : isExp ? 100 : 80} loading={loading} />
            </div>
          </Section>
          <Section title="Category Split" subtitle="Revenue by category" icon={Package} accent="blue">
            <div className={cn(pad, "pt-0")}>
              <DonutChart segments={pieSegments} centerLabel="CATS" height={isCpt ? 60 : isExp ? 100 : 80} loading={loading} />
            </div>
          </Section>
          <Section title="Country Sales" subtitle="Revenue by country" icon={Globe2} accent="cyan">
            <div className={cn(pad, "pt-0")}>
              <Bars data={countryBars} height={isCpt ? 60 : isExp ? 100 : 80} loading={loading} valueFormat={compactMoney} />
            </div>
          </Section>
        </div>

        {/* ── ROW 3: TREASURY ── */}
        <Section title="Treasury" subtitle="Live ledger" icon={Wallet} accent="amber"
          status={(data?.treasury.active_disputes ?? 0) > 0 ? "warn" : "live"}
          count={data?.treasury.active_disputes ?? 0}>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-1.5">
            <Stat label="Cash" value={data?.treasury.available_cash ?? 0} format={compactMoney} icon={Banknote} accent="green" loading={loading} />
            <Stat label="Locked" value={data?.treasury.locked_cash ?? 0} format={compactMoney} icon={Lock} accent="amber" loading={loading} />
            <Stat label="VAT" value={data?.treasury.vat_liability ?? 0} format={compactMoney} icon={DollarSign} accent="red" loading={loading} />
            <Stat label="Supplier Pay." value={data?.treasury.supplier_payables ?? 0} format={compactMoney} icon={Store} accent="amber" loading={loading} />
            <Stat label="Pending Payouts" value={data?.treasury.pending_payouts ?? 0} format={compactMoney} icon={Users} accent="amber" loading={loading} />
          </div>
        </Section>

        {/* ── ROW 4: GROWTH / PRODUCTS / DEPARTMENT ── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-1.5">
          <Section title="Top Products" subtitle="Revenue leaders" icon={Package} accent="green">
            <div className="max-h-28 overflow-y-auto space-y-1 pr-0.5">
              {loading ? Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-5 w-full rounded bg-surface-2/60 animate-pulse" />)
              : (data?.growth.top_products ?? []).slice(0, 6).map((p, i) => (
                <RankRow key={p.product_id} rank={i + 1} label={p.product_name} primary={compactMoney(p.revenue)} secondary={`${p.units_sold} u`} accent="green" />
              ))}
              {!loading && !data?.growth.top_products?.length && <p className="py-4 text-center text-[8px] text-text-faint font-mono">No data</p>}
            </div>
          </Section>
          <Section title="Top Searches" subtitle="Market demand signals" icon={Search} accent="cyan">
            <div className="max-h-28 overflow-y-auto space-y-1 pr-0.5">
              {loading ? Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-5 w-full rounded bg-surface-2/60 animate-pulse" />)
              : (data?.growth.top_searches ?? []).map((s, i) => (
                <RankRow key={s.query} rank={i + 1} label={s.query} primary={`${s.count}x`} secondary={s.zero_results > 0 ? `${s.zero_results} zero` : undefined} accent={s.zero_results > 0 ? "red" : "cyan"} />
              ))}
              {!loading && !data?.growth.top_searches?.length && <p className="py-4 text-center text-[8px] text-text-faint font-mono">No data</p>}
            </div>
          </Section>
          <Section title="Departments" subtitle="Headcount distribution" icon={Users} accent="purple">
            <div className="space-y-1.5">
              {loading ? Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-4 w-full rounded bg-surface-2/60 animate-pulse" />)
              : (data?.workforce.employees_by_department ?? []).slice(0, 6).map((d) => {
                const mx = Math.max(...(data?.workforce.employees_by_department ?? []).map(x => x.count), 1);
                return (
                  <div key={d.department} className="flex items-center gap-1.5">
                    <span className="w-16 shrink-0 truncate text-[8px] font-medium text-text">{d.department}</span>
                    <div className="h-1.5 flex-1 rounded-full bg-surface-2/50 overflow-hidden">
                      <div className="h-full rounded-full transition-all duration-500"
                        style={{ width: `${(d.count / mx) * 100}%`, background: `linear-gradient(90deg, ${HUD.purple}70, ${HUD.purple})`, boxShadow: `0 0 6px ${HUD.purple}30` }} />
                    </div>
                    <span className="w-5 shrink-0 text-right text-[8px] font-bold font-mono text-text tabular-nums">{d.count}</span>
                  </div>
                );
              })}
              {!loading && !data?.workforce.employees_by_department?.length && <p className="py-4 text-center text-[8px] text-text-faint font-mono">No data</p>}
            </div>
          </Section>
        </div>

        {/* ── ROW 5: ENGINE ROOM & SYSTEM HEALTH ── */}
        <Section title="Engine Room" subtitle="Infrastructure · performance" icon={Cpu} accent="green" status={wsStatus === "connected" ? "live" : "idle"}>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 lg:grid-cols-7 gap-2 items-center">
            <Gauge value={data?.system.cpu_usage ?? 0} label="CPU" color="green" warn={60} crit={85} size={isCpt ? 40 : isExp ? 60 : 48} loading={loading} />
            <Gauge value={data?.system.memory_usage ?? 0} label="Memory" color="blue" warn={65} crit={85} size={isCpt ? 40 : isExp ? 60 : 48} loading={loading} />
            <div className="space-y-2 col-span-2">
              <Meter label="API Latency" value={data?.system.api_latency ?? 0} max={1000} color="green" warn={300} crit={800} loading={loading} />
              <Meter label="Error Rate" value={data?.system.error_rate ?? 0} max={5} color="red" warn={2} crit={4} loading={loading} />
            </div>
            <div className="theme-elevated rounded-lg p-2 text-center col-span-2" style={{ border: `1px solid ${HUD.green}15` }}>
              <p className="text-[7px] font-bold font-mono uppercase tracking-wider text-text-faint">Active Sessions</p>
              <p className="text-lg font-bold text-text tabular-nums">{data?.system.active_sessions ?? 0}</p>
            </div>
            <div className="theme-elevated rounded-lg p-2 text-center" style={{ border: `1px solid ${HUD.green}15` }}>
              <p className="text-[7px] font-bold font-mono uppercase tracking-wider text-text-faint">Redis Hit</p>
              <p className="text-sm font-bold font-mono" style={{ color: HUD.green }}>
                {((data?.system.redis_hit_ratio ?? 0) * 100) > 0 ? `${((data?.system.redis_hit_ratio ?? 0) * 100).toFixed(0)}%` : "—"}
              </p>
            </div>
            <div className="theme-elevated rounded-lg p-2 text-center" style={{ border: `1px solid ${HUD.blue}15` }}>
              <p className="text-[7px] font-bold font-mono uppercase tracking-wider text-text-faint">DB Conns</p>
              <p className="text-sm font-bold text-text tabular-nums">{data?.system.db_connections ?? 0}</p>
            </div>
          </div>
        </Section>

        {/* ── ROW 6: MARKET INTEL + ALERTS + FRAUD ── */}
        <Section title="Market Intel" subtitle="News · alerts · risk" icon={Globe2} accent="cyan">
          <div className={gap}>
            <Ticker items={(data?.headlines ?? []).map((h) => ({ title: h.title, category: h.category, sentiment: h.sentiment }))} loading={loading} />

            <div className="grid grid-cols-1 md:grid-cols-3 gap-1.5">
              {/* Alerts */}
              <div className="md:col-span-2">
                <div className="flex items-center justify-between mb-1.5">
                  <h4 className="text-[8px] font-bold font-mono uppercase tracking-wider text-text-faint">
                    Active Alerts <span className="text-text-muted">({(data?.alerts ?? []).length})</span>
                  </h4>
                  <div className="flex items-center gap-1.5">
                    <div className="relative">
                      <Search className="pointer-events-none absolute left-2 top-1/2 h-2.5 w-2.5 -translate-y-1/2 text-text-faint" />
                      <input value={alertFilter} onChange={(e) => setAlertFilter(e.target.value)}
                        placeholder="Filter…" className="theme-input w-24 rounded-lg py-1 pl-6 pr-2 text-[8px]" />
                    </div>
                    <button onClick={() => router.push("/admin/command-center/alerts")} className="text-[8px] font-bold font-mono text-brand hover:underline">All →</button>
                  </div>
                </div>
                <div className="max-h-24 overflow-y-auto space-y-1 pr-0.5">
                  {loading ? Array.from({ length: 2 }).map((_, i) => <div key={i} className="h-8 w-full rounded bg-surface-2/60 animate-pulse" />)
                  : filteredAlerts.length === 0 ? <p className="py-3 text-center text-[8px] text-text-faint font-mono">No alerts</p>
                  : filteredAlerts.slice(0, 4).map((a) => <AlertRow key={a.id} alert={a} onOpen={() => router.push("/admin/command-center/alerts")} />)}
                </div>
              </div>

              {/* Fraud */}
              <div>
                <h4 className="text-[8px] font-bold font-mono uppercase tracking-wider text-text-faint mb-1.5">
                  Fraud <span className="text-text-muted">({(data?.fraud_alerts ?? []).length})</span>
                </h4>
                <div className="max-h-24 overflow-y-auto space-y-1 pr-0.5">
                  {loading ? Array.from({ length: 2 }).map((_, i) => <div key={i} className="h-8 w-full rounded bg-surface-2/60 animate-pulse" />)
                  : (data?.fraud_alerts ?? []).length === 0 ? <p className="py-3 text-center text-[8px] text-text-faint font-mono">No fraud</p>
                  : (data?.fraud_alerts ?? []).slice(0, 3).map((fa) => <FraudRow key={fa.id} fa={fa} onOpen={() => router.push("/admin/command-center/fraud")} />)}
                </div>
                <button onClick={() => router.push("/admin/command-center/fraud")} className="mt-1 text-[8px] font-bold font-mono text-danger hover:underline">Dashboard →</button>
              </div>
            </div>
          </div>
        </Section>

        {/* ── FOOTER ── */}
        <div className="flex items-center justify-between">
          <div className="flex gap-2">
            <button onClick={() => router.push("/admin/command-center/headlines/create")}
              className="theme-elevated inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[8px] font-semibold hover:text-text transition-colors">
              + Publish News
            </button>
            <button onClick={() => router.push("/admin/dashboard")}
              className="theme-btn-primary inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[8px] font-semibold">
              Dashboard →
            </button>
          </div>
          <p className="font-mono text-[7px] uppercase tracking-[0.25em] text-text-faint">
            {lastUpdated ? `SYNC ${lastUpdated}` : "INITIALISING…"}
          </p>
        </div>
      </PanelContent>
    </AdminLayout>
  );
}
