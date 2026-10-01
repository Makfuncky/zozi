"use client";
import { useEffect, useState, useCallback } from "react";
import { DollarSign, RefreshCw, Wallet, CheckCircle, Send, Clock, UploadCloud } from "@/lib/icons";
import { PanelContent } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useToastStore } from "@/lib/toastStore";

interface PartnerPayout {
  id: number;
  amount: number;
  status: string;
  method?: string | null;
  reference?: string | null;
  notes?: string | null;
  created_at: string;
  processed_at?: string | null;
}

interface FinanceSummary {
  total_delivery_fees?: number;
  available_balance?: number;
  pending_payouts?: number;
  total_completed?: number;
  currency?: string;
  has_pending_cod?: boolean;
  pending_cod_amount?: number;
  bank_instruction?: string;
}

interface Settlement {
  id: number;
  order_id?: number;
  total_delivery_fee?: number;
  currency?: string;
  cod_collected?: number;
  cod_retained?: number;
  cod_remitted?: number;
  cod_remittance_status?: string;
  status?: string;
  created_at?: string;
}

interface CodReceipt {
  id: number;
  settlement_id?: number;
  partner_id?: number;
  order_id?: number;
  amount?: number;
  currency?: string;
  bank_reference?: string;
  receipt_file_url?: string;
  notes?: string;
  status?: string;
  review_note?: string;
  created_at?: string;
}

function normalizeStatus(value?: string | null) {
  return String(value || "").trim().toLowerCase();
}

function titleCase(value?: string | null) {
  if (!value) return "Unknown";
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function statusTone(status?: string | null) {
  const n = normalizeStatus(status);
  if (n === "completed" || n === "verified") return "bg-success/20 text-success";
  if (n === "rejected") return "bg-danger/20 text-danger";
  if (n === "processing") return "bg-info/20 text-info";
  return "bg-warning/20 text-warning";
}

export default function FinanceSection() {
  const formatMoney = useCurrencyStore((s) => s.format);
  const addToast = useToastStore((s) => s.addToast);
  const [payouts, setPayouts] = useState<PartnerPayout[]>([]);
  const [summary, setSummary] = useState<FinanceSummary | null>(null);
  const [settlements, setSettlements] = useState<Settlement[]>([]);
  const [receipts, setReceipts] = useState<CodReceipt[]>([]);
  const [loading, setLoading] = useState(true);
  const [codForm, setCodForm] = useState({ amount: "", bank_reference: "", notes: "" });
  const [codFile, setCodFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [codMessage, setCodMessage] = useState<string | null>(null);

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const [payoutsRes, summaryRes, settlementsRes, receiptsRes] = await Promise.all([
        apiFetch("/logistics-partner/payouts").catch(() => null),
        apiFetch("/finance/logistics/summary").catch(() => null),
        apiFetch("/finance/logistics/settlements").catch(() => null),
        apiFetch("/logistics-partner/me/cod-remittance-receipts").catch(() => null),
      ]);
      if (payoutsRes?.ok) {
        const data = await payoutsRes.json();
        setPayouts(Array.isArray(data) ? data : data.items ?? []);
      }
      if (summaryRes?.ok) setSummary(await summaryRes.json());
      if (settlementsRes?.ok) {
        const data = await settlementsRes.json();
        setSettlements(Array.isArray(data) ? data : data.items ?? []);
      }
      if (receiptsRes?.ok) {
        const data = await receiptsRes.json();
        setReceipts(Array.isArray(data) ? data : data.items ?? []);
      }
    } catch {
      addToast("Failed to load finance data", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => { loadAll(); }, [loadAll]);

  const totalCompleted = payouts.filter((p) => normalizeStatus(p.status) === "completed").length;
  const totalValue = payouts.reduce((s, p) => s + p.amount, 0);

  async function submitCodProof() {
    if (!codFile || !codForm.amount) {
      setCodMessage("Attach a receipt file and enter the remitted amount.");
      return;
    }
    setSubmitting(true);
    setCodMessage(null);
    try {
      const body = new FormData();
      body.append("amount", codForm.amount);
      body.append("bank_reference", codForm.bank_reference);
      body.append("notes", codForm.notes);
      body.append("receipt_file", codFile);
      const res = await apiFetch("/logistics-partner/me/cod-remittance-receipts", {
        method: "POST",
        body,
      });
      if (res.ok) {
        const created = await res.json();
        setReceipts((prev) => [created, ...prev]);
        setCodForm({ amount: "", bank_reference: "", notes: "" });
        setCodFile(null);
        setCodMessage("COD receipt submitted for finance verification.");
      } else {
        setCodMessage("Unable to submit COD receipt.");
      }
    } catch {
      setCodMessage("Unable to submit COD receipt.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <PanelContent className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-bold text-text">Finance Overview</h2>
        <button onClick={loadAll} className="rounded-lg border border-border bg-surface-2 px-2.5 py-1.5 text-xs text-text-faint hover:bg-surface-3">
          <RefreshCw className={`h-3 w-3 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

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
          <p className="text-2xl font-bold text-text">{totalCompleted}</p>
        </div>
        <div className="theme-card rounded-xl border p-4">
          <div className="flex items-center gap-2 mb-1">
            <Send className="h-4 w-4 text-warning" />
            <span className="text-[10px] font-semibold uppercase text-text-faint">Total Value</span>
          </div>
          <p className="text-2xl font-bold text-text">{formatMoney(totalValue)}</p>
        </div>
      </div>

      <div className="theme-card rounded-xl border p-4 space-y-3">
        <h3 className="text-sm font-bold text-text">COD Receipt Upload</h3>
        {summary?.bank_instruction ? (
          <p className="text-[11px] text-text-muted">{summary.bank_instruction}</p>
        ) : null}
        <div className="grid gap-3 sm:grid-cols-3">
          <label className="flex flex-col gap-1 text-xs text-text-muted">
            Amount
            <input
              value={codForm.amount}
              onChange={(e) => setCodForm((c) => ({ ...c, amount: e.target.value }))}
              inputMode="decimal"
              placeholder="120.00"
              className="theme-input w-full rounded-xl border px-3 py-2 text-xs focus:border-primary focus:outline-none"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-text-muted">
            Bank deposit reference
            <input
              value={codForm.bank_reference}
              onChange={(e) => setCodForm((c) => ({ ...c, bank_reference: e.target.value }))}
              placeholder="Bank deposit reference"
              className="theme-input w-full rounded-xl border px-3 py-2 text-xs focus:border-primary focus:outline-none"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-text-muted">
            Optional note for finance review
            <textarea
              rows={1}
              value={codForm.notes}
              onChange={(e) => setCodForm((c) => ({ ...c, notes: e.target.value }))}
              placeholder="Optional note for finance review"
              className="theme-input w-full resize-none rounded-xl border px-3 py-2 text-xs focus:border-primary focus:outline-none"
            />
          </label>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <label className="inline-flex cursor-pointer items-center gap-2 rounded-xl border border-border bg-surface-2 px-3 py-2 text-xs text-text-muted">
            <UploadCloud className="h-4 w-4" />
            Attach receipt
            <input
              type="file"
              accept="image/*,application/pdf"
              className="hidden"
              onChange={(e) => setCodFile(e.target.files?.[0] ?? null)}
            />
          </label>
          <button
            type="button"
            onClick={submitCodProof}
            disabled={submitting}
            className="theme-btn-accent rounded-xl px-4 py-2 text-xs font-bold disabled:opacity-50"
          >
            {submitting ? "Submitting..." : "Submit COD proof"}
          </button>
        </div>
        {codMessage ? (
          <div className={`rounded-xl border px-3 py-2 text-xs font-medium ${codMessage.includes("Unable") || codMessage.includes("Attach") ? "border-danger/30 bg-danger/10 text-danger" : "border-success/30 bg-success/10 text-success"}`}>
            {codMessage}
          </div>
        ) : null}

        {receipts.length > 0 ? (
          <div className="overflow-x-auto rounded-xl border">
            <table className="w-full text-xs">
              <thead className="bg-surface-2 text-text-muted">
                <tr>
                  <th className="px-3 py-2 text-left">Reference</th>
                  <th className="px-3 py-2 text-left">Amount</th>
                  <th className="px-3 py-2 text-left">Status</th>
                </tr>
              </thead>
              <tbody>
                {receipts.map((r) => (
                  <tr key={r.id} className="border-t">
                    <td className="px-3 py-2 font-mono text-text-muted">{r.bank_reference || "—"}</td>
                    <td className="px-3 py-2 text-text">{r.amount != null ? formatMoney(r.amount) : "—"}</td>
                    <td className="px-3 py-2">
                      <span className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold ${statusTone(r.status)}`}>
                        {r.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>

      <div className="theme-card rounded-xl border overflow-hidden">
        <h3 className="px-4 pt-4 text-sm font-bold text-text">COD Settlements</h3>
        <table className="mt-3 w-full text-sm">
          <thead className="bg-surface-2 border-b border-border">
            <tr>
              <th className="text-left p-3 font-semibold text-[11px]">Order</th>
              <th className="text-right p-3 font-semibold text-[11px]">COD Collected</th>
              <th className="text-right p-3 font-semibold text-[11px]">Remitted</th>
              <th className="text-center p-3 font-semibold text-[11px]">Status</th>
            </tr>
          </thead>
          <tbody>
            {settlements.length === 0 ? (
              <tr><td colSpan={4} className="p-6 text-center text-text-muted text-sm">
                <DollarSign className="h-8 w-8 mx-auto mb-2 opacity-40" />
                <p>No COD settlements yet.</p>
              </td></tr>
            ) : (
              settlements.map((s) => (
                <tr key={s.id} className="border-b border-border last:border-0 hover:bg-surface-1/50">
                  <td className="p-3 font-mono text-xs">#{s.order_id}</td>
                  <td className="p-3 text-right font-semibold">{s.cod_collected != null ? formatMoney(s.cod_collected) : "—"}</td>
                  <td className="p-3 text-right font-semibold">{s.cod_remitted != null ? formatMoney(s.cod_remitted) : "—"}</td>
                  <td className="p-3 text-center">
                    <span className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold ${statusTone(s.cod_remittance_status)}`}>
                      {s.cod_remittance_status}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </PanelContent>
  );
}
