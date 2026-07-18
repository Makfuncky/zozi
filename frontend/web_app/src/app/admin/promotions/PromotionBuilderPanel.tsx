"use client";

import { Button } from "@/components/ui/Button";

import { useEffect, useMemo, useState } from "react";
import {
  Calculator,
  Plus,
  RefreshCw,
  Save,
  Settings2,
  Sparkles,
  Trash2,
  X,
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { useAdminCountry } from "@/lib/useAdminCountry";
import { useCurrencyStore } from "@/lib/currencyStore";

type StackingMode = "best_only" | "stack_all" | "custom";

type PromotionConfig = {
  id: number;
  engine_enabled: boolean;
  allow_product_coupons: boolean;
  allow_category_coupons: boolean;
  allow_order_tier_discounts: boolean;
  allow_referral_rewards: boolean;
  allow_supplier_promotions: boolean;
  allow_global_coupons: boolean;
  stacking_mode: StackingMode;
  max_combined_discount_percent: number;
  max_combined_discount_amount: number;
  show_savings_line_item: boolean;
  tier_discount_visible: boolean;
  points_per_omr: number;
  referral_referrer_points: number;
  referral_referee_points: number;
  points_expiry_months: number;
  referral_monthly_cap: number;
  referral_verification_delay_days: number;
  min_points_redeem: number;
  allow_partial_points_redemption: boolean;
};

type PromotionTier = {
  id: number;
  tier_name: string;
  min_order: number;
  max_order: number | null;
  discount_type: "fixed" | "percent";
  discount_value: number;
  stacking_allowed: boolean;
  is_active: boolean;
  sort_order: number;
};

type TierForm = {
  tier_name: string;
  min_order: string;
  max_order: string;
  discount_type: "fixed" | "percent";
  discount_value: string;
  stacking_allowed: boolean;
  is_active: boolean;
  sort_order: string;
};

const EMPTY_TIER_FORM: TierForm = {
  tier_name: "",
  min_order: "",
  max_order: "",
  discount_type: "fixed",
  discount_value: "",
  stacking_allowed: false,
  is_active: true,
  sort_order: "0",
};

function boolLabel(v: boolean): string {
  return v ? "ON" : "OFF";
}

function normalizeTierToForm(tier: PromotionTier): TierForm {
  return {
    tier_name: tier.tier_name,
    min_order: String(tier.min_order),
    max_order: tier.max_order != null ? String(tier.max_order) : "",
    discount_type: tier.discount_type,
    discount_value: String(tier.discount_value),
    stacking_allowed: tier.stacking_allowed,
    is_active: tier.is_active,
    sort_order: String(tier.sort_order),
  };
}

export default function PromotionBuilderPanel() {
  const formatMoney = useCurrencyStore((s) => s.format);
  const { selectedCountry } = useAdminCountry();
  const countryCode = selectedCountry?.code || "*";

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [savingConfig, setSavingConfig] = useState(false);
  const [savingTier, setSavingTier] = useState(false);
  const [draft, setDraft] = useState<PromotionConfig | null>(null);
  const [tiers, setTiers] = useState<PromotionTier[]>([]);
  const [error, setError] = useState("");

  const [showTierModal, setShowTierModal] = useState(false);
  const [editingTierId, setEditingTierId] = useState<number | null>(null);
  const [tierForm, setTierForm] = useState<TierForm>({ ...EMPTY_TIER_FORM });
  const [tierError, setTierError] = useState("");

  const [previewSubtotal, setPreviewSubtotal] = useState("100");
  const [previewCoupon, setPreviewCoupon] = useState("0");
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewResult, setPreviewResult] = useState<any>(null);

  const activeTierCount = useMemo(() => tiers.filter((tier) => tier.is_active).length, [tiers]);

  async function loadWorkspace(isManualRefresh = false): Promise<void> {
    if (isManualRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError("");
    try {
      const [cfgRes, tiersRes] = await Promise.all([
        apiFetch(`/admin/promotions/config`),
        apiFetch(`/admin/promotions/tiers`),
      ]);

      if (!cfgRes.ok || !tiersRes.ok) {
        throw new Error("Failed to load promotion builder workspace.");
      }

      const cfg = (await cfgRes.json()) as PromotionConfig;
      const tierRows = (await tiersRes.json()) as PromotionTier[];

      setDraft(cfg);
      setTiers(Array.isArray(tierRows) ? tierRows : []);
    } catch (err: any) {
      setError(err?.message || "Failed to load promotion builder workspace.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void loadWorkspace();
  }, []);

  function patchDraft<K extends keyof PromotionConfig>(key: K, value: PromotionConfig[K]) {
    setDraft((prev) => (prev ? { ...prev, [key]: value } : prev));
  }

  async function saveConfig(): Promise<void> {
    if (!draft) return;
    setSavingConfig(true);
    setError("");
    try {
      const res = await apiFetch(`/admin/promotions/config`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(draft),
      });
      if (!res.ok) {
        const payload = await res.json().catch(() => ({}));
        throw new Error(payload?.detail || "Failed to save promotion settings.");
      }
      const next = (await res.json()) as PromotionConfig;
      setDraft(next);
    } catch (err: any) {
      setError(err?.message || "Failed to save promotion settings.");
    } finally {
      setSavingConfig(false);
    }
  }

  function openCreateTierModal() {
    setEditingTierId(null);
    setTierForm({ ...EMPTY_TIER_FORM, sort_order: String(tiers.length + 1) });
    setTierError("");
    setShowTierModal(true);
  }

  function openEditTierModal(tier: PromotionTier) {
    setEditingTierId(tier.id);
    setTierForm(normalizeTierToForm(tier));
    setTierError("");
    setShowTierModal(true);
  }

  async function saveTier(): Promise<void> {
    if (!tierForm.tier_name.trim()) {
      setTierError("Tier name is required.");
      return;
    }
    if (!tierForm.min_order.trim() || !tierForm.discount_value.trim()) {
      setTierError("Min order and discount value are required.");
      return;
    }

    setSavingTier(true);
    setTierError("");
    try {
      const payload = {
        tier_name: tierForm.tier_name.trim(),
        min_order: Number(tierForm.min_order),
        max_order: tierForm.max_order.trim() ? Number(tierForm.max_order) : null,
        discount_type: tierForm.discount_type,
        discount_value: Number(tierForm.discount_value),
        stacking_allowed: tierForm.stacking_allowed,
        is_active: tierForm.is_active,
        sort_order: Number(tierForm.sort_order || "0"),
      };
      const endpoint = editingTierId ? `/admin/promotions/tiers/${editingTierId}` : `/admin/promotions/tiers`;
      const method = editingTierId ? "PUT" : "POST";
      const res = await apiFetch(endpoint, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body?.detail || "Failed to save tier.");
      }
      setShowTierModal(false);
      await loadWorkspace(true);
    } catch (err: any) {
      setTierError(err?.message || "Failed to save tier.");
    } finally {
      setSavingTier(false);
    }
  }

  async function toggleTierActive(tier: PromotionTier): Promise<void> {
    try {
      const res = await apiFetch(`/admin/promotions/tiers/${tier.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: !tier.is_active }),
      });
      if (!res.ok) return;
      const updated = (await res.json()) as PromotionTier;
      setTiers((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
    } catch {
      // Keep UI stable even if toggle fails.
    }
  }

  async function deleteTier(id: number): Promise<void> {
    if (!confirm("Delete this tier?")) return;
    try {
      const res = await apiFetch(`/admin/promotions/tiers/${id}`, { method: "DELETE" });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body?.detail || "Failed to delete tier.");
      }
      setTiers((prev) => prev.filter((tier) => tier.id !== id));
    } catch (err: any) {
      setError(err?.message || "Failed to delete tier.");
    }
  }

  async function runPreview(): Promise<void> {
    setPreviewLoading(true);
    try {
      const res = await apiFetch(`/admin/promotions/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          order_subtotal: Number(previewSubtotal || "0"),
          coupon_discount: Number(previewCoupon || "0"),
        }),
      });
      if (!res.ok) {
        const payload = await res.json().catch(() => ({}));
        throw new Error(payload?.detail || "Failed to run preview.");
      }
      setPreviewResult(await res.json());
    } catch (err: any) {
      setError(err?.message || "Failed to run preview.");
    } finally {
      setPreviewLoading(false);
    }
  }

  if (loading || !draft) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="h-24 animate-pulse rounded-xl bg-surface-2" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {error ? <p className="rounded-lg border border-danger/40 bg-danger/10 px-3 py-2 text-xs text-danger">{error}</p> : null}

      <div className="grid gap-3 md:grid-cols-4">
        <div className="rounded-xl border border-border bg-surface-1 p-3">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-text-faint">Engine</p>
          <p className="mt-1 text-lg font-bold text-text">{boolLabel(draft.engine_enabled)}</p>
          <p className="text-[11px] text-text-muted">Master switch</p>
        </div>
        <div className="rounded-xl border border-border bg-surface-1 p-3">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-text-faint">Tiers</p>
          <p className="mt-1 text-lg font-bold text-text">{activeTierCount}</p>
          <p className="text-[11px] text-text-muted">Active order bands</p>
        </div>
        <div className="rounded-xl border border-border bg-surface-1 p-3">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-text-faint">Referral Points</p>
          <p className="mt-1 text-lg font-bold text-text">{draft.referral_referrer_points} / {draft.referral_referee_points}</p>
          <p className="text-[11px] text-text-muted">Referrer / Referee</p>
        </div>
        <div className="rounded-xl border border-border bg-surface-1 p-3">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-text-faint">Redemption</p>
          <p className="mt-1 text-lg font-bold text-text">{draft.points_per_omr}:1 OMR</p>
          <p className="text-[11px] text-text-muted">Points conversion</p>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-surface-1 p-4">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-text">
            <Settings2 className="h-4 w-4" /> Engine Controls
          </h3>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => void loadWorkspace(true)}
              disabled={refreshing}
              className="rounded-lg border border-border bg-surface-2 px-2.5 py-1.5 text-xs text-text-muted hover:bg-surface"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`} />
            </button>
            <button
              type="button"
              onClick={() => void saveConfig()}
              disabled={savingConfig}
              className="inline-flex items-center gap-1.5 rounded-lg theme-btn-primary px-3 py-1.5 text-xs font-semibold disabled:opacity-60"
            >
              <Save className="h-3.5 w-3.5" /> {savingConfig ? "Saving..." : "Save Settings"}
            </button>
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <label className="flex items-center justify-between rounded-lg border border-border px-3 py-2 text-xs text-text">
            Engine Enabled
            <input type="checkbox" checked={draft.engine_enabled} onChange={(e) => patchDraft("engine_enabled", e.target.checked)} className="h-4 w-4 accent-primary" />
          </label>
          <label className="flex items-center justify-between rounded-lg border border-border px-3 py-2 text-xs text-text">
            Tier Discounts
            <input type="checkbox" checked={draft.allow_order_tier_discounts} onChange={(e) => patchDraft("allow_order_tier_discounts", e.target.checked)} className="h-4 w-4 accent-primary" />
          </label>
          <label className="flex items-center justify-between rounded-lg border border-border px-3 py-2 text-xs text-text">
            Referral Rewards
            <input type="checkbox" checked={draft.allow_referral_rewards} onChange={(e) => patchDraft("allow_referral_rewards", e.target.checked)} className="h-4 w-4 accent-primary" />
          </label>
          <label className="flex items-center justify-between rounded-lg border border-border px-3 py-2 text-xs text-text">
            Product Coupons
            <input type="checkbox" checked={draft.allow_product_coupons} onChange={(e) => patchDraft("allow_product_coupons", e.target.checked)} className="h-4 w-4 accent-primary" />
          </label>
          <label className="flex items-center justify-between rounded-lg border border-border px-3 py-2 text-xs text-text">
            Category Coupons
            <input type="checkbox" checked={draft.allow_category_coupons} onChange={(e) => patchDraft("allow_category_coupons", e.target.checked)} className="h-4 w-4 accent-primary" />
          </label>
          <label className="flex items-center justify-between rounded-lg border border-border px-3 py-2 text-xs text-text">
            Global Coupons
            <input type="checkbox" checked={draft.allow_global_coupons} onChange={(e) => patchDraft("allow_global_coupons", e.target.checked)} className="h-4 w-4 accent-primary" />
          </label>
          <label className="flex items-center justify-between rounded-lg border border-border px-3 py-2 text-xs text-text">
            Supplier Promotions
            <input type="checkbox" checked={draft.allow_supplier_promotions} onChange={(e) => patchDraft("allow_supplier_promotions", e.target.checked)} className="h-4 w-4 accent-primary" />
          </label>
          <label className="flex items-center justify-between rounded-lg border border-border px-3 py-2 text-xs text-text">
            Show Savings Line
            <input type="checkbox" checked={draft.show_savings_line_item} onChange={(e) => patchDraft("show_savings_line_item", e.target.checked)} className="h-4 w-4 accent-primary" />
          </label>
          <label className="flex items-center justify-between rounded-lg border border-border px-3 py-2 text-xs text-text">
            Partial Points Redeem
            <input type="checkbox" checked={draft.allow_partial_points_redemption} onChange={(e) => patchDraft("allow_partial_points_redemption", e.target.checked)} className="h-4 w-4 accent-primary" />
          </label>
        </div>

        <div className="mt-3 grid gap-3 md:grid-cols-3">
          <div>
            <label className="mb-1 block text-xs text-text-muted">Stacking Mode</label>
            <select
              value={draft.stacking_mode}
              onChange={(e) => patchDraft("stacking_mode", e.target.value as StackingMode)}
              className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-xs text-text"
            >
              <option value="best_only">Best Only</option>
              <option value="stack_all">Stack All</option>
              <option value="custom">Custom</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs text-text-muted">Max Discount %</label>
            <input
              type="number"
              min={0}
              max={100}
              value={draft.max_combined_discount_percent}
              onChange={(e) => patchDraft("max_combined_discount_percent", Number(e.target.value || 0))}
              className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-xs text-text"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-text-muted">Max Discount Amount</label>
            <input
              type="number"
              min={0}
              step="0.01"
              value={draft.max_combined_discount_amount}
              onChange={(e) => patchDraft("max_combined_discount_amount", Number(e.target.value || 0))}
              className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-xs text-text"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-text-muted">Referrer Points</label>
            <input
              type="number"
              min={0}
              value={draft.referral_referrer_points}
              onChange={(e) => patchDraft("referral_referrer_points", Number(e.target.value || 0))}
              className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-xs text-text"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-text-muted">Referee Points</label>
            <input
              type="number"
              min={0}
              value={draft.referral_referee_points}
              onChange={(e) => patchDraft("referral_referee_points", Number(e.target.value || 0))}
              className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-xs text-text"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-text-muted">Points per 1 OMR</label>
            <input
              type="number"
              min={1}
              value={draft.points_per_omr}
              onChange={(e) => patchDraft("points_per_omr", Number(e.target.value || 1))}
              className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-xs text-text"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-text-muted">Min Points to Redeem</label>
            <input
              type="number"
              min={0}
              value={draft.min_points_redeem}
              onChange={(e) => patchDraft("min_points_redeem", Number(e.target.value || 0))}
              className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-xs text-text"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-text-muted">Points Expiry (months)</label>
            <input
              type="number"
              min={0}
              value={draft.points_expiry_months}
              onChange={(e) => patchDraft("points_expiry_months", Number(e.target.value || 0))}
              className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-xs text-text"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-text-muted">Referral Monthly Cap</label>
            <input
              type="number"
              min={0}
              value={draft.referral_monthly_cap}
              onChange={(e) => patchDraft("referral_monthly_cap", Number(e.target.value || 0))}
              className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-xs text-text"
            />
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-surface-1 p-4">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-text">
            <Sparkles className="h-4 w-4" /> Order Tier Editor
          </h3>
          <button
            type="button"
            onClick={openCreateTierModal}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-surface-2 px-3 py-1.5 text-xs font-semibold text-text hover:bg-surface"
          >
            <Plus className="h-3.5 w-3.5" /> Add Tier
          </button>
        </div>

        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full min-w-190 text-xs">
            <thead className="bg-surface-2">
              <tr>
                <th className="px-3 py-2 text-left font-semibold text-text-faint">Tier</th>
                <th className="px-3 py-2 text-left font-semibold text-text-faint">Order Range</th>
                <th className="px-3 py-2 text-left font-semibold text-text-faint">Discount</th>
                <th className="px-3 py-2 text-left font-semibold text-text-faint">Stacking</th>
                <th className="px-3 py-2 text-left font-semibold text-text-faint">Status</th>
                <th className="px-3 py-2 text-left font-semibold text-text-faint">Sort</th>
                <th className="px-3 py-2 text-right font-semibold text-text-faint">Actions</th>
              </tr>
            </thead>
            <tbody>
              {tiers.map((tier) => (
                <tr key={tier.id} className="border-t border-border/70">
                  <td className="px-3 py-2 font-semibold text-text">{tier.tier_name}</td>
                  <td className="px-3 py-2 text-text-muted">
                    {formatMoney(tier.min_order)} - {tier.max_order == null ? "No max" : formatMoney(tier.max_order)}
                  </td>
                  <td className="px-3 py-2 text-text">
                    {tier.discount_type === "percent"
                      ? `${tier.discount_value}%`
                      : formatMoney(tier.discount_value)}
                  </td>
                  <td className="px-3 py-2 text-text-muted">{boolLabel(tier.stacking_allowed)}</td>
                  <td className="px-3 py-2">
                    <button
                      type="button"
                      onClick={() => void toggleTierActive(tier)}
                      className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                        tier.is_active
                          ? "bg-success/10 text-success"
                          : "bg-surface-3 text-text-muted"
                      }`}
                    >
                      {tier.is_active ? "Active" : "Inactive"}
                    </button>
                  </td>
                  <td className="px-3 py-2 text-text-muted">{tier.sort_order}</td>
                  <td className="px-3 py-2 text-right">
                    <div className="inline-flex gap-1">
                      <button
                        type="button"
                        onClick={() => openEditTierModal(tier)}
                        className="rounded-lg border border-border bg-surface-2 px-2 py-1 text-[11px] text-text-muted hover:bg-surface"
                      >
                        Edit
                      </button>
                      <Button variant="danger" className="rounded-lg border border-danger/40 px-2 py-1 text-[11px] text-danger" type="button"
                        onClick={() => void deleteTier(tier.id)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
              {tiers.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-3 py-6 text-center text-xs text-text-faint">No tiers configured yet.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-surface-1 p-4">
        <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-text">
          <Calculator className="h-4 w-4" /> Promotion Preview
        </h3>
        <div className="grid gap-3 md:grid-cols-4">
          <div>
            <label className="mb-1 block text-xs text-text-muted">Order Subtotal</label>
            <input
              type="number"
              min={0}
              value={previewSubtotal}
              onChange={(e) => setPreviewSubtotal(e.target.value)}
              className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-xs text-text"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-text-muted">Coupon Discount</label>
            <input
              type="number"
              min={0}
              value={previewCoupon}
              onChange={(e) => setPreviewCoupon(e.target.value)}
              className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-xs text-text"
            />
          </div>
          <div className="md:col-span-2 flex items-end">
            <button
              type="button"
              onClick={() => void runPreview()}
              disabled={previewLoading}
              className="inline-flex items-center gap-1.5 rounded-lg theme-btn-primary px-3 py-2 text-xs font-semibold disabled:opacity-60"
            >
              {previewLoading ? "Running..." : "Run Preview"}
            </button>
          </div>
        </div>

        {previewResult ? (
          <div className="mt-3 grid gap-3 md:grid-cols-4">
            <div className="rounded-lg border border-border bg-surface-2 p-3">
              <p className="text-[10px] uppercase tracking-[0.16em] text-text-faint">After Coupon</p>
              <p className="mt-1 text-sm font-semibold text-text">{formatMoney(previewResult.after_coupon)}</p>
            </div>
            <div className="rounded-lg border border-border bg-surface-2 p-3">
              <p className="text-[10px] uppercase tracking-[0.16em] text-text-faint">Tier Discount</p>
              <p className="mt-1 text-sm font-semibold text-text">{formatMoney(previewResult.tier_discount)}</p>
            </div>
            <div className="rounded-lg border border-border bg-surface-2 p-3">
              <p className="text-[10px] uppercase tracking-[0.16em] text-text-faint">Final Discount</p>
              <p className="mt-1 text-sm font-semibold text-text">{formatMoney(previewResult.final_discount)}</p>
            </div>
            <div className="rounded-lg border border-border bg-surface-2 p-3">
              <p className="text-[10px] uppercase tracking-[0.16em] text-text-faint">Matched Tier</p>
              <p className="mt-1 text-sm font-semibold text-text">{previewResult?.matched_tier?.tier_name || "None"}</p>
            </div>
          </div>
        ) : null}
      </div>

      {showTierModal ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4">
          <div className="w-full max-w-lg rounded-xl theme-modal-shell p-5">
            <div className="mb-4 flex items-center justify-between">
              <h4 className="text-base font-semibold text-text">{editingTierId ? "Edit Tier" : "Add Tier"}</h4>
              <button type="button" onClick={() => setShowTierModal(false)} className="rounded-lg p-1 text-text-muted hover:bg-surface-2">
                <X className="h-4 w-4" />
              </button>
            </div>

            {tierError ? <p className="mb-3 rounded-lg bg-danger/10 px-3 py-2 text-xs text-danger">{tierError}</p> : null}

            <div className="grid gap-3 md:grid-cols-2">
              <div className="md:col-span-2">
                <label className="mb-1 block text-xs text-text-muted">Tier Name</label>
                <input
                  value={tierForm.tier_name}
                  onChange={(e) => setTierForm((prev) => ({ ...prev, tier_name: e.target.value }))}
                  className="w-full rounded-lg border border-border bg-surface-1 px-3 py-2 text-xs text-text"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-text-muted">Min Order</label>
                <input
                  type="number"
                  min={0}
                  value={tierForm.min_order}
                  onChange={(e) => setTierForm((prev) => ({ ...prev, min_order: e.target.value }))}
                  className="w-full rounded-lg border border-border bg-surface-1 px-3 py-2 text-xs text-text"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-text-muted">Max Order (optional)</label>
                <input
                  type="number"
                  min={0}
                  value={tierForm.max_order}
                  onChange={(e) => setTierForm((prev) => ({ ...prev, max_order: e.target.value }))}
                  className="w-full rounded-lg border border-border bg-surface-1 px-3 py-2 text-xs text-text"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-text-muted">Discount Type</label>
                <select
                  value={tierForm.discount_type}
                  onChange={(e) => setTierForm((prev) => ({ ...prev, discount_type: e.target.value as "fixed" | "percent" }))}
                  className="w-full rounded-lg border border-border bg-surface-1 px-3 py-2 text-xs text-text"
                >
                  <option value="fixed">Fixed Amount</option>
                  <option value="percent">Percentage</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs text-text-muted">Discount Value</label>
                <input
                  type="number"
                  min={0}
                  value={tierForm.discount_value}
                  onChange={(e) => setTierForm((prev) => ({ ...prev, discount_value: e.target.value }))}
                  className="w-full rounded-lg border border-border bg-surface-1 px-3 py-2 text-xs text-text"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-text-muted">Sort Order</label>
                <input
                  type="number"
                  min={0}
                  value={tierForm.sort_order}
                  onChange={(e) => setTierForm((prev) => ({ ...prev, sort_order: e.target.value }))}
                  className="w-full rounded-lg border border-border bg-surface-1 px-3 py-2 text-xs text-text"
                />
              </div>
              <div className="flex items-end gap-4">
                <label className="flex items-center gap-2 text-xs text-text">
                  <input
                    type="checkbox"
                    checked={tierForm.stacking_allowed}
                    onChange={(e) => setTierForm((prev) => ({ ...prev, stacking_allowed: e.target.checked }))}
                    className="h-4 w-4 accent-primary"
                  />
                  Stacking Allowed
                </label>
                <label className="flex items-center gap-2 text-xs text-text">
                  <input
                    type="checkbox"
                    checked={tierForm.is_active}
                    onChange={(e) => setTierForm((prev) => ({ ...prev, is_active: e.target.checked }))}
                    className="h-4 w-4 accent-primary"
                  />
                  Active
                </label>
              </div>
            </div>

            <div className="mt-4 flex gap-2">
              <button
                type="button"
                onClick={() => setShowTierModal(false)}
                className="flex-1 rounded-lg border border-border bg-surface-2 px-3 py-2 text-xs text-text-muted hover:bg-surface"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => void saveTier()}
                disabled={savingTier}
                className="flex-1 rounded-lg theme-btn-primary px-3 py-2 text-xs font-semibold disabled:opacity-60"
              >
                {savingTier ? "Saving..." : "Save Tier"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}


