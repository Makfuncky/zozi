"use client";

import { Fragment } from "react";
import { Button } from "@/components/ui/Button";
import { Save, Trash2, Plus, Eye, UploadCloud, RefreshCw, Edit3, X, Check } from "@/lib/icons";
import type { CountriesTabProps } from "./CountriesTabProps";

export default function LegalRulesTab({
  ...p
}: CountriesTabProps) {
  const { busyAction, canSubmit, maxReturnsAllowed, minimumOrderAge, productRestrictions, refundProcessingDays, requiresCommercialLicense, requiresVatRegistration, returnWindowDays, submitLegalRulesDraft, setMaxReturnsAllowed, setMinimumOrderAge, setProductRestrictions, setRefundProcessingDays, setRequiresCommercialLicense, setRequiresVatRegistration, setReturnWindowDays } = p;

  return (
    <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
      <h3 className="text-sm font-bold text-text">Legal Constraints & Return Operations</h3>
      <p className="text-xs text-text-muted">General regulatory and legal requirements including minimum consumer age, refund timelines, and commercial registration rules.</p>

      <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-4">
        <label className="space-y-1 text-xs text-text-muted">
          Minimum Order Age
          <input type="number" className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={minimumOrderAge} onChange={(e) => setMinimumOrderAge(Number(e.target.value))} />
        </label>
        <label className="space-y-1 text-xs text-text-muted">
          Max Returns Allowed per Order
          <input type="number" className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={maxReturnsAllowed} onChange={(e) => setMaxReturnsAllowed(Number(e.target.value))} />
        </label>
        <label className="space-y-1 text-xs text-text-muted">
          Return Window (Days)
          <input type="number" className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={returnWindowDays} onChange={(e) => setReturnWindowDays(Number(e.target.value))} />
        </label>
        <label className="space-y-1 text-xs text-text-muted">
          Refund SLA (Processing Days)
          <input type="number" className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={refundProcessingDays} onChange={(e) => setRefundProcessingDays(Number(e.target.value))} />
        </label>
      </div>

      <div className="flex flex-wrap gap-4 pt-2">
        <label className="inline-flex items-center gap-2 text-xs font-semibold text-text cursor-pointer">
          <input type="checkbox" checked={requiresCommercialLicense} onChange={(e) => setRequiresCommercialLicense(e.target.checked)} />
          Requires valid Commercial Registration (CR) from Suppliers
        </label>
        <label className="inline-flex items-center gap-2 text-xs font-semibold text-text cursor-pointer">
          <input type="checkbox" checked={requiresVatRegistration} onChange={(e) => setRequiresVatRegistration(e.target.checked)} />
          Requires explicit VAT Certificate from Suppliers
        </label>
      </div>

      <label className="block space-y-1 text-xs text-text-muted">
        Restricted Products & Categories (comma-separated slugs to block import / sale)
        <input
          className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text"
          value={productRestrictions}
          onChange={(e) => setProductRestrictions(e.target.value)}
          placeholder="e.g. alcohol, tobacco, pork_products"
        />
      </label>

      <div className="flex justify-end pt-2">
        <Button variant="primary" type="button"
          onClick={submitLegalRulesDraft}
          disabled={!canSubmit || busyAction === "legal_rules"}>
          <Save className="h-3.5 w-3.5" />
          {busyAction === "legal_rules" ? "Creating draft..." : "Save Legal Rules Draft"}
        </Button>
      </div>
    </section>
  );
}
