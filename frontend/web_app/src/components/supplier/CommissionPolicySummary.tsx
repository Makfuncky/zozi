import { Layers3, ShieldCheck, Tag, TrendingUp } from "@/lib/icons";
import { formatCurrencyAmount } from "@/lib/currencyStore";

export interface SupplierCommissionPolicySnapshot {
  updated_at: string | null;
  global_config: {
    default_rate: number;
    low_value_threshold: number;
    fixed_cap_amount: number;
    fixed_cap_enabled: boolean;
    margin_protection_enabled: boolean;
    margin_threshold: number | null;
  };
  supplier_rate: {
    current_rate: number;
    calculation_method: string;
    badge_level: string | null;
    using_default: boolean;
    combined_default_rate?: number;
    default_base_rate?: number;
  } | null;
  active_categories: Array<{
    category_slug: string;
    category_display_name: string;
    rate: number;
    notes: string | null;
  }>;
  active_badge_tiers: Array<{
    badge_level: string;
    commission_rate: number;
    setup_fee: number;
    recurring_fee: number;
    recurring_interval: string | null;
    min_fulfilled_orders: number | null;
    min_monthly_revenue: number | null;
  }>;
  resolution_order: Array<{
    order: number;
    label: string;
    state: string;
    detail: string;
  }>;
}

interface CommissionPolicySummaryProps {
  policy: SupplierCommissionPolicySnapshot;
  title?: string;
  subtitle?: string;
  compact?: boolean;
}

function fmtPct(value: number): string {
  return `${(value * 100).toFixed(2)}%`;
}

function fmtMoney(value: number | null | undefined): string {
  return formatCurrencyAmount(value ?? 0);
}

function fmtDate(value: string | null): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
  } catch {
    return value;
  }
}

function labelize(rawValue: string | null | undefined): string {
  return String(rawValue || "none").replace(/_/g, " ");
}

export default function CommissionPolicySummary({
  policy,
  title = "Current Commission Policy",
  subtitle = "This snapshot stays aligned with the current commission policy configured by admin.",
  compact = false,
}: CommissionPolicySummaryProps) {
  const currentRate = policy.supplier_rate?.current_rate ?? 0;
  const defaultBaseRate = policy.supplier_rate?.default_base_rate ?? policy.global_config.default_rate;
  const combinedDefaultRate = policy.supplier_rate?.combined_default_rate ?? (currentRate + defaultBaseRate);
  const currentMethod = policy.supplier_rate?.calculation_method ?? "global";
  const cardPadding = compact ? "p-3" : "p-4";

  return (
    <section className={`theme-card rounded-xl border ${cardPadding}`}>
      <div className="flex flex-col gap-3 border-b border-border pb-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-primary/10 p-2 text-primary">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-text">{title}</h2>
            <p className="text-xs text-text-muted">{subtitle}</p>
          </div>
        </div>
        <span className="rounded-full border border-border bg-surface-2 px-3 py-1 text-[11px] font-semibold text-text-muted">
          Updated {fmtDate(policy.updated_at)}
        </span>
      </div>

      <div className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-lg border border-border bg-surface-2 px-3 py-2.5">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-text-faint">Supplier Component</p>
          <p className="mt-1 text-lg font-bold text-text">{fmtPct(currentRate)}</p>
          <p className="text-[11px] capitalize text-text-muted">Driven by {labelize(currentMethod)}</p>
        </div>
        <div className="rounded-lg border border-border bg-surface-2 px-3 py-2.5">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-text-faint">Default Base Rate</p>
          <p className="mt-1 text-lg font-bold text-text">{fmtPct(defaultBaseRate)}</p>
          <p className="text-[11px] text-text-muted">Used when no product or category base applies</p>
        </div>
        <div className="rounded-lg border border-border bg-surface-2 px-3 py-2.5">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-text-faint">Combined Default Total</p>
          <p className="mt-1 text-lg font-bold text-text">{fmtPct(combinedDefaultRate)}</p>
          <p className="text-[11px] text-text-muted">Supplier component + default base before guardrails</p>
        </div>
        <div className="rounded-lg border border-border bg-surface-2 px-3 py-2.5">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-text-faint">Low-value Cap</p>
          <p className="mt-1 text-sm font-bold text-text">
            {policy.global_config.fixed_cap_enabled ? fmtMoney(policy.global_config.fixed_cap_amount) : "Off"}
          </p>
          <p className="text-[11px] text-text-muted">Below {fmtMoney(policy.global_config.low_value_threshold)}</p>
        </div>
      </div>

      <div className="mt-3 rounded-lg border border-border bg-surface px-3 py-2.5">
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-faint">Combined Flow</p>
          {policy.resolution_order.map((step) => (
            <span
              key={`${step.order}-${step.label}`}
              className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${
                step.state === "active"
                  ? "bg-primary text-white"
                  : step.state === "fallback"
                    ? "bg-surface-2 text-text"
                    : "border border-border bg-surface-2 text-text-muted"
              }`}
            >
              {step.order}. {step.label}
            </span>
          ))}
        </div>
      </div>

      <div className="mt-3 grid gap-3 xl:grid-cols-[1fr_1fr]">
        <div className="rounded-lg border border-border bg-surface-2 p-3">
          <div className="flex items-center gap-2">
            <Layers3 className="h-4 w-4 text-primary" />
            <p className="text-xs font-semibold text-text">Active Category Rates</p>
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            {policy.active_categories.length === 0 ? (
              <span className="text-[11px] text-text-muted">No active category rates.</span>
            ) : (
              policy.active_categories.slice(0, 8).map((category) => (
                <span key={category.category_slug} className="rounded-full border border-border bg-surface px-2.5 py-1 text-[11px] font-semibold text-text">
                  {category.category_display_name} {fmtPct(category.rate)}
                </span>
              ))
            )}
          </div>
        </div>

        <div className="rounded-lg border border-border bg-surface-2 p-3">
          <div className="flex items-center gap-2">
            <Tag className="h-4 w-4 text-primary" />
            <p className="text-xs font-semibold text-text">Active Badge Tiers</p>
          </div>
          <div className="mt-2 space-y-2">
            {policy.active_badge_tiers.length === 0 ? (
              <span className="text-[11px] text-text-muted">No active badge tiers.</span>
            ) : (
              policy.active_badge_tiers.slice(0, 4).map((tier) => (
                <div key={tier.badge_level} className="rounded-lg border border-border bg-surface px-3 py-2">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-xs font-semibold capitalize text-text">{labelize(tier.badge_level)}</p>
                    <span className="text-[11px] font-semibold text-primary">{fmtPct(tier.commission_rate)}</span>
                  </div>
                  <p className="mt-1 text-[11px] text-text-muted">
                    Setup {fmtMoney(tier.setup_fee)} · Recurring {fmtMoney(tier.recurring_fee)} {tier.recurring_interval ? `/${tier.recurring_interval}` : ""}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="mt-3 rounded-lg border border-border bg-surface px-3 py-2.5">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-primary" />
          <p className="text-xs font-semibold text-text">Supplier-facing workflow</p>
        </div>
        <p className="mt-1 text-[11px] text-text-muted">
          Your dashboard, terms page, and payout math follow this same live policy snapshot so supplier communication stays aligned with the supplier component + base-rate formula used by the commission engine.
        </p>
      </div>
    </section>
  );
}


