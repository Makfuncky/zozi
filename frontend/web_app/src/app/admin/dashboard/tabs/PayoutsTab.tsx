"use client";

import { Button } from "@/components/ui/Button";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  AlertCircle,
  CheckCircle2,
  DollarSign,
  Download,
  RefreshCw,
  Search,
  XCircle,
} from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import ApprovalActionModal from "@/components/ApprovalActionModal";
import BulkActionBar from "@/components/BulkActionBar";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useAdminCountry } from "@/lib/useAdminCountry";
import { useToastStore } from "@/lib/toastStore";
import { hasAdminPermission } from "@shared/adminPermissions";
import { dc, useDensity } from "@/lib/densityContext";
import { PanelContent, PanelTabs } from "@/components/PanelPage";
import { EnterpriseDataTable, type EnterpriseColumn } from "@shared/components/EnterpriseDataTable";
import { getPendingPayouts, verifyPayout as apiVerifyPayout } from "@/lib/payoutsApi";
import type { AdminPayoutRecord } from "@shared/types";
import { useApprovalCheck } from "@/hooks/useApprovalCheck";

type Section = "pending" | "history";

const SECTIONS = [
  { key: "pending", label: "Pending", icon: DollarSign },
  { key: "history", label: "History", icon: CheckCircle2 },
] as const;

const STATUS_TONE: Record<string, string> = {
  pending: "theme-chip-warning",
  processing: "theme-chip-info",
  completed: "theme-chip-success",
  failed: "theme-chip-danger",
};

type PendingVerify = { payoutId: number } | null;

function PayoutsInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const section = (searchParams?.get("section") || "pending") as Section;
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();
  const role = user?.role ?? null;
  const addToast = useToastStore((state) => state.addToast);
  const formatMoney = useCurrencyStore((state) => state.format);
  const { density } = useDensity();
  const { selectedCountry, isGlobalView } = useAdminCountry();
  const countryCode = isGlobalView ? "*" : selectedCountry?.code || "*";
  const canVerify = hasAdminPermission(role, "payouts.verify");
  const { canApprove } = useApprovalCheck(user);

  const [payouts, setPayouts] = useState<AdminPayoutRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [verifyingId, setVerifyingId] = useState<number | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [verifyNote, setVerifyNote] = useState<Record<number, string>>({});
  const [search, setSearch] = useState("");
  const [pendingVerify, setPendingVerify] = useState<PendingVerify>(null);

  const loadPending = useCallback(async () => {
    if (section !== "pending") return;
    try {
      const data = await getPendingPayouts(countryCode);
      setPayouts(data.items);
      setTotal(data.total);
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Failed to load payouts", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast, section, countryCode]);

  useEffect(() => {
    if (!isLoggedIn) return;
    if (!canVerify) {
      router.replace("/admin/dashboard");
      return;
    }
    if (section === "pending") loadPending();
  }, [isLoggedIn, canVerify, router, section, loadPending]);

  const refresh = useCallback(async () => {
    setRefreshing(true);
    await loadPending();
    setRefreshing(false);
  }, [loadPending]);

  const confirmVerify = useCallback(
    async (payoutId: number, note?: string) => {
      setVerifyingId(payoutId);
      try {
        await apiVerifyPayout(countryCode, payoutId, { note: note || undefined });
        addToast(`Payout #${payoutId} verified`, "success");
        setPayouts((curr) => curr.filter((p) => p.id !== payoutId));
        setSelectedIds((curr) => { const n = new Set(curr); n.delete(payoutId); return n; });
      } catch (err) {
        addToast(err instanceof Error ? err.message : `Failed to verify payout #${payoutId}`, "error");
      } finally {
        setVerifyingId(null);
      }
    },
    [addToast, countryCode],
  );

  const requestVerify = useCallback(
    async (payoutId: number) => {
      const payout = payouts.find((p) => p.id === payoutId);
      const eligibility = await canApprove("payout", payout?.amount);
      if (!eligibility.eligible) {
        setPendingVerify({ payoutId });
        return;
      }
      await confirmVerify(payoutId, verifyNote[payoutId]);
    },
    [canApprove, confirmVerify, payouts, verifyNote],
  );

  const bulkVerify = useCallback(async () => {
    const ids = Array.from(selectedIds);
    if (!ids.length) return;
    setRefreshing(true);
    try {
      await Promise.all(ids.map((id) => apiVerifyPayout(countryCode, id, { note: verifyNote[id] || undefined })));
      addToast(`${ids.length} payout(s) verified`, "success");
      setSelectedIds(new Set());
      setPayouts((curr) => curr.filter((p) => !ids.includes(p.id)));
    } catch {
      addToast("Some payouts failed to verify", "error");
    } finally {
      setRefreshing(false);
    }
  }, [addToast, countryCode, selectedIds, verifyNote]);

  const filtered = useMemo(() => {
    if (!search.trim()) return payouts;
    const q = search.trim().toLowerCase();
    return payouts.filter((p) =>
      [p.supplier_name, p.reference, `#${p.id}`, p.status].some((v) => String(v).toLowerCase().includes(q))
    );
  }, [payouts, search]);

  const columns = useMemo<Array<EnterpriseColumn<AdminPayoutRecord>>>(
    () => [
      { key: "id", label: "ID", width: "110px", sortable: true, sortValue: (r) => r.id, render: (r) => <span className="font-mono text-xs">#{r.id}</span> },
      { key: "supplier_name", label: "Supplier", width: "220px", sortable: true, sortValue: (r) => (r.supplier_name || "").toLowerCase(), render: (r) => <span className="text-xs font-semibold text-text">{r.supplier_name || `Supplier #${r.supplier_id}`}</span> },
      { key: "amount", label: "Amount", width: "140px", sortable: true, sortValue: (r) => r.amount, align: "right", render: (r) => <span className="font-mono text-xs font-semibold text-text">{formatMoney(r.amount)}</span> },
      { key: "reference", label: "Reference", width: "180px", sortable: true, sortValue: (r) => (r.reference || ""), render: (r) => <span className="font-mono text-xs text-text-muted">{r.reference || "—"}</span> },
      { key: "status", label: "Status", width: "150px", sortable: true, sortValue: (r) => r.status, render: (r) => (
        <span className={`inline-flex rounded-full px-1.5 py-0.5 text-[10px] font-semibold capitalize ${STATUS_TONE[r.status] || "theme-chip-muted"}`}>{r.status}</span>
      )},
      { key: "created_at", label: "Created", width: "160px", sortable: true, sortValue: (r) => new Date(r.created_at).getTime(), render: (r) => <span className="text-xs text-text-muted">{new Date(r.created_at).toLocaleDateString()}</span> },
      {
        key: "actions",
        label: "Actions",
        width: "220px",
        render: (r) => (
          <div className="flex items-center gap-2">
            <input
              value={verifyNote[r.id] || ""}
              onChange={(e) => setVerifyNote((curr) => ({ ...curr, [r.id]: e.target.value }))}
              placeholder="Note"
              className="theme-input rounded-lg border px-2 py-1 text-[11px] w-28"
            />
            <Button variant="primary" className="rounded-lg px-2 py-1 text-[11px] font-semibold disabled:opacity-50" type="button"
              onClick={() => requestVerify(r.id)}
              disabled={verifyingId === r.id}
            >
              {verifyingId === r.id ? "..." : "Verify"}
            </Button>
          </div>
        ),
      },
    ],
    [formatMoney, requestVerify, verifyNote, verifyingId],
  );

  return (
    <AdminLayout title="Payouts" headerMode="compact">
      <PanelContent className="space-y-4">
        <div className="theme-card rounded-xl border p-2">
          <PanelTabs
            items={SECTIONS}
            value={section}
            onChange={(next) => router.replace(`/admin/finance?section=${next}`, { scroll: false })}
            className="border-0 bg-transparent p-0"
          />
        </div>

        {section === "pending" && (
          <>
            <div className="grid gap-2 sm:grid-cols-3">
              <div className="rounded-xl border border-border bg-surface-1 px-3 py-2.5">
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-text-faint">Pending</p>
                <p className="mt-1 text-lg font-bold text-text">{total}</p>
              </div>
              <div className="rounded-xl border border-border bg-surface-1 px-3 py-2.5">
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-text-faint">Total Value</p>
                <p className="mt-1 text-lg font-bold text-text">{formatMoney(payouts.reduce((s, p) => s + p.amount, 0))}</p>
              </div>
              <div className="rounded-xl border border-border bg-surface-1 px-3 py-2.5">
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-text-faint">Selected</p>
                <p className="mt-1 text-lg font-bold text-text">{selectedIds.size}</p>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="relative min-w-45 flex-1">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-text-faint" />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search supplier, reference, or ID..."
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
              <div className="theme-card rounded-2xl border p-8 text-center text-xs text-text-muted">No pending payouts.</div>
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
                emptyState="No pending payouts matched."
                rowActions={(p) => (
                  <div className="flex flex-wrap justify-end gap-1">
                    <Button variant="primary" className="rounded-md px-2 py-1 text-[11px] font-semibold disabled:opacity-50" onClick={() => requestVerify(p.id)} disabled={verifyingId === p.id}>
                      {verifyingId === p.id ? "..." : "Verify"}
                    </Button>
                  </div>
                )}
              />
            )}
          </>
        )}

        {section === "history" && (
          <div className="theme-card rounded-2xl border p-6 text-center text-xs text-text-muted">
            Verified payouts history will appear here.
          </div>
        )}

        {selectedIds.size > 0 && section === "pending" && (
          <BulkActionBar
            selectedCount={selectedIds.size}
            onClearSelection={() => setSelectedIds(new Set())}
            actions={[
              { label: "Verify Selected", onClick: bulkVerify, variant: "primary", loading: refreshing },
            ]}
          />
        )}

        <ApprovalActionModal
          isOpen={!!pendingVerify}
          resourceType="payout"
          resourceLabel={pendingVerify ? `#${pendingVerify.payoutId}` : undefined}
          action="verify"
          onClose={() => setPendingVerify(null)}
          onConfirm={async (options) => { if (!pendingVerify) return; await confirmVerify(pendingVerify.payoutId, options?.note); }}
        />
      </PanelContent>
    </AdminLayout>
  );
}

export default function AdminPayoutsPage() {
  return (
    <Suspense>
      <PayoutsInner />
    </Suspense>
  );
}
