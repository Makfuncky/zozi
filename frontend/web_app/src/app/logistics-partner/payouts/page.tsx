"use client";

import { Fragment, useCallback, useEffect, useMemo, useState } from "react";
import { CheckCircle, Clock, RefreshCw, Search, Send } from "@/lib/icons";
import LogisticsPartnerLayout from "@/components/LogisticsPartnerLayout";
import { PanelContent } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import FinanceSection from "./FinanceSection";

interface LogisticsPayout {
  id: number;
  amount: number;
  status: string;
  method?: string | null;
  reference?: string | null;
  notes?: string | null;
  created_at?: string | null;
  processed_at?: string | null;
}

interface PayoutSummary {
  total_earned: number;
  available_balance: number;
  pending_amount: number;
  completed_amount: number;
  payout_count: number;
}

interface DashboardResponse {
  payout_summary: PayoutSummary;
}

type PayoutStatusFilter = "all" | "pending" | "processing" | "completed" | "rejected";

function normalizeStatus(value?: string | null) {
  return String(value || "").trim().toLowerCase();
}

function titleCase(value?: string | null) {
  if (!value) return "Unknown";
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function payoutStatusTone(status?: string | null) {
  const normalized = normalizeStatus(status);
  if (normalized === "completed") return "theme-chip-success";
  if (normalized === "rejected") return "theme-chip-danger";
  if (normalized === "processing") return "theme-chip-info";
  return "theme-chip-warning";
}

export default function LogisticsPartnerPayoutsPage() {
  const formatMoney = useCurrencyStore((state) => state.format);
  const [summary, setSummary] = useState<PayoutSummary | null>(null);
  const [payouts, setPayouts] = useState<LogisticsPayout[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<PayoutStatusFilter>("all");
  const [expandedPayoutId, setExpandedPayoutId] = useState<number | null>(null);
  const [form, setForm] = useState({ amount: "", notes: "" });

  const load = useCallback(async ({ silent = false }: { silent?: boolean } = {}) => {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    const [dashboardRes, payoutsRes] = await Promise.all([
      apiFetch("/logistics-partner/dashboard").catch(() => null),
      apiFetch("/logistics-partner/payouts").catch(() => null),
    ]);
    if (dashboardRes?.ok) {
      const dashboard = (await dashboardRes.json()) as DashboardResponse;
      setSummary(dashboard.payout_summary);
    }
    if (payoutsRes?.ok) {
      const payoutData = (await payoutsRes.json()) as LogisticsPayout[];
      setPayouts(payoutData);
    }
    setLoading(false);
    setRefreshing(false);
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const canSubmit = useMemo(() => {
    const amount = Number(form.amount);
    return amount > 0 && Boolean(summary) && amount <= Number(summary?.available_balance || 0);
  }, [form.amount, summary]);

  const filteredPayouts = useMemo(() => {
    const search = searchTerm.trim().toLowerCase();
    return payouts.filter((payout) => {
      if (statusFilter !== "all" && normalizeStatus(payout.status) !== statusFilter) return false;
      if (!search) return true;
      return [
        String(payout.id),
        String(payout.reference || ""),
        String(payout.notes || ""),
        String(payout.status || ""),
      ].some((value) => value.toLowerCase().includes(search));
    });
  }, [payouts, searchTerm, statusFilter]);

  const submitRequest = async () => {
    if (!canSubmit) return;
    setSubmitting(true);
    setMessage(null);
    const res = await apiFetch("/logistics-partner/payouts/request", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        amount: Number(form.amount),
        method: "bank",
        notes: form.notes.trim() || undefined,
      }),
    }).catch(() => null);
    if (res?.ok) {
      setForm({ amount: "", notes: "" });
      setMessage("Payout request submitted.");
      await load();
    } else {
      setMessage("Unable to submit payout request.");
    }
    setSubmitting(false);
  };

  return (
    <LogisticsPartnerLayout title="Payouts">
      <PanelContent className="space-y-6">
        <FinanceSection />

        <div className="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
          <div className="theme-card rounded-xl border p-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h3 className="flex items-center gap-2 text-sm font-bold text-text">
                  <Send className="h-4 w-4 text-primary" /> Request payout
                </h3>
                <p className="mt-1 text-xs text-text-muted">Only cleared delivery earnings can be requested. COD remittance verification remains separate from payout approval.</p>
              </div>
              <button
                onClick={() => void load({ silent: true })}
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-border bg-surface-2 px-3 py-2 text-[11px] font-semibold text-text-muted hover:text-text sm:w-auto"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`} /> Refresh
              </button>
            </div>

            <div className="mt-4 grid grid-cols-3 gap-2 text-[11px]">
              <div className="rounded-xl border border-border bg-surface-2 px-3 py-2">
                <p className="text-text-faint">Available</p>
                <p className="mt-1 font-bold text-text">{formatMoney(summary?.available_balance || 0)}</p>
              </div>
              <div className="rounded-xl border border-border bg-surface-2 px-3 py-2">
                <p className="text-text-faint">Pending</p>
                <p className="mt-1 font-bold text-warning">{formatMoney(summary?.pending_amount || 0)}</p>
              </div>
              <div className="rounded-xl border border-border bg-surface-2 px-3 py-2">
                <p className="text-text-faint">Completed</p>
                <p className="mt-1 font-bold text-success">{formatMoney(summary?.completed_amount || 0)}</p>
              </div>
            </div>

            <div className="mt-4 space-y-3">
              <div>
                <label className="mb-1 block text-xs text-text-muted">Amount</label>
                <input
                  value={form.amount}
                  onChange={(event) => setForm((current) => ({ ...current, amount: event.target.value }))}
                  inputMode="decimal"
                  placeholder="150.00"
                  className="theme-input w-full rounded-xl border px-3 py-2 text-xs focus:border-primary focus:outline-none"
                />
              </div>
              <div className="rounded-xl border border-info/20 bg-info/5 px-3 py-2 text-[11px] text-info">
                Method: Bank transfer
              </div>
              <div>
                <label className="mb-1 block text-xs text-text-muted">Notes</label>
                <textarea
                  rows={3}
                  value={form.notes}
                  onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))}
                  placeholder="Settlement note or internal payout reference"
                  className="theme-input w-full resize-none rounded-xl border px-3 py-2 text-xs focus:border-primary focus:outline-none"
                />
              </div>
              {message ? (
                <div className={`rounded-xl border px-3 py-2 text-xs font-medium ${message.includes("Unable") ? "border-danger/30 bg-danger/10 text-danger" : "border-success/30 bg-success/10 text-success"}`}>
                  {message}
                </div>
              ) : null}
              <button
                onClick={submitRequest}
                disabled={!canSubmit || submitting}
                className="theme-btn-accent w-full rounded-xl py-2.5 text-xs font-bold disabled:opacity-50"
              >
                {submitting ? "Submitting..." : "Submit request"}
              </button>
            </div>
          </div>

          <div className="theme-card overflow-hidden rounded-xl border">
            <div className="border-b border-border px-4 py-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className="text-sm font-bold text-text">Payout history</h3>
                  <p className="mt-1 text-xs text-text-muted">Track request status separately from COD remittance settlement verification.</p>
                </div>
                <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row sm:flex-wrap">
                  <label className="relative w-full sm:min-w-52 sm:w-auto">
                    <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                    <input
                      value={searchTerm}
                      onChange={(event) => setSearchTerm(event.target.value)}
                      placeholder="Search id, reference, notes"
                      className="w-full rounded-xl border border-border bg-surface-2 py-2 pl-9 pr-3 text-xs text-text outline-none focus:border-primary"
                    />
                  </label>
                  <select
                    value={statusFilter}
                    onChange={(event) => setStatusFilter(event.target.value as PayoutStatusFilter)}
                    className="w-full rounded-xl border border-border bg-surface-2 px-3 py-2 text-xs text-text sm:w-auto"
                  >
                    <option value="all">All statuses</option>
                    <option value="pending">Pending</option>
                    <option value="processing">Processing</option>
                    <option value="completed">Completed</option>
                    <option value="rejected">Rejected</option>
                  </select>
                </div>
              </div>
            </div>
            {loading ? (
              <div className="p-6 text-center text-xs text-text-muted">Loading payout history...</div>
            ) : filteredPayouts.length === 0 ? (
              <div className="p-6 text-center text-xs text-text-muted">No payout requests match the current filters.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-border bg-surface-2/40">
                      {["Request", "Requested", "Amount", "Reference", "Status", "Processed"].map((header) => (
                        <th key={header} className="px-3 py-2 text-left font-semibold text-text-faint">{header}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filteredPayouts.map((payout) => {
                      const expanded = expandedPayoutId === payout.id;
                      return (
                        <Fragment key={payout.id}>
                          <tr key={payout.id} className="border-b border-border/50 align-top last:border-0">
                            <td className="px-3 py-3 text-text">
                              <button type="button" onClick={() => setExpandedPayoutId(expanded ? null : payout.id)} className="text-left">
                                <div className="font-semibold">#{payout.id}</div>
                                <div className="mt-1 text-[10px] text-primary">{expanded ? "Hide detail" : "Show detail"}</div>
                              </button>
                            </td>
                            <td className="px-3 py-3 text-text-muted">{payout.created_at ? new Date(payout.created_at).toLocaleDateString() : "Pending"}</td>
                            <td className="px-3 py-3 font-semibold text-text">{formatMoney(payout.amount)}</td>
                            <td className="px-3 py-3 text-text-muted">{payout.reference || "Pending"}</td>
                            <td className="px-3 py-3">
                              <span className={`inline-flex items-center gap-1 rounded-lg px-2.5 py-1 text-[11px] font-semibold ${payoutStatusTone(payout.status)}`}>
                                {normalizeStatus(payout.status) === "completed" ? <CheckCircle className="h-3.5 w-3.5" /> : <Clock className="h-3.5 w-3.5" />}
                                {titleCase(payout.status)}
                              </span>
                            </td>
                            <td className="px-3 py-3 text-text-muted">{payout.processed_at ? new Date(payout.processed_at).toLocaleDateString() : "Pending"}</td>
                          </tr>
                          {expanded ? (
                            <tr className="border-b border-border/50 bg-surface-2/40">
                              <td colSpan={6} className="px-4 py-3">
                                <div className="grid gap-3 md:grid-cols-3">
                                  <div className="rounded-xl border border-border bg-surface px-3 py-2">
                                    <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-text-faint">Transfer method</p>
                                    <p className="mt-2 text-xs font-semibold text-text">Bank transfer</p>
                                  </div>
                                  <div className="rounded-xl border border-border bg-surface px-3 py-2">
                                    <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-text-faint">Timeline</p>
                                    <p className="mt-2 text-xs text-text-muted">Requested {payout.created_at ? new Date(payout.created_at).toLocaleString() : "recently"}</p>
                                    <p className="mt-1 text-xs text-text-muted">Processed {payout.processed_at ? new Date(payout.processed_at).toLocaleString() : "not yet"}</p>
                                  </div>
                                  <div className="rounded-xl border border-border bg-surface px-3 py-2">
                                    <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-text-faint">Notes</p>
                                    <p className="mt-2 text-xs text-text-muted">{payout.notes || "No extra notes attached to this request."}</p>
                                  </div>
                                </div>
                              </td>
                            </tr>
                          ) : null}
                        </Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </PanelContent>
    </LogisticsPartnerLayout>
  );
}


