"use client";

import { Fragment } from "react";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Save, Trash2, Plus, Eye, UploadCloud, RefreshCw, Edit3, X, Check } from "@/lib/icons";
import type { CountriesTabProps } from "./CountriesTabProps";

export default function PayoutSettingsTab({
  ...p
}: CountriesTabProps) {
  const { loadPayoutRules, addToast, allCategories, batchSize, busyAction, canSubmit, catPayoutRules, countries, country, minimumPayoutAmount, name, newCatPayoutRate, newCatPayoutSlug, newProdPayoutId, newProdPayoutRate, payoutCurrency, payoutDay, payoutSchedule, prodPayoutRules, selectedCountryCode, submitPayoutSettingsDraft, setBatchSize, setMinimumPayoutAmount, setNewCatPayoutRate, setNewCatPayoutSlug, setNewProdPayoutId, setNewProdPayoutRate, setPayoutCurrency, setPayoutDay, setPayoutSchedule } = p;

  return (
    <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
      <h3 className="text-sm font-bold text-text">Supplier Settlement & Payout Rules</h3>
      <p className="text-xs text-text-muted">Manage standard payment intervals and transaction batch sizes for suppliers in this country.</p>

      <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-5">
        <label className="space-y-1 text-xs text-text-muted">
          Minimum Payout Amount
          <input className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={minimumPayoutAmount} onChange={(e) => setMinimumPayoutAmount(e.target.value)} />
        </label>
        <label className="space-y-1 text-xs text-text-muted">
          Settlement Cycle
          <select className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={payoutSchedule} onChange={(e) => setPayoutSchedule(e.target.value)}>
            <option value="daily">Daily Settlements</option>
            <option value="weekly">Weekly Cycle</option>
            <option value="biweekly">Bi-weekly (Fortnightly)</option>
            <option value="monthly">Monthly Settlements</option>
          </select>
        </label>
        <label className="space-y-1 text-xs text-text-muted">
          Weekly Payout Day
          <select className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={payoutDay} onChange={(e) => setPayoutDay(e.target.value)}>
            <option value="sunday">Sunday</option>
            <option value="monday">Monday</option>
            <option value="tuesday">Tuesday</option>
            <option value="wednesday">Wednesday</option>
            <option value="thursday">Thursday</option>
          </select>
        </label>
        <label className="space-y-1 text-xs text-text-muted">
          Settlement Batch Size
          <input type="number" className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={batchSize} onChange={(e) => setBatchSize(e.target.value)} />
        </label>
        <label className="space-y-1 text-xs text-text-muted">
          Payout Currency Override
          <input className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={payoutCurrency} onChange={(e) => setPayoutCurrency(e.target.value)} placeholder="SAR" />
        </label>
      </div>

      <div className="flex justify-end pt-2">
        <Button variant="primary" type="button"
          onClick={submitPayoutSettingsDraft}
          disabled={!canSubmit || busyAction === "payout_settings"}>
          <Save className="h-3.5 w-3.5" />
          {busyAction === "payout_settings" ? "Creating draft..." : "Save Payout Settings Draft"}
        </Button>
      </div>

      <div className="pt-4 border-t border-border/60">
        <h4 className="text-xs font-bold text-text mb-2">Category-Level Payout Overrides</h4>
        <p className="text-[10px] text-text-muted mb-3">
          Override the country-level payout rate for specific product categories.
          Higher priority than the default payout rate but lower than per-product rules.
        </p>

        <div className="flex items-center gap-2 mb-3">
          <select
            className="rounded border border-border bg-surface px-2 py-1.5 text-xs text-text max-w-[200px] flex-1"
            value={newCatPayoutSlug}
            onChange={(e) => setNewCatPayoutSlug(e.target.value)}
          >
            <option value="">Select category...</option>
            {allCategories
              .filter((c) => !catPayoutRules.some((r) => r.category_slug === c.slug))
              .map((c) => (
                <option key={c.slug} value={c.slug}>{c.name}</option>
              ))}
          </select>
          <label className="text-[10px] text-text-muted flex items-center gap-1">
            Rate:
            <input
              type="number"
              step="0.01"
              min="0"
              max="1"
              className="w-16 rounded border border-border bg-surface px-1.5 py-1.5 text-xs text-text"
              value={newCatPayoutRate}
              onChange={(e) => setNewCatPayoutRate(e.target.value)}
            />
          </label>
          <Button variant="primary" className="rounded text-primary px-2.5 py-1.5 text-[10px] font-semibold transition" type="button"
            disabled={!newCatPayoutSlug || !newCatPayoutRate}
            onClick={async () => {
              const slug = newCatPayoutSlug;
              const rate = Number(newCatPayoutRate);
              if (!slug || Number.isNaN(rate)) return;
              try {
                const res = await apiFetch(`/admin/countries/${selectedCountryCode}/payout-rules/categories`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ category_slug: slug, payout_rate: rate, is_active: true }),
                });
                const data = await parseJsonResponse(res);
                if (!res.ok) throw new Error(data?.detail || "Failed to create rule");
                addToast("Category payout rule created", "success");
                setNewCatPayoutSlug("");
                setNewCatPayoutRate("0.80");
                loadPayoutRules(selectedCountryCode);
              } catch (err: any) {
                addToast(err.message, "error");
              }
            }}
          >
            Add Rule
          </Button>
        </div>

        {catPayoutRules.length > 0 && (
          <div className="space-y-1">
            {catPayoutRules.map((rule) => (
              <div key={rule.id} className="flex items-center justify-between rounded border border-border/50 bg-surface px-3 py-2 text-xs">
                <span className="font-medium text-text">{rule.category_slug}</span>
                <div className="flex items-center gap-3">
                  <span className="text-text-muted">Rate: <strong className="text-text">{(rule.payout_rate * 100).toFixed(1)}%</strong></span>
                  <button
                    type="button"
                    onClick={async () => {
                      try {
                        const res = await apiFetch(`/admin/countries/${selectedCountryCode}/payout-rules/categories/${rule.id}`, { method: "DELETE" });
                        if (!res.ok) throw new Error("Failed to delete");
                        addToast("Rule deleted", "success");
                        loadPayoutRules(selectedCountryCode);
                      } catch (err: any) {
                        addToast(err.message, "error");
                      }
                    }}
                    className="text-danger hover:text-danger/80 transition"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
        {catPayoutRules.length === 0 && (
          <p className="text-[10px] text-text-muted italic">No category-level payout overrides configured.</p>
        )}
      </div>

      <div className="pt-4 border-t border-border/60">
        <h4 className="text-xs font-bold text-text mb-2">Product-Level Payout Overrides</h4>
        <p className="text-[10px] text-text-muted mb-3">
          Override the payout rate for individual products.
          These take the highest precedence in the payout resolution chain.
        </p>

        <div className="flex items-center gap-2 mb-3">
          <input
            type="number"
            className="rounded border border-border bg-surface px-2 py-1.5 text-xs text-text w-28"
            placeholder="Product ID"
            value={newProdPayoutId}
            onChange={(e) => setNewProdPayoutId(e.target.value)}
          />
          <label className="text-[10px] text-text-muted flex items-center gap-1">
            Rate:
            <input
              type="number"
              step="0.01"
              min="0"
              max="1"
              className="w-16 rounded border border-border bg-surface px-1.5 py-1.5 text-xs text-text"
              value={newProdPayoutRate}
              onChange={(e) => setNewProdPayoutRate(e.target.value)}
            />
          </label>
          <Button variant="primary" className="rounded text-primary px-2.5 py-1.5 text-[10px] font-semibold transition" type="button"
            disabled={!newProdPayoutId || !newProdPayoutRate}
            onClick={async () => {
              const pid = Number(newProdPayoutId);
              const rate = Number(newProdPayoutRate);
              if (!pid || Number.isNaN(rate)) return;
              try {
                const res = await apiFetch(`/admin/countries/${selectedCountryCode}/payout-rules/products`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ product_id: pid, payout_rate: rate, is_active: true }),
                });
                const data = await parseJsonResponse(res);
                if (!res.ok) throw new Error(data?.detail || "Failed to create rule");
                addToast("Product payout rule created", "success");
                setNewProdPayoutId("");
                setNewProdPayoutRate("0.85");
                loadPayoutRules(selectedCountryCode);
              } catch (err: any) {
                addToast(err.message, "error");
              }
            }}
          >
            Add Rule
          </Button>
        </div>

        {prodPayoutRules.length > 0 && (
          <div className="space-y-1">
            {prodPayoutRules.map((rule) => (
              <div key={rule.id} className="flex items-center justify-between rounded border border-border/50 bg-surface px-3 py-2 text-xs">
                <span className="font-medium text-text">Product #{rule.product_id}</span>
                <div className="flex items-center gap-3">
                  <span className="text-text-muted">Rate: <strong className="text-text">{(rule.payout_rate * 100).toFixed(1)}%</strong></span>
                  <button
                    type="button"
                    onClick={async () => {
                      try {
                        const res = await apiFetch(`/admin/countries/${selectedCountryCode}/payout-rules/products/${rule.id}`, { method: "DELETE" });
                        if (!res.ok) throw new Error("Failed to delete");
                        addToast("Rule deleted", "success");
                        loadPayoutRules(selectedCountryCode);
                      } catch (err: any) {
                        addToast(err.message, "error");
                      }
                    }}
                    className="text-danger hover:text-danger/80 transition"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
        {prodPayoutRules.length === 0 && (
          <p className="text-[10px] text-text-muted italic">No product-level payout overrides configured.</p>
        )}
      </div>
    </section>
  );
}
