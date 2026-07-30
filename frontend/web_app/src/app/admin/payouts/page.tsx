"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  DollarSign,
  TrendingUp,
  Users,
  CheckCircle2,
  XCircle,
  Send,
  Loader2,
  ChevronDown,
  ChevronRight,
  Clock,
  Ban,
  AlertTriangle,
  Eye,
  FileText,
  Truck,
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";
import { useLocaleStore } from "@/lib/localeStore";
import { isRtlLocale } from "@shared/localization";

// ── Types ───────────────────────────────────────────────────────────────────

interface BatchItem {
  id: number;
  entity_type: string;
  entity_id: number;
  amount: number;
  currency: string;
  reference: string | null;
  status: string;
  entity_name?: string;
}

interface PayoutBatch {
  id: number;
  batch_number: string;
  country_code: string;
  total_amount: number;
  item_count: number;
  status: string;
  notes: string | null;
  created_at: string | null;
  items: BatchItem[];
}

interface UnbatchedPayout {
  id: number;
  supplier_id: number | null;
  order_id: number | null;
  amount: number;
  currency: string;
  method: string;
  status: string;
  reference: string | null;
  notes: string | null;
  country_code: string;
  created_at: string | null;
  supplier_name?: string | null;
}

interface UnbatchedLogisticsPayout {
  id: number;
  partner_id: number | null;
  partner_name?: string | null;
  amount: number;
  currency: string;
  status: string;
  reference: string | null;
  notes: string | null;
  created_at: string | null;
}

interface PendingResponse {
  pending_batches: PayoutBatch[];
  unbatched_payouts: UnbatchedPayout[];
  unbatched_logistics_payouts: UnbatchedLogisticsPayout[];
  summary: {
    total_batches: number;
    total_amount: number;
    total_items: number;
    pending_payouts_count: number;
    pending_logistics_payouts_count: number;
  };
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function formatCurrency(amount: number, currency = "OMR"): string {
  const fmt = new Intl.NumberFormat("en-US", { style: "currency", currency, minimumFractionDigits: 2 });
  return fmt.format(amount);
}

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return "—";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

function statusColor(status: string): string {
  switch (status) {
    case "draft": return "text-text-muted bg-surface-2";
    case "pending": return "text-amber-700 bg-amber-50";
    case "approved": return "text-emerald-700 bg-emerald-50";
    case "rejected": return "text-red-700 bg-red-50";
    case "dispatched": return "text-blue-700 bg-blue-50";
    case "paid": return "text-emerald-700 bg-emerald-50";
    default: return "text-text-muted bg-surface-1";
  }
}

function statusLabel(status: string): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}

// ── Component ───────────────────────────────────────────────────────────────

export default function AdminPayoutApprovalPage() {
  const addToast = useToastStore((s) => s.addToast);
  const locale = useLocaleStore((s) => s.locale);
  const isRtl = isRtlLocale(locale);
  const tr = useLocaleStore((s) => s.t);

  const [data, setData] = useState<PendingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedBatches, setExpandedBatches] = useState<Set<number>>(new Set());
  const [actionLoading, setActionLoading] = useState<{ [key: string]: boolean }>({});
  const [confirmModal, setConfirmModal] = useState<{
    batchId?: number;
    batchNumber?: string;
    payoutId?: number;
    action: "approve" | "reject" | "dispatch";
  } | null>(null);
  const [actionNotes, setActionNotes] = useState("");

  const fetchPending = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch("/admin/payout-approval/pending");
      if (res.ok) {
        const d = await res.json();
        setData(d as PendingResponse);
      } else {
        addToast("Failed to load pending payouts", "error");
      }
    } catch {
      addToast("Network error loading pending payouts", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    fetchPending();
  }, [fetchPending]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(fetchPending, 30000);
    return () => clearInterval(interval);
  }, [fetchPending]);

  const toggleExpand = (batchId: number) => {
    setExpandedBatches((prev) => {
      const next = new Set(prev);
      if (next.has(batchId)) next.delete(batchId);
      else next.add(batchId);
      return next;
    });
  };

  const approveSinglePayout = (payoutId: number) => {
    setConfirmModal({ payoutId, action: "approve" });
  };
  const rejectSinglePayout = (payoutId: number) => {
    setConfirmModal({ payoutId, action: "reject" });
  };

  const performAction = async (action: "approve" | "reject" | "dispatch") => {
    if (!confirmModal) return;
    const { batchId, payoutId } = confirmModal;
    const isBatch = !!batchId;
    const entity = isBatch ? "batches" : "payouts";
    const entityId = isBatch ? batchId! : payoutId!;
    const key = `${action}-${isBatch ? batchId : `payout-${payoutId}`}`;
    setActionLoading((prev) => ({ ...prev, [key]: true }));
    try {
      const res = await apiFetch(`/admin/payout-approval/${entity}/${entityId}/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes: actionNotes || undefined }),
      });
      if (res.ok) {
        addToast(isBatch ? `Batch ${statusLabel(action)}d successfully` : `Payout #${payoutId} ${action}d successfully`, "success");
        setConfirmModal(null);
        setActionNotes("");
        fetchPending();
      } else {
        const err = await res.json().catch(() => ({ detail: "Action failed" }));
        addToast(err.detail || `Failed to ${action} ${isBatch ? "batch" : "payout"}`, "error");
      }
    } catch {
      addToast(`Network error during ${action}`, "error");
    } finally {
      setActionLoading((prev) => ({ ...prev, [key]: false }));
    }
  };

  // ── Summary Stats ─────────────────────────────────────────────────────────

  const stats = useMemo(() => {
    if (!data) return [];
    const s = data.summary;
    return [
      { label: "Pending Batches", value: s.total_batches, icon: FileText, color: "text-blue-600" },
      { label: "Total Amount", value: formatCurrency(s.total_amount), icon: DollarSign, color: "text-emerald-600" },
      { label: "Items in Batches", value: s.total_items, icon: TrendingUp, color: "text-purple-600" },
      { label: "Unbatched Payouts", value: s.pending_payouts_count, icon: Users, color: "text-amber-600" },
      { label: "Logistics Payouts", value: s.pending_logistics_payouts_count ?? 0, icon: Truck, color: "text-purple-600" },
    ];
  }, [data]);

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <main className="min-h-screen" dir={isRtl ? "rtl" : "ltr"}>
      <div className="mx-auto max-w-7xl px-4 sm:px-6 py-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-text">Payout Approval Dashboard</h1>
            <p className="text-sm text-text-faint mt-1">
              Review, approve, reject, and dispatch supplier logistics payout batches
            </p>
          </div>
          <button
            onClick={fetchPending}
            disabled={loading}
            className="theme-btn-outline rounded-xl px-4 py-2 text-xs font-semibold flex items-center gap-2"
          >
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Eye className="w-3.5 h-3.5" />}
            Refresh
          </button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {stats.map((stat) => {
            const Icon = stat.icon;
            return (
              <div key={stat.label} className="theme-card rounded-xl border border-border p-4">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg bg-surface-2 flex items-center justify-center ${stat.color}`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-xs text-text-faint">{stat.label}</p>
                    <p className="text-lg font-bold text-text">{stat.value}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Batches List */}
        {loading && !data ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-text-faint animate-spin" />
          </div>
        ) : data && data.pending_batches.length === 0 && data.unbatched_payouts.length === 0 && (!data.unbatched_logistics_payouts || data.unbatched_logistics_payouts.length === 0) ? (
          <div className="theme-card rounded-xl border border-border p-12 text-center">
            <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-text mb-1">All Clear</h3>
            <p className="text-sm text-text-faint">No pending payout batches or unbatched payouts.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Pending Payout Batches */}
            {data?.pending_batches.map((batch) => {
              const isExpanded = expandedBatches.has(batch.id);
              const canApprove = batch.status === "draft" || batch.status === "pending";
              const canReject = batch.status === "draft" || batch.status === "pending" || batch.status === "approved";
              const canDispatch = batch.status === "approved";

              return (
                <motion.div
                  key={batch.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="theme-card rounded-xl border border-border overflow-hidden"
                >
                  {/* Batch Header */}
                  <div
                    className="flex items-center justify-between p-4 cursor-pointer hover:bg-surface-1/50 transition-colors"
                    onClick={() => toggleExpand(batch.id)}
                  >
                    <div className="flex items-center gap-3 min-w-0 flex-1">
                      {isExpanded ? <ChevronDown className="w-4 h-4 text-text-faint shrink-0" /> : <ChevronRight className="w-4 h-4 text-text-faint shrink-0" />}
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-sm text-text">{batch.batch_number}</span>
                          <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${statusColor(batch.status)}`}>
                            {statusLabel(batch.status)}
                          </span>
                        </div>
                        <p className="text-[11px] text-text-faint truncate mt-0.5">
                          {batch.item_count} item{batch.item_count !== 1 ? "s" : ""} · {batch.country_code} · Created {timeAgo(batch.created_at)}
                        </p>
                      </div>
                    </div>
                    <div className="text-right shrink-0 ml-4">
                      <p className="text-sm font-bold text-text">{formatCurrency(batch.total_amount, "OMR")}</p>
                    </div>
                  </div>

                  {/* Expanded Items */}
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="border-t border-border"
                      >
                        {/* Items Table */}
                        <div className="overflow-x-auto">
                          <table className="w-full text-xs">
                            <thead>
                              <tr className="bg-surface-1 text-text-faint text-[10px] uppercase tracking-wider">
                                <th className="text-left px-4 py-2 font-medium">Entity</th>
                                <th className="text-left px-4 py-2 font-medium">Type</th>
                                <th className="text-right px-4 py-2 font-medium">Amount</th>
                                <th className="text-left px-4 py-2 font-medium">Status</th>
                                <th className="text-left px-4 py-2 font-medium">Reference</th>
                              </tr>
                            </thead>
                            <tbody>
                              {batch.items.map((item) => (
                                <tr key={item.id} className="border-t border-border/50 hover:bg-surface-1/30">
                                  <td className="px-4 py-2.5 font-medium text-text">{item.entity_name || `#${item.entity_id}`}</td>
                                  <td className="px-4 py-2.5 text-text-muted">
                                    <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
                                      item.entity_type === "supplier" ? "bg-blue-50 text-blue-700" : "bg-purple-50 text-purple-700"
                                    }`}>
                                      {item.entity_type}
                                    </span>
                                  </td>
                                  <td className="px-4 py-2.5 text-right font-semibold text-text">{formatCurrency(item.amount, item.currency)}</td>
                                  <td className="px-4 py-2.5">
                                    <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${statusColor(item.status)}`}>
                                      {statusLabel(item.status)}
                                    </span>
                                  </td>
                                  <td className="px-4 py-2.5 text-text-faint max-w-[200px] truncate">{item.reference || "—"}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex items-center gap-2 p-3 border-t border-border bg-surface-1/50">
                          {batch.notes && (
                            <div className="flex-1 min-w-0">
                              <p className="text-[10px] text-text-faint truncate">{batch.notes.split("\n").pop()}</p>
                            </div>
                          )}
                          <div className="flex items-center gap-2 shrink-0">
                            {canApprove && (
                              <button
                                onClick={(e) => { e.stopPropagation(); setConfirmModal({ batchId: batch.id, batchNumber: batch.batch_number, action: "approve" }); }}
                                className="theme-btn-primary rounded-lg px-3 py-1.5 text-[11px] font-semibold flex items-center gap-1.5"
                              >
                                <CheckCircle2 className="w-3.5 h-3.5" /> Approve
                              </button>
                            )}
                            {canReject && (
                              <button
                                onClick={(e) => { e.stopPropagation(); setConfirmModal({ batchId: batch.id, batchNumber: batch.batch_number, action: "reject" }); }}
                                className="theme-action-danger rounded-lg px-3 py-1.5 text-[11px] font-semibold flex items-center gap-1.5"
                              >
                                <XCircle className="w-3.5 h-3.5" /> Reject
                              </button>
                            )}
                            {canDispatch && (
                              <button
                                onClick={(e) => { e.stopPropagation(); setConfirmModal({ batchId: batch.id, batchNumber: batch.batch_number, action: "dispatch" }); }}
                                disabled={actionLoading[`dispatch-${batch.id}`]}
                                className="theme-btn-primary rounded-lg px-3 py-1.5 text-[11px] font-semibold flex items-center gap-1.5"
                              >
                                {actionLoading[`dispatch-${batch.id}`] ? (
                                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                ) : (
                                  <Send className="w-3.5 h-3.5" />
                                )}
                                Dispatch
                              </button>
                            )}
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              );
            })}

            {/* Unbatched Payouts */}
            {data && data.unbatched_payouts.length > 0 && (
              <div className="theme-card rounded-xl border border-border p-4">
                <h3 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-500" />
                  Unbatched Payouts ({data.unbatched_payouts.length})
                </h3>
                <p className="text-[11px] text-text-faint mb-3">
                  These individual supplier payouts were created but not yet grouped into a batch. Approve or reject them individually.
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="bg-surface-1 text-text-faint text-[10px] uppercase tracking-wider">
                        <th className="text-left px-3 py-2 font-medium">ID</th>
                        <th className="text-left px-3 py-2 font-medium">Supplier</th>
                        <th className="text-right px-3 py-2 font-medium">Amount</th>
                        <th className="text-left px-3 py-2 font-medium">Status</th>
                        <th className="text-center px-3 py-2 font-medium">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.unbatched_payouts.map((p) => (
                        <tr key={p.id} className="border-t border-border/50 hover:bg-surface-1/30">
                          <td className="px-3 py-2 font-medium text-text">#{p.id}</td>
                          <td className="px-3 py-2 text-text-muted">{p.supplier_name || `Supplier #${p.supplier_id}`}</td>
                          <td className="px-3 py-2 text-right font-semibold text-text">{formatCurrency(p.amount, p.currency)}</td>
                          <td className="px-3 py-2">
                            <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${statusColor(p.status)}`}>
                              {statusLabel(p.status)}
                            </span>
                          </td>
                          <td className="px-3 py-2">
                            <div className="flex items-center justify-center gap-1.5">
                              <button
                                onClick={() => approveSinglePayout(p.id)}
                                disabled={p.status !== "pending" && p.status !== "draft"}
                                className={`rounded-lg px-2.5 py-1 text-[10px] font-semibold flex items-center gap-1 ${
                                  p.status === "pending" || p.status === "draft"
                                    ? "bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
                                    : "bg-surface-1 text-text-faint cursor-not-allowed"
                                }`}
                              >
                                <CheckCircle2 className="w-3 h-3" /> Approve
                              </button>
                              <button
                                onClick={() => rejectSinglePayout(p.id)}
                                disabled={p.status !== "pending" && p.status !== "draft"}
                                className={`rounded-lg px-2.5 py-1 text-[10px] font-semibold flex items-center gap-1 ${
                                  p.status === "pending" || p.status === "draft"
                                    ? "bg-red-50 text-red-700 hover:bg-red-100"
                                    : "bg-surface-1 text-text-faint cursor-not-allowed"
                                }`}
                              >
                                <XCircle className="w-3 h-3" /> Reject
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Unbatched Logistics Payouts */}
            {data && data.unbatched_logistics_payouts && data.unbatched_logistics_payouts.length > 0 && (
              <div className="theme-card rounded-xl border border-border p-4">
                <h3 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
                  <Truck className="w-4 h-4 text-purple-500" />
                  Logistics Partner Payouts ({data.unbatched_logistics_payouts.length})
                </h3>
                <p className="text-[11px] text-text-faint mb-3">
                  Pending payouts for logistics partners. Approve or reject them to manage the disbursement workflow.
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="bg-surface-1 text-text-faint text-[10px] uppercase tracking-wider">
                        <th className="text-left px-3 py-2 font-medium">ID</th>
                        <th className="text-left px-3 py-2 font-medium">Partner</th>
                        <th className="text-right px-3 py-2 font-medium">Amount</th>
                        <th className="text-left px-3 py-2 font-medium">Status</th>
                        <th className="text-center px-3 py-2 font-medium">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.unbatched_logistics_payouts.map((lp) => (
                        <tr key={lp.id} className="border-t border-border/50 hover:bg-surface-1/30">
                          <td className="px-3 py-2 font-medium text-text">#{lp.id}</td>
                          <td className="px-3 py-2 text-text-muted">{lp.partner_name || `Partner #${lp.partner_id}`}</td>
                          <td className="px-3 py-2 text-right font-semibold text-text">{formatCurrency(lp.amount, lp.currency)}</td>
                          <td className="px-3 py-2">
                            <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${statusColor(lp.status)}`}>
                              {statusLabel(lp.status)}
                            </span>
                          </td>
                          <td className="px-3 py-2 text-center text-[10px] text-text-faint">
                            Manage via batch actions above
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Confirm Action Modal */}
      <AnimatePresence>
        {confirmModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
            onClick={() => setConfirmModal(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-2xl shadow-xl border border-border max-w-md w-full p-6"
              onClick={(e: React.MouseEvent) => e.stopPropagation()}
            >
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                  confirmModal.action === "approve" ? "bg-emerald-100 text-emerald-600" :
                  confirmModal.action === "reject" ? "bg-red-100 text-red-600" :
                  "bg-blue-100 text-blue-600"
                }`}>
                  {confirmModal.action === "approve" ? <CheckCircle2 className="w-5 h-5" /> :
                   confirmModal.action === "reject" ? <Ban className="w-5 h-5" /> :
                   <Send className="w-5 h-5" />}
                </div>
                <div>
                  <h3 className="text-sm font-bold text-text capitalize">
                    {confirmModal.payoutId ? `Payout #${confirmModal.payoutId}` : confirmModal.action} {confirmModal.payoutId ? "" : "Batch"}
                  </h3>
                  <p className="text-xs text-text-faint">{confirmModal.batchNumber || (confirmModal.payoutId ? `Payout #${confirmModal.payoutId}` : "")}</p>
                </div>
              </div>

              <p className="text-xs text-text-muted mb-4">
                {confirmModal.payoutId ? (
                  confirmModal.action === "approve" ? "This will approve this individual payout for disbursement." :
                  "This will reject this payout. The settlement will remain pending for future batches."
                ) : (
                  confirmModal.action === "approve" ? "This will mark the batch as approved. Approved batches can then be dispatched for payment." :
                  confirmModal.action === "reject" ? "This will reject the batch and reset all items to pending. You can add a reason below." :
                  "This will mark all items in the batch as paid and update related payout records. This action cannot be undone."
                )}
              </p>

              <textarea
                value={actionNotes}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setActionNotes(e.target.value)}
                placeholder="Add notes or reason (optional)..."
                rows={2}
                className="theme-input w-full rounded-xl border border-border px-3 py-2 text-xs resize-none mb-4"
              />

              <div className="flex items-center justify-end gap-2">
                <button
                  onClick={() => { setConfirmModal(null); setActionNotes(""); }}
                  className="theme-btn-outline rounded-xl px-4 py-2 text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  onClick={() => performAction(confirmModal.action)}
                  disabled={actionLoading[`${confirmModal.action}-${confirmModal.payoutId ? `payout-${confirmModal.payoutId}` : confirmModal.batchId}`]}
                  className={`rounded-xl px-4 py-2 text-xs font-semibold flex items-center gap-2 ${
                    confirmModal.action === "reject"
                      ? "theme-action-danger"
                      : "theme-btn-primary"
                  }`}
                >
                  {actionLoading[`${confirmModal.action}-${confirmModal.payoutId ? `payout-${confirmModal.payoutId}` : confirmModal.batchId}`] ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : null}
                  Confirm {confirmModal.action === "dispatch" ? "Dispatch" : confirmModal.action === "approve" ? "Approval" : "Rejection"}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}
