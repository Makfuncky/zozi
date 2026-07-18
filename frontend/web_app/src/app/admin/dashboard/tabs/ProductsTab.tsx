"use client";

import { Button } from "@/components/ui/Button";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  CheckCircle2,
  Eye,
  RefreshCw,
  Search,
  ShieldCheck,
  XCircle,
} from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import ApprovalActionModal from "@/components/ApprovalActionModal";
import BulkActionBar from "@/components/BulkActionBar";
import QuickDetailModal from "@/components/QuickDetailModal";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { useToastStore } from "@/lib/toastStore";
import { hasAdminPermission } from "@shared/adminPermissions";
import { dc, useDensity, type Density } from "@/lib/densityContext";
import { PanelContent, PanelTabs } from "@/components/PanelPage";
import { EnterpriseDataTable, type EnterpriseColumn } from "@shared/components/EnterpriseDataTable";
import type { AdminProductRecord } from "@shared/types";
import { useApprovalCheck } from "@/hooks/useApprovalCheck";

type Section = "pending" | "all";

type PendingAction = { productId: number; action: "approve" | "reject" } | null;

const SECTIONS = [
  { key: "pending", label: "Pending Moderation", icon: ShieldCheck },
  { key: "all", label: "All Products", icon: Eye },
] as const;

const STATUS_TONE: Record<string, string> = {
  pending: "theme-chip-warning",
  approved: "theme-chip-success",
  rejected: "theme-chip-danger",
};

function ProductsInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const section = (searchParams?.get("section") || "pending") as Section;
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();
  const role = user?.role ?? null;
  const addToast = useToastStore((state) => state.addToast);
  const { density } = useDensity();
  const textCls = DENSITY_TEXT(density);
  const canModerate = hasAdminPermission(role, "moderation.products");
  const canManage = hasAdminPermission(role, "products.manage");
  const { canApprove, loading: approvalLoading } = useApprovalCheck(user);

  const [products, setProducts] = useState<AdminProductRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [actionId, setActionId] = useState<number | null>(null);
  const [detailId, setDetailId] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [pendingAction, setPendingAction] = useState<PendingAction>(null);

  const loadPending = useCallback(async () => {
    if (section !== "pending") return;
    setLoading(true);
    try {
      const res = await apiFetch("/admin/products/pending");
      if (!res.ok) throw new Error("Failed");
      const payload = await res.json();
      const items = Array.isArray(payload?.data) ? payload.data : Array.isArray(payload) ? payload : [];
      setProducts(items);
    } catch {
      addToast("Failed to load pending products", "error");
      setProducts([]);
    } finally {
      setLoading(false);
    }
  }, [addToast, section]);

  const loadAll = useCallback(async () => {
    if (section !== "all") return;
    setLoading(true);
    try {
      const res = await apiFetch("/admin/products?limit=100");
      if (!res.ok) throw new Error("Failed");
      const payload = await res.json();
      const items = Array.isArray(payload?.data) ? payload.data : Array.isArray(payload) ? payload : [];
      setProducts(items);
    } catch {
      addToast("Failed to load products", "error");
      setProducts([]);
    } finally {
      setLoading(false);
    }
  }, [addToast, section]);

  useEffect(() => {
    if (!isLoggedIn || !(canModerate || canManage)) {
      router.replace("/admin/dashboard");
      return;
    }
    if (section === "pending") loadPending();
    else loadAll();
  }, [isLoggedIn, canModerate, canManage, router, section, loadPending, loadAll]);

  const refresh = useCallback(async () => {
    setRefreshing(true);
    if (section === "pending") await loadPending();
    else await loadAll();
    setRefreshing(false);
  }, [section, loadPending, loadAll]);

  const confirmModerate = useCallback(
    async (productId: number, action: "approve" | "reject", note?: string) => {
      setActionId(productId);
      try {
        const res = await apiFetch(`/admin/products/${productId}/${action}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ note: note || undefined }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          const status = res.status;
          if (status === 403) throw new Error(err.detail || "You do not have authority to perform this action.");
          if (status === 422) throw new Error(err.detail || "Validation error. This product may be blocked by country restriction.");
          throw new Error(err.detail || `Failed to ${action} product`);
        }
        addToast(`Product #${productId} ${action}d`, "success");
        setProducts((curr) => curr.filter((p) => p.id !== productId));
        setSelectedIds((curr) => { const n = new Set(curr); n.delete(productId); return n; });
      } catch (err) {
        addToast(err instanceof Error ? err.message : `Failed to ${action} product`, "error");
      } finally {
        setActionId(null);
      }
    },
    [addToast],
  );

  const requestModerate = useCallback(
    async (productId: number, action: "approve" | "reject", note?: string) => {
      const eligibility = await canApprove("product");
      if (!eligibility.eligible) {
        setPendingAction({ productId, action });
        return;
      }
      await confirmModerate(productId, action, note);
    },
    [canApprove, confirmModerate],
  );

  const bulkModerate = useCallback(
    async (action: "approve" | "reject") => {
      const ids = Array.from(selectedIds);
      if (!ids.length) return;
      setRefreshing(true);
      try {
        const res = await apiFetch("/admin/products/bulk-moderate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ product_ids: ids, action, note: `Bulk ${action} by admin` }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Bulk ${action} failed`);
        }
        addToast(`${ids.length} products ${action}d`, "success");
        setSelectedIds(new Set());
        setProducts((curr) => curr.filter((p) => !ids.includes(p.id)));
      } catch (err) {
        addToast(err instanceof Error ? err.message : `Bulk ${action} failed`, "error");
      } finally {
        setRefreshing(false);
      }
    },
    [addToast, selectedIds],
  );

  const filtered = useMemo(() => {
    if (!search.trim()) return products;
    const q = search.trim().toLowerCase();
    return products.filter((p) => [p.name, p.category, p.supplier_name, `#${p.id}`].some((v) => String(v).toLowerCase().includes(q)));
  }, [products, search]);

  const columns = useMemo<Array<EnterpriseColumn<AdminProductRecord>>>(
    () => [
      { key: "id", label: "ID", width: "100px", sortable: true, sortValue: (r) => r.id, render: (r) => <span className="font-mono text-xs">#{r.id}</span> },
      { key: "name", label: "Product", width: "260px", sortable: true, sortValue: (r) => r.name.toLowerCase(), render: (r) => <span className="text-xs font-semibold text-text">{r.name}</span> },
      { key: "category", label: "Category", width: "160px", render: (r) => <span className="text-xs text-text-muted">{r.category}</span> },
      { key: "supplier_name", label: "Supplier", width: "180px", render: (r) => <span className="text-xs text-text-muted">{r.supplier_name || "—"}</span> },
      { key: "price", label: "Price", width: "120px", sortable: true, sortValue: (r) => Number(r.price ?? 0), align: "right", render: (r) => <span className="font-mono text-xs">{r.price != null ? r.price.toLocaleString() : "—"}</span> },
      { key: "stock", label: "Stock", width: "100px", sortable: true, sortValue: (r) => r.stock, align: "right", render: (r) => <span className="text-xs font-semibold">{r.stock}</span> },
      {
        key: "moderation_status",
        label: "Status",
        width: "160px",
        sortable: true,
        sortValue: (r) => r.moderation_status || "pending",
        render: (r) => (
          <span className={`inline-flex rounded-full px-1.5 py-0.5 text-[10px] font-semibold capitalize ${STATUS_TONE[r.moderation_status || "pending"] || "theme-chip-muted"}`}>
            {r.moderation_status || "pending"}
          </span>
        ),
      },
      {
        key: "actions",
        label: "Actions",
        width: "200px",
        render: (r) => (
          <div className="flex flex-wrap gap-1">
            <Button variant="primary" className="rounded-md px-2 py-1 text-[11px] font-semibold disabled:opacity-50" type="button" onClick={() => requestModerate(r.id, "approve")} disabled={actionId === r.id}>
              {actionId === r.id ? "..." : "Approve"}
            </Button>
            <Button variant="danger" className="rounded-md px-2 py-1 text-[11px] font-semibold disabled:opacity-50" type="button" onClick={() => requestModerate(r.id, "reject")} disabled={actionId === r.id}>
              {actionId === r.id ? "..." : "Reject"}
            </Button>
            <button type="button" onClick={() => setDetailId(r.id)} className="rounded-md border border-border bg-surface-2 px-2 py-1 text-[11px] font-semibold text-text-muted hover:bg-surface-1">
              View
            </button>
          </div>
        ),
      },
    ],
    [actionId, confirmModerate],
  );

  return (
    <AdminLayout title="Product Moderation" headerMode="compact">
      <PanelContent className="space-y-4">
        <div className="theme-card rounded-xl border p-2">
          <PanelTabs
            items={SECTIONS}
            value={section}
            onChange={(next) => router.replace(`/admin/products?section=${next}`, { scroll: false })}
            className="border-0 bg-transparent p-0"
          />
        </div>

        {section === "pending" && (
          <>
            <div className="grid gap-2 sm:grid-cols-3">
              <div className="rounded-xl border border-border bg-surface-1 px-3 py-2.5">
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-text-faint">Pending</p>
                <p className="mt-1 text-lg font-bold text-text">{products.filter((p) => (p.moderation_status || "pending") === "pending").length}</p>
              </div>
              <div className="rounded-xl border border-border bg-surface-1 px-3 py-2.5">
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-text-faint">Selected</p>
                <p className="mt-1 text-lg font-bold text-text">{selectedIds.size}</p>
              </div>
              <div className="rounded-xl border border-border bg-surface-1 px-3 py-2.5">
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-text-faint">Total</p>
                <p className="mt-1 text-lg font-bold text-text">{products.length}</p>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="relative min-w-45 flex-1">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-text-faint" />
                <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search products..." className="theme-input w-full rounded-xl border py-2 pl-9 pr-3 text-xs" />
              </div>
              <button onClick={refresh} disabled={refreshing} className="theme-btn-secondary rounded-lg border px-3 py-2 text-xs font-semibold text-text-muted disabled:opacity-50">
                <RefreshCw className={`inline h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`} /> Refresh
              </button>
            </div>

            {loading ? (
              <div className="space-y-2">{Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-14 animate-pulse rounded-xl bg-surface-2" />)}</div>
            ) : (
              <EnterpriseDataTable
                columns={columns}
                rows={filtered}
                rowKey={(p) => p.id}
                densityMode={density}
                initialRowsPerPage={25}
                enableBulkActions
                enableGlobalSearch={false}
                selectedRowKeys={Array.from(selectedIds)}
                onSelectedRowKeysChange={(keys) => setSelectedIds(new Set(keys.map((k) => Number(k))))}
                emptyState="No pending products."
              />
            )}
          </>
        )}

        {section === "all" && (
          <div className="theme-card rounded-2xl border p-6 text-center text-xs text-text-muted">
            Full product catalog moderation workspace.
          </div>
        )}

        {selectedIds.size > 0 && section === "pending" && (
          <BulkActionBar
            selectedCount={selectedIds.size}
            onClearSelection={() => setSelectedIds(new Set())}
            actions={[
              { label: "Bulk Approve", onClick: () => bulkModerate("approve"), variant: "primary", loading: refreshing },
              { label: "Bulk Reject", onClick: () => bulkModerate("reject"), variant: "danger", loading: refreshing },
            ]}
          />
        )}

        <QuickDetailModal open={detailId != null} title={detailId ? `Product #${detailId}` : "Product details"} onClose={() => setDetailId(null)}>
          {detailId && (() => {
            const product = products.find((p) => p.id === detailId);
            if (!product) return null;
            return (
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-xl border border-border bg-surface-1 p-4">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-faint">Product</p>
                  <div className="mt-3 space-y-2 text-sm text-text-muted">
                    <p><span className="font-medium text-text">Name:</span> {product.name}</p>
                    <p><span className="font-medium text-text">Category:</span> {product.category}</p>
                    <p><span className="font-medium text-text">Price:</span> {product.price != null ? product.price.toLocaleString() : "—"}</p>
                    <p><span className="font-medium text-text">Stock:</span> {product.stock}</p>
                  </div>
                </div>
                <div className="rounded-xl border border-border bg-surface-1 p-4">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-faint">Supplier</p>
                  <div className="mt-3 space-y-2 text-sm text-text-muted">
                    <p><span className="font-medium text-text">Name:</span> {product.supplier_name || "—"}</p>
                    <p><span className="font-medium text-text">ID:</span> {product.supplier_id || "—"}</p>
                  </div>
                </div>
              </div>
            );
          })()}
        </QuickDetailModal>

        <ApprovalActionModal
          isOpen={pendingAction?.action === "approve"}
          resourceType="product"
          resourceLabel={pendingAction ? `#${pendingAction.productId}` : undefined}
          action="approve"
          onClose={() => setPendingAction(null)}
          onConfirm={(options) => pendingAction ? confirmModerate(pendingAction.productId, "approve", options?.note) : Promise.resolve()}
        />
        <ApprovalActionModal
          isOpen={pendingAction?.action === "reject"}
          resourceType="product"
          resourceLabel={pendingAction ? `#${pendingAction.productId}` : undefined}
          action="reject"
          onClose={() => setPendingAction(null)}
          onConfirm={(options) => pendingAction ? confirmModerate(pendingAction.productId, "reject", options?.note) : Promise.resolve()}
        />
      </PanelContent>
    </AdminLayout>
  );
}

function DENSITY_TEXT(mode: Density) {
  return dc(mode, "text-[11px]", "text-xs", "text-sm");
}

export default function AdminProductsPage() {
  return (
    <Suspense>
      <ProductsInner />
    </Suspense>
  );
}
