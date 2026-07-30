"use client";

import { useEffect, useState, useCallback } from "react";
import { Plus, Tag, RefreshCw, Trash2 } from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { normalizeListPage } from "@/lib/listResponse";
import { dc, useDensity } from "@/lib/densityContext";
import { useCurrencyStore } from "@/lib/currencyStore";

interface AdminCoupon {
  id: number;
  code: string;
  discount_type: string;
  value: number;
  min_order: number;
  max_uses?: number;
  uses_count: number;
  expires_at?: string;
  is_active: boolean;
  created_at: string;
}

export default function CouponsTab() {
  const { density } = useDensity();
  const cellPad = dc(density, "p-2", "p-3", "p-4");
  const bodyText = dc(density, "text-[11px]", "text-xs", "text-sm");
  const formatMoney = useCurrencyStore((s) => s.format);
  const [coupons, setCoupons] = useState<AdminCoupon[]>([]);
  const [couponsLoading, setCouponsLoading] = useState(false);
  const [couponForm, setCouponForm] = useState({
    code: "", discount_type: "percent", value: "10",
    min_order: "0", max_uses: "", expires_at: "", is_active: true,
  });
  const [couponFormError, setCouponFormError] = useState("");
  const [couponSaving, setCouponSaving] = useState(false);
  const [showCouponForm, setShowCouponForm] = useState(false);

  const fetchCoupons = useCallback(async () => {
    setCouponsLoading(true);
    try {
      const res = await apiFetch("/admin/coupons");
      if (res.ok) {
        const raw = normalizeListPage<AdminCoupon>(await res.json());
        setCoupons(raw.data);
      }
    } catch {}
    setCouponsLoading(false);
  }, []);

  useEffect(() => { fetchCoupons(); }, [fetchCoupons]);

  const handleCreateCoupon = async () => {
    setCouponFormError("");
    if (!couponForm.code.trim()) { setCouponFormError("Code is required"); return; }
    setCouponSaving(true);
    try {
      const res = await apiFetch("/admin/coupons", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...couponForm,
          value: parseFloat(couponForm.value) || 0,
          min_order: parseFloat(couponForm.min_order) || 0,
          max_uses: couponForm.max_uses ? parseInt(couponForm.max_uses) : null,
        }),
      });
      if (res.ok) {
        setShowCouponForm(false);
        setCouponForm({ code: "", discount_type: "percent", value: "10", min_order: "0", max_uses: "", expires_at: "", is_active: true });
        fetchCoupons();
      } else {
        const err = await res.json().catch(() => ({}));
        setCouponFormError(err.detail || "Failed to create coupon");
      }
    } catch { setCouponFormError("Network error"); }
    setCouponSaving(false);
  };

  const handleDeleteCoupon = async (id: number) => {
    if (!confirm("Delete this coupon?")) return;
    try {
      const res = await apiFetch(`/admin/coupons/${id}`, { method: "DELETE" });
      if (res.ok) setCoupons((prev) => prev.filter((c) => c.id !== id));
    } catch {}
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xs font-bold text-text">Coupon Management</h2>
        <button
          onClick={() => setShowCouponForm((v) => !v)}
          className="theme-chip-warning flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-semibold transition-colors"
        >
          <Plus className="w-3.5 h-3.5" /> New Coupon
        </button>
      </div>

      {showCouponForm && (
        <div className="theme-card border rounded-xl p-5 mb-4">
          <h3 className="text-xs font-bold text-text mb-4 flex items-center gap-2">
            <Tag className="w-4 h-4 theme-status-warning" /> Create Coupon
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-text-muted mb-1">Code *</label>
              <input
                value={couponForm.code}
                onChange={(e) => setCouponForm({ ...couponForm, code: e.target.value.toUpperCase() })}
                placeholder="SAVE20"
                className="w-full px-3 py-2 rounded-xl theme-input border text-text text-xs font-mono focus:outline-none focus:border-primary"
              />
            </div>
            <div>
              <label className="block text-xs text-text-muted mb-1">Type</label>
              <select
                value={couponForm.discount_type}
                onChange={(e) => setCouponForm({ ...couponForm, discount_type: e.target.value })}
                className="w-full px-3 py-2 rounded-xl theme-input border text-text text-xs focus:outline-none focus:border-primary"
              >
                <option value="percent">Percentage (%)</option>
                <option value="fixed">Fixed Amount</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-text-muted mb-1">Value</label>
              <input
                type="number"
                value={couponForm.value}
                onChange={(e) => setCouponForm({ ...couponForm, value: e.target.value })}
                className="w-full px-3 py-2 rounded-xl theme-input border text-text text-xs focus:outline-none focus:border-primary"
              />
            </div>
            <div>
              <label className="block text-xs text-text-muted mb-1">Min Order Amount</label>
              <input
                type="number"
                value={couponForm.min_order}
                onChange={(e) => setCouponForm({ ...couponForm, min_order: e.target.value })}
                className="w-full px-3 py-2 rounded-xl theme-input border text-text text-xs focus:outline-none focus:border-primary"
              />
            </div>
            <div>
              <label className="block text-xs text-text-muted mb-1">Max Uses (optional)</label>
              <input
                type="number"
                value={couponForm.max_uses}
                onChange={(e) => setCouponForm({ ...couponForm, max_uses: e.target.value })}
                placeholder="Unlimited"
                className="w-full px-3 py-2 rounded-xl theme-input border text-text text-xs focus:outline-none focus:border-primary"
              />
            </div>
            <div>
              <label className="block text-xs text-text-muted mb-1">Expires At (optional)</label>
              <input
                type="datetime-local"
                value={couponForm.expires_at}
                onChange={(e) => setCouponForm({ ...couponForm, expires_at: e.target.value })}
                className="w-full px-3 py-2 rounded-xl theme-input border text-text text-xs focus:outline-none focus:border-primary"
              />
            </div>
          </div>
          {couponFormError && (
            <p className="mt-2 text-xs theme-status-danger">{couponFormError}</p>
          )}
          <div className="flex gap-2 mt-4">
            <button
              onClick={handleCreateCoupon}
              disabled={couponSaving}
              className="theme-btn-admin flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold disabled:opacity-50"
            >
              {couponSaving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
              Create
            </button>
            <button onClick={() => setShowCouponForm(false)} className="px-4 py-2 rounded-xl text-text-muted hover:text-text text-xs transition-colors">
              Cancel
            </button>
          </div>
        </div>
      )}

      {couponsLoading ? (
        <div className="space-y-2">{Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-14 rounded-xl bg-surface-2 animate-pulse" />
        ))}</div>
      ) : coupons.length === 0 ? (
        <p className="text-xs text-text-faint text-center py-8">No coupons yet. Create one above.</p>
      ) : (
        <div className="theme-card border rounded-xl overflow-hidden">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border">
                {["Code", "Type", "Value", "Uses", "Expires", "Active", ""].map((h) => (
                    <th key={h} className={`text-left ${cellPad} text-[10px] font-semibold text-text-faint`}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {coupons.map((c) => (
                <tr key={c.id} className="group border-b border-border/50 last:border-0">
                  <td className={`${cellPad} font-mono font-bold text-text`}>{c.code}</td>
                  <td className={`${cellPad} ${bodyText} text-text-muted capitalize`}>{c.discount_type}</td>
                  <td className={`${cellPad} ${bodyText} text-text`}>{c.discount_type === "percent" ? `${c.value}%` : formatMoney(Number(c.value) || 0)}</td>
                  <td className={`${cellPad} ${bodyText} text-text-muted`}>{c.uses_count}{c.max_uses ? `/${c.max_uses}` : ""}</td>
                  <td className={`${cellPad} ${bodyText} text-text-muted`}>{c.expires_at ? new Date(c.expires_at).toLocaleDateString() : "\u2014"}</td>
                  <td className={cellPad}>
                    <span className={`px-2 py-0.5 rounded-lg text-[10px] font-semibold ${c.is_active ? "theme-chip-success" : "theme-chip-muted"}`}>
                      {c.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className={`${cellPad} opacity-0 group-hover:opacity-100 transition-opacity`}>
                    <button onClick={() => handleDeleteCoupon(c.id)} className="theme-action-danger rounded p-1">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}


