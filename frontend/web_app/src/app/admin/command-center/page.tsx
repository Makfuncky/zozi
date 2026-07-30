"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Activity, AlertCircle, Banknote, Building2, Cpu,
  DollarSign, Globe2, Inbox, LayoutGrid, Lock, Package, RefreshCw, Rows3,
  Search, ShoppingCart, Store, TrendingUp,
  UserCheck, Users, Wallet, Zap, Database, Radio,
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

/* ============================ Types ============================ */
type DensityMode = "compact" | "balanced" | "expanded";
type PayloadState = "idle" | "ok" | "empty" | "malformed" | "error";

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
const EXPECTED_KEYS = ["heartbeat","treasury","operations","ecosystem","growth","workforce","system"] as const;

function loadDensity(): DensityMode {
  if (typeof window === "undefined") return "balanced";
  try { const v = localStorage.getItem(DENSITY_KEY) as DensityMode | null; if (v === "compact" || v === "balanced" || v === "expanded") return v; } catch { }
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

function useRelativeTime(ms: number | null): string {
  const [, force] = useState(0);
  useEffect(() => {
    const id = setInterval(() => force((x) => x + 1), 1000);
    return () => clearInterval(id);
  }, []);
  if (!ms) return "—";
  const s = Math.max(0, Math.round((Date.now() - ms) / 1000));
  if (s < 5) return "just now";
  if (s < 60) return `${s}s ago`;
  return `${Math.round(s / 60)}m ago`;
}

function compactMoney(n: number): string {
  if (Math.abs(n) >= 1e6) return `${(n / 1e6).toFixed(2)}M`;
  if (Math.abs(n) >= 1e3) return `${(n / 1e3).toFixed(1)}K`;
  return Math.round(n).toLocaleString();
}

/** Classify the payload so we never fake zeros for a broken contract. */
function assessPayload(json: any): { state: PayloadState; missing: string[]; receivedKeys: string[] } {
  const receivedKeys = json && typeof json === "object" ? Object.keys(json) : [];
  const missing = EXPECTED_KEYS.filter((k) => !json || typeof json[k] !== "object");
  if (missing.length) return { state: "malformed", missing, receivedKeys };
  const hb = json.heartbeat ?? {};
  const growth = json.growth ?? {};
  const anyActivity =
    [hb.today_orders, hb.today_revenue, hb.today_gmv].some((n: number) => Number(n) > 0) ||
    (Array.isArray(growth.revenue_trend) && growth.revenue_trend.length > 0) ||
    (Array.isArray(growth.top_products) && growth.top_products.length > 0);
  return { state: anyActivity ? "ok" : "empty", missing: [], receivedKeys };
}

/* ============================ Small presentational helpers ============================ */
function Spark({ values, color }: { values: number[]; color: string }) {
  if (values.length < 2) return null;
  const max = Math.max(...values, 1), min = Math.min(...values, 0), w = 72, h = 22;
  const pts = values.map((v, i) => `${(i / (values.length - 1)) * w},${h - ((v - min) / (max - min || 1)) * h}`).join(" ");
  return (
    <svg width={w} height={h} className="overflow-visible" aria-hidden>
      <polyline points={pts} fill="none" stroke={color} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" opacity={0.9} />
    </svg>
  );
}

function HeroKpi({ label, value, format, accent, spark, loading }: { label: string; value: number; format?: (n: number) => string; accent: HudColor; spark?: number[]; loading?: boolean }) {
  const color = (accent in HUD ? HUD[accent as keyof typeof HUD] : accent) ?? accent;
  return (
    <div className="theme-elevated relative flex-1 overflow-hidden rounded-2xl p-3.5" style={{ border: `1px solid color-mix(in srgb, ${color} 22%, transparent)` }}>
      <span className="absolute inset-y-0 left-0 w-[3px]" style={{ background: color, boxShadow: `0 0 12px ${color}55` }} />
      <p className="text-[9px] font-bold uppercase tracking-[0.18em] text-text-faint">{label}</p>
      <div className="mt-1 flex items-end justify-between gap-2">
        {loading ? <div className="h-7 w-20 rounded bg-surface-2/60 animate-pulse" />
          : <p className="text-2xl font-bold tabular-nums leading-none text-text">{format ? format(value) : value.toLocaleString()}</p>}
        {spark && spark.length > 1 && <Spark values={spark} color={color} />}
      </div>
    </div>
  );
}

function EmptyBlock({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-1 py-6 text-center">
      <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-surface-2/50"><Inbox className="h-4 w-4 text-text-faint" /></div>
      <p className="text-[10px] font-semibold text-text-muted">{title}</p>
      {hint && <p className="max-w-[180px] text-[9px] leading-snug text-text-faint">{hint}</p>}
    </div>
  );
}

/* ============================ MAIN PAGE ============================ */
export default function AdminCommandCenterPage() {
  const router = useRouter();
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();
  const { selectedCountry, loading: countryLoading } = useAdminCountry();
  const clock = useClock();

  const role = user?.role ?? null;
  const canView = hasAdminPermission(role, "analytics.view");
  const countryCode = selectedCountry?.code ?? null;

  const [data, setData] = useState<ComprehensiveData | null>(null);
  const [loading, setLoading] = useState(true);
  const [payloadState, setPayloadState] = useState<PayloadState>("idle");
  const [schemaInfo, setSchemaInfo] = useState<{ missing: string[]; receivedKeys: string[] }>({ missing: [], receivedKeys: [] });
  const [lastUpdatedMs, setLastUpdatedMs] = useState<number | null>(null);
  const [wsStatus, setWsStatus] = useState<"connecting" | "connected" | "disconnected">("disconnected");
  const [density, setDensity] = useState<DensityMode>("balanced");
  const [alertFilter, setAlertFilter] = useState("");

  useEffect(() => { setDensity(loadDensity()); }, []);
  const updateDensity = (next: DensityMode) => { setDensity(next); try { localStorage.setItem(DENSITY_KEY, next); } catch { } };
  const relativeSync = useRelativeTime(lastUpdatedMs);

  /* ---- Data layer: sends country, validates shape, logs raw payload ---- */
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const qs = countryCode ? `?country_code=${encodeURIComponent(countryCode)}` : "";
      const res = await apiFetch(`/admin/command-center/comprehensive${qs}`, { disableCache: true });
      if (!res.ok) { setPayloadState("error"); return; }
      const json = await res.json();
      if (process.env.NODE_ENV !== "production") console.info("[command-center] payload", json);
      const { state, missing, receivedKeys } = assessPayload(json);
      setSchemaInfo({ missing, receivedKeys });
      setPayloadState(state);
      if (state !== "malformed") {
        setData(json as ComprehensiveData);
        setLastUpdatedMs(Date.now());
      }
    } catch (e) {
      if (process.env.NODE_ENV !== "production") console.error("[command-center] fetch failed", e);
      setPayloadState("error");
    } finally { setLoading(false); }
  }, [countryCode]);

  useEffect(() => {
    if (authLoading || countryLoading) return;
    if (!isLoggedIn) { router.push("/admin/login"); return; }
    if (!isAdminStaffRole(role) || !canView) { router.push("/admin/dashboard"); return; }
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [authLoading, countryLoading, isLoggedIn, role, canView, router, fetchData]);

  /* ---- WebSocket: live heartbeat patch ---- */
  useEffect(() => {
    if (!isLoggedIn) return;
    let ws: WebSocket | null = null; let rt: ReturnType<typeof setTimeout>; let attempts = 0;
    const connect = () => {
      if (attempts >= 3) { setWsStatus("disconnected"); return; }
      attempts++; setWsStatus("connecting");
      const p = window.location.protocol === "https:" ? "wss:" : "ws:";
      ws = new WebSocket(`${p}//${window.location.host}/admin/command-center/ws`);
      ws.onopen = () => setWsStatus("connected");
      ws.onclose = () => { setWsStatus("disconnected"); if (attempts < 3) rt = setTimeout(connect, 5000); };
      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);
          if (msg.type === "heartbeat" && msg.data) {
            setData((prev) => (prev ? { ...prev, heartbeat: msg.data, timestamp: msg.timestamp } : prev));
            setLastUpdatedMs(Date.now());
          }
        } catch { }
      };
    };
    connect();
    return () => { ws?.close(); clearTimeout(rt); };
  }, [isLoggedIn]);

  /* ---- Derived ---- */
  const revenueSpark = useMemo(() => data?.growth.revenue_trend.map((d) => d.revenue) ?? [], [data]);
  const filteredAlerts = useMemo(() => {
    const all = data?.alerts ?? [];
    if (!alertFilter.trim()) return all;
    const q = alertFilter.toLowerCase();
    return all.filter((a) => a.title.toLowerCase().includes(q) || a.message.toLowerCase().includes(q));
  }, [data, alertFilter]);
  const revenueTrend = data?.growth.revenue_trend ?? [];
  const pieSegments = (data?.growth.category_trends ?? []).slice(0, 6).map((c, i) => ({
    label: c.category, value: c.revenue,
    color: [HUD.green, HUD.blue, HUD.amber, HUD.red, HUD.purple, HUD.cyan][i % 6] as HudColor,
  }));
  const countryBars = (data?.growth.country_sales ?? []).slice(0, 7).map((c) => ({
    label: c.country, value: c.revenue, color: HUD.cyan as HudColor,
  }));

  const wsColor: keyof typeof HUD = wsStatus === "connected" || data ? "green" : wsStatus === "connecting" ? "amber" : "slate";
  const isCpt = density === "compact"; const isExp = density === "expanded";
  const gap = isCpt ? "gap-1.5" : isExp ? "gap-3" : "gap-2.5";
  const pad = isCpt ? "p-2" : isExp ? "p-4" : "p-3";

  return (
    <AdminLayout title="Command Center" headerMode="compact">
      <HudBackground />
      <PanelContent className={cn("relative", gap, "pb-6")}>

        {/* ── State banners ── */}
        {payloadState === "error" && !loading && (
          <div className="theme-elevated flex items-center gap-3 rounded-xl border border-danger/25 p-3">
            <AlertCircle className="h-4 w-4 shrink-0 text-danger" />
            <p className="flex-1 text-[11px] font-semibold text-text">Telemetry link lost — the backend did not return a usable response.</p>
            <button onClick={fetchData} className="theme-btn-primary rounded-lg px-3 py-1.5 text-[11px] font-semibold">Reconnect</button>
          </div>
        )}
        {payloadState === "malformed" && !loading && (
          <div className="theme-elevated rounded-xl border border-warning/30 p-3">
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4 shrink-0 text-warning" />
              <p className="flex-1 text-[11px] font-semibold text-text">Connected, but the telemetry payload doesn&apos;t match the expected schema.</p>
            </div>
            <p className="mt-1.5 text-[10px] leading-relaxed text-text-muted">
              Expected sections: <span className="font-mono">{EXPECTED_KEYS.join(", ")}</span>.<br />
              Missing: <span className="font-mono text-warning">{schemaInfo.missing.join(", ") || "—"}</span>.<br />
              Received top-level keys: <span className="font-mono">{schemaInfo.receivedKeys.join(", ") || "(none)"}</span>.
              {schemaInfo.missing.length > 0 && <> Fix the response of <span className="font-mono">/admin/command-center/comprehensive</span> to match the contract.</>}
            </p>
          </div>
        )}
        {payloadState === "empty" && !loading && (
          <div className="theme-elevated flex items-center gap-2 rounded-xl border border-border p-2.5">
            <Radio className="h-3.5 w-3.5 shrink-0 text-text-faint" />
            <p className="text-[10px] font-medium text-text-muted">Telemetry healthy — no commercial activity recorded for {countryCode ?? "this scope"} in the current period.</p>
          </div>
        )}

        {/* ── Header band ── */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl theme-elevated" style={{ border: `1px solid ${HUD.cyan}30`, boxShadow: `0 0 20px ${HUD.cyan}18` }}>
              <Zap className="h-5 w-5" style={{ color: HUD.cyan, filter: `drop-shadow(0 0 5px ${HUD.cyan})` }} />
            </div>
            <div>
              <h1 className="text-base font-bold tracking-tight text-text">Command Center</h1>
              <p className="font-mono text-[9px] uppercase tracking-[0.22em] text-text-faint">Mission control · {clock}</p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {countryCode && !countryLoading && (
              <span className="theme-elevated inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[10px] font-semibold text-text-muted">
                <Globe2 className="h-3 w-3" style={{ color: HUD.cyan }} />{countryCode}
              </span>
            )}
            <span className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[10px] font-semibold backdrop-blur-sm"
              style={{ color: HUD[wsColor], background: `color-mix(in srgb, ${HUD[wsColor]} 8%, var(--color-glass-mid))`, border: `1px solid color-mix(in srgb, ${HUD[wsColor]} 25%, transparent)` }}>
              <span className="relative flex h-2 w-2">
                {wsStatus === "connected" && <span className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-70" style={{ background: HUD[wsColor] }} />}
                <span className="relative inline-flex h-2 w-2 rounded-full" style={{ background: HUD[wsColor], boxShadow: `0 0 6px ${HUD[wsColor]}` }} />
              </span>
              {wsStatus === "connected" || data ? "LIVE" : wsStatus === "connecting" ? "SYNC" : "OFF"}
            </span>
            <div className="theme-elevated inline-flex overflow-hidden rounded-lg">
              {([{ key: "compact" as DensityMode, icon: Rows3 }, { key: "balanced" as DensityMode, icon: LayoutGrid }, { key: "expanded" as DensityMode, icon: Activity }]).map((opt) => (
                <button key={opt.key} onClick={() => updateDensity(opt.key)} aria-pressed={density === opt.key}
                  className={cn("px-2 py-1.5 transition-all", density === opt.key ? "text-text" : "text-text-faint hover:text-text-muted")}
                  style={density === opt.key ? { background: `color-mix(in srgb, var(--color-surface-2) 60%, transparent)` } : {}}>
                  <opt.icon className="h-3 w-3" />
                </button>
              ))}
            </div>
            <button onClick={fetchData} disabled={loading} className="theme-elevated inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[10px] font-semibold text-text-muted hover:text-text disabled:opacity-50">
              <RefreshCw className={cn("h-3 w-3", loading && "animate-spin")} />
            </button>
          </div>
        </div>

        {/* ── Hero KPI strip ── */}
        <div className="flex flex-col gap-2.5 sm:flex-row">
          <HeroKpi label="Revenue today" value={data?.heartbeat.today_revenue ?? 0} format={compactMoney} accent="green" spark={revenueSpark} loading={loading} />
          <HeroKpi label="Orders today" value={data?.heartbeat.today_orders ?? 0} accent="cyan" loading={loading} />
          <HeroKpi label="Available cash" value={data?.treasury.available_cash ?? 0} format={compactMoney} accent="amber" loading={loading} />
          <HeroKpi label="Active sessions" value={data?.system.active_sessions ?? 0} accent="blue" loading={loading} />
        </div>

        {/* ── ROW 1: OPERATIONAL HEARTBEAT ── */}
        <Section title="Operational Overview" subtitle="Today's commercial pulse" icon={ShoppingCart} accent="cyan" status={wsStatus === "connected" ? "live" : "idle"}>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
            <Stat label="Orders" value={data?.heartbeat.today_orders ?? 0} icon={ShoppingCart} accent="cyan" loading={loading} />
            <Stat label="Revenue" value={data?.heartbeat.today_revenue ?? 0} format={compactMoney} icon={DollarSign} accent="green" loading={loading} sparkline={revenueSpark} />
            <Stat label="GMV" value={data?.heartbeat.today_gmv ?? 0} format={compactMoney} icon={TrendingUp} accent="blue" loading={loading} />
            <Stat label="Buying" value={data?.heartbeat.active_customers_buying ?? 0} icon={UserCheck} accent="green" trend={(data?.heartbeat.active_customers_buying ?? 0) > 0 ? "up" : "neutral"} loading={loading} />
            <Stat label="Employees" value={data?.heartbeat.employees_working ?? 0} icon={Building2} accent="purple" loading={loading} />
          </div>
        </Section>

        {/* ── ROW 2: CHARTS ── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
          <Section title="Revenue Trend" subtitle="30-day rolling" icon={TrendingUp} accent="green">
            <div className={cn(pad, "pt-0")}>
              {loading ? <div className="h-20 w-full rounded bg-surface-2/50 animate-pulse" />
                : revenueTrend.length ? <AreaChart data={revenueTrend.map((d) => ({ label: d.date, value: d.revenue }))} color="green" height={isCpt ? 64 : isExp ? 104 : 84} loading={loading} />
                : <EmptyBlock title="No revenue history" hint="Activity will plot here once orders are recorded." />}
            </div>
          </Section>
          <Section title="Category Split" subtitle="Revenue by category" icon={Package} accent="blue">
            <div className={cn(pad, "pt-0")}>
              {loading ? <div className="h-20 w-full rounded bg-surface-2/50 animate-pulse" />
                : pieSegments.length ? <DonutChart segments={pieSegments} centerLabel="CATS" height={isCpt ? 64 : isExp ? 104 : 84} loading={loading} />
                : <EmptyBlock title="No category data" />}
            </div>
          </Section>
          <Section title="Country Sales" subtitle="Revenue by country" icon={Globe2} accent="cyan">
            <div className={cn(pad, "pt-0")}>
              {loading ? <div className="h-20 w-full rounded bg-surface-2/50 animate-pulse" />
                : countryBars.length ? <Bars data={countryBars} height={isCpt ? 64 : isExp ? 104 : 84} loading={loading} valueFormat={compactMoney} />
                : <EmptyBlock title="No country data" />}
            </div>
          </Section>
        </div>

        {/* ── ROW 3: TREASURY ── */}
        <Section title="Treasury" subtitle="Live ledger" icon={Wallet} accent="amber"
          status={(data?.treasury.active_disputes ?? 0) > 0 ? "warn" : "live"}
          count={data?.treasury.active_disputes ?? 0}>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2">
            <Stat label="Cash" value={data?.treasury.available_cash ?? 0} format={compactMoney} icon={Banknote} accent="green" loading={loading} />
            <Stat label="Locked" value={data?.treasury.locked_cash ?? 0} format={compactMoney} icon={Lock} accent="amber" loading={loading} />
            <Stat label="VAT" value={data?.treasury.vat_liability ?? 0} format={compactMoney} icon={DollarSign} accent="red" loading={loading} />
            <Stat label="Supplier Pay." value={data?.treasury.supplier_payables ?? 0} format={compactMoney} icon={Store} accent="amber" loading={loading} />
            <Stat label="Pending Payouts" value={data?.treasury.pending_payouts ?? 0} format={compactMoney} icon={Users} accent="amber" loading={loading} />
          </div>
        </Section>

        {/* ── ROW 4: GROWTH / SEARCHES / DEPARTMENTS ── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
          <Section title="Top Products" subtitle="Revenue leaders" icon={Package} accent="green">
            <div className="max-h-32 overflow-y-auto space-y-1 pr-0.5">
              {loading ? Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-5 w-full rounded bg-surface-2/60 animate-pulse" />)
              : (data?.growth.top_products ?? []).length ? (data!.growth.top_products).slice(0, 6).map((p, i) => (
                <RankRow key={p.product_id} rank={i + 1} label={p.product_name} primary={compactMoney(p.revenue)} secondary={`${p.units_sold} u`} accent="green" />))
              : <EmptyBlock title="No products sold yet" />}
            </div>
          </Section>
          <Section title="Top Searches" subtitle="Market demand signals" icon={Search} accent="cyan">
            <div className="max-h-32 overflow-y-auto space-y-1 pr-0.5">
              {loading ? Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-5 w-full rounded bg-surface-2/60 animate-pulse" />)
              : (data?.growth.top_searches ?? []).length ? data!.growth.top_searches.map((s, i) => (
                <RankRow key={s.query} rank={i + 1} label={s.query} primary={`${s.count}x`} secondary={s.zero_results > 0 ? `${s.zero_results} zero` : undefined} accent={s.zero_results > 0 ? "red" : "cyan"} />))
              : <EmptyBlock title="No search signals" />}
            </div>
          </Section>
          <Section title="Departments" subtitle="Headcount distribution" icon={Users} accent="purple">
            <div className="space-y-2 py-1">
              {loading ? Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-4 w-full rounded bg-surface-2/60 animate-pulse" />)
              : (data?.workforce.employees_by_department ?? []).length ? (data!.workforce.employees_by_department).slice(0, 6).map((d) => {
                const mx = Math.max(...data!.workforce.employees_by_department.map((x) => x.count), 1);
                return (
                  <div key={d.department} className="flex items-center gap-2">
                    <span className="w-20 shrink-0 truncate text-[10px] font-medium text-text">{d.department}</span>
                    <div className="h-2 flex-1 rounded-full bg-surface-2/50 overflow-hidden">
                      <div className="h-full rounded-full transition-all duration-500"
                        style={{ width: `${(d.count / mx) * 100}%`, background: `linear-gradient(90deg, ${HUD.purple}70, ${HUD.purple})`, boxShadow: `0 0 6px ${HUD.purple}30` }} />
                    </div>
                    <span className="w-6 shrink-0 text-right text-[10px] font-bold font-mono text-text tabular-nums">{d.count}</span>
                  </div>
                );
              }) : <EmptyBlock title="No workforce data" />}
            </div>
          </Section>
        </div>

        {/* ── ROW 5: ENGINE ROOM ── */}
        <Section title="Engine Room" subtitle="Infrastructure · performance" icon={Cpu} accent="green" status={wsStatus === "connected" ? "live" : "idle"}>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 lg:grid-cols-7 gap-2.5 items-center">
            <Gauge value={data?.system.cpu_usage ?? 0} label="CPU" color="green" warn={60} crit={85} size={isCpt ? 44 : isExp ? 64 : 52} loading={loading} />
            <Gauge value={data?.system.memory_usage ?? 0} label="Memory" color="blue" warn={65} crit={85} size={isCpt ? 44 : isExp ? 64 : 52} loading={loading} />
            <div className="space-y-2.5 col-span-2">
              <Meter label="API Latency" value={data?.system.api_latency ?? 0} max={1000} color="green" warn={300} crit={800} loading={loading} />
              <Meter label="Error Rate" value={data?.system.error_rate ?? 0} max={5} color="red" warn={2} crit={4} loading={loading} />
            </div>
            <div className="theme-elevated rounded-xl p-2.5 text-center col-span-2" style={{ border: `1px solid ${HUD.green}18` }}>
              <p className="text-[8px] font-bold font-mono uppercase tracking-wider text-text-faint">Active Sessions</p>
              <p className="text-xl font-bold text-text tabular-nums">{data?.system.active_sessions ?? 0}</p>
            </div>
            <div className="theme-elevated rounded-xl p-2.5 text-center" style={{ border: `1px solid ${HUD.green}18` }}>
              <p className="text-[8px] font-bold font-mono uppercase tracking-wider text-text-faint">Redis Hit</p>
              <p className="text-base font-bold font-mono" style={{ color: HUD.green }}>
                {((data?.system.redis_hit_ratio ?? 0) * 100) > 0 ? `${((data?.system.redis_hit_ratio ?? 0) * 100).toFixed(0)}%` : "—"}
              </p>
            </div>
            <div className="theme-elevated rounded-xl p-2.5 text-center" style={{ border: `1px solid ${HUD.blue}18` }}>
              <p className="text-[8px] font-bold font-mono uppercase tracking-wider text-text-faint">DB Conns</p>
              <p className="text-base font-bold text-text tabular-nums">{data?.system.db_connections ?? 0}</p>
            </div>
          </div>
        </Section>

        {/* ── ROW 6: MARKET INTEL ── */}
        <Section title="Market Intel" subtitle="News · alerts · risk" icon={Globe2} accent="cyan">
          <div className={gap}>
            <Ticker items={(data?.headlines ?? []).map((h) => ({ title: h.title, category: h.category, sentiment: h.sentiment }))} loading={loading} />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
              <div className="md:col-span-2">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-[9px] font-bold font-mono uppercase tracking-wider text-text-faint">Active Alerts <span className="text-text-muted">({(data?.alerts ?? []).length})</span></h4>
                  <div className="flex items-center gap-2">
                    <div className="relative">
                      <Search className="pointer-events-none absolute left-2 top-1/2 h-3 w-3 -translate-y-1/2 text-text-faint" />
                      <input value={alertFilter} onChange={(e) => setAlertFilter(e.target.value)} placeholder="Filter…" className="theme-input w-28 rounded-lg py-1.5 pl-6 pr-2 text-[10px]" />
                    </div>
                    <button onClick={() => router.push("/admin/command-center/alerts")} className="text-[10px] font-bold font-mono text-primary hover:underline">All →</button>
                  </div>
                </div>
                <div className="max-h-28 overflow-y-auto space-y-1 pr-0.5">
                  {loading ? Array.from({ length: 2 }).map((_, i) => <div key={i} className="h-9 w-full rounded bg-surface-2/60 animate-pulse" />)
                  : filteredAlerts.length === 0 ? <EmptyBlock title="No active alerts" hint="System is nominal." />
                  : filteredAlerts.slice(0, 4).map((a) => <AlertRow key={a.id} alert={a} onOpen={() => router.push("/admin/command-center/alerts")} />)}
                </div>
              </div>
              <div>
                <h4 className="text-[9px] font-bold font-mono uppercase tracking-wider text-text-faint mb-2">Fraud <span className="text-text-muted">({(data?.fraud_alerts ?? []).length})</span></h4>
                <div className="max-h-28 overflow-y-auto space-y-1 pr-0.5">
                  {loading ? Array.from({ length: 2 }).map((_, i) => <div key={i} className="h-9 w-full rounded bg-surface-2/60 animate-pulse" />)
                  : (data?.fraud_alerts ?? []).length === 0 ? <EmptyBlock title="No fraud signals" />
                  : (data!.fraud_alerts).slice(0, 3).map((fa) => <FraudRow key={fa.id} fa={fa} onOpen={() => router.push("/admin/command-center/fraud")} />)}
                </div>
                <button onClick={() => router.push("/admin/command-center/fraud")} className="mt-1.5 text-[10px] font-bold font-mono text-danger hover:underline">Dashboard →</button>
              </div>
            </div>
          </div>
        </Section>

        {/* ── FOOTER ── */}
        <div className="flex items-center justify-between">
          <div className="flex gap-2">
            <button onClick={() => router.push("/admin/command-center/headlines/create")}
              className="theme-elevated inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-[10px] font-semibold hover:text-text transition-colors">+ Publish News</button>
            <button onClick={() => router.push("/admin/dashboard")}
              className="theme-btn-primary inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-[10px] font-semibold">Dashboard →</button>
          </div>
          <p className="font-mono text-[9px] uppercase tracking-[0.22em] text-text-faint">
            {lastUpdatedMs ? `SYNC ${relativeSync}` : "INITIALISING…"}
          </p>
        </div>
      </PanelContent>
    </AdminLayout>
  );
}
