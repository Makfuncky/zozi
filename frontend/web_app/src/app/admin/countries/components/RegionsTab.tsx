"use client";

import { Fragment } from "react";
import { Button } from "@/components/ui/Button";
import { Save, Trash2, Plus, Eye, UploadCloud, RefreshCw, ChevronDown, ChevronRight, Edit3, X, Check } from "@/lib/icons";
import type { CountriesTabProps } from "./CountriesTabProps";

export default function RegionsTab({
  ...p
}: CountriesTabProps) {
  const { busyAction, canSubmit, cities, expandedRegions, name, newRegionCities, newRegionName, regions, submitRegionsDraft, setExpandedRegions, setNewRegionCities, setNewRegionName, setRegions } = p;

  return (
    <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
      <h3 className="text-sm font-bold text-text">Regions & Cities Coverage</h3>
      <p className="text-xs text-text-muted">Set up regional hubs and map specific cities inside this country's delivery footprint.</p>

      <div className="grid gap-2 sm:grid-cols-3 items-end p-3 rounded-lg border border-border bg-surface">
        <label className="space-y-1 text-[10px] text-text-muted">
          Region / Governorate Name
          <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newRegionName} onChange={(e) => setNewRegionName(e.target.value)} placeholder="e.g. Riyadh Province" />
        </label>
        <label className="space-y-1 text-[10px] text-text-muted">
          Cities (comma-separated list)
          <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newRegionCities} onChange={(e) => setNewRegionCities(e.target.value)} placeholder="Riyadh, Diriyah, Kharj" />
        </label>
        <button
          type="button"
          onClick={() => {
            const rname = newRegionName.trim();
            if (!rname) return;
            const rid = rname.toLowerCase().replace(/\s+/g, "_");
            const citiesArr = newRegionCities.split(",").map((c) => c.trim()).filter(Boolean);
            setRegions([
              ...regions,
              {
                region_id: rid,
                name: rname,
                cities: citiesArr
              }
            ]);
            setNewRegionName("");
            setNewRegionCities("");
          }}
          className="inline-flex h-9 items-center justify-center gap-1.5 rounded-lg border border-border bg-surface-2 px-3 text-xs font-semibold text-text hover:bg-surface-3 transition"
        >
          <Plus className="h-3.5 w-3.5" />
          Add Region Hub
        </button>
      </div>

      <div className="space-y-2 mt-2">
        {regions.map((reg, index) => {
          const isExpanded = expandedRegions[reg.region_id] ?? true;
          return (
            <div key={index} className="rounded-lg border border-border bg-surface overflow-hidden">
              <div className="flex items-center justify-between px-3 py-2 bg-surface-2">
                <button
                  type="button"
                  onClick={() => setExpandedRegions({ ...expandedRegions, [reg.region_id]: !isExpanded })}
                  className="flex items-center gap-2 text-xs font-bold text-text text-left"
                >
                  {isExpanded ? <ChevronDown className="h-4 w-4 shrink-0 text-text-muted" /> : <ChevronRight className="h-4 w-4 shrink-0 text-text-muted" />}
                  <span>{reg.name}</span>
                  <span className="text-[10px] text-text-faint font-mono font-normal">({reg.region_id})</span>
                  <span className="text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded font-normal">{reg.cities.length} cities</span>
                </button>
                <Button variant="danger" className="p-1 rounded transition" type="button"
                  onClick={() => setRegions(regions.filter((_, i) => i !== index))}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>

              {isExpanded && (
                <div className="p-3 text-xs border-t border-border/60">
                  <div className="flex flex-wrap gap-1">
                    {reg.cities.map((city, cidx) => (
                      <span key={cidx} className="inline-flex items-center gap-1 bg-surface-2 px-2 py-1 rounded border border-border font-mono text-[10px] text-text">
                        {city}
                        <button
                          type="button"
                          onClick={() => {
                            const updated = [...regions];
                            updated[index].cities = reg.cities.filter((_, i) => i !== cidx);
                            setRegions(updated);
                          }}
                          className="text-text-faint hover:text-danger transition"
                        >
                          &times;
                        </button>
                      </span>
                    ))}
                    <span className="inline-flex gap-1 items-center">
                      <input
                        type="text"
                        placeholder="Add city..."
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            const val = e.currentTarget.value.trim();
                            if (val && !reg.cities.includes(val)) {
                              const updated = [...regions];
                              updated[index].cities = [...reg.cities, val];
                              setRegions(updated);
                              e.currentTarget.value = "";
                            }
                          }
                        }}
                        className="border rounded bg-surface px-1.5 py-0.5 text-[10px] text-text w-24 outline-none"
                      />
                    </span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
        {regions.length === 0 && (
          <div className="text-center py-6 text-text-faint italic border rounded-lg bg-surface">No regions or hubs mapped. Add a region to setup regional logistics rules.</div>
        )}
      </div>

      <div className="flex justify-end pt-2">
        <Button variant="primary" type="button"
          onClick={submitRegionsDraft}
          disabled={!canSubmit || busyAction === "regions"}>
          <Save className="h-3.5 w-3.5" />
          {busyAction === "regions" ? "Creating draft..." : "Save Regions Draft"}
        </Button>
      </div>
    </section>
  );
}
