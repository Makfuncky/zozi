"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { PanelContent } from "@/components/PanelPage";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import { useAdminCountry } from "@/lib/useAdminCountry";
import { useToastStore } from "@/lib/toastStore";
import { Zap, Plus, RefreshCw, Search, Archive, RotateCcw, Loader2, AlertCircle } from "@/lib/icons";
import { Button } from "@/components/ui/Button";
import { Table, TableHeader, TableHeaderCell, TableBody, TableRow, TableCell } from "@/components/ui/shared/Table";
import { EmptyState } from "@/components/ui/shared/EmptyState";
import { StatusBadge } from "@/components/ui/shared/Badge";


interface FlashSale {
  id: number;
  title: string;
  description: string | null;
  starts_at: string;
  ends_at: string;
  discount_pct: number;
  is_active: boolean;
  is_deleted: boolean;
  product_ids: number[] | null;
  country_code: string | null;
  created_at: string;
}

export default function FlashSalesPanel() {
  const { selectedCountry } = useAdminCountry();
  const countryCode = selectedCountry?.code || "*";
  const { addToast } = useToastStore();

  const [loading, setLoading] = useState(true);
  const [sales, setSales] = useState<FlashSale[]>([]);
  const [searchQuery, setSearchQuery] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    title: "",
    description: "",
    discount_pct: "",
    starts_at: "",
    ends_at: "",
    is_active: true,
  });

  const loadSales = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch(`/admin/promotions/flash-sales`);
      if (res.ok) {
        const data = await parseJsonResponse(res);
        const items = Array.isArray(data) ? data : Array.isArray(data?.flash_sales) ? data.flash_sales : [];
        setSales(items);
      } else {
        addToast("Failed to load flash sales", "error");
      }
    } catch {
      addToast("Network error loading flash sales", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast, countryCode]);

  useEffect(() => { loadSales(); }, [loadSales]);

  const filtered = useMemo(() => {
    if (!searchQuery) return sales;
    const q = searchQuery.toLowerCase();
    return sales.filter((s) => s.title.toLowerCase().includes(q));
  }, [sales, searchQuery]);

  const activeCount = useMemo(() => {
    const now = new Date();
    return sales.filter((s) => s.is_active && !s.is_deleted && new Date(s.starts_at) <= now && new Date(s.ends_at) >= now).length;
  }, [sales]);

  const upcomingCount = useMemo(() => {
    const now = new Date();
    return sales.filter((s) => !s.is_deleted && new Date(s.starts_at) > now).length;
  }, [sales]);

  const resetForm = () => {
    setForm({ title: "", description: "", discount_pct: "", starts_at: "", ends_at: "", is_active: true });
    setEditingId(null);
  };

  const handleEdit = (sale: FlashSale) => {
    setForm({
      title: sale.title,
      description: sale.description ?? "",
      discount_pct: String(sale.discount_pct ?? ""),
      starts_at: sale.starts_at ? sale.starts_at.slice(0, 16) : "",
      ends_at: sale.ends_at ? sale.ends_at.slice(0, 16) : "",
      is_active: sale.is_active,
    });
    setEditingId(sale.id);
    setShowForm(true);
  };

  const handleSubmit = async () => {
    if (!form.title || !form.discount_pct || !form.starts_at || !form.ends_at) {
      addToast("Title, discount, start and end dates are required", "error");
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        title: form.title,
        description: form.description || undefined,
        discount_pct: parseFloat(form.discount_pct),
        starts_at: form.starts_at,
        ends_at: form.ends_at,
        is_active: form.is_active,
      };

      if (editingId) {
        const res = await apiFetch(`/admin/promotions/flash-sales/${editingId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          addToast("Flash sale updated", "success");
          setShowForm(false);
          resetForm();
          loadSales();
        } else {
          const err = await parseJsonResponse(res);
          addToast(err?.detail ?? "Failed to update flash sale", "error");
        }
      } else {
        const res = await apiFetch(`/admin/promotions/flash-sales`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          addToast("Flash sale created", "success");
          setShowForm(false);
          resetForm();
          loadSales();
        } else {
          const err = await parseJsonResponse(res);
          addToast(err?.detail ?? "Failed to create flash sale", "error");
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
      const res = await apiFetch(`/admin/promotions/flash-sales/${id}/archive`, { method: "POST" });
      if (res.ok) {
        addToast("Flash sale archived", "success");
        loadSales();
      } else {
        addToast("Failed to archive flash sale", "error");
      }
    } catch {
      addToast("Network error", "error");
    }
  };

  const handleRestore = async (id: number) => {
    try {
      const res = await apiFetch(`/admin/promotions/flash-sales/${id}/restore`, { method: "POST" });
      if (res.ok) {
        addToast("Flash sale restored", "success");
        loadSales();
      } else {
        addToast("Failed to restore flash sale", "error");
      }
    } catch {
      addToast("Network error", "error");
    }
  };

  if (loading) {
    return (
      <PanelContent title="Flash Sales">
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 animate-pulse rounded-xl bg-surface-2" />
          ))}
        </div>
      </PanelContent>
    );
  }

  const statusForSale = (s: FlashSale): "active" | "inactive" | "expired" | "upcoming" => {
    if (s.is_deleted) return "inactive";
    if (!s.is_active) return "inactive";
    const now = new Date();
    const start = new Date(s.starts_at);
    const end = new Date(s.ends_at);
    if (now < start) return "upcoming";
    if (now > end) return "expired";
    return "active";
  };

  const statusLabel = (s: string) => {
    const map: Record<string, string> = { active: "Active", upcoming: "Upcoming", expired: "Expired", inactive: "Inactive" };
    return map[s] || s;
  };

  return (
    <PanelContent title="Flash Sales">
      <div className="space-y-4">
        {/* Stats cards */}
        <div className="grid grid-cols-3 gap-3">
          <div className="theme-card rounded-xl border p-3">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-text-faint">Active Now</p>
            <p className="mt-1 text-xl font-bold text-success">{activeCount}</p>
          </div>
          <div className="theme-card rounded-xl border p-3">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-text-faint">Upcoming</p>
            <p className="mt-1 text-xl font-bold text-warning">{upcomingCount}</p>
          </div>
          <div className="theme-card rounded-xl border p-3">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-text-faint">Total</p>
            <p className="mt-1 text-xl font-bold text-text">{sales.length}</p>
          </div>
        </div>

        {/* Toolbar */}
        <div className="flex items-center justify-between gap-3">
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-text-faint" />
            <input
              type="text"
              placeholder="Search flash sales..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-lg border border-glass-border bg-glass-mid pl-8 pr-3 py-2 text-xs text-text placeholder:text-text-faint outline-none focus:border-primary/50"
            />
          </div>
          <div className="flex items-center gap-2">
            <button onClick={loadSales} className="rounded-lg border border-glass-border p-2 text-text-muted hover:text-text transition-colors">
              <RefreshCw className="h-3.5 w-3.5" />
            </button>
            <Button size="sm" onClick={() => { resetForm(); setShowForm(true); }}>
              <Plus className="h-3.5 w-3.5" />
              Create Flash Sale
            </Button>
          </div>
        </div>

        {/* Table */}
        {filtered.length === 0 ? (
          <EmptyState icon={Zap} title="No flash sales" description="Create a time-limited promotion to boost sales" />
        ) : (
          <div className="rounded-lg border border-glass-border bg-glass-panel overflow-hidden">
            <Table>
              <TableHeader>
                <TableHeaderCell>Title</TableHeaderCell>
                <TableHeaderCell>Discount</TableHeaderCell>
                <TableHeaderCell>Start</TableHeaderCell>
                <TableHeaderCell>End</TableHeaderCell>
                <TableHeaderCell>Duration</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
                <TableHeaderCell>Actions</TableHeaderCell>
              </TableHeader>
              <TableBody>
                {filtered.map((sale) => {
                  const st = statusForSale(sale);
                  const start = new Date(sale.starts_at);
                  const end = new Date(sale.ends_at);
                  const durationMs = end.getTime() - start.getTime();
                  const durationDays = Math.floor(durationMs / (1000 * 60 * 60 * 24));
                  const durationHours = Math.floor((durationMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                  return (
                    <TableRow key={sale.id}>
                      <TableCell>
                        <span className="text-xs font-semibold text-text">{sale.title}</span>
                        {sale.description && (
                          <p className="text-[10px] text-text-faint truncate max-w-[200px]">{sale.description}</p>
                        )}
                      </TableCell>
                      <TableCell>
                        <span className="text-xs font-mono font-semibold text-success">-{sale.discount_pct}%</span>
                      </TableCell>
                      <TableCell>
                        <span className="text-xs text-text-muted">{start.toLocaleDateString()} {start.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                      </TableCell>
                      <TableCell>
                        <span className="text-xs text-text-muted">{end.toLocaleDateString()} {end.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                      </TableCell>
                      <TableCell>
                        <span className="text-xs text-text-muted">{durationDays > 0 ? `${durationDays}d ` : ""}{durationHours}h</span>
                      </TableCell>
                      <TableCell>
                        <span className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                          st === "active" ? "bg-success/10 text-success" :
                          st === "upcoming" ? "bg-warning/10 text-warning" :
                          st === "expired" ? "bg-danger/10 text-danger" :
                          "bg-surface-2 text-text-faint"
                        }`}>{statusLabel(st)}</span>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          {!sale.is_deleted && (
                            <>
                              <button
                                onClick={() => handleEdit(sale)}
                                className="rounded-md border border-glass-border px-2 py-1 text-[10px] text-text-muted hover:text-primary transition-colors"
                              >
                                Edit
                              </button>
                              <button
                                onClick={() => handleArchive(sale.id)}
                                className="rounded-md border border-glass-border px-2 py-1 text-[10px] text-text-muted hover:text-danger transition-colors"
                                title="Archive"
                              >
                                <Archive className="h-3 w-3" />
                              </button>
                            </>
                          )}
                          {sale.is_deleted && (
                            <button
                              onClick={() => handleRestore(sale.id)}
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

        {/* Flash Sale Form Modal */}
        {showForm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay" onClick={() => !submitting && setShowForm(false)}>
            <div className="w-full max-w-lg rounded-xl border border-glass-border bg-glass-panel p-6 shadow-2xl" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-text">{editingId ? "Edit Flash Sale" : "Create Flash Sale"}</h3>
                <button onClick={() => setShowForm(false)} className="text-text-muted hover:text-text"><AlertCircle className="h-4 w-4" /></button>
              </div>
              <div className="space-y-3">
                <div>
                  <label className="block text-[10px] font-semibold uppercase tracking-wider text-text-faint mb-1">Title*</label>
                  <input type="text" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
                    className="w-full rounded-lg border border-glass-border bg-glass-mid px-3 py-2 text-xs text-text outline-none focus:border-primary/50" />
                </div>
                <div>
                  <label className="block text-[10px] font-semibold uppercase tracking-wider text-text-faint mb-1">Description</label>
                  <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={2}
                    className="w-full rounded-lg border border-glass-border bg-glass-mid px-3 py-2 text-xs text-text outline-none focus:border-primary/50 resize-none" />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] font-semibold uppercase tracking-wider text-text-faint mb-1">Discount %*</label>
                    <input type="number" step="0.01" min="0" max="100" value={form.discount_pct} onChange={(e) => setForm({ ...form, discount_pct: e.target.value })}
                      className="w-full rounded-lg border border-glass-border bg-glass-mid px-3 py-2 text-xs text-text outline-none focus:border-primary/50" />
                  </div>
                  <div className="flex items-end pb-2">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                        className="rounded border-glass-border" />
                      <span className="text-xs text-text">Active</span>
                    </label>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] font-semibold uppercase tracking-wider text-text-faint mb-1">Start Date*</label>
                    <input type="datetime-local" value={form.starts_at} onChange={(e) => setForm({ ...form, starts_at: e.target.value })}
                      className="w-full rounded-lg border border-glass-border bg-glass-mid px-3 py-2 text-xs text-text outline-none focus:border-primary/50" />
                  </div>
                  <div>
                    <label className="block text-[10px] font-semibold uppercase tracking-wider text-text-faint mb-1">End Date*</label>
                    <input type="datetime-local" value={form.ends_at} onChange={(e) => setForm({ ...form, ends_at: e.target.value })}
                      className="w-full rounded-lg border border-glass-border bg-glass-mid px-3 py-2 text-xs text-text outline-none focus:border-primary/50" />
                  </div>
                </div>
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
