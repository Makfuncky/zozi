"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { PanelContent } from "@/components/PanelPage";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import { useAdminCountry } from "@/lib/useAdminCountry";
import { useToastStore } from "@/lib/toastStore";
import { Tag, Plus, RefreshCw, Search, Archive, RotateCcw, Trash2, Loader2, AlertCircle } from "@/lib/icons";
import { Button } from "@/components/ui/Button";
import { Table, TableHeader, TableHeaderCell, TableBody, TableRow, TableCell } from "@/components/ui/shared/Table";
import { EmptyState } from "@/components/ui/shared/EmptyState";
import { StatusBadge } from "@/components/ui/shared/Badge";


interface Coupon {
  id: number;
  code: string;
  discount_type: "percentage" | "fixed";
  discount_value: number;
  minimum_order: number | null;
  maximum_discount: number | null;
  usage_limit: number | null;
  usage_count: number;
  starts_at: string | null;
  expires_at: string | null;
  is_active: boolean;
  is_deleted: boolean;
  country_code: string | null;
  created_at: string;
}

const DISCOUNT_TYPE_OPTIONS = [
  { value: "percentage", label: "Percentage" },
  { value: "fixed", label: "Fixed Amount" },
];

export default function CouponsPanel() {
  const { selectedCountry } = useAdminCountry();
  const countryCode = selectedCountry?.code || "*";
  const { addToast } = useToastStore();

  const [loading, setLoading] = useState(true);
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [searchQuery, setSearchQuery] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    code: "",
    discount_type: "percentage" as "percentage" | "fixed",
    discount_value: "",
    minimum_order: "",
    maximum_discount: "",
    usage_limit: "",
    starts_at: "",
    expires_at: "",
    is_active: true,
  });

  const loadCoupons = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch(`/admin/promotions/coupons`);
      if (res.ok) {
        const data = await parseJsonResponse(res);
        const items = Array.isArray(data) ? data : Array.isArray(data?.coupons) ? data.coupons : [];
        setCoupons(items);
      } else {
        addToast("Failed to load coupons", "error");
      }
    } catch {
      addToast("Network error loading coupons", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => { loadCoupons(); }, [loadCoupons]);

  const filtered = useMemo(() => {
    if (!searchQuery) return coupons;
    const q = searchQuery.toLowerCase();
    return coupons.filter((c) => c.code.toLowerCase().includes(q));
  }, [coupons, searchQuery]);

  const activeCount = useMemo(() => coupons.filter((c) => c.is_active && !c.is_deleted).length, [coupons]);
  const expiredCount = useMemo(() => {
    const now = new Date();
    return coupons.filter((c) => c.expires_at && new Date(c.expires_at) < now && !c.is_deleted).length;
  }, [coupons]);

  const resetForm = () => {
    setForm({ code: "", discount_type: "percentage", discount_value: "", minimum_order: "", maximum_discount: "", usage_limit: "", starts_at: "", expires_at: "", is_active: true });
    setEditingId(null);
  };

  const handleEdit = (coupon: Coupon) => {
    setForm({
      code: coupon.code,
      discount_type: coupon.discount_type,
      discount_value: String(coupon.discount_value ?? ""),
      minimum_order: coupon.minimum_order != null ? String(coupon.minimum_order) : "",
      maximum_discount: coupon.maximum_discount != null ? String(coupon.maximum_discount) : "",
      usage_limit: coupon.usage_limit != null ? String(coupon.usage_limit) : "",
      starts_at: coupon.starts_at ? coupon.starts_at.slice(0, 16) : "",
      expires_at: coupon.expires_at ? coupon.expires_at.slice(0, 16) : "",
      is_active: coupon.is_active,
    });
    setEditingId(coupon.id);
    setShowForm(true);
  };

  const handleSubmit = async () => {
    if (!form.code || !form.discount_value) {
      addToast("Code and discount value are required", "error");
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        code: form.code,
        discount_type: form.discount_type,
        discount_value: parseFloat(form.discount_value),
        minimum_order: form.minimum_order ? parseFloat(form.minimum_order) : undefined,
        maximum_discount: form.maximum_discount ? parseFloat(form.maximum_discount) : undefined,
        usage_limit: form.usage_limit ? parseInt(form.usage_limit) : undefined,
        starts_at: form.starts_at || undefined,
        expires_at: form.expires_at || undefined,
        is_active: form.is_active,
      };

      if (editingId) {
        const res = await apiFetch(`/admin/promotions/coupons/${editingId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          addToast("Coupon updated", "success");
          setShowForm(false);
          resetForm();
          loadCoupons();
        } else {
          const err = await parseJsonResponse(res);
          addToast(err?.detail ?? "Failed to update coupon", "error");
        }
      } else {
        const res = await apiFetch(`/admin/promotions/coupons`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          addToast("Coupon created", "success");
          setShowForm(false);
          resetForm();
          loadCoupons();
        } else {
          const err = await parseJsonResponse(res);
          addToast(err?.detail ?? "Failed to create coupon", "error");
        }
      }
    } catch {
      addToast("Network error", "error");
    } finally {
      setSubmitting(false);
    }
  };

  const handleArchive = async (id: number) => {
    try {
      const res = await apiFetch(`/admin/promotions/coupons/${id}/archive`, { method: "POST" });
      if (res.ok) {
        addToast("Coupon archived", "success");
        loadCoupons();
      } else {
        addToast("Failed to archive coupon", "error");
      }
    } catch {
      addToast("Network error", "error");
    }
  };

  const handleRestore = async (id: number) => {
    try {
      const res = await apiFetch(`/admin/promotions/coupons/${id}/restore`, { method: "POST" });
      if (res.ok) {
        addToast("Coupon restored", "success");
        loadCoupons();
      } else {
        addToast("Failed to restore coupon", "error");
      }
    } catch {
      addToast("Network error", "error");
    }
  };

  if (loading) {
    return (
      <PanelContent title="Coupons">
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 animate-pulse rounded-xl bg-surface-2" />
          ))}
        </div>
      </PanelContent>
    );
  }

  return (
    <PanelContent title="Coupons">
      <div className="space-y-4">
        {/* Stats cards */}
        <div className="grid grid-cols-3 gap-3">
          <div className="theme-card rounded-xl border p-3">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-text-faint">Active</p>
            <p className="mt-1 text-xl font-bold text-text">{activeCount}</p>
          </div>
          <div className="theme-card rounded-xl border p-3">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-text-faint">Expired</p>
            <p className="mt-1 text-xl font-bold text-text">{expiredCount}</p>
          </div>
          <div className="theme-card rounded-xl border p-3">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-text-faint">Total</p>
            <p className="mt-1 text-xl font-bold text-text">{coupons.length}</p>
          </div>
        </div>

        {/* Toolbar */}
        <div className="flex items-center justify-between gap-3">
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-text-faint" />
            <input
              type="text"
              placeholder="Search by coupon code..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-lg border border-glass-border bg-glass-mid pl-8 pr-3 py-2 text-xs text-text placeholder:text-text-faint outline-none focus:border-primary/50"
            />
          </div>
          <div className="flex items-center gap-2">
            <button onClick={loadCoupons} className="rounded-lg border border-glass-border p-2 text-text-muted hover:text-text transition-colors">
              <RefreshCw className="h-3.5 w-3.5" />
            </button>
            <Button size="sm" onClick={() => { resetForm(); setShowForm(true); }}>
              <Plus className="h-3.5 w-3.5" />
              Add Coupon
            </Button>
          </div>
        </div>

        {/* Table */}
        {filtered.length === 0 ? (
          <EmptyState icon={Tag} title="No coupons found" description="Create your first coupon to start promoting" />
        ) : (
          <div className="rounded-lg border border-glass-border bg-glass-panel overflow-hidden">
            <Table>
              <TableHeader>
                <TableHeaderCell>Code</TableHeaderCell>
                <TableHeaderCell>Discount</TableHeaderCell>
                <TableHeaderCell>Min Order</TableHeaderCell>
                <TableHeaderCell>Usage</TableHeaderCell>
                <TableHeaderCell>Expires</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
                <TableHeaderCell>Actions</TableHeaderCell>
              </TableHeader>
              <TableBody>
                {filtered.map((coupon) => {
                  const isExpired = coupon.expires_at && new Date(coupon.expires_at) < new Date();
                  return (
                    <TableRow key={coupon.id}>
                      <TableCell>
                        <span className="font-mono text-[12px] font-semibold text-text">{coupon.code}</span>
                      </TableCell>
                      <TableCell>
                        <span className="text-xs text-text">
                          {coupon.discount_type === "percentage"
                            ? `${coupon.discount_value}%`
                            : `${coupon.discount_value} ${coupon.country_code || ""}`}
                          {coupon.maximum_discount && coupon.discount_type === "percentage"
                            ? ` (max ${coupon.maximum_discount})` : ""}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="text-xs text-text-muted">
                          {coupon.minimum_order ? `${coupon.minimum_order}` : "—"}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="text-xs text-text-muted">
                          {coupon.usage_count}{coupon.usage_limit ? ` / ${coupon.usage_limit}` : ""}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className={`text-xs ${isExpired ? "text-danger" : "text-text-muted"}`}>
                          {coupon.expires_at ? new Date(coupon.expires_at).toLocaleDateString() : "—"}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          {coupon.is_deleted ? (
                            <StatusBadge status="archived" />
                          ) : (
                            <StatusBadge status={coupon.is_active ? "active" : "inactive"} />
                          )}
                          {isExpired && !coupon.is_deleted && (
                            <StatusBadge status="expired" />
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          {!coupon.is_deleted && (
                            <>
                              <button
                                onClick={() => handleEdit(coupon)}
                                className="rounded-md border border-glass-border px-2 py-1 text-[10px] text-text-muted hover:text-primary transition-colors"
                              >
                                Edit
                              </button>
                              <button
                                onClick={() => handleArchive(coupon.id)}
                                className="rounded-md border border-glass-border px-2 py-1 text-[10px] text-text-muted hover:text-danger transition-colors"
                                title="Archive"
                              >
                                <Archive className="h-3 w-3" />
                              </button>
                            </>
                          )}
                          {coupon.is_deleted && (
                            <button
                              onClick={() => handleRestore(coupon.id)}
                              className="rounded-md border border-glass-border px-2 py-1 text-[10px] text-text-muted hover:text-success transition-colors"
                              title="Restore"
                            >
                              <RotateCcw className="h-3 w-3" />
                            </button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}

        {/* Coupon Form Modal */}
        {showForm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay" onClick={() => !submitting && setShowForm(false)}>
            <div className="w-full max-w-lg rounded-xl border border-glass-border bg-glass-panel p-6 shadow-2xl" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-text">{editingId ? "Edit Coupon" : "Create Coupon"}</h3>
                <button onClick={() => setShowForm(false)} className="text-text-muted hover:text-text"><AlertCircle className="h-4 w-4" /></button>
              </div>
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] font-semibold uppercase tracking-wider text-text-faint mb-1">Code*</label>
                    <input type="text" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })}
                      className="w-full rounded-lg border border-glass-border bg-glass-mid px-3 py-2 text-xs text-text outline-none focus:border-primary/50" />
                  </div>
                  <div>
                    <label className="block text-[10px] font-semibold uppercase tracking-wider text-text-faint mb-1">Type</label>
                    <select value={form.discount_type} onChange={(e) => setForm({ ...form, discount_type: e.target.value as "percentage" | "fixed" })}
                      className="w-full rounded-lg border border-glass-border bg-glass-mid px-3 py-2 text-xs text-text outline-none focus:border-primary/50">
                      {DISCOUNT_TYPE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                    </select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] font-semibold uppercase tracking-wider text-text-faint mb-1">Value*</label>
                    <input type="number" step="0.01" min="0" value={form.discount_value} onChange={(e) => setForm({ ...form, discount_value: e.target.value })}
                      className="w-full rounded-lg border border-glass-border bg-glass-mid px-3 py-2 text-xs text-text outline-none focus:border-primary/50" />
                  </div>
                  <div>
                    <label className="block text-[10px] font-semibold uppercase tracking-wider text-text-faint mb-1">Max Discount</label>
                    <input type="number" step="0.01" min="0" value={form.maximum_discount} onChange={(e) => setForm({ ...form, maximum_discount: e.target.value })}
                      className="w-full rounded-lg border border-glass-border bg-glass-mid px-3 py-2 text-xs text-text outline-none focus:border-primary/50" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] font-semibold uppercase tracking-wider text-text-faint mb-1">Min Order</label>
                    <input type="number" step="0.01" min="0" value={form.minimum_order} onChange={(e) => setForm({ ...form, minimum_order: e.target.value })}
                      className="w-full rounded-lg border border-glass-border bg-glass-mid px-3 py-2 text-xs text-text outline-none focus:border-primary/50" />
                  </div>
                  <div>
                    <label className="block text-[10px] font-semibold uppercase tracking-wider text-text-faint mb-1">Usage Limit</label>
                    <input type="number" min="0" value={form.usage_limit} onChange={(e) => setForm({ ...form, usage_limit: e.target.value })}
                      className="w-full rounded-lg border border-glass-border bg-glass-mid px-3 py-2 text-xs text-text outline-none focus:border-primary/50" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] font-semibold uppercase tracking-wider text-text-faint mb-1">Start Date</label>
                    <input type="datetime-local" value={form.starts_at} onChange={(e) => setForm({ ...form, starts_at: e.target.value })}
                      className="w-full rounded-lg border border-glass-border bg-glass-mid px-3 py-2 text-xs text-text outline-none focus:border-primary/50" />
                  </div>
                  <div>
                    <label className="block text-[10px] font-semibold uppercase tracking-wider text-text-faint mb-1">Expiry Date</label>
                    <input type="datetime-local" value={form.expires_at} onChange={(e) => setForm({ ...form, expires_at: e.target.value })}
                      className="w-full rounded-lg border border-glass-border bg-glass-mid px-3 py-2 text-xs text-text outline-none focus:border-primary/50" />
                  </div>
                </div>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                    className="rounded border-glass-border" />
                  <span className="text-xs text-text">Active on creation</span>
                </label>
              </div>
              <div className="mt-5 flex justify-end gap-2">
                <button onClick={() => setShowForm(false)} disabled={submitting}
                  className="rounded-lg border border-glass-border px-4 py-2 text-xs text-text-muted hover:text-text transition-colors">Cancel</button>
                <Button variant="primary" onClick={handleSubmit} disabled={submitting}>
                  {submitting ? <Loader2 className="h-3.5 w-3.5 animate-spin inline mr-1" /> : null}
                  {editingId ? "Update" : "Create"}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </PanelContent>
  );
}
