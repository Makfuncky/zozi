"use client";

import { Button } from "@/components/ui/Button";

import { useState, useEffect } from "react";
import { Save, RefreshCw } from "@/lib/icons";
import { apiFetch, getErrorMessage, parseJsonResponse } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";

interface OverviewTabProps {
  countryCode: string;
  initialData: {
    name: string;
    currency_symbol: string | null;
    phone_code: string | null;
    language: string;
    is_active: boolean;
  };
  onSaved?: () => void;
}

export default function OverviewTab({ countryCode, initialData, onSaved }: OverviewTabProps) {
  const addToast = useToastStore((s) => s.addToast);
  const [name, setName] = useState(initialData.name);
  const [currencySymbol, setCurrencySymbol] = useState(initialData.currency_symbol || "");
  const [phoneCode, setPhoneCode] = useState(initialData.phone_code || "");
  const [language, setLanguage] = useState(initialData.language || "en");
  const [isActive, setIsActive] = useState(initialData.is_active);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setName(initialData.name);
    setCurrencySymbol(initialData.currency_symbol || "");
    setPhoneCode(initialData.phone_code || "");
    setLanguage(initialData.language || "en");
    setIsActive(initialData.is_active);
  }, [initialData]);

  const submit = async () => {
    setSaving(true);
    try {
      const res = await apiFetch(`/admin/countries/${countryCode}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          currency_symbol: currencySymbol.trim() || null,
          phone_code: phoneCode.trim() || null,
          language: language.trim() || "en",
          is_active: isActive,
        }),
      });
      const data = await parseJsonResponse(res);
      if (!res.ok) throw new Error(getErrorMessage(data) || "Failed to update");
      addToast("Country identity updated", "success");
      onSaved?.();
    } catch (err: any) {
      addToast(err.message, "error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
      <h3 className="text-sm font-bold text-text">Overview & Identity</h3>
      <p className="text-xs text-text-muted">Configure the static identification details of this country.</p>

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
            <option value="en">English</option>
            <option value="ar">Arabic</option>
            <option value="fr">French</option>
            <option value="es">Spanish</option>
            <option value="ur">Urdu</option>
          </select>
        </label>
        <label className="inline-flex items-center gap-2 text-xs font-semibold text-text cursor-pointer self-end pb-2">
          <input
            type="checkbox"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
          />
          Country Active
        </label>
      </div>

      <div className="flex justify-end">
        <Button variant="primary" type="button"
          onClick={submit}
          disabled={saving}>
          {saving ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
          Save Identity
        </Button>
      </div>
    </section>
  );
}
