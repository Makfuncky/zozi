"use client";

import { useEffect, useState, useCallback } from "react";
import { FileText, Download, Eye, RefreshCw, Search } from "@/lib/icons";
import { useAuth } from "@/lib/useAuth";
import { isAdminStaffRole } from "@shared/adminPermissions";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useAdminCountry } from "@/lib/useAdminCountry";

interface Invoice {
  id: number;
  invoice_number: string;
  order_id: number;
  supplier_id?: number;
  total_amount: number;
  currency: string;
  status: string;
  created_at: string;
  due_at?: string;
  paid_at?: string;
  notes?: string;
}

export default function InvoicesPage() {
  const { user, isLoggedIn, isLoading } = useAuth();
  const role = user?.role ?? null;
  const formatMoney = useCurrencyStore((s) => s.format);
  const { selectedCountry, isGlobalView } = useAdminCountry();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  const fetchInvoices = useCallback(async () => {
    setLoading(true);
    try {
      const path = "/invoices/";
      const res = await apiFetch(path);
      if (res.ok) {
        const data = await res.json();
        setInvoices(Array.isArray(data) ? data : data.items ?? []);
      }
    } catch (err) {
      console.error("Failed to load invoices:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isLoading) return;
    if (!isLoggedIn || !isAdminStaffRole(role)) return;
    fetchInvoices();
  }, [isLoading, isLoggedIn, role, fetchInvoices]);

  if (isLoading || !isLoggedIn || !isAdminStaffRole(role)) {
    return <AdminLayout title="Invoices"><PanelLoadingState count={3} /></AdminLayout>;
  }

  const filtered = invoices.filter((inv) =>
    !search.trim() || [inv.invoice_number, String(inv.order_id), inv.status].some((v) => v?.toLowerCase().includes(search.toLowerCase()))
  );

  const statusTone = (s: string) => {
    if (s === "paid" || s === "completed") return "bg-success/20 text-success";
    if (s === "overdue" || s === "cancelled") return "bg-danger/20 text-danger";
    if (s === "issued" || s === "pending") return "bg-warning/20 text-warning";
    return "bg-surface-2 text-text-faint";
  };

  return (
    <AdminLayout title="Invoices" headerMode="compact">
      <PanelContent className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-text">Invoice Management</h2>
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-text-faint">{isGlobalView ? "Global View" : `Country: ${selectedCountry?.code}`}</span>
            <button onClick={fetchInvoices} className="rounded-lg border border-border bg-surface-2 px-2.5 py-1.5 text-xs text-text-faint hover:bg-surface-3">
              <RefreshCw className="h-3 w-3" />
            </button>
          </div>
        </div>

        <div className="relative max-w-xs">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3 w-3 -translate-y-1/2 text-text-faint" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search invoices..." className="w-full rounded-lg border border-border bg-surface-2 py-1.5 pl-8 pr-3 text-xs text-text" />
        </div>

        <div className="grid gap-3 sm:grid-cols-3">
          <div className="theme-card rounded-xl border p-3">
            <p className="text-[10px] text-text-faint uppercase">Total</p>
            <p className="text-xl font-bold text-text">{invoices.length}</p>
          </div>
          <div className="theme-card rounded-xl border p-3">
            <p className="text-[10px] text-text-faint uppercase">Outstanding</p>
            <p className="text-xl font-bold text-warning">{invoices.filter((i) => i.status === "issued" || i.status === "overdue").length}</p>
          </div>
          <div className="theme-card rounded-xl border p-3">
            <p className="text-[10px] text-text-faint uppercase">Total Value</p>
            <p className="text-xl font-bold text-text">{formatMoney(invoices.reduce((s, i) => s + i.total_amount, 0))}</p>
          </div>
        </div>

        {loading ? (
          <PanelLoadingState count={4} />
        ) : filtered.length === 0 ? (
          <div className="theme-card rounded-xl border p-8 text-center text-text-muted">
            <FileText className="h-8 w-8 mx-auto mb-2 opacity-40" />
            <p className="text-sm">No invoices found</p>
          </div>
        ) : (
          <div className="theme-card rounded-xl border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-surface-2 border-b border-border">
                <tr>
                  <th className="text-left p-2 font-semibold text-[11px]">Invoice #</th>
                  <th className="text-left p-2 font-semibold text-[11px]">Order</th>
                  <th className="text-right p-2 font-semibold text-[11px]">Amount</th>
                  <th className="text-center p-2 font-semibold text-[11px]">Status</th>
                  <th className="text-left p-2 font-semibold text-[11px]">Created</th>
                  <th className="text-left p-2 font-semibold text-[11px]">Due</th>
                  <th className="text-center p-2 font-semibold text-[11px]">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((inv) => (
                  <tr key={inv.id} className="border-b border-border last:border-0 hover:bg-surface-1/50">
                    <td className="p-2 font-mono text-xs">{inv.invoice_number}</td>
                    <td className="p-2 text-xs text-text-faint">#{inv.order_id}</td>
                    <td className="p-2 text-right font-semibold">{formatMoney(inv.total_amount)}</td>
                    <td className="p-2 text-center">
                      <span className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold ${statusTone(inv.status)}`}>{inv.status}</span>
                    </td>
                    <td className="p-2 text-xs text-text-faint">{inv.created_at?.slice(0, 10)}</td>
                    <td className="p-2 text-xs text-text-faint">{inv.due_at?.slice(0, 10) || "—"}</td>
                    <td className="p-2 text-center">
                      <div className="flex items-center justify-center gap-1">
                        <button className="rounded p-1 text-text-faint hover:text-text" title="View"><Eye className="h-3.5 w-3.5" /></button>
                        <button className="rounded p-1 text-text-faint hover:text-text" title="Download"><Download className="h-3.5 w-3.5" /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </PanelContent>
    </AdminLayout>
  );
}
