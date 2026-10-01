"use client";

import { Fragment } from "react";
import { Button } from "@/components/ui/Button";
import { Save, Trash2, Plus, Eye, UploadCloud, RefreshCw, Edit3, X, Check } from "@/lib/icons";
import type { CountriesTabProps } from "./CountriesTabProps";

export default function CategoryCommissionsTab({
  ...p
}: CountriesTabProps) {
  const { allCategories, bulkFillRate, busyAction, canSubmit, categoryCommissions, name, newCategoryNotes, newCategoryRate, newCategorySlug, submitCategoryCommissionsDraft, setBulkFillRate, setCategoryCommissions, setNewCategoryNotes, setNewCategoryRate, setNewCategorySlug } = p;

  return (
    <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1" data-testid="country-commission-panel">
      <h3 className="text-sm font-bold text-text">Category Specific Commissions</h3>
      <p className="text-xs text-text-muted">Override base commission rates for specific category slugs (e.g. smartphones, fashion, home_appliances).</p>

      <div className="grid gap-2 grid-cols-2 md:grid-cols-4 items-end p-3 rounded-lg border border-border bg-surface">
        <label className="space-y-1 text-[10px] text-text-muted">
          Category
          <select
            className="w-full rounded border bg-surface px-2 py-1 text-xs text-text"
            value={newCategorySlug}
            onChange={(e) => setNewCategorySlug(e.target.value)}
          >
            <option value="">-- Select category --</option>
            {allCategories.map((cat) => (
              <option key={cat.id} value={cat.slug}>{cat.name} ({cat.slug})</option>
            ))}
          </select>
        </label>
        <label className="space-y-1 text-[10px] text-text-muted">
          Commission Rate (0 to 1)
          <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newCategoryRate} onChange={(e) => setNewCategoryRate(e.target.value)} />
        </label>
        <label className="space-y-1 text-[10px] text-text-muted md:col-span-2">
          Internal Notes
          <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newCategoryNotes} onChange={(e) => setNewCategoryNotes(e.target.value)} placeholder="Low margin category" />
        </label>
        <button
          type="button"
          onClick={() => {
            const slug = newCategorySlug.trim().toLowerCase();
            const rate = Number(newCategoryRate);
            if (!slug || Number.isNaN(rate)) return;
            setCategoryCommissions([
              ...categoryCommissions,
              {
                category_slug: slug,
                commission_rate: rate,
                notes: newCategoryNotes.trim() || null,
                is_active: true
              }
            ]);
            setNewCategorySlug("");
            setNewCategoryNotes("");
          }}
          className="inline-flex h-9 items-center justify-center gap-1.5 rounded-lg border border-border bg-surface-2 px-3 text-xs font-semibold text-text hover:bg-surface-3 transition"
        >
          <Plus className="h-3.5 w-3.5" />
          Add Category Rule
        </button>
      </div>

      {allCategories.length > 0 && (
        <div className="flex flex-wrap items-center gap-3 text-xs text-text-muted p-3 rounded-lg border border-border/60 bg-surface">
          <span>Total: <strong className="text-text">{allCategories.length}</strong></span>
          <span>Override: <strong className="text-text">{categoryCommissions.length}</strong></span>
          <span>Missing: <strong className="text-text">{allCategories.length - categoryCommissions.length}</strong></span>
          <span className="text-text-faint">
            Coverage: <strong className={categoryCommissions.length >= allCategories.length ? "text-success" : "text-warning"}>
              {allCategories.length > 0 ? ((categoryCommissions.length / allCategories.length) * 100).toFixed(0) : 0}%
            </strong>
          </span>
          <span className="ml-auto flex items-center gap-2">
            <span className="text-text-faint text-[10px]">Bulk fill missing:</span>
            <input
              type="number"
              step="0.01"
              min="0"
              max="1"
              value={bulkFillRate}
              onChange={(e) => setBulkFillRate(e.target.value)}
              className="w-16 rounded border border-border bg-surface px-1.5 py-1 text-xs text-text"
              placeholder="0.10"
            />
            <button
              type="button"
              onClick={() => {
                const rate = Number(bulkFillRate);
                if (Number.isNaN(rate) || rate < 0 || rate > 1) return;
                const existingSlugs = new Set(categoryCommissions.map((c) => c.category_slug));
                const newRates = allCategories
                  .filter((cat) => !existingSlugs.has(cat.slug))
                  .map((cat) => ({
                    category_slug: cat.slug,
                    commission_rate: rate,
                    notes: "Bulk default",
                    is_active: true,
                  }));
                setCategoryCommissions([...categoryCommissions, ...newRates]);
              }}
              className="rounded bg-primary/10 text-primary px-2 py-1 text-[10px] font-semibold hover:bg-primary/20 transition"
            >
              Apply
            </button>
          </span>
        </div>
      )}

      <div className="overflow-x-auto rounded-lg border border-border bg-surface mt-2">
        <table className="w-full border-collapse text-left text-xs">
          <thead className="bg-surface-2 text-text-muted">
            <tr>
              <th className="px-3 py-2 font-semibold">Category</th>
              <th className="px-3 py-2 font-semibold">Commission Rate</th>
              <th className="px-3 py-2 font-semibold">Internal Notes</th>
              <th className="px-3 py-2 font-semibold w-16 text-center">Action</th>
            </tr>
          </thead>
          <tbody>
            {categoryCommissions.map((row, idx) => {
              const cat = allCategories.find((c) => c.slug === row.category_slug);
              return (
              <tr key={idx} className="border-t border-border">
                <td className="px-3 py-2 text-text font-bold">{cat ? `${cat.name} ` : ""}<span className="font-mono text-text-muted">{row.category_slug}</span></td>
                <td className="px-3 py-2 text-text font-bold text-primary">{(row.commission_rate * 100).toFixed(1)}%</td>
                <td className="px-3 py-2 text-text-muted italic">{row.notes || "-"}</td>
                <td className="px-3 py-2 text-center">
                  <Button variant="danger" className="p-1 rounded transition" type="button"
                    onClick={() => setCategoryCommissions(categoryCommissions.filter((_, i) => i !== idx))}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </td>
              </tr>
            );
          })}
          {categoryCommissions.length === 0 && (
            <tr>
              <td colSpan={4} className="px-3 py-3 text-center text-text-faint italic">No custom category rates defined. Default store commission applies.</td>
            </tr>
          )}
          </tbody>
        </table>
      </div>

      <div className="flex justify-end pt-2">
        <Button variant="primary" type="button"
          onClick={submitCategoryCommissionsDraft}
          disabled={!canSubmit || busyAction === "category_commissions"}>
          <Save className="h-3.5 w-3.5" />
          {busyAction === "category_commissions" ? "Creating draft..." : "Save Category Commissions Draft"}
        </Button>
      </div>
    </section>
  );
}
