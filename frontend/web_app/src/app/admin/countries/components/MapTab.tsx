"use client";

import { Fragment } from "react";
import CountryMapView from "@/components/country/CountryMapView";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import { toErrorMessage, toNumberOrNull, formatIso } from "../constants";
import { Button } from "@/components/ui/Button";
import { Save, Trash2, Plus, Eye, UploadCloud, RefreshCw, Edit3, X, Check } from "@/lib/icons";
import type { CountriesTabProps } from "./CountriesTabProps";

export default function MapTab({
  ...p
}: CountriesTabProps) {
  const { addToast, busyAction, cities, countries, selectedCountryCode, setActivityMessage, setBusyAction, setCities } = p;

  return (
    <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
      <h3 className="text-sm font-bold text-text">Interactive Country Map</h3>
      <p className="text-xs text-text-muted">Visual management of cities and key locations. Click on the map to add new cities or select existing ones to edit.</p>

      <CountryMapView
        countryCode={selectedCountryCode}
        cities={cities}
        onCitiesChange={setCities}
      />

      <div className="flex justify-end pt-2">
        <Button variant="primary" className="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-semibold transition hover:opacity-90 disabled:opacity-60 shadow" type="button"
          onClick={async () => {
          if (!selectedCountryCode) return;
          setBusyAction("map");
          try {
            const response = await apiFetch(`/admin/countries/${selectedCountryCode}/cities`, {
              method: "PUT",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ cities }),
            });
            const data = await parseJsonResponse(response);
            if (!response.ok) {
              throw new Error(toErrorMessage(response.status, data, "Failed to save cities"));
            }
            addToast("Cities map saved", "success");
            setActivityMessage("Interactive map updated successfully.");
          } catch (error) {
            addToast(error instanceof Error ? error.message : "Failed to save cities", "error");
          } finally {
            setBusyAction(null);
          }
        }}
          disabled={busyAction === "map"}
          data-testid="save-cities-map-button"
        >
          <Save className="h-3.5 w-3.5" />
          {busyAction === "map" ? "Saving..." : "Save Map"}
        </Button>
      </div>
    </section>
  );
}
