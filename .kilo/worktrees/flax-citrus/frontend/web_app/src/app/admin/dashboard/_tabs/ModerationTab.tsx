"use client";

import { Button } from "@/components/ui/Button";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  CheckCircle2,
  RefreshCw,
  Search,
  ShieldCheck,
  Store,
  XCircle,
} from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import ApprovalActionModal from "@/components/ApprovalActionModal";
import BulkActionBar from "@/components/BulkActionBar";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { useToastStore } from "@/lib/toastStore";
import { hasAdminPermission } from "@shared/adminPermissions";
import { dc, useDensity } from "@/lib/densityContext";
import { PanelContent, PanelTabs } from "@/components/PanelPage";
import { EnterpriseDataTable, type EnterpriseColumn } from "@shared/components/EnterpriseDataTable";

interface AdminSupplierRecord {
  id: number;
  business_name?: string | null;
  username: string;
  email: string;
  verification_status?: string | null;
  is_active?: boolean | number;
  created_at?: string | null;
}

import { useApprovalCheck } from "@/hooks/useApprovalCheck";

type Section = "queue" | "all";

const SECTIONS = [
  { key: "queue", label: "Verification Queue", icon: ShieldCheck },
  { key: "all", label: "All Suppliers", icon: Store },
] as const;

const STATUS_TONE: Record<string, string> = {
  pending: "theme-chip-warning",
  approved: "theme-chip-success",
  rejected: "theme-chip-danger",
  verified: "theme-chip-success",
};

type PendingSupplierAction = { supplierId: number; action: "verify" | "reject" } | null;

function ModerationInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const section = (searchParams?.get("section") || "queue") as Section;
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();
  const role = user?.role ?? null;
  const addToast = useToastStore((state) => state.addToast);
  const { density } = useDensity();
  const canModerate = hasAdminPermission(role, "moderation.suppliers");
  const { canApprove } = useApprovalCheck(user);

  const [suppliers, setSuppliers] = useState<AdminSupplierRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [actionId, setActionId] = useState<number | null>(null);
  const [noteMap, setNoteMap] = useState<Record<number, string>>({});
  const [search, setSearch] = useState("");
  const [pendingSupplierAction, setPendingSupplierAction] = useState<PendingSupplierAction>(null);

  const loadQueue = useCallback(async () => {
    if (section !== "queue") return;
    setLoading(true);
    try {
      const res = await apiFetch("/admin/suppliers/pending");
      if (!res.ok) throw new Error("Failed");
      const payload = await res.json();
      const items = Array.isArray(payload?.data) ? payload.data : Array.isArray(payload) ? payload : [];
      setSuppliers(items);
    } catch {
      addToast("Failed to load pending suppliers", "error");
      setSuppliers([]);
    } finally {
      setLoading(false);
    }
  }, [addToast, section]);

  const loadAll = useCallback(async () => {
    if (section !== "all") return;
    setLoading(true);
    try {
      const res = await apiFetch("/admin/suppliers/all?limit=100");
      if (!res.ok) throw new Error("Failed");
      const payload = await res.json();
      const items = Array.isArray(payload?.items) ? payload.items : Array.isArray(payload) ? payload : [];
      setSuppliers(items);
    } catch {
      addToast("Failed to load suppliers", "error");
      setSuppliers([]);
    } finally {
      setLoading(false);
    }
  }, [addToast, section]);

  useEffect(() => {
    if (!isLoggedIn || !canModerate) {
      router.replace("/admin/dashboard");
      return;
    }
    if (section === "queue") loadQueue();
    else loadAll();
  }, [isLoggedIn, canModerate, router, section, loadQueue, loadAll]);

  const refresh = useCallback(async () => {
    setRefreshing(true);
    if (section === "queue") await loadQueue();
    else await loadAll();
    setRefreshing(false);
  }, [section, loadQueue, loadAll]);

  const confirmSupplierAction = useCallback(
    async (supplierId: number, action: "verify" | "reject", note?: string) => {
      setActionId(supplierId);
      try {
        const res = await apiFetch(`/admin/suppliers/${supplierId}/${action}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ note: note || undefined }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          const status = res.status;
          if (status === 403) throw new Error(err.detail || "You do not have authority to perform this action.");
          throw new Error(err.detail || `Failed to ${action} supplier`);
        }
        addToast(`Supplier #${supplierId} ${action}d`, "success");
        setSuppliers((curr) => curr.filter((s) => s.id !== supplierId));
        setSelectedIds((curr) => { const n = new Set(curr); n.delete(supplierId); return n; });
      } catch (err) {
        addToast(err instanceof Error ? err.message : `Failed to ${action} supplier`, "error");
      } finally {
        setActionId(null);
      }
    },
    [addToast],
  );

  const requestSupplierAction = useCallback(
    async (supplierId: number, action: "verify" | "reject") => {
      const eligibility = await canApprove("supplier");
      if (!eligibility.eligible) {
        setPendingSupplierAction({ supplierId, action });
        return;
      }
      await confirmSupplierAction(supplierId, action, noteMap[supplierId]);
    },
    [canApprove, confirmSupplierAction, noteMap],
  );

  const bulkVerify = useCallback(
    async (action: "verify" | "reject") => {
      const ids = Array.from(selectedIds);
      if (!ids.length) return;
      setRefreshing(true);
      const results = { ok: 0, fail: 0 };
      for (const id of ids) {
        try {
          const res = await apiFetch(`/admin/suppliers/${id}/${action}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ note: noteMap[id] || `Bulk ${action}` }),
          });
          if (res.ok) results.ok += 1;
          else results.fail += 1;
        } catch {
          results.fail += 1;
        }
      }
      if (results.ok > 0) {
        addToast(`${results.ok} supplier(s) ${action}d`, "success");
        setSelectedIds(new Set());
        setSuppliers((curr) => curr.filter((s) => !ids.includes(s.id)));
      }
      if (results.fail > 0) {
        addToast(`${results.fail} supplier(s) failed`, "error");
      }
    },
    [addToast, selectedIds, noteMap],
  );

  const columns = useMemo<Array<EnterpriseColumn<AdminSupplierRecord>>>(
    () => [
      {
        key: "id",
        label: "ID",
        width: "110px",
        sortable: true,
        sortValue: (row) => row.id,
        render: (row) => <span className="font-mono text-xs text-text">#{row.id}</span>,
      },
      {
        key: "name",
        label: "Supplier",
        width: "240px",
        sortable: true,
        sortValue: (row) => (row.business_name || row.username || "").toLowerCase(),
        render: (row) => (
          <div>
            <div className="text-xs font-semibold text-text">{row.business_name || row.username}</div>
            <div className="text-[10px] text-text-faint">@{row.username}</div>
          </div>
        ),
      },
      {
        key: "email",
        label: "Email",
        width: "220px",
        sortable: true,
        sortValue: (row) => (row.email || "").toLowerCase(),
        render: (row) => <span className="text-xs text-text-muted">{row.email}</span>,
      },
      {
        key: "status",
        label: "Status",
        width: "150px",
        sortable: true,
        sortValue: (row) => row.verification_status || "pending",
        render: (row) => (
          <span className={`inline-flex rounded-full px-1.5 py-0.5 text-[10px] font-semibold capitalize ${STATUS_TONE[row.verification_status || "pending"] || "theme-chip-muted"}`}>
            {row.verification_status || "pending"}
          </span>
        ),
      },
      {
        key: "created",
        label: "Created",
        width: "140px",
        sortable: true,
        sortValue: (row) => new Date(row.created_at || 0).getTime(),
        render: (row) => <span className="text-xs text-text-muted">{new Date(row.created_at || 0).toLocaleDateString()}</span>,
      },
      {
        key: "actions",
        label: "Actions",
        width: "260px",
        render: (row) => (
          <div className="flex flex-wrap items-center gap-2">
            <input
              value={noteMap[row.id] || ""}
              onChange={(event) => setNoteMap((current) => ({ ...current, [row.id]: event.target.value }))}
              placeholder="Note"
              className="theme-input rounded-lg border px-2 py-1 text-[11px] w-28"
            />
            {row.verification_status === "pending" ? (
              <Button variant="primary" className="rounded-lg px-2 py-1 text-[11px] font-semibold disabled:opacity-50" type="button"
                onClick={() => requestSupplierAction(row.id, "verify")}
                disabled={actionId === row.id}
              >
                {actionId === row.id ? "..." : "Verify"}
              </Button>
            ) : null}
            {row.verification_status !== "approved" && row.verification_status !== "rejected" ? (
              <Button variant="danger" className="rounded-lg px-2 py-1 text-[11px] font-semibold disabled:opacity-50" type="button"
                onClick={() => requestSupplierAction(row.id, "reject")}
                disabled={actionId === row.id}
              >
                {actionId === row.id ? "..." : "Reject"}
              </Button>
            ) : null}
          </div>
        ),
      },
    ],
    [actionId, noteMap, requestSupplierAction],
  );

  const filtered = useMemo(() => {
    if (!search.trim()) return suppliers;
    const q = search.trim().toLowerCase();
    return suppliers.filter((row) =>
      [row.business_name, row.username, row.email, `#${row.id}`, row.verification_status].some((value) => String(value || "").toLowerCase().includes(q))
    );
  }, [suppliers, search]);

  return (
    <AdminLayout title="Moderation" headerMode="compact">
      <PanelContent className="space-y-4">
        <div className="theme-card rounded-xl border p-2">
          <PanelTabs
            items={SECTIONS}
            value={section}
            onChange={(next) => router.replace(`/admin/dashboard?section=${next}`, { scroll: false })}
            className="border-0 bg-transparent p-0"
          />
        </div>

        {section === "queue" && (
          <div className="grid gap-2 sm:grid-cols-3">
            <div className="rounded-xl border border-border bg-surface-1 px-3 py-2.5">
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-text-faint">Pending</p>
              <p className="mt-1 text-lg font-bold text-text">{suppliers.length}</p>
            </div>
            <div className="rounded-xl border border-border bg-surface-1 px-3 py-2.5">
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-text-faint">Selected</p>
              <p className="mt-1 text-lg font-bold text-text">{selectedIds.size}</p>
            </div>
            <div className="rounded-xl border border-border bg-surface-1 px-3 py-2.5">
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-text-faint">Actions</p>
              <p className="mt-1 text-lg font-bold text-text">{suppliers.filter((row) => row.verification_status === "pending").length}</p>
            </div>
          </div>
        )}

        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="relative min-w-45 flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-text-faint" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search supplier, email, or ID..."
              className="theme-input w-full rounded-xl border py-2 pl-9 pr-3 text-xs"
            />
          </div>
          <div className="flex gap-2">
            <button onClick={refresh} disabled={refreshing} className="theme-btn-secondary rounded-lg border px-3 py-2 text-xs font-semibold text-text-muted disabled:opacity-50">
              <RefreshCw className={`inline h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`} /> Refresh
            </button>
          </div>
        </div>

        {loading ? (
          <div className="space-y-2">{Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-16 animate-pulse rounded-xl bg-surface-2" />)}</div>
        ) : filtered.length === 0 ? (
          <div className="theme-card rounded-2xl border p-8 text-center text-xs text-text-muted">No suppliers matched.</div>
        ) : (
          <EnterpriseDataTable
            columns={columns}
            rows={filtered}
            rowKey={(row) => row.id}
            densityMode={density}
            initialRowsPerPage={25}
            enableBulkActions
            enableGlobalSearch={false}
            selectedRowKeys={Array.from(selectedIds)}
            onSelectedRowKeysChange={(keys) => setSelectedIds(new Set(keys.map((k) => Number(k))))}
            emptyState="No suppliers matched."
            rowActions={(row) => (
              <div className="flex flex-wrap justify-end gap-1">
                <Button variant="primary" className="rounded-md px-2 py-1 text-[11px] font-semibold disabled:opacity-50" onClick={() => requestSupplierAction(row.id, "verify")} disabled={actionId === row.id}>
                  {actionId === row.id ? "..." : "Verify"}
                </Button>
                <Button variant="danger" className="rounded-md px-2 py-1 text-[11px] font-semibold disabled:opacity-50" onClick={() => requestSupplierAction(row.id, "reject")} disabled={actionId === row.id}>
                  {actionId === row.id ? "..." : "Reject"}
                </Button>
              </div>
            )}
          />
        )}

        {section === "all" && (
          <div className="theme-card rounded-2xl border p-6 text-center text-xs text-text-muted">
            Moderation history will appear here.
          </div>
        )}

        {selectedIds.size > 0 && (
          <BulkActionBar
            selectedCount={selectedIds.size}
            onClearSelection={() => setSelectedIds(new Set())}
            actions={[
              { label: "Approve Selected", onClick: () => bulkVerify("verify"), variant: "success", loading: refreshing },
              { label: "Reject Selected", onClick: () => bulkVerify("reject"), variant: "danger", loading: refreshing },
            ]}
          />
        )}

        <ApprovalActionModal
          isOpen={!!pendingSupplierAction}
          resourceType="supplier"
          resourceLabel={pendingSupplierAction ? `#${pendingSupplierAction.supplierId}` : undefined}
          action={pendingSupplierAction?.action || "verify"}
          onClose={() => setPendingSupplierAction(null)}
          onConfirm={async (options) => { if (!pendingSupplierAction) return; await confirmSupplierAction(pendingSupplierAction.supplierId, pendingSupplierAction.action, options?.note); }}
        />
      </PanelContent>
    </AdminLayout>
  );
}

export default function AdminModerationPage() {
  return (
    <Suspense>
      <ModerationInner />
    </Suspense>
  );
}
