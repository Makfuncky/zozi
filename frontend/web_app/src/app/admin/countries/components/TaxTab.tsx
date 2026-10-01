"use client";

import { Fragment } from "react";
import { Button } from "@/components/ui/Button";
import { Save, Trash2, Plus, Eye, UploadCloud, RefreshCw, Edit3, X, Check } from "@/lib/icons";
import type { CountriesTabProps } from "./CountriesTabProps";

export default function TaxTab({
  ...p
}: CountriesTabProps) {
  const { busyAction, canSubmit, newReducedCategory, newReducedRate, previewAmount, previewCategory, previewInclusive, previewResult, previewTax, reducedTaxRates, submitTaxDraft, taxExemptCategories, taxInclusive, taxName, taxRate, taxType, setNewReducedCategory, setNewReducedRate, setPreviewAmount, setPreviewCategory, setPreviewInclusive, setReducedTaxRates, setTaxExemptCategories, setTaxInclusive, setTaxName, setTaxRate, setTaxType } = p;

  return (
    <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1" data-testid="country-tax-panel">
      <h3 className="text-sm font-bold text-text">Tax & VAT Configuration</h3>
      <div className="grid gap-3 sm:grid-cols-3">
        <label className="space-y-1 text-xs text-text-muted">
          Tax Type
          <input className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={taxType} onChange={(event) => setTaxType(event.target.value)} />
        </label>
        <label className="space-y-1 text-xs text-text-muted">
          Tax Rate (0 to 1)
          <input className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={taxRate} onChange={(event) => setTaxRate(event.target.value)} />
        </label>
        <label className="space-y-1 text-xs text-text-muted">
          Tax Name
          <input className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={taxName} onChange={(event) => setTaxName(event.target.value)} />
        </label>
      </div>

      <label className="inline-flex items-center gap-2 text-xs font-semibold text-text cursor-pointer">
        <input type="checkbox" checked={taxInclusive} onChange={(event) => setTaxInclusive(event.target.checked)} />
        Tax is inclusive in retail prices
      </label>

      <label className="block space-y-1 text-xs text-text-muted">
        Tax Exempt Categories (comma-separated slugs)
        <input
          className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text"
          value={taxExemptCategories}
          onChange={(event) => setTaxExemptCategories(event.target.value)}
          placeholder="books, medicine, exports"
        />
      </label>

      <div className="space-y-2">
        <span className="block text-xs font-semibold text-text-muted">Reduced Tax Rates by Category</span>
        <div className="grid gap-2 sm:grid-cols-3 items-end">
          <label className="space-y-1 text-[11px] text-text-muted">
            Category Slug
            <input
              className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text"
              value={newReducedCategory}
              onChange={(e) => setNewReducedCategory(e.target.value)}
              placeholder="e.g. basic_foods"
            />
          </label>
          <label className="space-y-1 text-[11px] text-text-muted">
            Rate (0 to 1)
            <input
              className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text"
              value={newReducedRate}
              onChange={(e) => setNewReducedRate(e.target.value)}
              placeholder="0.05"
            />
          </label>
          <button
            type="button"
            onClick={() => {
              const cat = newReducedCategory.trim().toLowerCase();
              const r = newReducedRate.trim();
              if (cat && r) {
                setReducedTaxRates([...reducedTaxRates, { category: cat, rate: r }]);
                setNewReducedCategory("");
              }
            }}
            className="inline-flex h-9 items-center justify-center gap-1.5 rounded-lg border border-border bg-surface px-3 text-xs font-semibold text-text hover:bg-surface-2"
          >
            <Plus className="h-3.5 w-3.5" />
            Add Category Rate
          </button>
        </div>

        <div className="overflow-x-auto rounded-lg border border-border mt-2 bg-surface">
          <table className="w-full border-collapse text-left text-xs">
            <thead className="bg-surface-2 text-text-muted">
              <tr>
                <th className="px-3 py-2 font-semibold">Category Slug</th>
                <th className="px-3 py-2 font-semibold">Reduced Rate</th>
                <th className="px-3 py-2 font-semibold w-16 text-center">Action</th>
              </tr>
            </thead>
            <tbody>
              {reducedTaxRates.map((item, idx) => (
                <tr key={idx} className="border-t border-border">
                  <td className="px-3 py-2 text-text font-mono">{item.category}</td>
                  <td className="px-3 py-2 text-text font-medium">{(Number(item.rate) * 100).toFixed(1)}% ({item.rate})</td>
                  <td className="px-3 py-2 text-center">
                    <Button variant="danger" className="p-1 rounded transition" type="button"
                      onClick={() => setReducedTaxRates(reducedTaxRates.filter((_, i) => i !== idx))}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </td>
                </tr>
              ))}
              {reducedTaxRates.length === 0 && (
                <tr>
                  <td colSpan={3} className="px-3 py-3 text-center text-text-faint italic">No reduced categories defined.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid gap-3 rounded-lg border border-border bg-surface p-3 md:grid-cols-4">
        <label className="space-y-1 text-[11px] text-text-muted">
          Preview Price Amount
          <input
            className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text"
            value={previewAmount}
            onChange={(event) => setPreviewAmount(event.target.value)}
          />
        </label>
        <label className="space-y-1 text-[11px] text-text-muted">
          Preview Category Slug
          <input
            className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text"
            value={previewCategory}
            onChange={(event) => setPreviewCategory(event.target.value)}
            placeholder="e.g. food"
          />
        </label>
        <label className="space-y-1 text-[11px] text-text-muted">
          Pricing Mode
          <select
            className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text"
            value={previewInclusive}
            onChange={(event) => setPreviewInclusive(event.target.value as "auto" | "inclusive" | "exclusive")}
          >
            <option value="auto">Auto (Default)</option>
            <option value="inclusive">Inclusive</option>
            <option value="exclusive">Exclusive</option>
          </select>
        </label>
        <div className="flex items-end">
          <button
            type="button"
            onClick={previewTax}
            className="inline-flex h-9 w-full items-center justify-center gap-2 rounded-lg border border-border bg-surface px-3 text-xs font-semibold text-text transition hover:bg-surface-2"
            disabled={!canSubmit || busyAction === "tax-preview"}
            data-testid="preview-tax-button"
          >
            <Eye className="h-3.5 w-3.5" />
            {busyAction === "tax-preview" ? "Previewing..." : "Simulate VAT"}
          </button>
        </div>
      </div>

      {previewResult ? (
        <div className="rounded-lg border border-border bg-surface p-3 text-xs text-text grid grid-cols-2 gap-2" data-testid="tax-preview-result">
          <div><span className="font-semibold text-text-muted">Tax Applied:</span> {previewResult.tax_name}</div>
          <div><span className="font-semibold text-text-muted">Rate Applied:</span> {(previewResult.tax_rate * 100).toFixed(1)}%</div>
          <div><span className="font-semibold text-text-muted">Tax Amount:</span> {previewResult.tax_amount.toFixed(2)} {previewResult.currency}</div>
          <div><span className="font-semibold text-text-muted">Net Price:</span> {previewResult.net_amount.toFixed(2)} {previewResult.currency}</div>
          <div className="col-span-2 border-t border-border pt-1 font-bold text-primary">
            Total Checkout Price: {previewResult.total_amount.toFixed(2)} {previewResult.currency}
          </div>
        </div>
      ) : null}

      <div className="flex justify-end pt-2">
        <Button variant="primary" type="button"
          onClick={submitTaxDraft}
          disabled={!canSubmit || busyAction === "tax"}
          data-testid="create-tax-draft-button">
          <Save className="h-3.5 w-3.5" />
          {busyAction === "tax" ? "Creating draft..." : "Save Tax Draft"}
        </Button>
      </div>
    </section>
  );
}
