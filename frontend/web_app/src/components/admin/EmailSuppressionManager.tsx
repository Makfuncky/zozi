"use client";

import { useEffect, useState } from "react";
import { RefreshCw, ShieldAlert, ShieldOff } from "@/lib/icons";
import { apiFetch, getErrorMessage } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";

interface SuppressionRecord {
  id: number;
  email: string;
  reason: string;
  source: string;
  provider: string | null;
  status: "active" | "inactive";
  notes: string | null;
  suppressed_at: string | null;
  last_event_at: string | null;
}

type StatusFilter = "all" | "active" | "inactive";

export default function EmailSuppressionManager() {
  const { addToast } = useToastStore();
  const [records, setRecords] = useState<SuppressionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<StatusFilter>("active");
  const [updating, setUpdating] = useState<number | null>(null);

  const fetchRecords = async (statusFilter: StatusFilter) => {
    setLoading(true);
    try {
      const params = statusFilter !== "all" ? `?status=${statusFilter}` : "";
      const res = await apiFetch(`/email/suppressions${params}`);
      if (!res.ok) throw new Error(await res.text());
      const data: SuppressionRecord[] = await res.json();
      setRecords(data);
    } catch (err) {
      addToast(
        err instanceof Error ? err.message : getErrorMessage(err ?? {}),
        "error"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords(filter);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  const handleToggleStatus = async (record: SuppressionRecord) => {
    const newStatus = record.status === "active" ? "inactive" : "active";
    setUpdating(record.id);
    try {
      const res = await apiFetch(`/email/suppressions/${record.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
      if (!res.ok) throw new Error(await res.text());
      const updated: SuppressionRecord = await res.json();
      setRecords((prev) =>
        prev.map((r) => (r.id === updated.id ? updated : r))
      );
      addToast(
        `Suppression ${newStatus === "active" ? "re-activated" : "deactivated"} for ${record.email}`,
        "success"
      );
    } catch (err) {
      addToast(
        err instanceof Error ? err.message : getErrorMessage(err ?? {}),
        "error"
      );
    } finally {
      setUpdating(null);
    }
  };

  const formatDate = (iso: string | null) =>
    iso ? new Date(iso).toLocaleDateString() : "—";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <ShieldAlert className="w-6 h-6 theme-status-warning" />
          <div>
            <h2 className="text-xl font-semibold text-text">Email Suppressions</h2>
            <p className="text-sm text-text-muted">
              Addresses blocked from receiving outbound email (bounces, complaints, unsubscribes)
            </p>
          </div>
        </div>
        <button
          onClick={() => fetchRecords(filter)}
          className="theme-btn-secondary flex items-center gap-2 px-3 py-2 rounded-xl text-sm"
          disabled={loading}
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="theme-panel flex space-x-1 rounded-2xl p-1 w-fit">
        {(["active", "inactive", "all"] as StatusFilter[]).map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`px-4 py-1.5 rounded-xl text-sm font-medium capitalize transition-colors ${
              filter === s
                ? "theme-btn-primary"
                : "text-text-muted hover:bg-surface-2 hover:text-text"
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="theme-card overflow-hidden rounded-2xl">
        {loading ? (
          <div className="flex items-center justify-center h-40 text-text-muted">
            Loading suppressions...
          </div>
        ) : records.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-text-muted gap-2">
            <ShieldOff className="w-8 h-8 opacity-40" />
            <p className="text-sm">No suppression records found.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-border">
              <thead className="bg-surface-2">
                <tr>
                  {["Email", "Reason", "Source", "Provider", "Status", "Suppressed At", "Action"].map(
                    (col) => (
                      <th
                        key={col}
                        className="px-4 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wider"
                      >
                        {col}
                      </th>
                    )
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {records.map((rec) => (
                  <tr key={rec.id} className="hover:bg-surface-2 transition-colors">
                    <td className="px-4 py-3 text-sm font-medium text-text">{rec.email}</td>
                    <td className="px-4 py-3 text-sm text-text-muted">{rec.reason}</td>
                    <td className="px-4 py-3 text-sm text-text-muted">{rec.source}</td>
                    <td className="px-4 py-3 text-sm text-text-muted">{rec.provider ?? "—"}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          rec.status === "active"
                            ? "theme-chip-danger"
                            : "theme-chip-success"
                        }`}
                      >
                        {rec.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-text-muted">
                      {formatDate(rec.suppressed_at)}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => handleToggleStatus(rec)}
                        disabled={updating === rec.id}
                        className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-colors ${
                          rec.status === "active"
                            ? "theme-btn-danger-outline"
                            : "theme-btn-success-outline"
                        }`}
                      >
                        {updating === rec.id
                          ? "Saving…"
                          : rec.status === "active"
                          ? "Deactivate"
                          : "Reactivate"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}


