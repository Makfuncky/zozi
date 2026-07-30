"use client";

import { Fragment } from "react";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Save, Trash2, Plus, Eye, UploadCloud, RefreshCw, Edit3, X, Check } from "@/lib/icons";
import type { CountriesTabProps } from "./CountriesTabProps";

export default function PromotionsTab({
  ...p
}: CountriesTabProps) {
  const { addToast, countries, country, name, newPromoMinOrder, newPromoName, newPromoSlug, newPromoType, newPromoValue, promotionRules, selectedCountry, selectedCountryCode, setNewPromoMinOrder, setNewPromoName, setNewPromoSlug, setNewPromoType, setNewPromoValue, setPromotionRules } = p;

  return (
    <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1" data-testid="country-promotions-panel">
      <h3 className="text-sm font-bold text-text">Promotion Rules & Discounts</h3>
      <p className="text-xs text-text-muted">Configure country-specific promotion rules and discount policies.</p>

      <div className="border border-border rounded-lg p-4 bg-surface space-y-3">
        <h4 className="text-xs font-bold text-text">Create New Promotion Rule</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <label className="space-y-1 text-[10px] text-text-muted">
            Slug (URL-safe ID)
            <input
              type="text"
              className="w-full rounded border border-border bg-surface px-2 py-1.5 text-xs text-text"
              value={newPromoSlug}
              onChange={(e) => setNewPromoSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '').replace(/-/g, '-').replace(/^-+|-+$/g, ''))}
              placeholder="summer-sale-2024"
            />
          </label>
          <label className="space-y-1 text-[10px] text-text-muted">
            Promotion Name
            <input
              type="text"
              className="w-full rounded border border-border bg-surface px-2 py-1.5 text-xs text-text"
              value={newPromoName}
              onChange={(e) => setNewPromoName(e.target.value)}
              placeholder="Summer Festival Sale"
            />
          </label>
          <label className="space-y-1 text-[10px] text-text-muted">
            Discount Type
            <select
              className="w-full rounded border border-border bg-surface px-2 py-1.5 text-xs text-text"
              value={newPromoType}
              onChange={(e) => setNewPromoType(e.target.value as "percentage" | "fixed")}
            >
              <option value="percentage">Percentage (%)</option>
              <option value="fixed">Fixed Amount</option>
            </select>
          </label>
          <label className="space-y-1 text-[10px] text-text-muted">
            Discount Value
            <input
              type="number"
              step="0.01"
              className="w-full rounded border border-border bg-surface px-2 py-1.5 text-xs text-text"
              value={newPromoValue}
              onChange={(e) => setNewPromoValue(e.target.value)}
              placeholder={newPromoType === "percentage" ? "10" : "50"}
            />
          </label>
          <label className="space-y-1 text-[10px] text-text-muted md:col-span-2">
            Minimum Order Value (Optional)
            <input
              type="number"
              step="0.01"
              className="w-full rounded border border-border bg-surface px-2 py-1.5 text-xs text-text"
              value={newPromoMinOrder}
              onChange={(e) => setNewPromoMinOrder(e.target.value)}
              placeholder="100.00"
            />
          </label>
          <div className="flex items-end">
            <Button variant="primary" className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold hover:opacity-90 transition disabled:opacity-40" type="button"
              disabled={!newPromoSlug || !newPromoName || !newPromoValue}
              onClick={async () => {
                if (!selectedCountryCode) return;
                try {
                  const res = await apiFetch(`/admin/countries/${selectedCountryCode}/promotions`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      slug: newPromoSlug,
                      name: newPromoName,
                      discount_type: newPromoType,
                      discount_value: Number(newPromoValue),
                      min_order_value: newPromoMinOrder ? Number(newPromoMinOrder) : null,
                      is_active: true,
                    }),
                  });
                  if (!res.ok) throw new Error("Failed to create promotion");
                  addToast("Promotion created", "success");
                  setNewPromoSlug("");
                  setNewPromoName("");
                  setNewPromoType("percentage");
                  setNewPromoValue("10");
                  setNewPromoMinOrder("");
                  if (res.ok) {
                    const data = await parseJsonResponse(res);
                    setPromotionRules(Array.isArray(data) ? data : []);
                  }
                } catch (err: any) {
                  addToast(err.message, "error");
                }
              }}
            >
              <Plus className="h-3.5 w-3.5" />
              Create Promotion
            </Button>
          </div>
        </div>
      </div>

      <div className="space-y-2">
        {promotionRules.length === 0 ? (
          <p className="text-sm text-text-muted italic">No promotion rules configured for this country.</p>
        ) : (
          <div className="space-y-2">
            {promotionRules.map((promo) => (
              <div key={promo.slug} className="rounded-lg border border-border bg-surface p-3 text-xs" data-testid={`promotion-rule-${promo.slug}`}>
                <div className="flex items-center justify-between">
                  <span className="font-medium text-text">{promo.name}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-text-muted">
                      {promo.discount_type === "percentage" 
                        ? `${promo.discount_value}% off` 
                        : `${promo.discount_value} ${selectedCountry?.currency} off`}
                    </span>
                    {promo.min_order_value && (
                      <span className="text-text-faint">
                        (min: {promo.min_order_value})
                      </span>
                    )}
                    <Button variant="danger" className="p-1 rounded transition" type="button"
                      onClick={async () => {
                        try {
                          await apiFetch(`/admin/countries/${selectedCountryCode}/promotions/${promo.slug}`, { method: "DELETE" });
                          addToast("Promotion deleted", "success");
                          setPromotionRules(promotionRules.filter(p => p.slug !== promo.slug));
                        } catch {
                          addToast("Failed to delete promotion", "error");
                        }
                      }}
                      title="Delete promotion"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
                <div className="text-text-faint mt-1 text-[10px]">
                  Slug: <span className="font-mono">{promo.slug}</span> | 
                  Type: <span className="font-mono">{promo.discount_type}</span> | 
                  Status: <span className={promo.is_active ? "text-success" : "text-danger"}>{promo.is_active ? "Active" : "Inactive"}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
