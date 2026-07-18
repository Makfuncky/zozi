"use client";

import { Button } from "@/components/ui/Button";

import { useCallback, useEffect, useState } from "react";
import SupplierLayout from "@/components/SupplierLayout";
import { PanelContent, PanelHero } from "@/components/PanelPage";
import { apiFetch, getErrorMessage, parseJsonResponse } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";
import { Globe2, Loader2, Plus, X } from "@/lib/icons";

type RegionsData = {
  operating_regions: string[];
  origin_country?: string | null;
  city?: string | null;
};

export default function SupplierRegionsPage() {
  const [data, setData] = useState<RegionsData | null>(null);
  const [draft, setDraft] = useState<string[]>([]);
  const [originCountry, setOriginCountry] = useState("");
  const [city, setCity] = useState("");
  const [newRegion, setNewRegion] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const addToast = useToastStore((state) => state.addToast);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const res = await apiFetch("/supplier/regions");
      const json = (await parseJsonResponse(res)) as RegionsData;
      if (!res.ok) {
        throw new Error(getErrorMessage(json || {}));
      }
      setData(json);
      setDraft(json.operating_regions ?? []);
      setOriginCountry(json.origin_country ?? "");
      setCity(json.city ?? "");
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Failed to load regions");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const addRegion = () => {
    const value = newRegion.trim();
    if (!value) return;
    if (draft.some((r) => r.toLowerCase() === value.toLowerCase())) {
      setNewRegion("");
      return;
    }
    setDraft((prev) => [...prev, value]);
    setNewRegion("");
  };

  const removeRegion = (region: string) => {
    setDraft((prev) => prev.filter((r) => r !== region));
  };

  const save = async () => {
    setSaving(true);
    try {
      const res = await apiFetch("/supplier/regions", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          operating_regions: draft,
          origin_country: originCountry,
          city,
        }),
      });
      const json = (await parseJsonResponse(res)) as RegionsData;
      if (!res.ok) {
        throw new Error(getErrorMessage(json || {}));
      }
      setData(json);
      setDraft(json.operating_regions ?? []);
      setOriginCountry(json.origin_country ?? "");
      setCity(json.city ?? "");
      addToast("Operating regions updated", "success");
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Failed to save regions", "error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <SupplierLayout title="Regions">
      <PanelContent width="wide">
        <PanelHero
          eyebrow="Account"
          title="Regions & Countries of Operation"
          description="Define where you ship from and the regions you serve. Buyers see your products based on these settings."
          icon={<Globe2 className="h-5 w-5" />}
        />

        {loading ? (
          <div className="theme-card rounded-xl border p-8 text-center text-xs text-text-muted">
            <Loader2 className="mx-auto h-5 w-5 animate-spin text-primary" />
            <p className="mt-2">Loading regions…</p>
          </div>
        ) : loadError ? (
          <div className="theme-card rounded-xl border border-danger/30 bg-danger/10 p-6 text-center">
            <p className="text-sm font-semibold text-text">{loadError}</p>
            <button
              onClick={() => void load()}
              className="theme-btn-primary mt-4 rounded-xl px-4 py-2 text-xs font-semibold"
            >
              Retry
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="theme-card rounded-xl border p-5">
                <label className="mb-1 block text-[11px] font-semibold uppercase tracking-[0.2em] text-text-faint">
                  Origin Country
                </label>
                <input
                  value={originCountry}
                  onChange={(e) => setOriginCountry(e.target.value)}
                  placeholder="e.g. EG"
                  className="theme-input h-10 w-full rounded-xl border px-3 text-sm"
                />
              </div>
              <div className="theme-card rounded-xl border p-5">
                <label className="mb-1 block text-[11px] font-semibold uppercase tracking-[0.2em] text-text-faint">
                  City
                </label>
                <input
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  placeholder="e.g. Cairo"
                  className="theme-input h-10 w-full rounded-xl border px-3 text-sm"
                />
              </div>
            </div>

            <div className="theme-card rounded-xl border p-5">
              <p className="text-sm font-semibold text-text">Operating Regions</p>
              <p className="mt-1 text-xs text-text-muted">
                Add the countries or regions you actively serve.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {draft.length === 0 ? (
                  <p className="text-xs text-text-faint">No regions configured yet.</p>
                ) : (
                  draft.map((region) => (
                    <span
                      key={region}
                      className="inline-flex items-center gap-1.5 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary"
                    >
                      {region}
                      <Button variant="primary" className="rounded-full p-0.5" type="button"
                        onClick={() => removeRegion(region)}
                        aria-label={`Remove ${region}`}
                      >
                        <X className="h-3 w-3" />
                      </Button>
                    </span>
                  ))
                )}
              </div>
              <div className="mt-4 flex items-center gap-2">
                <input
                  value={newRegion}
                  onChange={(e) => setNewRegion(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addRegion();
                    }
                  }}
                  placeholder="Add a country or region"
                  className="theme-input h-10 flex-1 rounded-xl border px-3 text-sm"
                />
                <button
                  type="button"
                  onClick={addRegion}
                  className="theme-btn-secondary inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-semibold"
                >
                  <Plus className="h-4 w-4" />
                  Add
                </button>
              </div>
            </div>

            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => void save()}
                disabled={saving}
                className="theme-btn-primary inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-xs font-semibold disabled:opacity-50"
              >
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                {saving ? "Saving…" : "Save Regions"}
              </button>
            </div>
          </div>
        )}
      </PanelContent>
    </SupplierLayout>
  );
}
