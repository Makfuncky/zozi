"use client";

import { Button } from "@/components/ui/Button";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  CheckCircle2,
  Package,
  RefreshCw,
  RotateCcw,
  Search,
  Trash2,
  XCircle,
} from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import BulkActionBar from "@/components/BulkActionBar";
import InlineActionButtons from "@/components/InlineActionButtons";
import { PanelContent, PanelHero } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { normalizeListPage } from "@/lib/listResponse";
import { useAuth } from "@/lib/useAuth";
import { useToastStore } from "@/lib/toastStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useAdminCountry } from "@/lib/useAdminCountry";
import { dc, useDensity } from "@/lib/densityContext";
import { EnterpriseDataTable, type EnterpriseColumn } from "@shared/components/EnterpriseDataTable";

interface AdminProduct {
  id: number;
  name: string;
  slug?: string | null;
  category?: string | null;
  brand?: string | null;
  price: number;
  stock: number;
  is_active: boolean;
  is_approved: boolean;
  is_deleted: boolean;
  is_featured?: boolean;
  is_verified?: boolean;
  moderation_status?: string | null;
  supplier_id?: number | null;
  country_code?: string | null;
  image_url?: string | null;
  sales_count?: number;
  rating?: number;
  created_at?: string;
}

type FilterKey = "all" | "pending" | "approved" | "rejected" | "deleted";

const PAGE_SIZE = 50;

const FILTERS: Array<{ key: FilterKey; label: string }> = [
  { key: "all", label: "All" },
  { key: "pending", label: "Pending" },
  { key: "approved", label: "Approved" },
  { key: "rejected", label: "Rejected" },
  { key: "deleted", label: "Deleted" },
];

function AdminProductsInner() {
  const router = useRouter();
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();
  const { density } = useDensity();
  const { selectedCountry, isGlobalView } = useAdminCountry();
  const addToast = useToastStore((s) => s.addToast);
  const formatMoney = useCurrencyStore((s) => s.format);

  const [products, setProducts] = useState<AdminProduct[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<FilterKey>("all");
  const [page, setPage] = useState(1);
  const [actionId, setActionId] = useState<number | null>(null);
  const [archiveTarget, setArchiveTarget] = useState<AdminProduct | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [bulkLoading, setBulkLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn || !["admin", "sub_admin", "moderator"].includes(user?.role || "")) {
      router.push("/admin/login");
    }
  }, [authLoading, isLoggedIn, user, router]);

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("limit", String(PAGE_SIZE));
      params.set("offset", String((page - 1) * PAGE_SIZE));
      if (search.trim()) params.set("search", search.trim());
      if (filter !== "all") params.set("filter", filter);
      const res = await apiFetch(`/admin/products?${params.toString()}`);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error((err as any).detail || "Unable to load products.");
      }
      const payload = normalizeListPage<AdminProduct>(await res.json());
      setProducts(payload.data);
      setTotal(payload.total);
      setLoadError(null);
    } catch (e) {
      setLoadError(e instanceof Error ? e.message : "Unable to load products.");
      setProducts([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [page, search, filter]);

  useEffect(() => {
    if (isLoggedIn) fetchProducts();
  }, [fetchProducts, isLoggedIn]);

  useEffect(() => { setPage(1); }, [search, filter]);

  const archiveProduct = async (id: number) => {
    setActionId(id);
    try {
      const res = await apiFetch(`/admin/products/${id}`, { method: "DELETE" });
      if (res.ok) { await fetchProducts(); addToast("Product deleted", "success"); }
      else { const err = await res.json().catch(() => ({})); addToast((err as any).detail || "Failed to delete", "error"); }
    } finally { setActionId(null); setArchiveTarget(null); }
  };

  const restoreProduct = async (id: number) => {
    setActionId(id);
    try {
      const res = await apiFetch(`/admin/products/${id}/restore`, { method: "POST" });
      if (res.ok) { await fetchProducts(); addToast("Product restored", "success"); }
      else { const err = await res.json().catch(() => ({})); addToast((err as any).detail || "Failed to restore", "error"); }
    } finally { setActionId(null); }
  };

  const moderateProduct = async (id: number, action: "approve" | "reject") => {
    setActionId(id);
    try {
      const res = await apiFetch(`/admin/products/${id}/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: action === "reject" ? JSON.stringify({ note: "Rejected from admin panel" }) : undefined,
      });
      if (res.ok) { await fetchProducts(); addToast(`Product ${action}d`, "success"); }
      else { const err = await res.json().catch(() => ({})); addToast((err as any).detail || `Failed to ${action}`, "error"); }
    } finally { setActionId(null); }
  };

  const bulkModerate = async (action: "approve" | "reject") => {
    const ids = Array.from(selectedIds);
    if (!ids.length) return;
    setBulkLoading(true);
    try {
      const res = await apiFetch("/admin/products/bulk-moderate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_ids: ids, action, note: action === "reject" ? "Bulk reject from admin panel" : undefined }),
      });
      if (res.ok) { await fetchProducts(); setSelectedIds(new Set()); addToast(`${ids.length} products ${action}d`, "success"); }
      else { const err = await res.json().catch(() => ({})); addToast((err as any).detail || "Bulk action failed", "error"); }
    } finally { setBulkLoading(false); }
  };

  const bulkDelete = async () => {
    const ids = Array.from(selectedIds);
    if (!ids.length) return;
    setBulkLoading(true);
    try {
      const res = await apiFetch("/admin/products/bulk", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_ids: ids }),
      });
      if (res.ok) { await fetchProducts(); setSelectedIds(new Set()); addToast(`${ids.length} products deleted`, "success"); }
      else { const err = await res.json().catch(() => ({})); addToast((err as any).detail || "Bulk delete failed", "error"); }
    } finally { setBulkLoading(false); }
  };

  const bodyText = dc(density, "text-[10px]", "text-xs", "text-sm");
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const statusBadge = (p: AdminProduct) => {
    if (p.is_deleted) return <span className="rounded-full bg-danger/10 px-2 py-0.5 text-[10px] font-semibold text-danger">Deleted</span>;
    if (p.is_approved) return <span className="rounded-full bg-success/10 px-2 py-0.5 text-[10px] font-semibold text-success">Approved</span>;
    return <span className="rounded-full bg-warning/10 px-2 py-0.5 text-[10px] font-semibold text-warning">Pending</span>;
  };

  const columns: Array<EnterpriseColumn<AdminProduct>> = [
    {
      key: "id", label: "#", width: "70px", sortable: true,
      render: (p) => <span className={`${bodyText} font-mono tabular-nums text-text-faint`}>#{p.id}</span>,
    },
    {
      key: "name", label: "Product", width: "280px", sortable: true, searchValue: (p) => p.name,
      render: (p) => (
        <div className="flex items-center gap-3">
          {p.image_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={p.image_url} alt="" className="h-9 w-9 flex-none rounded-lg border border-border object-cover"
              onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = "none"; }} />
          ) : (
            <div className="flex h-9 w-9 flex-none items-center justify-center rounded-lg border border-border bg-surface-2 text-text-faint">
              <Package className="h-4 w-4" />
            </div>
          )}
          <div className="min-w-0">
            <p className={`${bodyText} truncate font-medium text-text`}>{p.name}</p>
            <p className={`${bodyText} truncate text-text-faint`}>{p.brand ? `${p.brand} · ` : ""}{p.category || "—"}</p>
          </div>
        </div>
      ),
    },
    { key: "price", label: "Price", width: "110px", align: "right", sortable: true, render: (p) => <span className={`${bodyText} font-semibold tabular-nums text-text`}>{formatMoney(p.price)}</span> },
    { key: "stock", label: "Stock", width: "90px", align: "right", sortable: true, render: (p) => <span className={`${bodyText} tabular-nums ${p.stock <= 0 ? "text-danger" : "text-text-muted"}`}>{p.stock}</span> },
    {
      key: "is_approved", label: "Status", width: "100px",
      render: (p) => statusBadge(p),
    },
    {
      key: "is_featured", label: "Flags", width: "110px",
      render: (p) => (
        <div className="flex flex-wrap gap-1">
          {p.is_featured ? <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-semibold text-primary">Featured</span> : null}
          {p.is_verified ? <span className="rounded-full bg-info/10 px-2 py-0.5 text-[10px] font-semibold text-info">Verified</span> : null}
          {!p.is_active ? <span className="rounded-full bg-warning/10 px-2 py-0.5 text-[10px] font-semibold text-warning">Inactive</span> : null}
        </div>
      ),
    },
    { key: "supplier_id", label: "Supplier", width: "90px", render: (p) => <span className={`${bodyText} text-text-faint`}>{p.supplier_id ? `#${p.supplier_id}` : "—"}</span> },
    { key: "created_at", label: "Created", width: "120px", render: (p) => <span className={`${bodyText} tabular-nums text-text-faint`}>{p.created_at ? new Date(p.created_at).toLocaleDateString() : "—"}</span> },
  ];

  const hasActiveFilters = search.trim() !== "" || filter !== "all";
  const clearFilters = () => { setSearch(""); setFilter("all"); setPage(1); };

  const stats = useMemo(() => ({
    total: products.length,
    approved: products.filter((p) => !p.is_deleted && p.is_approved).length,
    pending: products.filter((p) => !p.is_deleted && !p.is_approved).length,
    deleted: products.filter((p) => p.is_deleted).length,
  }), [products]);

  if (authLoading) return null;

  return (
    <>
      {archiveTarget ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4">
          <div className="theme-card w-full max-w-sm rounded-xl border p-6">
            <h2 className="text-base font-semibold text-text">Delete product?</h2>
            <p className="mt-2 text-xs text-text-muted"><span className="font-medium text-text">{archiveTarget.name}</span> will be hidden from the storefront.</p>
            <div className="mt-5 flex gap-3">
              <button onClick={() => setArchiveTarget(null)} className="flex-1 rounded-xl border border-border py-2 text-xs text-text-muted hover:bg-surface-2">Cancel</button>
              <Button variant="danger" className="flex-1 rounded-xl py-2 text-xs font-medium disabled:opacity-50" onClick={() => archiveProduct(archiveTarget.id)} disabled={actionId === archiveTarget.id}>{actionId === archiveTarget.id ? "Deleting..." : "Delete"}</Button>
            </div>
          </div>
        </div>
      ) : null}

      <AdminLayout title="Products" headerMode="compact">
        <PanelContent width="full" className="space-y-4">
          <PanelHero
            eyebrow="Catalog"
            title="Products"
            description={isGlobalView ? "All assigned countries" : `Country: ${selectedCountry?.code ?? "—"}`}
            icon={<Package className="h-5 w-5" />}
            actions={
              <button onClick={fetchProducts} disabled={loading}
                className="flex items-center gap-2 rounded-xl border border-border bg-surface-2 px-4 py-2 text-xs font-semibold text-text-muted hover:text-text disabled:opacity-50">
                <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} /> Refresh
              </button>
            }
          />

          <div className="grid gap-3 sm:grid-cols-4">
            <div className="theme-card rounded-xl border p-4">
              <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-text-faint">Showing</p>
              <p className="mt-1.5 text-2xl font-bold text-text tabular-nums">{stats.total}</p>
            </div>
            <div className="theme-card rounded-xl border p-4">
              <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-text-faint">Approved</p>
              <p className="mt-1.5 text-2xl font-bold text-success tabular-nums">{stats.approved}</p>
            </div>
            <div className="theme-card rounded-xl border p-4">
              <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-text-faint">Pending</p>
              <p className="mt-1.5 text-2xl font-bold text-warning tabular-nums">{stats.pending}</p>
            </div>
            <div className="theme-card rounded-xl border p-4">
              <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-text-faint">Deleted</p>
              <p className="mt-1.5 text-2xl font-bold text-danger tabular-nums">{stats.deleted}</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {FILTERS.map((f) => (
              <button
                key={f.key}
                onClick={() => setFilter(f.key)}
                className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
                  filter === f.key ? "bg-primary text-on-brand" : "border border-border bg-surface-1 text-text-muted hover:text-text"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="space-y-2">
              {Array.from({ length: 10 }).map((_, i) => <div key={i} className="h-10 rounded-xl bg-surface-2 animate-pulse" />)}
            </div>
          ) : products.length === 0 ? (
            <div className="rounded-2xl border border-border bg-surface-1 px-6 py-12 text-center">
              <Package className="mx-auto h-8 w-8 text-text-faint" />
              <p className="mt-3 text-sm font-semibold text-text">{loadError || (hasActiveFilters ? "No products match filters" : "No products yet")}</p>
              <p className="mt-2 text-xs text-text-faint">{loadError || (hasActiveFilters ? "Try clearing filters" : "Products will appear here once suppliers add them.")}</p>
              <div className="mt-4 flex items-center justify-center gap-2">
                {loadError ? <Button variant="primary" onClick={fetchProducts}>Retry</Button> : null}
                {hasActiveFilters ? <button onClick={clearFilters} className="rounded-xl border border-border px-4 py-2 text-xs font-semibold text-text-muted hover:bg-surface-2">Clear filters</button> : null}
              </div>
            </div>
          ) : (
            <EnterpriseDataTable
              columns={columns}
              rows={products}
              rowKey={(p) => p.id}
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
                    <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search products, brand, category" className="h-9 w-full rounded-xl border border-border bg-surface-1 py-2 pl-9 pr-3 text-xs text-text placeholder:text-text-faint focus:border-primary focus:outline-none" />
                  </div>
                  <button onClick={fetchProducts} disabled={loading} className="flex h-9 items-center justify-center rounded-lg border border-border bg-surface-1 px-3 text-xs text-text-muted transition-colors hover:bg-surface-2 disabled:opacity-50"><RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} /></button>
                  {hasActiveFilters ? <button onClick={clearFilters} className="h-9 rounded-lg border border-border bg-surface-1 px-3 text-xs font-medium text-text-muted hover:bg-surface-2 hover:text-text">Clear</button> : null}
                </>
              )}
              emptyState={loadError || "No products matched."}
              rowActions={(p) => (
                <div className="flex justify-end">
                  <InlineActionButtons actions={[
                    ...(p.is_deleted
                      ? [{ label: "Restore", icon: <RotateCcw className="h-3.5 w-3.5" />, onClick: () => restoreProduct(p.id), tone: "success" as const, disabled: actionId === p.id }]
                      : [
                          { label: "Approve", icon: <CheckCircle2 className="h-3.5 w-3.5" />, onClick: () => moderateProduct(p.id, "approve"), tone: "success" as const, disabled: actionId === p.id },
                          { label: "Reject", icon: <XCircle className="h-3.5 w-3.5" />, onClick: () => moderateProduct(p.id, "reject"), tone: "danger" as const, disabled: actionId === p.id },
                          { label: "Delete", icon: <Trash2 className="h-3.5 w-3.5" />, onClick: () => setArchiveTarget(p), tone: "danger" as const, disabled: actionId === p.id },
                        ]
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
          { label: "Approve", onClick: () => bulkModerate("approve"), loading: bulkLoading, variant: "success" },
          { label: "Reject", onClick: () => bulkModerate("reject"), loading: bulkLoading, variant: "danger" },
          { label: "Delete", onClick: bulkDelete, loading: bulkLoading, variant: "danger" },
        ]}
      />
    </>
  );
}

export default function AdminProductsPage() {
  return (
    <Suspense>
      <AdminProductsInner />
    </Suspense>
  );
}
