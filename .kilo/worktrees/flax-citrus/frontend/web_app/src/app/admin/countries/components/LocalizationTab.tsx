"use client";

import { Fragment } from "react";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Save, Trash2, Plus, Eye, UploadCloud, RefreshCw, Edit3, X, Check } from "@/lib/icons";
import type { CountriesTabProps } from "./CountriesTabProps";

export default function LocalizationTab({
  ...p
}: CountriesTabProps) {
  const { addToast, countries, country, language, localization, selectedCountryCode, setLocalization } = p;

  return (
    <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
      <h3 className="text-sm font-bold text-text">Localization & Regional Settings</h3>
      <p className="text-xs text-text-muted">Configure language, currency, and regional display settings for this country.</p>

      <div className="grid gap-4">
        <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
          <label className="space-y-1 text-xs text-text-muted">
            Default Language
            <select
              className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text"
              value={localization.default_language}
              onChange={(e) => setLocalization({ ...localization, default_language: e.target.value })}
            >
              <option value="en">English</option>
              <option value="ar">Arabic</option>
              <option value="fr">French</option>
              <option value="es">Spanish</option>
            </select>
          </label>
          <label className="space-y-1 text-xs text-text-muted">
            Number Format
            <select
              className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text"
              value={localization.number_format}
              onChange={(e) => setLocalization({ ...localization, number_format: e.target.value as any })}
            >
              <option value="western">Western (1,234.56)</option>
              <option value="eastern">Eastern (1٬234٫56)</option>
            </select>
          </label>
          <label className="space-y-1 text-xs text-text-muted">
            Calendar Type
            <select
              className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text"
              value={localization.calendar_type}
              onChange={(e) => setLocalization({ ...localization, calendar_type: e.target.value as any })}
            >
              <option value="gregorian">Gregorian</option>
              <option value="hijri">Hijri</option>
            </select>
          </label>
        </div>

        <div className="flex gap-4">
          <label className="flex items-center gap-2 text-xs font-semibold text-text cursor-pointer">
            <input
              type="checkbox"
              checked={localization.rtl_enabled}
              onChange={(e) => setLocalization({ ...localization, rtl_enabled: e.target.checked })}
            />
            Enable RTL Layout
          </label>
          <label className="flex items-center gap-2 text-xs font-semibold text-text cursor-pointer">
            <input
              type="checkbox"
              checked={localization.supported_languages.includes("ar")}
              onChange={(e) => {
                const langs = e.target.checked
                  ? [...localization.supported_languages, "ar"]
                  : localization.supported_languages.filter((l) => l !== "ar");
                setLocalization({ ...localization, supported_languages: langs });
              }}
            />
            Support Arabic
          </label>
        </div>

        <div className="text-[10px] text-text-muted">
          <div className="font-semibold mb-1">Supported Languages</div>
          <div className="flex flex-wrap gap-1">
            {localization.supported_languages.map((lang) => (
              <span key={lang} className="bg-surface-2 px-2 py-0.5 rounded font-mono">
                {lang === "en" ? "English" : lang === "ar" ? "Arabic" : lang === "fr" ? "French" : lang}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="flex justify-end pt-2">
        <Button variant="primary" className="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-semibold transition hover:opacity-90 shadow" type="button"
          onClick={async () => {
            try {
              const res = await apiFetch(`/admin/countries/${selectedCountryCode}/localization`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(localization),
              });
              if (!res.ok) throw new Error("Failed to save");
              addToast("Localization settings saved", "success");
            } catch (err: any) {
              addToast(err.message, "error");
            }
          }}
        >
          <Save className="h-3.5 w-3.5" />
          Save Localization
        </Button>
      </div>
    </section>
  );
}
