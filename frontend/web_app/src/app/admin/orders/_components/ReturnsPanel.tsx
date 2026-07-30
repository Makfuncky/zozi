"use client";

import { Button } from "@/components/ui/Button";

import { useCallback, useEffect, useState } from "react";
import { RefreshCw, RotateCcw, CheckCircle2, XCircle, PackageCheck } from "@/lib/icons";
import { apiFetch } from "@/lib/api";

interface ReturnRequest {
  id: number;
  order_id: number;
  user_id?: number;
  intent?: string;
  reason?: string;
  description?: string;
  status?: string;
  refund_amount?: number | null;
  resolution_notes?: string | null;
  created_at?: string | null;
  customer_name?: string | null;
  product_name?: string | null;
}

const STATUS_CHIP: Record<string, string> = {
  pending: "bg-warning/10 text-warning",
  approved: "bg-success/10 text-success",
  rejected: "bg-danger/10 text-danger",
  completed: "bg-info/10 text-info",
  refunded: "bg-primary/10 text-primary",
};

export default function ReturnsPanel() {
  const [returns, setReturns] = useState<ReturnRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  const fetchReturns = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch("/returns?limit=100");
      if (!res.ok) throw new Error(`Failed to load returns (${res.status})`);
      const data = await res.json();
      setReturns(Array.isArray(data) ? data : (data?.data ?? []));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load returns");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchReturns();
  }, [fetchReturns]);

  async function setStatus(id: number, status: string) {
    setBusyId(id);
    try {
      const res = await apiFetch(`/returns/${id}/status?status=${status}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes: `Admin set status to ${status}` }),
      });
      if (res.ok) {
        setReturns((prev) => prev.map((r) => (r.id === id ? { ...r, status } : r)));
      } else {
        const j = await res.json().catch(() => ({}));
        setError(j.detail || "Failed to update return");
      }
    } catch {
      setError("Network error updating return");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-bold text-text">Return & Replacement Requests</h2>
        <button
          onClick={() => void fetchReturns()}
          disabled={loading}
          className="flex items-center gap-2 rounded-xl border border-border bg-surface-2 px-3 py-1.5 text-xs font-semibold text-text-muted hover:text-text disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {error && <div className="rounded-xl border border-danger/30 bg-danger/5 px-3 py-2 text-xs text-danger">{error}</div>}

      {loading ? (
        <div className="rounded-xl border border-border bg-surface-1 p-6 text-center text-xs text-text-muted">Loading returns…</div>
      ) : returns.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-xl border border-border bg-surface-1 py-10 text-center">
          <RotateCcw className="h-8 w-8 text-text-faint" />
          <p className="text-sm text-text-muted">No return or replacement requests.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border">
          <table className="w-full text-sm">
            <thead className="bg-surface-2 text-text-muted">
              <tr>
                <th className="px-2 py-2 text-left">#</th>
                <th className="px-2 py-2 text-left">Order</th>
                <th className="px-2 py-2 text-left">Intent</th>
                <th className="px-2 py-2 text-left">Customer</th>
                <th className="px-2 py-2 text-left">Reason</th>
                <th className="px-2 py-2 text-left">Status</th>
                <th className="px-2 py-2 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              {returns.map((r) => (
                <tr key={r.id} className="border-t">
                  <td className="px-2 py-2 font-mono text-text-faint">#{r.id}</td>
                  <td className="px-2 py-2 text-text">#{r.order_id}</td>
                  <td className="px-2 py-2 text-text">
                    <span className="rounded-full bg-surface-3 px-2 py-0.5 text-[10px] font-semibold uppercase text-text-muted">
                      {r.intent || "return"}
                    </span>
                  </td>
                  <td className="px-2 py-2 text-text-muted">{r.customer_name || r.user_id || "—"}</td>
                  <td className="px-2 py-2 text-text-muted">{r.reason || r.description || "—"}</td>
                  <td className="px-2 py-2">
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${STATUS_CHIP[r.status ?? ""] || "bg-surface-3 text-text-muted"}`}>
                      {r.status}
                    </span>
                  </td>
                  <td className="px-2 py-2">
                    <div className="flex flex-wrap gap-1">
                      <Button variant="primary" className="rounded-lg px-2 py-1 text-xs font-semibold text-success disabled:opacity-50" disabled={busyId === r.id || r.status === "completed"}
                        onClick={() => void setStatus(r.id, "approved")}
                      >
                        <CheckCircle2 className="mr-1 inline h-3.5 w-3.5" /> Approve
                      </Button>
                      <Button variant="danger" className="rounded-lg px-2 py-1 text-xs font-semibold text-danger disabled:opacity-50" disabled={busyId === r.id || r.status === "completed"}
                        onClick={() => void setStatus(r.id, "rejected")}
                      >
                        <XCircle className="mr-1 inline h-3.5 w-3.5" /> Reject
                      </Button>
                      <Button variant="info" className="rounded-lg px-2 py-1 text-xs font-semibold text-info disabled:opacity-50" disabled={busyId === r.id || r.status === "completed"}
                        onClick={() => void setStatus(r.id, "completed")}
                      >
                        <PackageCheck className="mr-1 inline h-3.5 w-3.5" /> Complete
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
