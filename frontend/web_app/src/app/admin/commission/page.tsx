"use client";

import { useEffect, useState, useCallback } from "react";
import { Percent, RefreshCw, TrendingUp, Search, Users, ShoppingCart, DollarSign, Shield, Plus, X, Edit3 } from "@/lib/icons";
import { useAuth } from "@/lib/useAuth";
import { isAdminStaffRole } from "@shared/adminPermissions";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelLoadingState, PanelTabs } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useAdminCountry } from "@/lib/useAdminCountry";

interface CommissionConfig {
  id: number;
  default_rate: number;
  low_value_threshold?: number;
  fixed_cap_amount?: number;
  fixed_cap_enabled?: boolean;
  margin_threshold?: number;
  is_active?: boolean;
}

interface SupplierCommission {
  supplier_id: number;
  supplier_name?: string;
  current_rate: number;
  combined_default_rate: number;
  total_earned: number;
  total_orders: number;
}

interface CategoryRate {
  id: number;
  category_slug: string;
  category_display_name?: string;
  rate: number;
  is_active: boolean;
  notes?: string;
  country_code: string;
}

interface BadgeTier {
  id: number;
  badge_level: string;
  commission_rate: number;
  min_fulfilled_orders?: number;
  is_active: boolean;
}

type TabKey = "overview" | "category-rates" | "badge-tiers";

export default function CommissionPage() {
  const { user, isLoggedIn, isLoading } = useAuth();
  const role = user?.role ?? null;
  const formatMoney = useCurrencyStore((s) => s.format);
  const { selectedCountry, isGlobalView } = useAdminCountry();
  const countryCode = isGlobalView || !selectedCountry?.code ? null : selectedCountry.code;

  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [globalConfig, setGlobalConfig] = useState<CommissionConfig | null>(null);
  const [suppliers, setSuppliers] = useState<SupplierCommission[]>([]);
  const [categoryRates, setCategoryRates] = useState<CategoryRate[]>([]);
  const [badgeTiers, setBadgeTiers] = useState<BadgeTier[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  // Category rate form
  const [showAddRate, setShowAddRate] = useState(false);
  const [rateForm, setRateForm] = useState({ category_slug: "", category_display_name: "", rate: 0.05, is_active: true });
  const [editingRateId, setEditingRateId] = useState<number | null>(null);
  const [savingRate, setSavingRate] = useState(false);

  // Badge tier form
  const [showAddTier, setShowAddTier] = useState(false);
  const [tierForm, setTierForm] = useState({ badge_level: "", commission_rate: 0.05, min_fulfilled_orders: 0, is_active: true });
  const [editingTierId, setEditingTierId] = useState<number | null>(null);
  const [savingTier, setSavingTier] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      if (!countryCode || isGlobalView) {
        const [globalRes, suppliersRes] = await Promise.all([
          apiFetch("/commission/global"),
          apiFetch("/commission/suppliers"),
        ]);
        if (globalRes.ok) setGlobalConfig(await globalRes.json());
        if (suppliersRes.ok) {
          const data = await suppliersRes.json();
          setSuppliers(Array.isArray(data) ? data : data.items ?? []);
        }
      }

      if (countryCode) {
        const [ratesRes, tiersRes] = await Promise.all([
          apiFetch(`/admin/${countryCode}/rates`),
          apiFetch(`/admin/${countryCode}/badge-tiers`),
        ]);
        if (ratesRes.ok) {
          const data = await ratesRes.json();
          setCategoryRates(Array.isArray(data) ? data : []);
        }
        if (tiersRes.ok) {
          const data = await tiersRes.json();
          setBadgeTiers(Array.isArray(data) ? data : []);
        }
      }
    } catch (err) {
      console.error("Failed to load commission data:", err);
    } finally {
      setLoading(false);
    }
  }, [countryCode, isGlobalView]);

  useEffect(() => {
    if (isLoading) return;
    if (!isLoggedIn || !isAdminStaffRole(role)) return;
    fetchData();
  }, [isLoading, isLoggedIn, role, fetchData]);

  const saveCategoryRate = async () => {
    if (!rateForm.category_slug || !countryCode) return;
    setSavingRate(true);
    try {
      const method = editingRateId ? "PUT" : "POST";
      const url = editingRateId
        ? `/admin/${countryCode}/rates/${editingRateId}`
        : `/admin/${countryCode}/rates`;
      const res = await apiFetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(rateForm),
      });
      if (res.ok) {
        setShowAddRate(false);
        setEditingRateId(null);
        setRateForm({ category_slug: "", category_display_name: "", rate: 0.05, is_active: true });
        fetchData();
      }
    } finally {
      setSavingRate(false);
    }
  };

  const saveBadgeTier = async () => {
    if (!tierForm.badge_level || !countryCode) return;
    setSavingTier(true);
    try {
      const method = editingTierId ? "PUT" : "POST";
      const url = editingTierId
        ? `/admin/${countryCode}/badge-tiers/${editingTierId}`
        : `/admin/${countryCode}/badge-tiers`;
      const res = await apiFetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(tierForm),
      });
      if (res.ok) {
        setShowAddTier(false);
        setEditingTierId(null);
        setTierForm({ badge_level: "", commission_rate: 0.05, min_fulfilled_orders: 0, is_active: true });
        fetchData();
      }
    } finally {
      setSavingTier(false);
    }
  };

  if (isLoading || !isLoggedIn || !isAdminStaffRole(role)) {
    return <AdminLayout title="Commission"><PanelLoadingState count={3} /></AdminLayout>;
  }

  const filteredSuppliers = suppliers.filter((s) =>
    !search.trim() || [String(s.supplier_id), s.supplier_name].some((v) => v?.toLowerCase().includes(search.toLowerCase()))
  );

  const totalEarned = suppliers.reduce((s, c) => s + (c.total_earned || 0), 0);
  const totalOrders = suppliers.reduce((s, c) => s + (c.total_orders || 0), 0);

  const tabs = [
    { key: "overview", label: "Overview", icon: TrendingUp },
    { key: "category-rates", label: "Category Rates", icon: Percent },
    { key: "badge-tiers", label: "Badge Tiers", icon: Shield },
  ];

  return (
    <AdminLayout title="Commission Management" headerMode="compact">
      <PanelContent className="space-y-4">
        <div className="flex items-center gap-2 text-[11px] text-text-faint bg-surface-2 rounded-lg px-3 py-1.5">
          <Shield className="h-3 w-3" />
          <span>{isGlobalView ? "Global View — All Countries" : `Country: ${selectedCountry?.name || selectedCountry?.code}`}</span>
        </div>

        <div className="theme-card rounded-xl border p-2">
          <PanelTabs items={tabs} value={activeTab} onChange={(v) => setActiveTab(v as TabKey)} className="border-0 bg-transparent p-0" />
        </div>

        {activeTab === "overview" && (
          <>
            {countryCode && (
              <div className="theme-card rounded-xl border p-4">
                <h3 className="text-sm font-bold text-text mb-3 flex items-center gap-2">
                  <Percent className="h-4 w-4 text-primary" />
                  Global Commission Configuration
                </h3>
                {globalConfig ? (
                  <div className="grid gap-4 sm:grid-cols-4">
                    <div>
                      <p className="text-[10px] text-text-faint uppercase">Default Rate</p>
                      <p className="text-lg font-bold text-text">{((globalConfig.default_rate ?? 0) * 100).toFixed(1)}%</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-text-faint uppercase">Min Order</p>
                      <p className="text-lg font-bold text-text">{formatMoney(globalConfig.low_value_threshold || 0)}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-text-faint uppercase">Max Cap</p>
                      <p className="text-lg font-bold text-text">{globalConfig.fixed_cap_amount ? formatMoney(globalConfig.fixed_cap_amount) : "Unlimited"}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-text-faint uppercase">Status</p>
                      <span className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold ${(globalConfig.is_active ?? true) ? "bg-success/20 text-success" : "bg-danger/20 text-danger"}`}>
                        {(globalConfig.is_active ?? true) ? "Active" : "Inactive"}
                      </span>
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-text-muted">No global configuration set</p>
                )}
              </div>
            )}

            <div className="grid gap-3 sm:grid-cols-3">
              <div className="theme-card rounded-xl border p-3">
                <div className="flex items-center gap-2 mb-1">
                  <Users className="h-4 w-4 text-primary" />
                  <span className="text-[10px] text-text-faint uppercase">Suppliers</span>
                </div>
                <p className="text-xl font-bold text-text">{suppliers.length}</p>
              </div>
              <div className="theme-card rounded-xl border p-3">
                <div className="flex items-center gap-2 mb-1">
                  <ShoppingCart className="h-4 w-4 text-warning" />
                  <span className="text-[10px] text-text-faint uppercase">Total Orders</span>
                </div>
                <p className="text-xl font-bold text-text">{totalOrders}</p>
              </div>
              <div className="theme-card rounded-xl border p-3">
                <div className="flex items-center gap-2 mb-1">
                  <DollarSign className="h-4 w-4 text-success" />
                  <span className="text-[10px] text-text-faint uppercase">Commission Earned</span>
                </div>
                <p className="text-xl font-bold text-text">{formatMoney(totalEarned)}</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div className="relative flex-1 max-w-xs">
                <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3 w-3 -translate-y-1/2 text-text-faint" />
                <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search suppliers..." className="w-full rounded-lg border border-border bg-surface-2 py-1.5 pl-8 pr-3 text-xs text-text" />
              </div>
              <button onClick={fetchData} className="rounded-lg border border-border bg-surface-2 px-2.5 py-1.5 text-xs text-text-faint hover:bg-surface-3">
                <RefreshCw className="h-3 w-3" />
              </button>
            </div>

            {loading ? <PanelLoadingState count={4} /> : filteredSuppliers.length === 0 ? (
              <div className="theme-card rounded-xl border p-8 text-center text-text-muted">
                <Percent className="h-8 w-8 mx-auto mb-2 opacity-40" />
                <p className="text-sm">No commission data found</p>
              </div>
            ) : (
              <div className="theme-card rounded-xl border overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-surface-2 border-b border-border">
                    <tr>
                      <th className="text-left p-2 font-semibold text-[11px]">Supplier</th>
                      <th className="text-right p-2 font-semibold text-[11px]">Rate</th>
                      <th className="text-right p-2 font-semibold text-[11px]">Effective Rate</th>
                      <th className="text-right p-2 font-semibold text-[11px]">Total Earned</th>
                      <th className="text-right p-2 font-semibold text-[11px]">Orders</th>
                    </tr>
                  </thead>
                  <tbody>
                        {filteredSuppliers.map((s) => (
                          <tr key={s.supplier_id} className="border-b border-border last:border-0 hover:bg-surface-1/50">
                            <td className="p-2 font-medium">{s.supplier_name || `Supplier #${s.supplier_id}`}</td>
                            <td className="p-2 text-right">{((s.current_rate ?? 0) * 100).toFixed(1)}%</td>
                            <td className="p-2 text-right">{((s.combined_default_rate ?? 0) * 100).toFixed(1)}%</td>
                            <td className="p-2 text-right font-semibold">{formatMoney(s.total_earned || 0)}</td>
                            <td className="p-2 text-right">{s.total_orders || 0}</td>
                          </tr>
                        ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}

        {activeTab === "category-rates" && (
          <div className="space-y-4">
            {!countryCode ? (
              <div className="p-8 text-center text-text-muted border border-dashed rounded-xl">
                <Shield className="h-8 w-8 mx-auto mb-2 opacity-40" />
                <p>Select a country to manage category rates</p>
              </div>
            ) : (
              <>
                <div className="flex justify-end">
                  <button onClick={() => { setShowAddRate(true); setEditingRateId(null); setRateForm({ category_slug: "", category_display_name: "", rate: 0.05, is_active: true }); }}
                    className="theme-btn-primary inline-flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-semibold">
                    <Plus className="h-3.5 w-3.5" /> Add Category Rate
                  </button>
                </div>

                <div className="theme-card rounded-xl border overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-surface-2 border-b border-border">
                      <tr>
                        <th className="text-left p-2 font-semibold text-[11px]">Category</th>
                        <th className="text-right p-2 font-semibold text-[11px]">Rate</th>
                        <th className="text-center p-2 font-semibold text-[11px]">Active</th>
                        <th className="text-right p-2 font-semibold text-[11px]">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                        {categoryRates.map((r) => (
                          <tr key={r.id} className="border-b border-border last:border-0 hover:bg-surface-1/50">
                            <td className="p-2 font-medium">{r.category_display_name || r.category_slug}</td>
                            <td className="p-2 text-right">{((r.rate ?? 0) * 100).toFixed(1)}%</td>
                            <td className="p-2 text-center">
                              <span className={`inline-block w-2 h-2 rounded-full ${r.is_active ? "bg-success" : "bg-text-faint"}`} />
                            </td>
                            <td className="p-2 text-right">
                               <button onClick={() => { setEditingRateId(r.id); setRateForm({ category_slug: r.category_slug || "", category_display_name: r.category_display_name || "", rate: r.rate ?? 0.05, is_active: r.is_active }); setShowAddRate(true); }} className="text-text-faint hover:text-text p-1"><Edit3 className="h-3.5 w-3.5" /></button>
                            </td>
                          </tr>
                        ))}
                      {categoryRates.length === 0 && (
                        <tr><td colSpan={4} className="p-4 text-center text-text-muted text-xs">No category rates configured</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>

                {showAddRate && (
                  <div className="theme-overlay fixed inset-0 z-50 flex items-center justify-center p-4">
                    <div className="theme-card w-full max-w-md rounded-2xl border p-6">
                      <h3 className="text-sm font-bold text-text mb-4">{editingRateId ? "Edit" : "Add"} Category Rate</h3>
                      <div className="space-y-3">
                        <label className="block"><span className="text-xs text-text-muted">Category Slug *</span>
                          <input value={rateForm.category_slug} onChange={(e) => setRateForm({ ...rateForm, category_slug: e.target.value })}
                            className="theme-input w-full rounded-xl border px-3 py-2 text-xs mt-1" /></label>
                        <label className="block"><span className="text-xs text-text-muted">Display Name</span>
                          <input value={rateForm.category_display_name} onChange={(e) => setRateForm({ ...rateForm, category_display_name: e.target.value })}
                            className="theme-input w-full rounded-xl border px-3 py-2 text-xs mt-1" /></label>
                        <label className="block"><span className="text-xs text-text-muted">Rate (decimal) *</span>
                          <input type="number" step="0.01" value={rateForm.rate} onChange={(e) => setRateForm({ ...rateForm, rate: parseFloat(e.target.value) || 0 })}
                            className="theme-input w-full rounded-xl border px-3 py-2 text-xs mt-1" /></label>
                        <label className="flex items-center gap-2 text-xs text-text-muted">
                          <input type="checkbox" checked={rateForm.is_active} onChange={(e) => setRateForm({ ...rateForm, is_active: e.target.checked })} className="accent-primary" />
                          Active
                        </label>
                      </div>
                      <div className="flex gap-2 mt-4 justify-end">
                        <button onClick={() => setShowAddRate(false)} className="theme-btn-secondary rounded-xl px-3 py-2 text-xs">Cancel</button>
                        <button onClick={saveCategoryRate} disabled={savingRate || !rateForm.category_slug} className="theme-btn-primary rounded-xl px-3 py-2 text-xs">{savingRate ? "Saving..." : "Save"}</button>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {activeTab === "badge-tiers" && (
          <div className="space-y-4">
            {!countryCode ? (
              <div className="p-8 text-center text-text-muted border border-dashed rounded-xl">
                <Shield className="h-8 w-8 mx-auto mb-2 opacity-40" />
                <p>Select a country to manage badge tiers</p>
              </div>
            ) : (
              <>
                <div className="flex justify-end">
                  <button onClick={() => { setShowAddTier(true); setEditingTierId(null); setTierForm({ badge_level: "", commission_rate: 0.05, min_fulfilled_orders: 0, is_active: true }); }}
                    className="theme-btn-primary inline-flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-semibold">
                    <Plus className="h-3.5 w-3.5" /> Add Badge Tier
                  </button>
                </div>

                <div className="theme-card rounded-xl border overflow-hidden">
                  <table className="w-full text-sm">
                      <thead className="bg-surface-2 border-b border-border">
                        <tr>
                          <th className="text-left p-2 font-semibold text-[11px]">Badge Level</th>
                          <th className="text-right p-2 font-semibold text-[11px]">Commission Rate</th>
                          <th className="text-right p-2 font-semibold text-[11px]">Min Orders</th>
                          <th className="text-center p-2 font-semibold text-[11px]">Active</th>
                          <th className="text-right p-2 font-semibold text-[11px]">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {badgeTiers.map((t) => (
                          <tr key={t.id} className="border-b border-border last:border-0 hover:bg-surface-1/50">
                            <td className="p-2 font-medium">{t.badge_level}</td>
                            <td className="p-2 text-right">{(t.commission_rate * 100).toFixed(1)}%</td>
                            <td className="p-2 text-right">{t.min_fulfilled_orders || 0}</td>
                            <td className="p-2 text-center">
                              <span className={`inline-block w-2 h-2 rounded-full ${t.is_active ? "bg-success" : "bg-text-faint"}`} />
                            </td>
                            <td className="p-2 text-right">
                              <button onClick={() => { setEditingTierId(t.id); setTierForm({ badge_level: t.badge_level, commission_rate: t.commission_rate ?? 0.05, min_fulfilled_orders: t.min_fulfilled_orders || 0, is_active: t.is_active }); setShowAddTier(true); }} className="text-text-faint hover:text-text p-1"><Edit3 className="h-3.5 w-3.5" /></button>
                            </td>
                          </tr>
                        ))}
                        {badgeTiers.length === 0 && (
                          <tr><td colSpan={5} className="p-4 text-center text-text-muted text-xs">No badge tiers configured</td></tr>
                        )}
                    </tbody>
                  </table>
                </div>

                {showAddTier && (
                  <div className="theme-overlay fixed inset-0 z-50 flex items-center justify-center p-4">
                    <div className="theme-card w-full max-w-md rounded-2xl border p-6">
                      <h3 className="text-sm font-bold text-text mb-4">{editingTierId ? "Edit" : "Add"} Badge Tier</h3>
                      <div className="space-y-3">
                        <label className="block"><span className="text-xs text-text-muted">Badge Level *</span>
                          <input value={tierForm.badge_level} onChange={(e) => setTierForm({ ...tierForm, badge_level: e.target.value })}
                            className="theme-input w-full rounded-xl border px-3 py-2 text-xs mt-1" /></label>
                        <label className="block"><span className="text-xs text-text-muted">Commission Rate (decimal) *</span>
                          <input type="number" step="0.01" value={tierForm.commission_rate} onChange={(e) => setTierForm({ ...tierForm, commission_rate: parseFloat(e.target.value) || 0 })}
                            className="theme-input w-full rounded-xl border px-3 py-2 text-xs mt-1" /></label>
                        <label className="block"><span className="text-xs text-text-muted">Min Fulfilled Orders</span>
                          <input type="number" value={tierForm.min_fulfilled_orders} onChange={(e) => setTierForm({ ...tierForm, min_fulfilled_orders: parseInt(e.target.value) || 0 })}
                            className="theme-input w-full rounded-xl border px-3 py-2 text-xs mt-1" /></label>
                        <label className="flex items-center gap-2 text-xs text-text-muted">
                          <input type="checkbox" checked={tierForm.is_active} onChange={(e) => setTierForm({ ...tierForm, is_active: e.target.checked })} className="accent-primary" />
                          Active
                        </label>
                      </div>
                      <div className="flex gap-2 mt-4 justify-end">
                        <button onClick={() => setShowAddTier(false)} className="theme-btn-secondary rounded-xl px-3 py-2 text-xs">Cancel</button>
                        <button onClick={saveBadgeTier} disabled={savingTier || !tierForm.badge_level} className="theme-btn-primary rounded-xl px-3 py-2 text-xs">{savingTier ? "Saving..." : "Save"}</button>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </PanelContent>
    </AdminLayout>
  );
}
