"use client";

import { Fragment } from "react";
import { Button } from "@/components/ui/Button";
import { Save, Trash2, Plus, Eye, UploadCloud, RefreshCw, Edit3, X, Check } from "@/lib/icons";
import type { CountriesTabProps } from "./CountriesTabProps";

export default function CommissionTiersTab({
  ...p
}: CountriesTabProps) {
  const { selectedCountry, busyAction, canSubmit, commissionTiers, newTierFixed, newTierMax, newTierMin, newTierPct, submitCommissionTiersDraft, setCommissionTiers, setNewTierFixed, setNewTierMax, setNewTierMin, setNewTierPct } = p;

  return (
    <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
      <h3 className="text-sm font-bold text-text">Value-Based Commission Tiers</h3>
      <p className="text-xs text-text-muted">Configure order value thresholds where commission rates change based on target sales volume (overrides base category rates).</p>

      <div className="grid gap-2 grid-cols-2 md:grid-cols-5 items-end p-3 rounded-lg border border-border bg-surface">
        <label className="space-y-1 text-[10px] text-text-muted">
          Min Order Value ({selectedCountry?.currency})
          <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newTierMin} onChange={(e) => setNewTierMin(e.target.value)} />
        </label>
        <label className="space-y-1 text-[10px] text-text-muted">
          Max Order Value (Leave empty for &infin;)
          <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newTierMax} onChange={(e) => setNewTierMax(e.target.value)} placeholder="Unlimited" />
        </label>
        <label className="space-y-1 text-[10px] text-text-muted">
          Commission Percentage
          <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newTierPct} onChange={(e) => setNewTierPct(e.target.value)} />
        </label>
        <label className="space-y-1 text-[10px] text-text-muted">
          Fixed Transaction Fee
          <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newTierFixed} onChange={(e) => setNewTierFixed(e.target.value)} />
        </label>
        <button
          type="button"
          onClick={() => {
            const min = Number(newTierMin);
            const max = newTierMax.trim() ? Number(newTierMax) : null;
            const pct = Number(newTierPct);
            const fixed = Number(newTierFixed);
            if (Number.isNaN(min) || Number.isNaN(pct)) return;
            setCommissionTiers([
              ...commissionTiers,
              {
                min_order_value: min,
                max_order_value: max,
                commission_percentage: pct,
                fixed_fee: fixed
              }
            ]);
            setNewTierMin("0");
            setNewTierMax("");
          }}
          className="inline-flex h-9 items-center justify-center gap-1.5 rounded-lg border border-border bg-surface-2 px-3 text-xs font-semibold text-text hover:bg-surface-3 transition"
        >
          <Plus className="h-3.5 w-3.5" />
          Add Value Tier
        </button>
      </div>

      <div className="overflow-x-auto rounded-lg border border-border bg-surface mt-2">
        <table className="w-full border-collapse text-left text-xs">
          <thead className="bg-surface-2 text-text-muted">
            <tr>
              <th className="px-3 py-2 font-semibold">Order Volume Range</th>
              <th className="px-3 py-2 font-semibold">Commission Rate</th>
              <th className="px-3 py-2 font-semibold">Fixed Fee Override</th>
              <th className="px-3 py-2 font-semibold w-16 text-center">Action</th>
            </tr>
          </thead>
          <tbody>
            {commissionTiers.map((tier, idx) => (
              <tr key={idx} className="border-t border-border">
                <td className="px-3 py-2 text-text font-medium">
                  {tier.min_order_value.toFixed(2)} {selectedCountry?.currency} &ndash;{" "}
                  {tier.max_order_value != null ? `${tier.max_order_value.toFixed(2)} ${selectedCountry?.currency}` : "Unlimited"}
                </td>
                <td className="px-3 py-2 text-text font-bold text-primary">{tier.commission_percentage}%</td>
                <td className="px-3 py-2 text-text">{tier.fixed_fee.toFixed(2)} {selectedCountry?.currency}</td>
                <td className="px-3 py-2 text-center">
                  <Button variant="danger" className="p-1 rounded transition" type="button"
                    onClick={() => setCommissionTiers(commissionTiers.filter((_, i) => i !== idx))}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </td>
              </tr>
            ))}
            {commissionTiers.length === 0 && (
              <tr>
                <td colSpan={4} className="px-3 py-3 text-center text-text-faint italic">No value-based commission tiers created. Category commission rates will apply uniformly.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="flex justify-end pt-2">
        <Button variant="primary" type="button"
          onClick={submitCommissionTiersDraft}
          disabled={!canSubmit || busyAction === "commission_tiers"}>
          <Save className="h-3.5 w-3.5" />
          {busyAction === "commission_tiers" ? "Creating draft..." : "Save Commission Tiers Draft"}
        </Button>
      </div>
    </section>
  );
}
