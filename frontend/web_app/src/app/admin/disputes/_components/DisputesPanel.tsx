"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { RefreshCw, ShieldAlert } from "@/lib/icons";
import BulkActionBar from "@/components/BulkActionBar";
import { PanelContent, PanelHero } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";
import { useAuth } from "@/lib/useAuth";
import { hasAdminPermission } from "@shared/adminPermissions";

interface AdminDispute {
  id: number;
  supplier_id?: number;
  dispute_type: string;
  priority?: string;
  status?: string;
  title?: string | null;
  description?: string | null;
  resolution_notes?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

const STATUS_OPTIONS = ["open", "under_review", "resolved", "rejected", "closed"];
const PRIORITY_OPTIONS = ["low", "medium", "high", "urgent"];

function statusChipClass(status?: string): string {
  switch (status) {
    case "resolved":
    case "closed":
      return "theme-chip-success";
    case "rejected":
      return "theme-chip-muted";
    case "under_review":
      return "theme-chip-warning";
    default:
      return "theme-chip-info";
  }
}

export default function DisputesPanel() {
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();
  const { addToast } = useToastStore();

  const [data, setData] = useState<AdminDispute[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");

  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [savingId, setSavingId] = useState<number | null>(null);
  const [bulkStatus, setBulkStatus] = useState("");
  const [bulkPriority, setBulkPriority] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set("status", statusFilter);
      if (priorityFilter) params.set("priority", priorityFilter);
      if (typeFilter) params.set("type", typeFilter);
      const response = await apiFetch(`/admin/disputes?${params.toString()}`);
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || "Failed to load disputes");
      }
      const payload = await response.json();
      const rows: AdminDispute[] = Array.isArray(payload) ? payload : payload?.data ?? [];
      setData(rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load disputes");
    } finally {
      setLoading(false);
    }
  }, [statusFilter, priorityFilter, typeFilter]);

  useEffect(() => {
    if (!authLoading && isLoggedIn && hasAdminPermission(user?.role, "moderation.suppliers")) {
      void load();
    }
  }, [authLoading, isLoggedIn, user?.role, load]);

  const patchDispute = useCallback(
    async (disputeId: number, payload: Record<string, unknown>) => {
      setSavingId(disputeId);
      try {
        const response = await apiFetch(`/admin/disputes/${disputeId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!response.ok) {
          const result = await response.json().catch(() => ({}));
          throw new Error(result.detail || "Failed to update dispute");
        }
        const result = await response.json();
        setData((current) => current.map((entry) => (entry.id === disputeId ? { ...entry, ...result } : entry)));
      } catch (err) {
        addToast(err instanceof Error ? err.message : "Failed to update dispute", "error");
      } finally {
        setSavingId(null);
      }
    },
    [addToast],
  );

  const bulkUpdate = useCallback(async () => {
    const dispute_ids = Array.from(selectedIds);
    if (!dispute_ids.length) return;
    const payload: Record<string, unknown> = { dispute_ids };
    if (bulkStatus) payload.status = bulkStatus;
    if (bulkPriority) payload.priority = bulkPriority;
    if (!bulkStatus && !bulkPriority) return;
    try {
      const response = await apiFetch("/admin/disputes/bulk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const result = await response.json().catch(() => ({}));
        throw new Error(result.detail || "Failed to run bulk action");
      }
      const result = await response.json();
      addToast(`Updated ${result.updated ?? dispute_ids.length} disputes`, "success");
      setSelectedIds(new Set());
      setBulkStatus("");
      setBulkPriority("");
      void load();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Failed to run bulk action", "error");
    }
  }, [selectedIds, bulkStatus, bulkPriority, addToast, load]);

  const allSelected = data.length > 0 && data.every((d) => selectedIds.has(d.id));
  const toggleAll = () => {
    if (allSelected) setSelectedIds(new Set());
    else setSelectedIds(new Set(data.map((d) => d.id)));
  };
  const toggleOne = (id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const filters = useMemo(
    () => (
      <div className="flex flex-wrap items-center gap-3">
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="theme-input min-w-40">
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {s.replace("_", " ")}
            </option>
          ))}
        </select>
        <select value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value)} className="theme-input min-w-40">
          <option value="">All priorities</option>
          {PRIORITY_OPTIONS.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} className="theme-input min-w-40">
          <option value="">All types</option>
          <option value="return">return</option>
          <option value="payment">payment</option>
          <option value="quality">quality</option>
          <option value="other">other</option>
        </select>
        <button
          onClick={() => void load()}
          className="inline-flex items-center gap-1.5 rounded-xl border border-border px-3 py-2 text-xs font-semibold text-primary hover:bg-surface-2"
        >
          <RefreshCw className="h-3.5 w-3.5" /> Refresh
        </button>
      </div>
    ),
    [statusFilter, priorityFilter, typeFilter, load],
  );

  if (authLoading) {
    return <PanelContent className="p-8 text-center text-sm text-text-muted">Loading…</PanelContent>;
  }
  if (!isLoggedIn || !hasAdminPermission(user?.role, "moderation.suppliers")) {
    return <PanelContent className="p-8 text-center text-sm text-text-muted">You do not have access to this section.</PanelContent>;
  }

  return (
    <div className="space-y-4">
      <PanelHero
        icon={<ShieldAlert className="h-5 w-5" />}
        eyebrow="Resolution"
        title="Supplier Disputes"
        description="Review supplier disputes, record arbitration outcomes, and run bulk moderation actions."
      />

      <PanelContent className="space-y-4">
        {filters}

        {error ? <div className="theme-card p-4 text-sm text-danger">{error}</div> : null}

        <div className="theme-card overflow-hidden rounded-xl border">
          <table className="w-full text-sm">
            <thead className="border-b border-border bg-surface-2 text-left text-xs uppercase tracking-wide text-text-muted">
              <tr>
                <th className="w-10 px-3 py-3">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={toggleAll}
                    aria-label="Select all disputes"
                    className="h-4 w-4"
                  />
                </th>
                <th className="px-3 py-3">Dispute</th>
                <th className="px-3 py-3">Supplier</th>
                <th className="px-3 py-3">Priority</th>
                <th className="px-3 py-3">Status</th>
                <th className="px-3 py-3">Resolution notes</th>
                <th className="px-3 py-3">Created</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-3 py-8 text-center text-text-muted">
                    Loading disputes…
                  </td>
                </tr>
              ) : data.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-3 py-8 text-center text-text-muted">
                    No disputes found.
                  </td>
                </tr>
              ) : (
                data.map((entry) => (
                  <tr key={entry.id} className="border-b border-border/60 last:border-0">
                    <td className="px-3 py-3">
                      <input
                        type="checkbox"
                        checked={selectedIds.has(entry.id)}
                        onChange={() => toggleOne(entry.id)}
                        aria-label={`Select dispute ${entry.id}`}
                        className="h-4 w-4"
                      />
                    </td>
                    <td className="px-3 py-3">
                      <p className="font-medium text-text">{entry.title || `#${entry.id}`}</p>
                      <p className="mt-1 text-text-muted">{entry.dispute_type} dispute</p>
                      {entry.resolution_notes ? (
                        <p className="mt-2 text-text-muted">Resolution: {entry.resolution_notes}</p>
                      ) : null}
                    </td>
                    <td className="px-3 py-3 text-text-muted">
                      {entry.supplier_id ? `Supplier #${entry.supplier_id}` : "—"}
                    </td>
                    <td className="px-3 py-3 capitalize text-text-muted">{entry.priority || "medium"}</td>
                    <td className="px-3 py-3">
                      <span className={`rounded-full px-2.5 py-1 text-xs font-semibold capitalize ${statusChipClass(entry.status)}`}>
                        {(entry.status || "open").replace("_", " ")}
                      </span>
                    </td>
                    <td className="px-3 py-3">
                      <input
                        defaultValue={entry.resolution_notes || ""}
                        onBlur={(e) => {
                          const nextValue = e.target.value.trim();
                          if ((entry.resolution_notes || "") === nextValue) return;
                          void patchDispute(entry.id, { resolution_notes: nextValue || null });
                        }}
                        placeholder="Add resolution notes…"
                        className="theme-input min-w-56"
                      />
                    </td>
                    <td className="px-3 py-3 text-text-muted">
                      {entry.created_at ? new Date(entry.created_at).toLocaleString() : "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </PanelContent>

      <BulkActionBar
        selectedCount={selectedIds.size}
        onClearSelection={() => setSelectedIds(new Set())}
        actions={[
          {
            label: "Apply bulk action",
            loading: savingId !== null,
            disabled: !bulkStatus && !bulkPriority,
            onClick: () => void bulkUpdate(),
          },
        ]}
      >
        <select
          value={bulkStatus}
          onChange={(e) => setBulkStatus(e.target.value)}
          aria-label="Bulk dispute status"
          className="theme-input min-w-40"
        >
          <option value="">Set status…</option>
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {s.replace("_", " ")}
            </option>
          ))}
        </select>
        <select
          value={bulkPriority}
          onChange={(e) => setBulkPriority(e.target.value)}
          aria-label="Bulk dispute priority"
          className="theme-input min-w-40"
        >
          <option value="">Set priority…</option>
          {PRIORITY_OPTIONS.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </BulkActionBar>
    </div>
  );
}
