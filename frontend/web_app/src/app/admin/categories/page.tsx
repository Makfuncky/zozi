"use client";

import { Button } from "@/components/ui/Button";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  CheckCircle,
  ChevronDown,
  ChevronRight,
  GripVertical,
  Layers3,
  Pencil,
  Plus,
  RefreshCw,
  RotateCcw,
  Search,
  Trash2,
  X,
} from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import BulkActionBar from "@/components/BulkActionBar";
import InlineActionButtons from "@/components/InlineActionButtons";
import { PanelContent } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { normalizeListPage } from "@/lib/listResponse";
import { useAuth } from "@/lib/useAuth";
import { useToastStore } from "@/lib/toastStore";
import { dc, useDensity } from "@/lib/densityContext";
import { EnterpriseDataTable, type EnterpriseColumn } from "@shared/components/EnterpriseDataTable";

interface AdminCategory {
  id: number;
  name: string;
  slug: string;
  description?: string | null;
  icon?: string | null;
  parent_id?: number | null;
  sort_order: number;
  is_active: boolean;
  is_featured: boolean;
  commission_rate?: number | null;
  is_deleted?: boolean;
  created_at?: string;
  updated_at?: string;
}

const PAGE_SIZE = 100;

function AdminCategoriesInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();
  const { density } = useDensity();
  const addToast = useToastStore((s) => s.addToast);

  const [categories, setCategories] = useState<AdminCategory[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [includeDeleted, setIncludeDeleted] = useState(false);
  const [page, setPage] = useState(1);
  const [actionId, setActionId] = useState<number | null>(null);
  const [archiveTarget, setArchiveTarget] = useState<AdminCategory | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [bulkLoading, setBulkLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState({ name: "", slug: "", description: "", icon: "", parent_id: "", commission_rate: "", is_active: true, is_featured: false });
  const [saving, setSaving] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn || !["admin", "sub_admin", "moderator"].includes(user?.role || "")) {
      router.push("/admin/login");
    }
  }, [authLoading, isLoggedIn, user, router]);

  const fetchCategories = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("limit", String(PAGE_SIZE));
      params.set("offset", String((page - 1) * PAGE_SIZE));
      if (search.trim()) params.set("search", search.trim());
      if (includeDeleted) params.set("include_deleted", "true");
      const res = await apiFetch(`/admin/categories?${params.toString()}`);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Unable to load categories.");
      }
      const payload = normalizeListPage<AdminCategory>(await res.json());
      setCategories(payload.data);
      setTotal(payload.total);
      setLoadError(null);
    } catch (e) {
      setLoadError(e instanceof Error ? e.message : "Unable to load categories.");
      setCategories([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [page, search, includeDeleted]);

  useEffect(() => {
    if (isLoggedIn) fetchCategories();
  }, [fetchCategories, isLoggedIn]);

  useEffect(() => { setPage(1); }, [search, includeDeleted]);

  const archiveCategory = async (id: number) => {
    setActionId(id);
    try {
      const res = await apiFetch(`/admin/categories/${id}/archive`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ reason: "Manual archive" }) });
      if (res.ok) { await fetchCategories(); addToast("Category archived", "success"); }
      else { const err = await res.json().catch(() => ({})); addToast(err.detail || "Failed to archive", "error"); }
    } finally { setActionId(null); setArchiveTarget(null); }
  };

  const restoreCategory = async (id: number) => {
    setActionId(id);
    try {
      const res = await apiFetch(`/admin/categories/${id}/restore`, { method: "POST" });
      if (res.ok) { await fetchCategories(); addToast("Category restored", "success"); }
      else { const err = await res.json().catch(() => ({})); addToast(err.detail || "Failed to restore", "error"); }
    } finally { setActionId(null); }
  };

  const saveCategory = async () => {
    setSaving(true);
    try {
      const body: Record<string, unknown> = { name: form.name, slug: form.slug, description: form.description || null, icon: form.icon || null, is_active: form.is_active, is_featured: form.is_featured };
      if (form.parent_id) body.parent_id = Number(form.parent_id);
      if (form.commission_rate) body.commission_rate = Number(form.commission_rate);

      const url = editingId ? `/admin/categories/${editingId}` : "/admin/categories";
      const method = editingId ? "PUT" : "POST";
      const res = await apiFetch(url, { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      if (res.ok) {
        await fetchCategories();
        setShowForm(false); setEditingId(null); setForm({ name: "", slug: "", description: "", icon: "", parent_id: "", commission_rate: "", is_active: true, is_featured: false });
        addToast(editingId ? "Category updated" : "Category created", "success");
      } else {
        const err = await res.json().catch(() => ({}));
        addToast(err.detail || "Failed to save", "error");
      }
    } finally { setSaving(false); }
  };

  const bulkArchive = async () => {
    const ids = Array.from(selectedIds);
    if (!ids.length) return;
    setBulkLoading(true);
    try {
      const res = await apiFetch("/admin/categories/bulk/archive", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ids, reason: "Bulk archive" }) });
      if (res.ok) { await fetchCategories(); setSelectedIds(new Set()); addToast(`${ids.length} categories archived`, "success"); }
      else { const err = await res.json().catch(() => ({})); addToast(err.detail || "Bulk archive failed", "error"); }
    } finally { setBulkLoading(false); }
  };

  const bulkRestore = async () => {
    const ids = Array.from(selectedIds);
    if (!ids.length) return;
    setBulkLoading(true);
    try {
      const res = await apiFetch("/admin/categories/bulk/restore", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ids }) });
      if (res.ok) { await fetchCategories(); setSelectedIds(new Set()); addToast(`${ids.length} categories restored`, "success"); }
      else { const err = await res.json().catch(() => ({})); addToast(err.detail || "Bulk restore failed", "error"); }
    } finally { setBulkLoading(false); }
  };

  const startEdit = (cat: AdminCategory) => {
    setForm({ name: cat.name, slug: cat.slug, description: cat.description || "", icon: cat.icon || "", parent_id: cat.parent_id ? String(cat.parent_id) : "", commission_rate: cat.commission_rate ? String(cat.commission_rate) : "", is_active: cat.is_active, is_featured: cat.is_featured });
    setEditingId(cat.id);
    setShowForm(true);
  };

  const hasActiveFilters = search.trim() !== "" || includeDeleted;
  const clearFilters = () => { setSearch(""); setIncludeDeleted(false); setPage(1); };

  const bodyText = dc(density, "text-[10px]", "text-xs", "text-sm");
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const columns: Array<EnterpriseColumn<AdminCategory>> = [
    { key: "id", label: "#", width: "60px", sortable: true, render: (cat) => <span className={`${bodyText} tabular-nums text-text-faint`}>{cat.id}</span> },
    { key: "name", label: "Name", width: "200px", sortable: true, searchValue: (cat) => cat.name, render: (cat) => (
      <div className="flex items-center gap-2">
        {cat.icon ? <span className="text-lg">{cat.icon}</span> : null}
        <span className={`${bodyText} font-medium text-text`}>{cat.name}</span>
        {cat.is_featured ? <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-semibold text-primary">Featured</span> : null}
      </div>
    )},
    { key: "slug", label: "Slug", width: "150px", render: (cat) => <span className={`${bodyText} text-text-muted`}>{cat.slug}</span> },
    { key: "parent_id", label: "Parent", width: "100px", render: (cat) => <span className={`${bodyText} text-text-faint`}>{cat.parent_id ? `#${cat.parent_id}` : "—"}</span> },
    { key: "sort_order", label: "Order", width: "70px", align: "right", render: (cat) => <span className={`${bodyText} tabular-nums text-text-muted`}>{cat.sort_order}</span> },
    { key: "commission_rate", label: "Comm%", width: "80px", align: "right", render: (cat) => <span className={`${bodyText} tabular-nums text-text-faint`}>{cat.commission_rate ? `${cat.commission_rate}%` : "—"}</span> },
    { key: "is_active", label: "Active", width: "80px", render: (cat) => cat.is_deleted ? <span className="rounded-full bg-danger/10 px-2 py-0.5 text-[10px] font-semibold text-danger">Deleted</span> : cat.is_active ? <span className="rounded-full bg-success/10 px-2 py-0.5 text-[10px] font-semibold text-success">Active</span> : <span className="rounded-full bg-warning/10 px-2 py-0.5 text-[10px] font-semibold text-warning">Inactive</span> },
    { key: "created_at", label: "Created", width: "140px", render: (cat) => <span className={`${bodyText} tabular-nums text-text-faint`}>{cat.created_at ? new Date(cat.created_at).toLocaleDateString() : "—"}</span> },
  ];

  if (authLoading) return null;

  return (
    <>
    {archiveTarget ? (
      <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4">
        <div className="theme-card w-full max-w-sm rounded-xl border p-6">
          <h2 className="text-base font-semibold text-text">Archive category?</h2>
          <p className="mt-2 text-xs text-text-muted"><span className="font-medium text-text">{archiveTarget.name}</span> will be hidden from the storefront.</p>
          <div className="mt-5 flex gap-3">
            <button onClick={() => setArchiveTarget(null)} className="flex-1 rounded-xl border border-border py-2 text-xs text-text-muted hover:bg-surface-2">Cancel</button>
            <Button variant="danger" className="flex-1 rounded-xl py-2 text-xs font-medium disabled:opacity-50" onClick={() => archiveCategory(archiveTarget.id)} disabled={actionId === archiveTarget.id}>{actionId === archiveTarget.id ? "Archiving..." : "Archive"}</Button>
          </div>
        </div>
      </div>
    ) : null}

    {/* Create/Edit modal */}
    {showForm ? (
      <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4">
        <div className="theme-card w-full max-w-lg rounded-xl border p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-text">{editingId ? "Edit Category" : "New Category"}</h2>
            <button onClick={() => { setShowForm(false); setEditingId(null); }} className="rounded-lg p-1.5 text-text-muted hover:bg-surface-2"><X className="h-4 w-4" /></button>
          </div>
          <div className="mt-4 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-text-muted">Name *</label>
                <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Category name" className="mt-1 h-9 w-full rounded-xl border border-border bg-surface-1 px-3 text-xs text-text placeholder:text-text-faint focus:border-primary focus:outline-none" />
              </div>
              <div>
                <label className="text-xs font-medium text-text-muted">Slug *</label>
                <input value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} placeholder="category-slug" className="mt-1 h-9 w-full rounded-xl border border-border bg-surface-1 px-3 text-xs text-text placeholder:text-text-faint focus:border-primary focus:outline-none" />
              </div>
            </div>
            <div>
              <label className="text-xs font-medium text-text-muted">Description</label>
              <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Optional description" className="mt-1 h-9 w-full rounded-xl border border-border bg-surface-1 px-3 text-xs text-text placeholder:text-text-faint focus:border-primary focus:outline-none" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-text-muted">Icon (emoji)</label>
                <input value={form.icon} onChange={(e) => setForm({ ...form, icon: e.target.value })} placeholder="📦" className="mt-1 h-9 w-full rounded-xl border border-border bg-surface-1 px-3 text-xs text-text placeholder:text-text-faint focus:border-primary focus:outline-none" />
              </div>
              <div>
                <label className="text-xs font-medium text-text-muted">Parent ID</label>
                <input value={form.parent_id} onChange={(e) => setForm({ ...form, parent_id: e.target.value })} placeholder="Leave blank for root" className="mt-1 h-9 w-full rounded-xl border border-border bg-surface-1 px-3 text-xs text-text placeholder:text-text-faint focus:border-primary focus:outline-none" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-text-muted">Commission rate %</label>
                <input value={form.commission_rate} onChange={(e) => setForm({ ...form, commission_rate: e.target.value })} type="number" step="0.1" placeholder="e.g. 5" className="mt-1 h-9 w-full rounded-xl border border-border bg-surface-1 px-3 text-xs text-text placeholder:text-text-faint focus:border-primary focus:outline-none" />
              </div>
              <div className="flex items-end gap-3 pb-1.5">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} className="rounded border-border" />
                  <span className="text-xs text-text-muted">Active</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={form.is_featured} onChange={(e) => setForm({ ...form, is_featured: e.target.checked })} className="rounded border-border" />
                  <span className="text-xs text-text-muted">Featured</span>
                </label>
              </div>
            </div>
          </div>
          <div className="mt-5 flex gap-3">
            <button onClick={() => { setShowForm(false); setEditingId(null); }} className="flex-1 rounded-xl border border-border py-2 text-xs text-text-muted hover:bg-surface-2">Cancel</button>
            <Button variant="primary" onClick={saveCategory} disabled={saving || !form.name || !form.slug}>{saving ? "Saving..." : editingId ? "Update" : "Create"}</Button>
          </div>
        </div>
      </div>
    ) : null}

    <AdminLayout title="Categories" headerMode="compact">
      <PanelContent width="full" className="space-y-4">
      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 10 }).map((_, i) => <div key={i} className="h-10 rounded-xl bg-surface-2 animate-pulse" />)}
        </div>
      ) : categories.length === 0 ? (
        <div className="rounded-2xl border border-border bg-surface-1 px-6 py-12 text-center">
          <Layers3 className="mx-auto h-8 w-8 text-text-faint" />
          <p className="mt-3 text-sm font-semibold text-text">{loadError || (hasActiveFilters ? "No categories match filters" : "No categories yet")}</p>
          <p className="mt-2 text-xs text-text-faint">{loadError || (hasActiveFilters ? "Try clearing filters" : "Create your first category to organize products.")}</p>
          <div className="mt-4 flex items-center justify-center gap-2">
            {loadError ? <Button variant="primary" onClick={fetchCategories}>Retry</Button> : <Button variant="primary" className="rounded-xl px-4 py-2 text-xs font-semibold" onClick={() => { setEditingId(null); setForm({ name: "", slug: "", description: "", icon: "", parent_id: "", commission_rate: "", is_active: true, is_featured: false }); setShowForm(true); }}><Plus className="mr-1 inline h-3.5 w-3.5" />Add Category</Button>}
            {hasActiveFilters ? <button onClick={clearFilters} className="rounded-xl border border-border px-4 py-2 text-xs font-semibold text-text-muted hover:bg-surface-2">Clear filters</button> : null}
          </div>
        </div>
      ) : (
        <EnterpriseDataTable
          columns={columns}
          rows={categories}
          rowKey={(cat) => cat.id}
          densityMode={density}
          enableBulkActions
          enableExport
          showPagination={false}
          selectedRowKeys={Array.from(selectedIds)}
          onSelectedRowKeysChange={(keys) => setSelectedIds(new Set(keys.map((k) => Number(k))))}
          toolbarSlot={(
            <>
              <div className="relative min-w-[16rem] flex-1 xl:w-72 xl:flex-none">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search categories" className="h-9 w-full rounded-xl border border-border bg-surface-1 py-2 pl-9 pr-3 text-xs text-text placeholder:text-text-faint focus:border-primary focus:outline-none" />
              </div>
              <Button variant="primary" className="flex h-9 items-center gap-1.5 rounded-lg px-3 text-xs font-semibold" onClick={() => { setEditingId(null); setForm({ name: "", slug: "", description: "", icon: "", parent_id: "", commission_rate: "", is_active: true, is_featured: false }); setShowForm(true); }}><Plus className="h-3.5 w-3.5" />Add</Button>
              <label className="flex items-center gap-1.5 cursor-pointer ml-1">
                <input type="checkbox" checked={includeDeleted} onChange={(e) => setIncludeDeleted(e.target.checked)} className="rounded border-border" />
                <span className="text-[11px] text-text-muted">Show deleted</span>
              </label>
              <button onClick={fetchCategories} disabled={loading} className="flex h-9 items-center justify-center rounded-lg border border-border bg-surface-1 px-3 text-xs text-text-muted transition-colors hover:bg-surface-2 disabled:opacity-50"><RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} /></button>
              {hasActiveFilters ? <button onClick={clearFilters} className="h-9 rounded-lg border border-border bg-surface-1 px-3 text-xs font-medium text-text-muted hover:bg-surface-2 hover:text-text">Clear</button> : null}
            </>
          )}
          emptyState={loadError || "No categories matched."}
          rowActions={(cat) => (
            <div className="flex justify-end">
              <InlineActionButtons actions={[
                { label: "Edit", icon: <Pencil className="h-3.5 w-3.5" />, onClick: () => startEdit(cat), tone: "primary" },
                ...(cat.is_deleted
                  ? [{ label: "Restore", icon: <RotateCcw className="h-3.5 w-3.5" />, onClick: () => restoreCategory(cat.id), tone: "success" as const, disabled: actionId === cat.id }]
                  : [{ label: "Archive", icon: <Trash2 className="h-3.5 w-3.5" />, onClick: () => setArchiveTarget(cat), tone: "danger" as const, disabled: actionId === cat.id }]
                ),
              ]} />
            </div>
          )}
        />
      )}

      {totalPages > 1 && (
        <div className="mt-3 flex items-center justify-between gap-3">
          <p className="text-xs text-text-faint">{total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, total)} of {total}</p>
          <div className="flex items-center gap-1">
            <button onClick={() => setPage(1)} disabled={page === 1} className="px-2 py-1 rounded-lg bg-surface-2 text-text-faint text-xs disabled:opacity-40">«</button>
            <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="px-2 py-1 rounded-lg bg-surface-2 text-text-faint text-xs disabled:opacity-40">‹</button>
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => { const start = Math.max(1, Math.min(page - 2, totalPages - 4)); return start + i; }).map((p) => (
              <button key={p} onClick={() => setPage(p)} className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${p === page ? "bg-primary text-on-brand" : "bg-surface-2 text-text-muted hover:bg-surface-1"}`}>{p}</button>
            ))}
            <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="px-2 py-1 rounded-lg bg-surface-2 text-text-faint text-xs disabled:opacity-40">›</button>
            <button onClick={() => setPage(totalPages)} disabled={page === totalPages} className="px-2 py-1 rounded-lg bg-surface-2 text-text-faint text-xs disabled:opacity-40">»</button>
          </div>
        </div>
      )}
      </PanelContent>
    </AdminLayout>

    <BulkActionBar
      selectedCount={selectedIds.size}
      onClearSelection={() => setSelectedIds(new Set())}
      actions={[
        { label: "Archive Selected", onClick: bulkArchive, loading: bulkLoading, variant: "danger" },
        { label: "Restore Selected", onClick: bulkRestore, loading: bulkLoading, variant: "success" },
      ]}
    />
    </>
  );
}

export default function AdminCategoriesPage() {
  return (
    <Suspense>
      <AdminCategoriesInner />
    </Suspense>
  );
}
