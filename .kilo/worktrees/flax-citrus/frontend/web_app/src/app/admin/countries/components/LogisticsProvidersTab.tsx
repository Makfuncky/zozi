"use client";

import { Fragment } from "react";
import { Button } from "@/components/ui/Button";
import { Save, Trash2, Plus, Eye, UploadCloud, RefreshCw, Edit3, X, Check } from "@/lib/icons";
import type { CountriesTabProps } from "./CountriesTabProps";

export default function LogisticsProvidersTab({
  ...p
}: CountriesTabProps) {
  const { selectedCountry, busyAction, canSubmit, name, newProviderBaseRate, newProviderCurrency, newProviderId, newProviderName, newProviderPerKg, newProviderServiceAreas, newProviderSlaExp, newProviderSlaStd, providers, submitLogisticsProvidersDraft, setNewProviderBaseRate, setNewProviderCurrency, setNewProviderId, setNewProviderName, setNewProviderPerKg, setNewProviderServiceAreas, setNewProviderSlaExp, setNewProviderSlaStd, setProviders } = p;

  return (
    <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
      <h3 className="text-sm font-bold text-text">Delivery Partners & Logistics Integrations</h3>
      <p className="text-xs text-text-muted">Manage active global delivery providers (e.g. Aramex, SMSA, J&T) with standard SLAs and custom tier-pricing rules.</p>

      <div className="grid gap-2 grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 p-3 rounded-lg border border-border bg-surface">
        <label className="space-y-1 text-[10px] text-text-muted">
          Provider ID
          <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newProviderId} onChange={(e) => setNewProviderId(e.target.value)} placeholder="aramex" />
        </label>
        <label className="space-y-1 text-[10px] text-text-muted">
          Provider Name
          <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newProviderName} onChange={(e) => setNewProviderName(e.target.value)} placeholder="Aramex Express" />
        </label>
        <label className="space-y-1 text-[10px] text-text-muted">
          Standard SLA (Days)
          <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newProviderSlaStd} onChange={(e) => setNewProviderSlaStd(e.target.value)} placeholder="2-3" />
        </label>
        <label className="space-y-1 text-[10px] text-text-muted">
          Express SLA (Days)
          <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newProviderSlaExp} onChange={(e) => setNewProviderSlaExp(e.target.value)} placeholder="1" />
        </label>
        <label className="space-y-1 text-[10px] text-text-muted">
          Base Rate
          <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newProviderBaseRate} onChange={(e) => setNewProviderBaseRate(e.target.value)} />
        </label>
        <label className="space-y-1 text-[10px] text-text-muted">
          Per KG Rate
          <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newProviderPerKg} onChange={(e) => setNewProviderPerKg(e.target.value)} />
        </label>
        <label className="space-y-1 text-[10px] text-text-muted">
          Currency Override
          <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newProviderCurrency} onChange={(e) => setNewProviderCurrency(e.target.value)} placeholder="SAR" />
        </label>
        <label className="space-y-1 text-[10px] text-text-muted sm:col-span-2">
          Service Areas (comma-separated)
          <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newProviderServiceAreas} onChange={(e) => setNewProviderServiceAreas(e.target.value)} placeholder="riyadh, jeddah, dammam" />
        </label>
        <div className="flex items-end sm:col-span-4 lg:col-span-5 justify-end mt-2">
          <button
            type="button"
            onClick={() => {
              const pid = newProviderId.trim().toLowerCase();
              const pname = newProviderName.trim();
              if (!pid || !pname) return;
              setProviders([
                ...providers,
                {
                  provider_id: pid,
                  name: pname,
                  enabled: true,
                  service_areas: newProviderServiceAreas.split(",").map((s) => s.trim()).filter(Boolean),
                  sla_standard_days: newProviderSlaStd.trim(),
                  sla_express_days: newProviderSlaExp.trim(),
                  base_rate: Number(newProviderBaseRate) || 0,
                  per_kg_rate: Number(newProviderPerKg) || 0,
                  currency: newProviderCurrency.trim() || null
                }
              ]);
              setNewProviderId("");
              setNewProviderName("");
              setNewProviderServiceAreas("all_regions");
            }}
            className="inline-flex h-9 items-center justify-center gap-1.5 rounded-lg border border-border bg-surface-2 px-4 text-xs font-semibold text-text hover:bg-surface-3 transition"
          >
            <Plus className="h-3.5 w-3.5" />
            Add Integration Partner
          </button>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2 mt-2">
        {providers.map((prov, index) => (
          <div key={index} className="rounded-xl border border-border bg-surface p-3 space-y-2 relative shadow-sm hover:shadow transition">
            <div className="flex items-center justify-between">
              <div>
                <span className="font-bold text-text block text-sm">{prov.name}</span>
                <span className="text-[10px] font-mono text-text-faint uppercase">{prov.provider_id}</span>
              </div>
              <div className="flex items-center gap-2">
                <label className="inline-flex items-center gap-1 text-[11px] font-semibold text-text-muted cursor-pointer">
                  <input
                    type="checkbox"
                    checked={prov.enabled}
                    onChange={(e) => {
                      const updated = [...providers];
                      updated[index].enabled = e.target.checked;
                      setProviders(updated);
                    }}
                  />
                  Enabled
                </label>
                <Button variant="danger" className="p-1.5 rounded transition" type="button"
                  onClick={() => setProviders(providers.filter((_, i) => i !== index))}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs border-t border-border/60 pt-2">
              <div><span className="text-text-muted font-semibold">Standard SLA:</span> {prov.sla_standard_days} days</div>
              <div><span className="text-text-muted font-semibold">Express SLA:</span> {prov.sla_express_days} days</div>
              <div><span className="text-text-muted font-semibold">Base Rate:</span> {prov.base_rate} {prov.currency || selectedCountry?.currency}</div>
              <div><span className="text-text-muted font-semibold">Weight rate:</span> +{prov.per_kg_rate}/KG</div>
              <div className="col-span-2 max-w-full truncate">
                <span className="text-text-muted font-semibold">Service Coverage:</span> <span className="font-mono">{prov.service_areas.join(", ")}</span>
              </div>
            </div>
          </div>
        ))}
        {providers.length === 0 && (
          <div className="col-span-2 text-center py-6 text-text-faint italic border rounded-xl bg-surface">No external delivery partners integrated yet.</div>
        )}
      </div>

      <div className="flex justify-end pt-2">
        <Button variant="primary" type="button"
          onClick={submitLogisticsProvidersDraft}
          disabled={!canSubmit || busyAction === "logistics_providers"}>
          <Save className="h-3.5 w-3.5" />
          {busyAction === "logistics_providers" ? "Creating draft..." : "Save Delivery Partners Draft"}
        </Button>
      </div>
    </section>
  );
}
