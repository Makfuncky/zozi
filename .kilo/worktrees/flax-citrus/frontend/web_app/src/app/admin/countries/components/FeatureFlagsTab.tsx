"use client";

import { Fragment } from "react";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Save, Trash2, Plus, Eye, UploadCloud, RefreshCw, Edit3, X, Check } from "@/lib/icons";
import type { CountriesTabProps } from "./CountriesTabProps";

export default function FeatureFlagsTab({
  ...p
}: CountriesTabProps) {
  const { addToast, countries, country, featureFlags, newFeatureEnabled, newFeatureKey, selectedCountryCode, setFeatureFlags, setNewFeatureEnabled, setNewFeatureKey } = p;

  return (
    <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
      <h3 className="text-sm font-bold text-text">Feature Flags & Platform Toggles</h3>
      <p className="text-xs text-text-muted">Enable or disable platform features per country (e.g., BNPL, AI Chatbot, COD).</p>

      <div className="space-y-3">
        {featureFlags.length === 0 ? (
          <p className="text-sm text-text-muted italic">No feature flags configured. Using default platform settings.</p>
        ) : (
          featureFlags.map((ff, idx) => (
            <div key={idx} className="flex items-center justify-between rounded-lg border border-border bg-surface p-3">
              <div>
                <span className="font-medium text-text">{ff.feature_key}</span>
                {ff.config && Object.keys(ff.config).length > 0 && (
                  <div className="text-[10px] text-text-faint mt-1">
                    Config: <span className="font-mono">{JSON.stringify(ff.config)}</span>
                  </div>
                )}
              </div>
              <label className="inline-flex items-center gap-2 text-xs font-semibold cursor-pointer">
                <input
                  type="checkbox"
                  checked={ff.enabled}
                  onChange={async (e) => {
                    const updated = [...featureFlags];
                    updated[idx].enabled = e.target.checked;
                    setFeatureFlags(updated);
                    // Auto-save on toggle
                    try {
                      await apiFetch(`/admin/countries/${selectedCountryCode}/feature-flags/${ff.feature_key}`, {
                        method: "PATCH",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ enabled: e.target.checked }),
                      });
                      addToast(`Feature flag updated`, "success");
                    } catch {
                      addToast("Failed to save feature flag", "error");
                    }
                  }}
                />
                Enabled
              </label>
            </div>
          ))
        )}
      </div>

      <div className="border-t border-border pt-4">
        <h4 className="text-xs font-bold text-text mb-2">Add New Feature Flag</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 items-end">
          <label className="space-y-1 text-[10px] text-text-muted">
            Feature Key
            <input
              type="text"
              className="w-full rounded border border-border bg-surface px-2 py-1 text-xs text-text"
              value={newFeatureKey}
              onChange={(e) => setNewFeatureKey(e.target.value)}
              placeholder="ai_chatbot"
            />
          </label>
          <div className="flex items-end pb-2">
            <label className="inline-flex items-center gap-1 text-xs font-semibold text-text cursor-pointer">
              <input type="checkbox" checked={newFeatureEnabled} onChange={(e) => setNewFeatureEnabled(e.target.checked)} />
              Enabled
            </label>
          </div>
          <button
            type="button"
            disabled={!newFeatureKey}
            onClick={async () => {
              try {
                const res = await apiFetch(`/admin/countries/${selectedCountryCode}/feature-flags`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ feature_key: newFeatureKey, enabled: newFeatureEnabled, config: {} }),
                });
                if (!res.ok) throw new Error("Failed to create");
                addToast("Feature flag created", "success");
                setNewFeatureKey("");
                setNewFeatureEnabled(true);
                if (res.ok) {
                  const data = await parseJsonResponse(res);
                  setFeatureFlags(Array.isArray(data) ? data : []);
                }
              } catch (err: any) {
                addToast(err.message, "error");
              }
            }}
            className="inline-flex h-8 items-center justify-center gap-1.5 rounded-lg border border-border bg-surface-2 px-3 text-xs font-semibold text-text hover:bg-surface-3 transition disabled:opacity-40"
          >
            <Plus className="h-3.5 w-3.5" />
            Add Flag
          </button>
        </div>
      </div>
    </section>
  );
}
