"use client";

import { Button } from "@/components/ui/Button";

import { useEffect, useState, useCallback, useMemo, useRef } from "react";
import {
  DollarSign, RefreshCw, Search, CheckCircle2, XCircle, Clock, ArrowDownUp, Shield,
  Plus, Pencil, Plug, PlugZap, Settings2, Globe2, Calculator, Trash2, Save,
} from "@/lib/icons";
import { useAuth } from "@/lib/useAuth";
import { isAdminStaffRole } from "@shared/adminPermissions";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelHero, PanelLoadingState, PanelTabs } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useAdminCountry } from "@/lib/useAdminCountry";
import { dc, useDensity } from "@/lib/densityContext";
import { useToastStore } from "@/lib/toastStore";

interface PaymentTx {
  id: number;
  order_id: number;
  amount: number;
  payment_method: string;
  provider?: string;
  status: string;
  created_at: string;
}

interface GatewayConnection {
  id: number | null;
  provider_code: string;
  provider_kind: "stripe" | "tap" | "custom";
  display_name: string;
  adapter_supported: boolean;
  is_enabled: boolean;
  supports_customer_checkout: boolean;
  supports_payouts: boolean;
  mode: "test" | "live";
  country_code: string;
  source: string;
  public_key: string | null;
  merchant_id: string | null;
  api_base_url: string | null;
  webhook_url: string | null;
  test_url: string | null;
  supported_currencies: string[];
  extra_config: Record<string, any>;
  notes: string | null;
  fee_percent: number;
  fixed_fee_amount: number;
  payout_fee_percent: number;
  payout_fixed_fee_amount: number;
  pass_fee_to_customer: boolean;
  settlement_cycle: "daily" | "weekly" | "monthly";
  secret_key_configured: boolean;
  webhook_secret_configured: boolean;
  test_status: "untested" | "passed" | "failed";
  test_message: string | null;
  last_tested_at: string | null;
}

interface RuntimeConfig {
  online_provider: "stripe" | "tap" | "both";
  stripe_configured: boolean;
  tap_configured: boolean;
  stripe_enabled: boolean;
  tap_enabled: boolean;
  enabled_processors: string[];
  can_accept_online_payments: boolean;
}

type Section = "transactions" | "gateways" | "runtime" | "finance" | "routing";

const STATUS_CHIP: Record<string, string> = {
  completed: "theme-chip-success",
  pending: "theme-chip-warning",
  failed: "theme-chip-danger",
  refunded: "theme-chip-info",
  cancelled: "theme-chip-muted",
};

const EMPTY_GATEWAY: GatewayConnection = {
  id: null,
  provider_code: "",
  provider_kind: "custom",
  display_name: "",
  adapter_supported: false,
  is_enabled: true,
  supports_customer_checkout: true,
  supports_payouts: false,
  mode: "test",
  country_code: "*",
  source: "database",
  public_key: null,
  merchant_id: null,
  api_base_url: null,
  webhook_url: null,
  test_url: null,
  supported_currencies: [],
  extra_config: {},
  notes: null,
  fee_percent: 0,
  fixed_fee_amount: 0,
  payout_fee_percent: 0,
  payout_fixed_fee_amount: 0,
  pass_fee_to_customer: false,
  settlement_cycle: "weekly",
  secret_key_configured: false,
  webhook_secret_configured: false,
  test_status: "untested",
  test_message: null,
  last_tested_at: null,
};

const GATEWAY_TEMPLATES: { code: string; label: string; json: string }[] = [
  {
    code: "paymob",
    label: "Paymob",
    json: JSON.stringify(
      {
        redirect_url_template:
          "https://ksa.paymob.com/api/acceptance/iframes/IFRAME_ID?payment_token={token}",
        create_url: "https://ksa.paymob.com/api/acceptance/payment_keys",
        create_method: "POST",
        create_auth_header: "Token {secret_key}",
        create_body: { order_id: "order_id", amount_cents: "amount", currency: "currency" },
        order_id_field: "order_id",
        transaction_ref_field: "id",
        status_field: "success",
        success_values: ["true", "paid", "success"],
      },
      null,
      2,
    ),
  },
  {
    code: "paytm",
    label: "Paytm",
    json: JSON.stringify(
      {
        redirect_url_template:
          "https://securegw.paytm.in/order/process?mid=MID&orderId={reference}&txnToken={token}",
        create_url: "https://securegw.paytm.in/order/initiate",
        create_method: "POST",
        create_auth_header: "OAuth {secret_key}",
        create_body: { orderId: "order_id", amount: "amount", customerEmail: "customer_email" },
        order_id_field: "orderId",
        transaction_ref_field: "txnId",
        status_field: "status",
        success_values: ["TXN_SUCCESS", "success"],
      },
      null,
      2,
    ),
  },
  {
    code: "thawani",
    label: "Thawani",
    json: JSON.stringify(
      {
        redirect_url_template: "https://payments.thawani.om/payment?session_id={reference}",
        create_url: "https://api.thawani.com/v1/checkout/session",
        create_method: "POST",
        create_auth_header: "Thawani-API-Key {secret_key}",
        create_body: {
          product_id: "order_id",
          amount: "amount",
          currency: "currency",
          success_url: "{success_url}",
          cancel_url: "{cancel_url}",
          metadata: { order_id: "order_id" },
        },
        redirect_url_field: "checkout_url",
        order_id_field: "product_id",
        transaction_ref_field: "session_id",
        status_field: "status",
        success_values: ["paid", "success"],
        verify_url: "https://api.thawani.com/v1/checkout/session/{reference}",
        verify_status_field: "status",
      },
      null,
      2,
    ),
  },
];

async function jsonOrThrow(res: Response): Promise<any> {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data?.detail || `Request failed (${res.status})`);
  return data;
}

export default function PaymentsPage() {
  const { user, isLoggedIn, isLoading } = useAuth();
  const { density } = useDensity();
  const role = user?.role ?? null;
  const addToast = useToastStore((s) => s.addToast);
  const formatMoney = useCurrencyStore((s) => s.format);
  const { selectedCountry, isGlobalView, assignedCountries } = useAdminCountry();
  const countryCode = isGlobalView || !selectedCountry?.code ? null : selectedCountry.code;

  const [section, setSection] = useState<Section>("gateways");
  const [payments, setPayments] = useState<PaymentTx[]>([]);
  const [gateways, setGateways] = useState<GatewayConnection[]>([]);
  const [runtime, setRuntime] = useState<RuntimeConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const [payRes, gwRes, rtRes] = await Promise.all([
        apiFetch("/payments/"),
        apiFetch("/payments/config/gateways"),
        apiFetch("/payments/config/runtime"),
      ]);
      if (payRes.ok) {
        const data = await payRes.json();
        setPayments(Array.isArray(data) ? data : data.items ?? []);
      }
      if (gwRes.ok) {
        const data = await gwRes.json();
        setGateways(Array.isArray(data) ? data : []);
      }
      if (rtRes.ok) {
        setRuntime(await rtRes.json());
      }
    } catch (err: any) {
      addToast(err?.message || "Failed to load payment data", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    if (isLoading) return;
    if (!isLoggedIn || !isAdminStaffRole(role)) return;
    loadAll();
  }, [isLoading, isLoggedIn, role, loadAll]);

  const bodyText = dc(density, "text-[10px]", "text-xs", "text-sm");

  // ── Transactions tab ───────────────────────────────────────────────
  const filtered = useMemo(() =>
    payments.filter((p) =>
      !search.trim() ||
      [String(p.id), String(p.order_id), p.status, p.payment_method, p.provider || ""]
        .some((v) => v?.toLowerCase().includes(search.toLowerCase()))
    ), [payments, search]);

  const txStats = useMemo(() => ({
    total: payments.length,
    completed: payments.filter((p) => p.status === "completed").length,
    pending: payments.filter((p) => p.status === "pending").length,
    totalValue: payments.reduce((s, p) => s + p.amount, 0),
  }), [payments]);

  const txColumns = [
    { key: "id", label: "#", render: (p: PaymentTx) => <span className={`${bodyText} font-mono tabular-nums text-text-faint`}>#{p.id}</span> },
    { key: "order_id", label: "Order", render: (p: PaymentTx) => <span className={`${bodyText} font-mono tabular-nums text-text-faint`}>#{p.order_id}</span> },
    { key: "amount", label: "Amount", render: (p: PaymentTx) => <span className={`${bodyText} font-semibold tabular-nums text-text`}>{formatMoney(p.amount)}</span> },
    { key: "payment_method", label: "Method", render: (p: PaymentTx) => <span className={`${bodyText} text-text-muted`}>{p.payment_method}</span> },
    { key: "provider", label: "Provider", render: (p: PaymentTx) => <span className={`${bodyText} text-text-faint`}>{p.provider || "—"}</span> },
    { key: "status", label: "Status", render: (p: PaymentTx) => (
      <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-semibold ${STATUS_CHIP[p.status] || "theme-chip-muted"}`}>
        {p.status === "completed" ? <CheckCircle2 className="h-3 w-3" /> : p.status === "failed" ? <XCircle className="h-3 w-3" /> : <Clock className="h-3 w-3" />}
        {p.status}
      </span>
    ) },
    { key: "created_at", label: "Date", render: (p: PaymentTx) => <span className={`${bodyText} tabular-nums text-text-faint`}>{p.created_at?.slice(0, 10)}</span> },
  ];

  if (isLoading || !isLoggedIn || !isAdminStaffRole(role)) {
    return <AdminLayout title="Payments"><PanelLoadingState count={3} /></AdminLayout>;
  }

  return (
    <AdminLayout title="Payments" headerMode="compact">
      <PanelContent className="space-y-4">
        <div className="flex items-center gap-2 text-[11px] text-text-faint bg-surface-2 rounded-lg px-3 py-1.5">
          <Shield className="h-3 w-3" />
          <span>{isGlobalView ? "Global View — All Countries" : `Country: ${selectedCountry?.name || selectedCountry?.code}`}</span>
        </div>

        <div className="theme-card rounded-xl border p-2">
          <PanelTabs
            items={[
              { key: "gateways", label: "Gateway Manager", icon: Plug },
              { key: "runtime", label: "Payment Mode", icon: Settings2 },
              { key: "finance", label: "Fee Quote", icon: Calculator },
              { key: "routing", label: "Country Routing", icon: Globe2 },
              { key: "transactions", label: "Transactions", icon: DollarSign },
            ]}
            value={section}
            onChange={(v) => setSection(v as Section)}
            className="border-0 bg-transparent p-0"
          />
        </div>

      {section === "gateways" && (
        <GatewaysTab
          gateways={gateways}
          loading={loading}
          bodyText={bodyText}
          countryCode={countryCode}
          assignedCountries={assignedCountries}
          onChanged={loadAll}
          addToast={addToast}
        />
      )}

        {section === "runtime" && (
          <RuntimeTab runtime={runtime} bodyText={bodyText} onChanged={loadAll} addToast={addToast} />
        )}

        {section === "finance" && (
          <FinanceTab gateways={gateways} bodyText={bodyText} addToast={addToast} />
        )}

        {section === "routing" && (
          <RoutingTab
            gateways={gateways}
            countryCode={countryCode}
            assignedCountries={assignedCountries}
            bodyText={bodyText}
            addToast={addToast}
          />
        )}

        {section === "transactions" && (
          <>
            <PanelHero
              eyebrow="Finance"
              title="Payment Transactions"
              description={`${countryCode ? `Country: ${countryCode}` : "All countries"} — ${txStats.total} payments`}
              icon={<DollarSign className="h-5 w-5" />}
              actions={
                <button onClick={loadAll} disabled={loading}
                  className="flex items-center gap-2 rounded-xl border border-border bg-surface-2 px-4 py-2 text-xs font-semibold text-text-muted hover:text-text disabled:opacity-50">
                  <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} /> Refresh
                </button>
              }
            />
            <div className="grid gap-3 sm:grid-cols-4">
              <StatCard label="Total" value={txStats.total} />
              <StatCard label="Completed" value={txStats.completed} tone="success" />
              <StatCard label="Pending" value={txStats.pending} tone="warning" />
              <StatCard label="Total Value" value={formatMoney(txStats.totalValue)} />
            </div>
            <div className="theme-card rounded-xl border overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-surface-2 border-b border-border">
                  <tr>{txColumns.map((c) => <th key={c.key} className="text-left p-2 font-semibold text-[11px]">{c.label}</th>)}</tr>
                </thead>
                <tbody>
                  {filtered.map((p) => (
                    <tr key={p.id} className="border-b border-border last:border-0 hover:bg-surface-1/50">
                      {txColumns.map((c) => <td key={c.key} className="p-2">{c.render(p)}</td>)}
                    </tr>
                  ))}
                  {filtered.length === 0 && (
                    <tr><td colSpan={txColumns.length} className="p-8 text-center text-text-muted text-sm">No payments found</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}
      </PanelContent>
    </AdminLayout>
  );
}

function StatCard({ label, value, tone }: { label: string; value: string | number; tone?: "success" | "warning" }) {
  const toneCls = tone === "success" ? "text-success" : tone === "warning" ? "text-warning" : "text-text";
  return (
    <div className="theme-card rounded-xl border p-4">
      <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-text-faint">{label}</p>
      <p className={`mt-1.5 text-2xl font-bold tabular-nums ${toneCls}`}>{value}</p>
    </div>
  );
}

// ── Gateway Manager ───────────────────────────────────────────────────────────

function GatewaysTab({
  gateways, loading, bodyText, countryCode, assignedCountries, onChanged, addToast,
}: {
  gateways: GatewayConnection[];
  loading: boolean;
  bodyText: string;
  countryCode: string | null;
  assignedCountries: { code: string; name: string }[];
  onChanged: () => void;
  addToast: (m: string, t?: "success" | "error" | "info") => void;
}) {
  const [editing, setEditing] = useState<GatewayConnection | null>(null);
  const [testing, setTesting] = useState<string | null>(null);

  const openAdd = () => setEditing({ ...EMPTY_GATEWAY, country_code: countryCode || "*" });

  const save = async (gw: GatewayConnection) => {
    try {
      const res = await apiFetch(`/payments/config/gateways/${gw.provider_code}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(gw),
      });
      await jsonOrThrow(res);
      addToast(`Gateway "${gw.display_name}" saved`, "success");
      setEditing(null);
      onChanged();
    } catch (err: any) {
      addToast(err?.message || "Failed to save gateway", "error");
    }
  };

  const toggleEnabled = async (gw: GatewayConnection) => {
    try {
      const res = await apiFetch(`/payments/config/gateways/${gw.provider_code}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...gw, is_enabled: !gw.is_enabled }),
      });
      await jsonOrThrow(res);
      addToast(`${gw.display_name} ${!gw.is_enabled ? "enabled" : "disabled"}`, "success");
      onChanged();
    } catch (err: any) {
      addToast(err?.message || "Failed to update gateway", "error");
    }
  };

  const test = async (gw: GatewayConnection) => {
    setTesting(gw.provider_code);
    try {
      const res = await apiFetch(`/payments/config/gateways/${gw.provider_code}/test`, { method: "POST" });
      const data = await jsonOrThrow(res);
      addToast(data.message || "Connection test passed", "success");
      onChanged();
    } catch (err: any) {
      addToast(err?.message || "Connection test failed", "error");
    } finally {
      setTesting(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-text">Payment Gateway Connections</h3>
        <Button variant="primary" onClick={openAdd}>
          <Plus className="h-4 w-4" /> Add Custom Gateway
        </Button>
      </div>

      {loading && gateways.length === 0 ? (
        <div className="theme-card rounded-xl border p-8 text-center text-text-muted">Loading gateways…</div>
      ) : gateways.length === 0 ? (
        <div className="theme-card rounded-xl border p-8 text-center text-text-muted">
          <Plug className="h-8 w-8 mx-auto mb-2 opacity-40" />
          <p className="text-sm">No gateway connections configured</p>
        </div>
      ) : (
        <div className="grid gap-3">
          {gateways.map((gw) => (
            <div key={gw.provider_code} className="theme-card rounded-xl border p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <span className={`inline-flex h-9 w-9 items-center justify-center rounded-lg ${gw.is_enabled ? "bg-primary/15 text-primary" : "bg-surface-2 text-text-faint"}`}>
                    <PlugZap className="h-4 w-4" />
                  </span>
                  <div>
                    <p className="text-sm font-bold text-text">{gw.display_name}</p>
                    <p className="text-[11px] text-text-faint">
                      {gw.provider_code} · <span className="uppercase">{gw.provider_kind}</span> · {gw.mode} · <span className="font-semibold text-primary">{gw.country_code || "*"}</span>
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {gw.adapter_supported ? (
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-success/20 text-success">Adapter ready</span>
                  ) : (
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-warning/20 text-warning">Custom / template</span>
                  )}
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                    gw.test_status === "passed" ? "bg-success/20 text-success" : gw.test_status === "failed" ? "bg-danger/20 text-danger" : "bg-surface-2 text-text-faint"
                  }`}>{gw.test_status}</span>
                  <button onClick={() => test(gw)} disabled={testing === gw.provider_code}
                    className="rounded-lg border border-border px-2.5 py-1.5 text-[11px] font-semibold text-text-muted hover:text-text disabled:opacity-50">
                    {testing === gw.provider_code ? "Testing…" : "Test"}
                  </button>
                  <button onClick={() => setEditing({ ...gw })}
                    className="rounded-lg border border-border p-1.5 text-text-muted hover:text-text"><Pencil className="h-3.5 w-3.5" /></button>
                  <button onClick={() => toggleEnabled(gw)}
                    className={`relative h-5 w-9 rounded-full transition-colors ${gw.is_enabled ? "bg-success" : "bg-text-faint/40"}`}>
                    <span className={`absolute top-0.5 h-4 w-4 rounded-full bg-white transition-all ${gw.is_enabled ? "left-4" : "left-0.5"}`} />
                  </button>
                </div>
              </div>
              <div className={`mt-2 flex flex-wrap gap-1.5 ${bodyText} text-text-faint`}>
                <span>Checkout: {gw.supports_customer_checkout ? "✓" : "—"}</span>
                <span>Payouts: {gw.supports_payouts ? "✓" : "—"}</span>
                <span>Fee: {gw.fee_percent}% + {gw.fixed_fee_amount}</span>
                <span>Settlement: {gw.settlement_cycle}</span>
                {gw.supported_currencies?.length > 0 && <span>Currencies: {gw.supported_currencies.join(", ")}</span>}
              </div>
            </div>
          ))}
        </div>
      )}

      {editing && (
        <GatewayEditor
          gw={editing}
          countryCode={countryCode}
          assignedCountries={assignedCountries}
          onClose={() => setEditing(null)}
          onSave={save}
          addToast={addToast}
        />
      )}
    </div>
  );
}

function GatewayEditor({
  gw, countryCode, assignedCountries, onClose, onSave, addToast,
}: {
  gw: GatewayConnection;
  countryCode: string | null;
  assignedCountries: { code: string; name: string }[];
  onClose: () => void;
  onSave: (gw: GatewayConnection) => void;
  addToast: (m: string, t?: "success" | "error" | "info") => void;
}) {
  const [draft, setDraft] = useState<GatewayConnection>(gw);
  const [secretKey, setSecretKey] = useState("");
  const [webhookSecret, setWebhookSecret] = useState("");
  const [extraText, setExtraText] = useState(JSON.stringify(gw.extra_config || {}, null, 2));
  const [extraError, setExtraError] = useState<string | null>(null);
  const set = <K extends keyof GatewayConnection>(k: K, v: GatewayConnection[K]) =>
    setDraft((d) => ({ ...d, [k]: v }));

  const isNew = !draft.id;

  const submit = () => {
    let extra: Record<string, any> = {};
    if (extraText.trim()) {
      try {
        extra = JSON.parse(extraText);
        setExtraError(null);
      } catch {
        setExtraError("extra_config must be valid JSON");
        return;
      }
    }
    const payload: any = { ...draft, extra_config: extra };
    if (secretKey.trim()) payload.secret_key = secretKey.trim();
    if (webhookSecret.trim()) payload.webhook_secret = webhookSecret.trim();
    onSave(payload);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4" onClick={onClose} role="dialog" aria-modal="true">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-border bg-surface-1 p-5" onClick={(e) => e.stopPropagation()}>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-base font-bold text-text">{isNew ? "Add Custom Gateway" : `Edit ${draft.display_name}`}</h3>
          <button onClick={onClose} className="text-text-faint hover:text-text">✕</button>
        </div>

        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Provider Kind">
              <select value={draft.provider_kind} onChange={(e) => set("provider_kind", e.target.value as any)}
                className="theme-input w-full rounded-lg border px-3 py-2 text-xs">
                <option value="custom">custom (universal)</option>
                <option value="stripe">stripe</option>
                <option value="tap">tap</option>
              </select>
            </Field>
            <Field label="Mode">
              <select value={draft.mode} onChange={(e) => set("mode", e.target.value as any)}
                className="theme-input w-full rounded-lg border px-3 py-2 text-xs">
                <option value="test">test</option>
                <option value="live">live</option>
              </select>
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Country Scope">
              <select value={draft.country_code || "*"} onChange={(e) => set("country_code", e.target.value)}
                className="theme-input w-full rounded-lg border px-3 py-2 text-xs">
                <option value="*">All Countries (global)</option>
                {(assignedCountries || []).filter((c) => c.code !== "*").map((c) => (
                  <option key={c.code} value={c.code}>{c.name} ({c.code})</option>
                ))}
              </select>
            </Field>
            <Field label="Provider Code *">
              <input value={draft.provider_code} disabled={!isNew} onChange={(e) => set("provider_code", e.target.value.trim().toLowerCase().replace(/[^a-z0-9_]/g, "_"))}
                className="theme-input w-full rounded-lg border px-3 py-2 text-xs" placeholder="e.g. paymob" />
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label="API Base URL">
              <input value={draft.api_base_url || ""} onChange={(e) => set("api_base_url", e.target.value || null)}
                className="theme-input w-full rounded-lg border px-3 py-2 text-xs" placeholder="https://api.gateway.com" />
            </Field>
            <Field label="Webhook / Callback URL">
              <input value={draft.webhook_url || ""} onChange={(e) => set("webhook_url", e.target.value || null)}
                className="theme-input w-full rounded-lg border px-3 py-2 text-xs" placeholder="https://…/payments/generic/CODE/callback" />
            </Field>
            <Field label="Public Key / Merchant ID">
              <input value={draft.public_key || draft.merchant_id || ""}
                onChange={(e) => { set("public_key", e.target.value || null); set("merchant_id", e.target.value || null); }}
                className="theme-input w-full rounded-lg border px-3 py-2 text-xs" />
            </Field>
            <Field label="Settlement Cycle">
              <select value={draft.settlement_cycle} onChange={(e) => set("settlement_cycle", e.target.value as any)}
                className="theme-input w-full rounded-lg border px-3 py-2 text-xs">
                <option value="daily">daily</option>
                <option value="weekly">weekly</option>
                <option value="monthly">monthly</option>
              </select>
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label={`Secret Key ${draft.secret_key_configured ? "(configured)" : ""}`}>
              <input type="password" value={secretKey} onChange={(e) => setSecretKey(e.target.value)}
                className="theme-input w-full rounded-lg border px-3 py-2 text-xs" placeholder={draft.secret_key_configured ? "•••• leave blank to keep" : "Enter secret key"} />
            </Field>
            <Field label={`Webhook Secret ${draft.webhook_secret_configured ? "(configured)" : ""}`}>
              <input type="password" value={webhookSecret} onChange={(e) => setWebhookSecret(e.target.value)}
                className="theme-input w-full rounded-lg border px-3 py-2 text-xs" placeholder={draft.webhook_secret_configured ? "•••• leave blank to keep" : "Enter webhook secret"} />
            </Field>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <Field label="Fee %">
              <input type="number" step="0.01" value={draft.fee_percent} onChange={(e) => set("fee_percent", Number(e.target.value))}
                className="theme-input w-full rounded-lg border px-3 py-2 text-xs" />
            </Field>
            <Field label="Fixed Fee">
              <input type="number" step="0.01" value={draft.fixed_fee_amount} onChange={(e) => set("fixed_fee_amount", Number(e.target.value))}
                className="theme-input w-full rounded-lg border px-3 py-2 text-xs" />
            </Field>
            <Field label="Supported Currencies">
              <input value={(draft.supported_currencies || []).join(", ")} onChange={(e) => set("supported_currencies", e.target.value.split(",").map((s) => s.trim().toUpperCase()).filter(Boolean))}
                className="theme-input w-full rounded-lg border px-3 py-2 text-xs" placeholder="AED, OMR, USD" />
            </Field>
          </div>

          <div className="flex flex-wrap gap-4">
            <label className="flex items-center gap-2 text-xs text-text-muted">
              <input type="checkbox" checked={draft.supports_customer_checkout} onChange={(e) => set("supports_customer_checkout", e.target.checked)} />
              Supports checkout
            </label>
            <label className="flex items-center gap-2 text-xs text-text-muted">
              <input type="checkbox" checked={draft.supports_payouts} onChange={(e) => set("supports_payouts", e.target.checked)} />
              Supports payouts
            </label>
            <label className="flex items-center gap-2 text-xs text-text-muted">
              <input type="checkbox" checked={draft.pass_fee_to_customer} onChange={(e) => set("pass_fee_to_customer", e.target.checked)} />
              Pass fee to customer
            </label>
            <label className="flex items-center gap-2 text-xs text-text-muted">
              <input type="checkbox" checked={draft.is_enabled} onChange={(e) => set("is_enabled", e.target.checked)} />
              Enabled
            </label>
          </div>

          <Field label="Notes">
            <input value={draft.notes || ""} onChange={(e) => set("notes", e.target.value || null)}
              className="theme-input w-full rounded-lg border px-3 py-2 text-xs" />
          </Field>

          <Field label="extra_config (JSON) — universal redirect mapping">
            <textarea value={extraText} onChange={(e) => setExtraText(e.target.value)} rows={7}
              className="theme-input w-full rounded-lg border px-3 py-2 text-[11px] font-mono" />
            {extraError && <p className="mt-1 text-[10px] text-status-danger">{extraError}</p>}
            <p className="mt-1 text-[10px] text-text-faint">
              Keys: <code>redirect_url_template</code>, <code>create_url</code>, <code>create_method</code>, <code>create_auth_header</code>,
              <code>create_body</code>, <code>redirect_url_field</code>, <code>order_id_field</code>, <code>transaction_ref_field</code>, <code>status_field</code>, <code>success_values</code>.
              Template placeholders: <code>{`{order_id} {amount} {currency} {reference} {callback_url} {success_url} {cancel_url}`}</code>
            </p>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <span className="text-[10px] font-semibold text-text-faint">Load example:</span>
              {GATEWAY_TEMPLATES.map((t) => (
                <button key={t.code} type="button"
                  onClick={() => { setExtraText(t.json); setExtraError(null); }}
                  className="rounded-lg border border-border px-2.5 py-1 text-[10px] font-semibold text-text-muted hover:text-text hover:border-primary/50">
                  {t.label}
                </button>
              ))}
            </div>
          </Field>
        </div>

        <div className="mt-5 flex justify-end gap-2">
          <button onClick={onClose} className="rounded-xl border border-border px-4 py-2 text-xs font-semibold text-text-muted">Cancel</button>
          <Button variant="primary" onClick={submit}>
            <Save className="h-4 w-4" /> {isNew ? "Create Gateway" : "Save Changes"}
          </Button>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-[11px] font-semibold text-text-muted">{label}</span>
      {children}
    </label>
  );
}

// ── Payment Mode (runtime provider) ──────────────────────────────────────────

function RuntimeTab({
  runtime, bodyText, onChanged, addToast,
}: {
  runtime: RuntimeConfig | null;
  bodyText: string;
  onChanged: () => void;
  addToast: (m: string, t?: "success" | "error" | "info") => void;
}) {
  const [mode, setMode] = useState<"stripe" | "tap" | "both">(runtime?.online_provider || "stripe");
  const [saving, setSaving] = useState(false);
  useEffect(() => { if (runtime) setMode(runtime.online_provider); }, [runtime]);

  const save = async () => {
    setSaving(true);
    try {
      const res = await apiFetch("/payments/config/runtime", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ online_provider: mode }),
      });
      await jsonOrThrow(res);
      addToast("Payment mode updated", "success");
      onChanged();
    } catch (err: any) {
      addToast(err?.message || "Failed to update payment mode", "error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="theme-card rounded-xl border p-5 space-y-4">
      <h3 className="text-sm font-bold text-text">Active Online Payment Provider</h3>
      <p className={`${bodyText} text-text-faint`}>
        Choose which online card processor is active at checkout. Both Stripe and Tap must be configured to enable "both".
      </p>
      <div className="flex flex-wrap gap-2">
        {(["stripe", "tap", "both"] as const).map((m) => (
          <button key={m} onClick={() => setMode(m)}
            className={`rounded-xl border px-4 py-2 text-xs font-semibold capitalize ${mode === m ? "border-primary bg-primary/10 text-primary" : "border-border text-text-muted"}`}>
            {m}
          </button>
        ))}
      </div>
      {runtime && (
        <div className={`flex flex-wrap gap-3 ${bodyText} text-text-faint`}>
          <span>Stripe configured: {runtime.stripe_configured ? "✓" : "✗"}</span>
          <span>Tap configured: {runtime.tap_configured ? "✓" : "✗"}</span>
          <span>Enabled processors: {runtime.enabled_processors.join(", ") || "none"}</span>
        </div>
      )}
      <Button variant="primary" onClick={save} disabled={saving}>
        <Save className="h-4 w-4" /> {saving ? "Saving…" : "Save Mode"}
      </Button>
    </div>
  );
}

// ── Finance Quote ────────────────────────────────────────────────────────────

function FinanceTab({
  gateways, bodyText, addToast,
}: {
  gateways: GatewayConnection[];
  bodyText: string;
  addToast: (m: string, t?: "success" | "error" | "info") => void;
}) {
  const checkoutGateways = gateways.filter((g) => g.supports_customer_checkout);
  const [code, setCode] = useState("");
  const [subtotal, setSubtotal] = useState(100);
  const [discount, setDiscount] = useState(0);
  const [shipping, setShipping] = useState(0);
  const [vat, setVat] = useState(5);
  const [quote, setQuote] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => { if (checkoutGateways[0]) setCode(checkoutGateways[0].provider_code); }, [checkoutGateways]);

  const run = async () => {
    setLoading(true);
    try {
      const res = await apiFetch("/payments/config/finance-quote", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          gateway_code: code || null,
          subtotal_amount: subtotal,
          discount_amount: discount,
          shipping_amount: shipping,
          vat_amount: (subtotal - discount) * (vat / 100),
        }),
      });
      setQuote(await jsonOrThrow(res));
    } catch (err: any) {
      addToast(err?.message || "Quote failed", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="theme-card rounded-xl border p-5 space-y-3">
        <h3 className="text-sm font-bold text-text">Fee & Payout Quote</h3>
        <Field label="Gateway">
          <select value={code} onChange={(e) => setCode(e.target.value)}
            className="theme-input w-full rounded-lg border px-3 py-2 text-xs">
            <option value="">Platform default</option>
            {checkoutGateways.map((g) => <option key={g.provider_code} value={g.provider_code}>{g.display_name}</option>)}
          </select>
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Subtotal"><Num value={subtotal} onChange={setSubtotal} /></Field>
          <Field label="Discount"><Num value={discount} onChange={setDiscount} /></Field>
          <Field label="Shipping"><Num value={shipping} onChange={setShipping} /></Field>
          <Field label="VAT %"><Num value={vat} onChange={setVat} /></Field>
        </div>
        <Button variant="primary" onClick={run} disabled={loading}>
          <Calculator className="h-4 w-4" /> {loading ? "Calculating…" : "Calculate"}
        </Button>
      </div>

      <div className="theme-card rounded-xl border p-5">
        <h3 className="text-sm font-bold text-text mb-3">Estimate</h3>
        {quote ? (
          <dl className={`space-y-2 ${bodyText}`}>
            <Row k="Order total" v={quote.order_total} />
            <Row k="Gateway fee" v={quote.gateway_fee_amount} />
            <Row k="Customer pays" v={quote.customer_payable_total} highlight />
            <Row k="Net capture" v={quote.processor_net_capture} />
            <Row k="Zozi commission" v={quote.zozi_commission_amount} />
            <Row k="Supplier payout" v={quote.supplier_payout_estimate} />
            <Row k="Logistics payout" v={quote.logistics_payout_estimate} />
            <Row k="Platform net" v={quote.platform_net_after_gateway_and_payout_costs} highlight />
            <p className="pt-2 text-[10px] text-text-faint">Adapter supported: {String(quote.adapter_supported)} · Pass fee to customer: {String(quote.pass_fee_to_customer)}</p>
          </dl>
        ) : (
          <p className="text-sm text-text-muted">Enter amounts and calculate to preview fees and payouts.</p>
        )}
      </div>
    </div>
  );
}

function Num({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  return <input type="number" step="0.01" value={value} onChange={(e) => onChange(Number(e.target.value))} className="theme-input w-full rounded-lg border px-3 py-2 text-xs" />;
}
function Row({ k, v, highlight }: { k: string; v: number; highlight?: boolean }) {
  return (
    <div className="flex justify-between border-b border-border/60 pb-1">
      <dt className="text-text-faint">{k}</dt>
      <dd className={`font-semibold tabular-nums ${highlight ? "text-primary" : "text-text"}`}>{typeof v === "number" ? v.toFixed(2) : v}</dd>
    </div>
  );
}

// ── Country Routing ──────────────────────────────────────────────────────────

function RoutingTab({
  gateways, countryCode, assignedCountries, bodyText, addToast,
}: {
  gateways: GatewayConnection[];
  countryCode: string | null;
  assignedCountries: { code: string; name: string }[];
  bodyText: string;
  addToast: (m: string, t?: "success" | "error" | "info") => void;
}) {
  const [code, setCode] = useState(countryCode || "");
  const [routing, setRouting] = useState<{ gateway_id: string; name: string; enabled: boolean }[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => { if (countryCode) setCode(countryCode); }, [countryCode]);

  const load = useCallback(async (c: string) => {
    if (!c) return;
    setLoading(true);
    try {
      const res = await apiFetch(`/admin/countries/${c}/payment-gateways`);
      if (res.ok) {
        const data = await res.json();
        setRouting(Array.isArray(data) ? data : []);
      }
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(code); }, [code, load]);

  const toggle = (gatewayId: string) => {
    setRouting((r) => r.map((g) => g.gateway_id === gatewayId ? { ...g, enabled: !g.enabled } : g));
  };

  const save = async () => {
    if (!code) return;
    try {
      const res = await apiFetch(`/admin/countries/${code}/payment-gateways`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ gateways: routing.map((g) => ({ gateway_id: g.gateway_id, name: g.name, enabled: g.enabled })) }),
      });
      await jsonOrThrow(res);
      addToast("Country gateway routing saved (draft)", "success");
    } catch (err: any) {
      addToast(err?.message || "Failed to save routing", "error");
    }
  };

  const checkoutGateways = gateways.filter((g) => g.supports_customer_checkout);

  return (
    <div className="theme-card rounded-xl border p-5 space-y-4">
      <h3 className="text-sm font-bold text-text">Per-Country Gateway Routing</h3>
      <div className="flex flex-wrap items-center gap-3">
        <select value={code} onChange={(e) => setCode(e.target.value)}
          className="theme-input rounded-lg border px-3 py-2 text-xs">
          <option value="">Select country…</option>
          {assignedCountries.filter((c) => c.code !== "*").map((c) => <option key={c.code} value={c.code}>{c.name} ({c.code})</option>)}
        </select>
        <button onClick={() => load(code)} className="rounded-lg border border-border px-3 py-2 text-[11px] font-semibold text-text-muted">Reload</button>
        <Button variant="primary" onClick={save} disabled={!code}>
          <Save className="h-4 w-4" /> Save Routing
        </Button>
      </div>

      {loading ? (
        <p className="text-sm text-text-muted">Loading…</p>
      ) : !code ? (
        <p className="text-sm text-text-muted">Select a country to configure which gateways are available for its customers.</p>
      ) : (
        <div className="space-y-2">
          {checkoutGateways.map((g) => {
            const existing = routing.find((r) => r.gateway_id === g.provider_code);
            const enabled = existing ? existing.enabled : false;
            return (
              <div key={g.provider_code} className="flex items-center justify-between rounded-lg border border-border px-3 py-2">
                <div>
                  <p className="text-xs font-semibold text-text">{g.display_name}</p>
                  <p className={`${bodyText} text-text-faint`}>{g.provider_code}</p>
                </div>
                <button onClick={() => {
                  const next = enabled ? false : true;
                  setRouting((r) => {
                    const others = r.filter((x) => x.gateway_id !== g.provider_code);
                    return [...others, { gateway_id: g.provider_code, name: g.display_name, enabled: next }].sort((a, b) => a.gateway_id.localeCompare(b.gateway_id));
                  });
                }}
                  className={`relative h-5 w-9 rounded-full transition-colors ${enabled ? "bg-success" : "bg-text-faint/40"}`}>
                  <span className={`absolute top-0.5 h-4 w-4 rounded-full bg-white transition-all ${enabled ? "left-4" : "left-0.5"}`} />
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
