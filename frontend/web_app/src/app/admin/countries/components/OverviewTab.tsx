"use client";

import { Fragment } from "react";
import { Button } from "@/components/ui/Button";
import { Save, Trash2, Plus, Eye, UploadCloud, RefreshCw, Edit3, X, Check } from "@/lib/icons";
import type { CountriesTabProps } from "./CountriesTabProps";

export default function OverviewTab({
  ...p
}: CountriesTabProps) {
  const { busyAction, country, currencySymbol, isActive, language, name, phoneCode, submitIdentity, setCurrencySymbol, setIsActive, setLanguage, setName, setPhoneCode } = p;

  return (
  <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
    <h3 className="text-sm font-bold text-text">Overview & Identity</h3>
    <p className="text-xs text-text-muted">Configure the static identification details of this country (updates immediately on save).</p>

    <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
      <label className="space-y-1 text-xs text-text-muted">
        Display Name
        <input
          className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </label>
      <label className="space-y-1 text-xs text-text-muted">
        Currency Symbol
        <input
          className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text"
          value={currencySymbol}
          onChange={(e) => setCurrencySymbol(e.target.value)}
        />
      </label>
      <label className="space-y-1 text-xs text-text-muted">
        Phone Code
        <input
          className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text"
          value={phoneCode}
          onChange={(e) => setPhoneCode(e.target.value)}
        />
      </label>
      <label className="space-y-1 text-xs text-text-muted">
        Language
        <select
          className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text"
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
        >
          <option value="en">English (en)</option>
          <option value="ar">Arabic (ar)</option>
        </select>
      </label>
      <div className="flex items-end pb-2">
        <label className="inline-flex items-center gap-2 text-xs font-semibold text-text cursor-pointer">
          <input
            type="checkbox"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
          />
          Active / Enabled
        </label>
      </div>
    </div>

    <div className="flex justify-end pt-2">
      <Button variant="primary" type="button"
        onClick={submitIdentity}
        disabled={busyAction === "identity"}>
        <Save className="h-3.5 w-3.5" />
        {busyAction === "identity" ? "Updating..." : "Update Identity"}
      </Button>
    </div>
  </section>
  );
}
