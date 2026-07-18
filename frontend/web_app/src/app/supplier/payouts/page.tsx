"use client";

import { Button } from "@/components/ui/Button";

import { useCallback, useEffect, useMemo, useState } from "react";
import { CheckCircle, Clock, FileText, Plus, RefreshCw, Search, Send, Wallet } from "@/lib/icons";
import SupplierLayout from "@/components/SupplierLayout";
import { PanelContent, PanelTabs } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useToastStore } from "@/lib/toastStore";

interface SupplierPayout {
  id: number;
  amount: number;
  status: string;
  method?: string | null;
  reference?: string | null;
  notes?: string | null;
  created_at: string;
  processed_at?: string | null;
}

interface InvoiceRecord {
  id: number;
  invoice_number: string;
  order_id: number;
  total_amount: number;
  currency: string;
  status: string;
  notes?: string;
  created_at: string;
  due_date?: string;
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
  const n = normalizeStatus(status);
  if (n === "completed") return "bg-success/20 text-success";
  if (n === "rejected") return "bg-danger/20 text-danger";
  if (n === "processing") return "bg-info/20 text-info";
  return "bg-warning/20 text-warning";
}

export default function SupplierPayoutsPage() {
  const formatMoney = useCurrencyStore((state) => state.format);
  const addToast = useToastStore((s) => s.addToast);
  const [payouts, setPayouts] = useState<SupplierPayout[]>([]);
  const [invoices, setInvoices] = useState<InvoiceRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<PayoutStatusFilter>("all");
  const [expandedPayoutId, setExpandedPayoutId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<"payouts" | "invoices">(
    typeof window !== "undefined" && new URLSearchParams(window.location.search).get("view") === "invoices"
      ? "invoices"
      : "payouts"
  );
  const [invoiceForm, setInvoiceForm] = useState({ order_id: "", shipment_id: "", notes: "" });
  const [requestAmount, setRequestAmount] = useState("");
  const [requesting, setRequesting] = useState(false);

  const load = useCallback(async ({ silent = false }: { silent?: boolean } = {}) => {
    if (silent) setRefreshing(true); else setLoading(true);
    const [payoutsRes, invoicesRes] = await Promise.all([
      apiFetch("/supplier/payouts").catch(() => null),
      apiFetch("/invoices/?page=1&page_size=10").catch(() => null),
    ]);
    if (payoutsRes?.ok) {
      const data = await payoutsRes.json();
      setPayouts(Array.isArray(data) ? data : []);
    }
    if (invoicesRes?.ok) {
      const invData = await invoicesRes.json();
      setInvoices(Array.isArray(invData) ? invData : invData.items ?? []);
    }
    setLoading(false);
    setRefreshing(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const filteredPayouts = useMemo(() => {
    let list = [...payouts];
    if (statusFilter !== "all") list = list.filter((p) => normalizeStatus(p.status) === statusFilter);
    if (searchTerm.trim()) {
      const q = searchTerm.trim().toLowerCase();
      list = list.filter((p) =>
        [String(p.id), p.reference, p.notes].some((v) => v?.toLowerCase().includes(q))
      );
    }
    return list;
  }, [payouts, statusFilter, searchTerm]);

  const handleCreateInvoice = async () => {
    if (!invoiceForm.order_id) { addToast("Order number is required", "error"); return; }
    try {
      const res = await apiFetch("/invoices/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          order_id: parseInt(invoiceForm.order_id),
          shipment_id: invoiceForm.shipment_id ? parseInt(invoiceForm.shipment_id) : undefined,
          currency: "AED",
          notes: invoiceForm.notes || undefined,
        }),
      });
      if (res.ok) {
        addToast("Invoice created", "success");
        setInvoiceForm({ order_id: "", shipment_id: "", notes: "" });
        load({ silent: true });
      } else {
        const err = await res.json().catch(() => ({}));
        addToast(err.detail || "Failed to create invoice", "error");
      }
    } catch {
      addToast("Network error", "error");
    }
  };

  const handleRequestPayout = async () => {
    const amount = parseFloat(requestAmount);
    if (!amount || amount <= 0) { addToast("Enter a valid payout amount", "error"); return; }
    setRequesting(true);
    try {
      const res = await apiFetch("/supplier/payouts/request", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount, method: "bank", notes: "Supplier-initiated payout request" }),
      });
      if (res.ok) {
        addToast("Payout request submitted for review", "success");
        setRequestAmount("");
        load({ silent: true });
      } else {
        const err = await res.json().catch(() => ({}));
        addToast(err.detail || "Failed to request payout", "error");
      }
    } catch {
      addToast("Network error", "error");
    } finally {
      setRequesting(false);
    }
  };

  const updateInvoiceStatus = async (invoiceId: number, status: string) => {
    try {
      const res = await apiFetch(`/invoices/${invoiceId}/status`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      if (res.ok) {
        addToast(`Invoice #${invoiceId} marked as ${status}`, "success");
        load({ silent: true });
      }
    } catch {
      addToast("Network error", "error");
    }
  };

  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = { all: payouts.length };
    payouts.forEach((p) => { const s = normalizeStatus(p.status); counts[s] = (counts[s] || 0) + 1; });
    return counts;
  }, [payouts]);

  const statusFilters: { key: PayoutStatusFilter; label: string }[] = [
    { key: "all", label: "All" },
    { key: "pending", label: "Pending" },
    { key: "processing", label: "Processing" },
    { key: "completed", label: "Completed" },
    { key: "rejected", label: "Rejected" },
  ];

  return (
    <SupplierLayout title="Payouts">
      <PanelContent className="space-y-4">
        {/* Summary Cards */}
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="theme-card rounded-xl border p-4">
            <div className="flex items-center gap-2 mb-1">
              <Wallet className="h-4 w-4 text-primary" />
              <span className="text-[10px] font-semibold uppercase text-text-faint">Total Payouts</span>
            </div>
            <p className="text-2xl font-bold text-text">{payouts.length}</p>
          </div>
          <div className="theme-card rounded-xl border p-4">
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle className="h-4 w-4 text-success" />
              <span className="text-[10px] font-semibold uppercase text-text-faint">Completed</span>
            </div>
            <p className="text-2xl font-bold text-text">{statusCounts.completed || 0}</p>
          </div>
          <div className="theme-card rounded-xl border p-4">
            <div className="flex items-center gap-2 mb-1">
              <Send className="h-4 w-4 text-warning" />
              <span className="text-[10px] font-semibold uppercase text-text-faint">Total Value</span>
            </div>
            <p className="text-2xl font-bold text-text">{formatMoney(payouts.reduce((s, p) => s + p.amount, 0))}</p>
          </div>
        </div>

        {/* Tabs: Payouts / Invoice Records */}
        <div className="theme-card rounded-xl border p-2">
          <PanelTabs
            items={[
              { key: "payouts", label: "Payout history", icon: Wallet },
              { key: "invoices", label: "Invoice records", icon: FileText },
            ]}
            value={activeTab}
            onChange={(next) => setActiveTab(next as "payouts" | "invoices")}
            className="border-0 bg-transparent p-0"
          />
        </div>

        {activeTab === "payouts" && (
          <>
            {/* Request Payout */}
            <div className="theme-card rounded-xl border p-4">
              <h3 className="text-sm font-bold text-text mb-3 flex items-center gap-2">
                <Send className="h-4 w-4 text-primary" />
                Request a Payout
              </h3>
              <div className="flex flex-wrap items-end gap-3">
                <div>
                  <label className="text-[10px] text-text-faint uppercase">Amount</label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="0.00"
                    value={requestAmount}
                    onChange={(e) => setRequestAmount(e.target.value)}
                    className="mt-1 block rounded-lg border border-border bg-surface-2 px-3 py-1.5 text-sm text-text w-36"
                  />
                </div>
                <Button variant="primary" onClick={handleRequestPayout}
                  disabled={requesting}>
                  {requesting ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : "Request Payout"}
                </Button>
              </div>
            </div>

            {/* Filters */}
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex gap-1">
                {statusFilters.map((f) => (
                  <button
                    key={f.key}
                    onClick={() => setStatusFilter(f.key)}
                    className={`rounded-lg px-2.5 py-1 text-[11px] font-medium transition ${
                      statusFilter === f.key ? "bg-primary text-primary-foreground" : "bg-surface-2 text-text-faint hover:bg-surface-3"
                    }`}
                  >
                    {f.label} ({statusCounts[f.key] || 0})
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3 w-3 -translate-y-1/2 text-text-faint" />
                  <input
                    placeholder="Search id, reference, notes"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="rounded-lg border border-border bg-surface-2 py-1.5 pl-8 pr-3 text-xs text-text placeholder:text-text-faint"
                  />
                </div>
                <button onClick={() => load({ silent: true })} disabled={refreshing} className="rounded-lg border border-border bg-surface-2 px-2.5 py-1.5 text-xs text-text-faint hover:bg-surface-3">
                  <RefreshCw className={`h-3 w-3 ${refreshing ? "animate-spin" : ""}`} />
                </button>
              </div>
            </div>

            {/* Payouts List */}
            {loading ? (
              <div className="space-y-2">{Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-16 animate-pulse rounded-xl bg-surface-2" />)}</div>
            ) : filteredPayouts.length === 0 ? (
              <div className="theme-card rounded-xl border p-8 text-center text-sm text-text-muted">
                <Wallet className="h-8 w-8 mx-auto mb-2 opacity-40" />
                <p>No payout history found</p>
              </div>
            ) : (
              <div className="theme-card rounded-xl border overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-surface-2 border-b border-border">
                    <tr>
                      <th className="text-left p-3 font-semibold text-[11px]">ID</th>
                      <th className="text-left p-3 font-semibold text-[11px]">Reference</th>
                      <th className="text-right p-3 font-semibold text-[11px]">Amount</th>
                      <th className="text-center p-3 font-semibold text-[11px]">Status</th>
                      <th className="text-left p-3 font-semibold text-[11px]">Date</th>
                      <th className="text-center p-3 font-semibold text-[11px]"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredPayouts.map((payout) => (
                      <Fragment key={payout.id}>
                        <tr className="border-b border-border last:border-0 hover:bg-surface-1/50 cursor-pointer" onClick={() => setExpandedPayoutId(expandedPayoutId === payout.id ? null : payout.id)}>
                          <td className="p-3 font-mono text-xs">#{payout.id}</td>
                          <td className="p-3 text-xs text-text-faint">{payout.reference || "—"}</td>
                          <td className="p-3 text-right font-semibold">{formatMoney(payout.amount)}</td>
                          <td className="p-3 text-center">
                            <span className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold ${payoutStatusTone(payout.status)}`}>
                              {titleCase(payout.status)}
                            </span>
                          </td>
                          <td className="p-3 text-xs text-text-faint">{payout.created_at?.slice(0, 10)}</td>
                          <td className="p-3 text-center">
                            <button className="text-[10px] text-primary hover:underline" onClick={(e) => { e.stopPropagation(); setExpandedPayoutId(expandedPayoutId === payout.id ? null : payout.id); }}>
                              Show detail
                            </button>
                          </td>
                        </tr>
                        {expandedPayoutId === payout.id && (
                          <tr className="bg-surface-1">
                            <td colSpan={6} className="p-3">
                              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                                <div>
                                  <p className="text-text-faint uppercase text-[10px]">Method</p>
                                  <p className="font-medium">{titleCase(payout.method) || "Bank Transfer"}</p>
                                </div>
                                <div>
                                  <p className="text-text-faint uppercase text-[10px]">Reference</p>
                                  <p className="font-mono">{payout.reference || "—"}</p>
                                </div>
                                <div>
                                  <p className="text-text-faint uppercase text-[10px]">Created</p>
                                  <p>{payout.created_at ? new Date(payout.created_at).toLocaleString() : "—"}</p>
                                </div>
                                <div>
                                  <p className="text-text-faint uppercase text-[10px]">Processed</p>
                                  <p>{payout.processed_at ? new Date(payout.processed_at).toLocaleString() : "—"}</p>
                                </div>
                                {payout.notes && (
                                  <div className="col-span-full">
                                    <p className="text-text-faint uppercase text-[10px]">Notes</p>
                                    <p>{payout.notes}</p>
                                  </div>
                                )}
                              </div>
                            </td>
                          </tr>
                        )}
                      </Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}

        {activeTab === "invoices" && (
          <>
            {/* Create Invoice */}
            <div className="theme-card rounded-xl border p-4">
              <h3 className="text-sm font-bold text-text mb-3 flex items-center gap-2">
                <Plus className="h-4 w-4 text-primary" />
                Create Invoice Record
              </h3>
              <div className="flex flex-wrap gap-3 items-end">
                <div>
                  <label className="text-[10px] text-text-faint uppercase">Order number</label>
                  <input
                    placeholder="Order number"
                    value={invoiceForm.order_id}
                    onChange={(e) => setInvoiceForm((f) => ({ ...f, order_id: e.target.value }))}
                    className="mt-1 block rounded-lg border border-border bg-surface-2 px-3 py-1.5 text-sm text-text w-32"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-text-faint uppercase">Shipment ID (optional)</label>
                  <input
                    placeholder="Optional shipment id"
                    value={invoiceForm.shipment_id}
                    onChange={(e) => setInvoiceForm((f) => ({ ...f, shipment_id: e.target.value }))}
                    className="mt-1 block rounded-lg border border-border bg-surface-2 px-3 py-1.5 text-sm text-text w-32"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-text-faint uppercase">Notes (optional)</label>
                  <input
                    placeholder="Optional invoice note"
                    value={invoiceForm.notes}
                    onChange={(e) => setInvoiceForm((f) => ({ ...f, notes: e.target.value }))}
                    className="mt-1 block rounded-lg border border-border bg-surface-2 px-3 py-1.5 text-sm text-text w-48"
                  />
                </div>
                <Button variant="primary" onClick={handleCreateInvoice}>
                  Create invoice record
                </Button>
              </div>
            </div>

            {/* Invoice History */}
            <div className="theme-card rounded-xl border p-4">
              <h3 className="text-sm font-bold text-text mb-3">Invoice history</h3>
              {invoices.length === 0 ? (
                <p className="text-center text-sm text-text-muted py-4">No invoice records</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border">
                        <th className="text-left p-2 font-semibold text-[11px]">Invoice #</th>
                        <th className="text-left p-2 font-semibold text-[11px]">Order</th>
                        <th className="text-right p-2 font-semibold text-[11px]">Amount</th>
                        <th className="text-center p-2 font-semibold text-[11px]">Status</th>
                        <th className="text-left p-2 font-semibold text-[11px]">Created</th>
                        <th className="text-center p-2 font-semibold text-[11px]">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {invoices.map((inv) => (
                        <tr key={inv.id} className="border-b border-border last:border-0">
                          <td className="p-2 font-mono text-xs">{inv.invoice_number}</td>
                          <td className="p-2 text-text-faint">#{inv.order_id}</td>
                          <td className="p-2 text-right font-semibold">{formatMoney(inv.total_amount)}</td>
                          <td className="p-2 text-center">
                            <span className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                               inv.status === "paid" ? "bg-success/20 text-success" : inv.status === "overdue" ? "bg-danger/20 text-danger" : "bg-warning/20 text-warning"
                            }`}>
                              {titleCase(inv.status)}
                            </span>
                          </td>
                          <td className="p-2 text-xs text-text-faint">{inv.created_at?.slice(0, 10)}</td>
                          <td className="p-2 text-center">
                            <div className="flex items-center justify-center gap-1">
                              <Button variant="primary" className="rounded px-2 py-0.5 text-[10px]" onClick={() => updateInvoiceStatus(inv.id, "paid")}>Paid</Button>
                               <Button variant="danger" className="rounded px-2 py-0.5 text-[10px]" onClick={() => updateInvoiceStatus(inv.id, "overdue")}>Overdue</Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}
      </PanelContent>
    </SupplierLayout>
  );
}

function Fragment({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
