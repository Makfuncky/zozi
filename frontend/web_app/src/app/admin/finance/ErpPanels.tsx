"use client";

import { Button } from "@/components/ui/Button";

import { useCallback, useEffect, useState } from "react";
import {
  Receipt, FileSpreadsheet, Wallet, Coins, PiggyBank, Landmark, Calculator,
  ArrowDownUp, BookOpen, Filter, Download, UploadCloud, FileText, BadgeCheck,
  CircleDollarSign, Banknote, Printer, Search, Plus, RefreshCw, Trash2, Pencil,
  CheckCircle2, XCircle, Split, FileSearch, ListChecks,
} from "@/lib/icons";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useAdminCountry } from "@/lib/useAdminCountry";
import { useToastStore } from "@/lib/toastStore";
import { motion } from "framer-motion";

const ACCOUNT_BASE = "/accounting";

/* ───────────────────────── Shared helpers ───────────────────────── */

export function csvExport(filename: string, rows: any[], columns: { key: string; header: string }[]) {
  const escape = (v: any) => {
    const s = v === null || v === undefined ? "" : String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const head = columns.map((c) => escape(c.header)).join(",");
  const body = rows.map((r) => columns.map((c) => escape(r[c.key])).join(",")).join("\n");
  const blob = new Blob([`${head}\n${body}`], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-[10px] uppercase text-text-faint font-semibold">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  );
}

/* Account picker: searches the COA for a code/name selection. */
export function AccountPicker({
  value, onChange, placeholder = "Search account...",
}: { value: string; onChange: (code: string) => void; placeholder?: string }) {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (!q) { setResults([]); return; }
    const t = setTimeout(async () => {
      const res = await apiFetch(`${ACCOUNT_BASE}/coa/search?search=${encodeURIComponent(q)}&limit=8`);
      if (res.ok) { const d = await res.json(); setResults(d.items || []); }
    }, 250);
    return () => clearTimeout(t);
  }, [q]);
  return (
    <div className="relative">
      <div className="flex items-center gap-2">
        <input className="fin-input" placeholder={placeholder} value={value || q}
          onChange={(e) => { setQ(e.target.value); setOpen(true); onChange(e.target.value); }}
          onFocus={() => setOpen(true)} />
        {value && <button onClick={() => { setQ(""); onChange(""); }} className="text-text-faint hover:text-danger"><XCircle className="h-3.5 w-3.5" /></button>}
      </div>
      {open && results.length > 0 && (
        <div className="absolute z-20 mt-1 w-full theme-card rounded-lg border max-h-56 overflow-y-auto">
          {results.map((a) => (
            <button key={a.code} onClick={() => { onChange(a.code); setQ(""); setOpen(false); }}
              className="w-full text-left px-3 py-1.5 text-xs hover:bg-surface-2 flex items-center gap-2">
              <span className="font-mono">{a.code}</span><span className="text-text-faint">{a.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/* ───────────────────────── Journal Browser ───────────────────────── */

export function JournalBrowserPanel() {
  const formatMoney = useCurrencyStore((s) => s.format);
  const { selectedCountry, isGlobalView } = useAdminCountry();
  const toast = useToastStore((s) => s.addToast);
  const [loading, setLoading] = useState(true);
  const [rows, setRows] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [accountCode, setAccountCode] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.set("search", search);
      if (accountCode) params.set("account_code", accountCode);
      if (startDate) params.set("start_date", startDate);
      if (endDate) params.set("end_date", endDate);
      if (!isGlobalView && selectedCountry?.code) params.set("country_code", selectedCountry.code);
      params.set("limit", "100");
      const res = await apiFetch(`${ACCOUNT_BASE}/journal/browse?${params.toString()}`);
      if (res.ok) { const d = await res.json(); setRows(d.items || []); setTotal(d.total || 0); }
      else toast("Failed to load journal", "error");
    } catch { toast("Network error", "error"); }
    finally { setLoading(false); }
  }, [search, accountCode, startDate, endDate, selectedCountry?.code, isGlobalView, toast]);

  useEffect(() => { const t = setTimeout(load, 200); return () => clearTimeout(t); }, [load]);

  const doExport = () => csvExport("journal_entries.csv", rows, [
    { key: "id", header: "ID" }, { key: "reference_number", header: "Ref" },
    { key: "entry_date", header: "Date" }, { key: "reference_type", header: "Type" },
    { key: "description", header: "Description" }, { key: "country_code", header: "Country" },
  ]);

  if (loading) return <PanelLoadingState count={3} blockClassName="h-16 rounded-xl bg-surface-2 animate-pulse" />;

  return (
    <PanelContent className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-text-faint"><BookOpen className="h-3 w-3" /> Journal Entries — {total} entries</div>
        <button onClick={doExport} className="flex items-center gap-1.5 rounded-lg bg-surface-2 px-3 py-1.5 text-xs hover:bg-surface-3"><Download className="h-3.5 w-3.5" /> Export CSV</button>
      </div>

      <div className="theme-card rounded-xl border p-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Field label="Search"><input className="fin-input" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="ref / description" /></Field>
        <Field label="Account">
          <AccountPicker value={accountCode} onChange={setAccountCode} placeholder="account code" />
        </Field>
        <Field label="From"><input type="date" className="fin-input" value={startDate} onChange={(e) => setStartDate(e.target.value)} /></Field>
        <Field label="To"><input type="date" className="fin-input" value={endDate} onChange={(e) => setEndDate(e.target.value)} /></Field>
      </div>

      <div className="theme-card rounded-xl border overflow-hidden">
        <div className="max-h-[60vh] overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="bg-surface-2 sticky top-0">
              <tr>
                <th className="text-left p-2 font-semibold">Ref</th>
                <th className="text-left p-2 font-semibold">Date</th>
                <th className="text-left p-2 font-semibold">Type</th>
                <th className="text-left p-2 font-semibold">Description</th>
                <th className="text-left p-2 font-semibold">Lines</th>
                <th className="text-center p-2 font-semibold">Country</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 ? <tr><td colSpan={6} className="p-6 text-center text-text-muted text-xs">No journal entries.</td></tr>
                : rows.map((e) => (
                  <tr key={e.id} className="border-b border-border last:border-0 align-top">
                    <td className="p-2 font-mono text-xs">{e.reference_number}</td>
                    <td className="p-2 text-xs text-text-faint">{e.entry_date?.slice(0, 10)}</td>
                    <td className="p-2 text-xs uppercase">{e.reference_type || "—"}</td>
                    <td className="p-2">{e.description || <span className="text-text-faint">—</span>}</td>
                    <td className="p-2">
                      <div className="space-y-0.5">
                        {e.lines.map((l: any, i: number) => (
                          <div key={i} className="text-xs flex gap-1.5">
                            <span className="font-mono">{l.account_code}</span>
                            <span className={l.side === "debit" ? "text-danger" : "text-success"}>{l.side[0].toUpperCase()}</span>
                            <span className="text-text-faint">{formatMoney(l.amount)}</span>
                          </div>
                        ))}
                      </div>
                    </td>
                    <td className="p-2 text-center text-xs text-text-faint">{e.country_code || "—"}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </PanelContent>
  );
}

/* ───────────────────────── AR Panel ───────────────────────── */

export function ARPanel() {
  const formatMoney = useCurrencyStore((s) => s.format);
  const { selectedCountry, isGlobalView } = useAdminCountry();
  const toast = useToastStore((s) => s.addToast);
  const [loading, setLoading] = useState(true);
  const [invoices, setInvoices] = useState<any[]>([]);
  const [aging, setAging] = useState<any>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ customer_id: "", invoice_number: "", amount: "", tax_amount: "0", account_code: "4010", description: "" });

  const cc = () => (!isGlobalView && selectedCountry?.code ? selectedCountry.code : "");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const p = new URLSearchParams(); const c = cc(); if (c) p.set("country_code", c);
      const [inv, age] = await Promise.all([
        apiFetch(`${ACCOUNT_BASE}/ar/invoices?${p.toString()}`),
        apiFetch(`${ACCOUNT_BASE}/ar/aging?${c ? "country_code=" + c : ""}`),
      ]);
      if (inv.ok) setInvoices((await inv.json()).items || []);
      if (age.ok) setAging(await age.json());
    } catch { toast("Network error", "error"); }
    finally { setLoading(false); }
  }, [selectedCountry?.code, isGlobalView, toast]);

  useEffect(() => { load(); }, [load]);

  const create = async () => {
    const res = await apiFetch(`${ACCOUNT_BASE}/ar/invoices`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        customer_id: parseInt(form.customer_id), invoice_number: form.invoice_number,
        invoice_date: new Date().toISOString(), account_code: form.account_code,
        amount: parseFloat(form.amount || "0"), tax_amount: parseFloat(form.tax_amount || "0"),
        description: form.description, country_code: cc(),
      }),
    });
    if (res.ok) { toast("AR invoice posted to GL", "success"); setShowForm(false); setForm({ customer_id: "", invoice_number: "", amount: "", tax_amount: "0", account_code: "4010", description: "" }); load(); }
    else { const e = await res.json().catch(() => ({})); toast(e.detail || "Failed", "error"); }
  };

  if (loading) return <PanelLoadingState count={3} />;

  const buckets = aging ? Object.entries(aging.buckets || {}) : [];
  return (
    <PanelContent className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-text-faint"><Receipt className="h-3 w-3" /> Accounts Receivable</div>
        <Button variant="primary" className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold" onClick={() => setShowForm((s) => !s)}><Plus className="h-3.5 w-3.5" /> New Invoice</Button>
      </div>

      {aging && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="theme-card rounded-xl border p-3">
            <div className="text-[10px] uppercase text-text-faint">Total AR</div>
            <div className="text-lg font-bold">{formatMoney(aging.total || 0)}</div>
          </div>
          {buckets.map(([k, v]) => (
            <div key={k} className="theme-card rounded-xl border p-3">
              <div className="text-[10px] uppercase text-text-faint">{k.replace("b", "bucket ")}</div>
              <div className="text-lg font-bold">{formatMoney(v as number)}</div>
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} className="theme-card rounded-xl border p-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <Field label="Customer ID"><input className="fin-input" value={form.customer_id} onChange={(e) => setForm({ ...form, customer_id: e.target.value })} placeholder="user id" /></Field>
          <Field label="Invoice #"><input className="fin-input" value={form.invoice_number} onChange={(e) => setForm({ ...form, invoice_number: e.target.value })} placeholder="INV-001" /></Field>
          <Field label="Amount"><input type="number" className="fin-input" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} /></Field>
          <Field label="VAT"><input type="number" className="fin-input" value={form.tax_amount} onChange={(e) => setForm({ ...form, tax_amount: e.target.value })} /></Field>
          <Field label="Revenue Account"><input className="fin-input" value={form.account_code} onChange={(e) => setForm({ ...form, account_code: e.target.value })} /></Field>
          <div className="flex items-end"><button onClick={create} disabled={!form.customer_id || !form.amount} className="theme-btn-primary px-4 py-1.5 text-sm rounded-lg disabled:opacity-50">Post Invoice</button></div>
          <div className="sm:col-span-2 lg:col-span-3"><Field label="Description"><textarea className="fin-input" rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></Field></div>
        </motion.div>
      )}

      <div className="theme-card rounded-xl border overflow-hidden">
        <div className="max-h-[55vh] overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="bg-surface-2 sticky top-0"><tr><th className="text-left p-2">Invoice #</th><th className="text-right p-2">Amount</th><th className="text-left p-2">Due</th><th className="text-center p-2">Status</th><th className="text-center p-2">Country</th></tr></thead>
            <tbody>
              {invoices.length === 0 ? <tr><td colSpan={5} className="p-6 text-center text-text-muted text-xs">No AR invoices.</td></tr>
                : invoices.map((r) => (
                  <tr key={r.id} className="border-b border-border last:border-0">
                    <td className="p-2 font-mono text-xs">{r.invoice_number}</td>
                    <td className="p-2 text-right">{formatMoney(r.amount)}</td>
                    <td className="p-2 text-xs text-text-faint">{r.due_date?.slice(0, 10)}</td>
                    <td className="p-2 text-center"><span className="text-[10px] bg-info/20 text-info px-1.5 py-0.5 rounded-full">{r.status}</span></td>
                    <td className="p-2 text-center text-xs text-text-faint">{r.country_code || "—"}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </PanelContent>
  );
}

/* ───────────────────────── AP Panel ───────────────────────── */

export function APPanel() {
  const formatMoney = useCurrencyStore((s) => s.format);
  const { selectedCountry, isGlobalView } = useAdminCountry();
  const toast = useToastStore((s) => s.addToast);
  const [loading, setLoading] = useState(true);
  const [bills, setBills] = useState<any[]>([]);
  const [aging, setAging] = useState<any>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ vendor_id: "", bill_number: "", amount: "", tax_amount: "0", account_code: "5030", description: "" });

  const cc = () => (!isGlobalView && selectedCountry?.code ? selectedCountry.code : "");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const p = new URLSearchParams(); const c = cc(); if (c) p.set("country_code", c);
      const [bl, age] = await Promise.all([
        apiFetch(`${ACCOUNT_BASE}/ap/bills?${p.toString()}`),
        apiFetch(`${ACCOUNT_BASE}/ap/aging?${c ? "country_code=" + c : ""}`),
      ]);
      if (bl.ok) setBills((await bl.json()).items || []);
      if (age.ok) setAging(await age.json());
    } catch { toast("Network error", "error"); }
    finally { setLoading(false); }
  }, [selectedCountry?.code, isGlobalView, toast]);

  useEffect(() => { load(); }, [load]);

  const create = async () => {
    const res = await apiFetch(`${ACCOUNT_BASE}/ap/bills`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        vendor_id: parseInt(form.vendor_id), bill_number: form.bill_number,
        bill_date: new Date().toISOString(), account_code: form.account_code,
        amount: parseFloat(form.amount || "0"), tax_amount: parseFloat(form.tax_amount || "0"),
        description: form.description, country_code: cc(),
      }),
    });
    if (res.ok) { toast("AP bill posted to GL", "success"); setShowForm(false); setForm({ vendor_id: "", bill_number: "", amount: "", tax_amount: "0", account_code: "5030", description: "" }); load(); }
    else { const e = await res.json().catch(() => ({})); toast(e.detail || "Failed", "error"); }
  };

  if (loading) return <PanelLoadingState count={3} />;

  const buckets = aging ? Object.entries(aging.buckets || {}) : [];
  return (
    <PanelContent className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-text-faint"><FileText className="h-3 w-3" /> Accounts Payable</div>
        <Button variant="primary" className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold" onClick={() => setShowForm((s) => !s)}><Plus className="h-3.5 w-3.5" /> New Bill</Button>
      </div>

      {aging && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="theme-card rounded-xl border p-3">
            <div className="text-[10px] uppercase text-text-faint">Total AP</div>
            <div className="text-lg font-bold">{formatMoney(aging.total || 0)}</div>
          </div>
          {buckets.map(([k, v]) => (
            <div key={k} className="theme-card rounded-xl border p-3">
              <div className="text-[10px] uppercase text-text-faint">{k.replace("b", "bucket ")}</div>
              <div className="text-lg font-bold">{formatMoney(v as number)}</div>
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} className="theme-card rounded-xl border p-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <Field label="Vendor ID"><input className="fin-input" value={form.vendor_id} onChange={(e) => setForm({ ...form, vendor_id: e.target.value })} placeholder="vendor id" /></Field>
          <Field label="Bill #"><input className="fin-input" value={form.bill_number} onChange={(e) => setForm({ ...form, bill_number: e.target.value })} placeholder="BILL-001" /></Field>
          <Field label="Amount"><input type="number" className="fin-input" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} /></Field>
          <Field label="VAT"><input type="number" className="fin-input" value={form.tax_amount} onChange={(e) => setForm({ ...form, tax_amount: e.target.value })} /></Field>
          <Field label="Expense Account"><input className="fin-input" value={form.account_code} onChange={(e) => setForm({ ...form, account_code: e.target.value })} /></Field>
          <div className="flex items-end"><button onClick={create} disabled={!form.vendor_id || !form.amount} className="theme-btn-primary px-4 py-1.5 text-sm rounded-lg disabled:opacity-50">Post Bill</button></div>
          <div className="sm:col-span-2 lg:col-span-3"><Field label="Description"><textarea className="fin-input" rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></Field></div>
        </motion.div>
      )}

      <div className="theme-card rounded-xl border overflow-hidden">
        <div className="max-h-[55vh] overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="bg-surface-2 sticky top-0"><tr><th className="text-left p-2">Bill #</th><th className="text-right p-2">Amount</th><th className="text-left p-2">Due</th><th className="text-center p-2">Status</th><th className="text-center p-2">Country</th></tr></thead>
            <tbody>
              {bills.length === 0 ? <tr><td colSpan={5} className="p-6 text-center text-text-muted text-xs">No AP bills.</td></tr>
                : bills.map((r) => (
                  <tr key={r.id} className="border-b border-border last:border-0">
                    <td className="p-2 font-mono text-xs">{r.bill_number}</td>
                    <td className="p-2 text-right">{formatMoney(r.amount)}</td>
                    <td className="p-2 text-xs text-text-faint">{r.due_date?.slice(0, 10)}</td>
                    <td className="p-2 text-center"><span className="text-[10px] bg-warning/20 text-warning px-1.5 py-0.5 rounded-full">{r.status}</span></td>
                    <td className="p-2 text-center text-xs text-text-faint">{r.country_code || "—"}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </PanelContent>
  );
}

/* ───────────────────────── Payments Register ───────────────────────── */

export function PaymentsRegisterPanel() {
  const formatMoney = useCurrencyStore((s) => s.format);
  const { selectedCountry, isGlobalView } = useAdminCountry();
  const toast = useToastStore((s) => s.addToast);
  const [loading, setLoading] = useState(true);
  const [rows, setRows] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [accountCode, setAccountCode] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const p = new URLSearchParams();
      if (accountCode) p.set("account_code", accountCode);
      if (startDate) p.set("start_date", startDate);
      if (endDate) p.set("end_date", endDate);
      if (!isGlobalView && selectedCountry?.code) p.set("country_code", selectedCountry.code);
      p.set("limit", "100");
      const res = await apiFetch(`${ACCOUNT_BASE}/payments/register?${p.toString()}`);
      if (res.ok) { const d = await res.json(); setRows(d.items || []); setTotal(d.total || 0); }
      else toast("Failed to load payments", "error");
    } catch { toast("Network error", "error"); }
    finally { setLoading(false); }
  }, [accountCode, startDate, endDate, selectedCountry?.code, isGlobalView, toast]);

  useEffect(() => { const t = setTimeout(load, 200); return () => clearTimeout(t); }, [load]);

  const doExport = () => csvExport("payments_register.csv", rows, [
    { key: "entry_id", header: "Entry ID" }, { key: "reference_number", header: "Ref" },
    { key: "entry_date", header: "Date" }, { key: "account_code", header: "Account" },
    { key: "account_name", header: "Name" }, { key: "side", header: "Side" },
    { key: "amount", header: "Amount" }, { key: "country_code", header: "Country" },
  ]);

  if (loading) return <PanelLoadingState count={3} />;

  return (
    <PanelContent className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-text-faint"><Wallet className="h-3 w-3" /> GL Payments Register — {total} entries</div>
        <button onClick={doExport} className="flex items-center gap-1.5 rounded-lg bg-surface-2 px-3 py-1.5 text-xs hover:bg-surface-3"><Download className="h-3.5 w-3.5" /> Export CSV</button>
      </div>

      <div className="theme-card rounded-xl border p-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <Field label="Account"><AccountPicker value={accountCode} onChange={setAccountCode} placeholder="account code" /></Field>
        <Field label="From"><input type="date" className="fin-input" value={startDate} onChange={(e) => setStartDate(e.target.value)} /></Field>
        <Field label="To"><input type="date" className="fin-input" value={endDate} onChange={(e) => setEndDate(e.target.value)} /></Field>
      </div>

      <div className="theme-card rounded-xl border overflow-hidden">
        <div className="max-h-[60vh] overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="bg-surface-2 sticky top-0"><tr><th className="text-left p-2">Ref</th><th className="text-left p-2">Date</th><th className="text-left p-2">Account</th><th className="text-center p-2">Side</th><th className="text-right p-2">Amount</th><th className="text-center p-2">Country</th></tr></thead>
            <tbody>
              {rows.length === 0 ? <tr><td colSpan={6} className="p-6 text-center text-text-muted text-xs">No payments.</td></tr>
                : rows.map((r, i) => (
                  <tr key={i} className="border-b border-border last:border-0">
                    <td className="p-2 font-mono text-xs">{r.reference_number}</td>
                    <td className="p-2 text-xs text-text-faint">{r.entry_date?.slice(0, 10)}</td>
                    <td className="p-2"><span className="font-mono text-xs">{r.account_code}</span> <span className="text-text-faint text-xs">{r.account_name}</span></td>
                    <td className="p-2 text-center text-xs uppercase"><span className={r.side === "debit" ? "text-danger" : "text-success"}>{r.side}</span></td>
                    <td className="p-2 text-right">{formatMoney(r.amount)}</td>
                    <td className="p-2 text-center text-xs text-text-faint">{r.country_code || "—"}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </PanelContent>
  );
}

/* ───────────────────────── Bank Reconciliation ───────────────────────── */

export function BankReconciliationPanel() {
  const { selectedCountry, isGlobalView } = useAdminCountry();
  const toast = useToastStore((s) => s.addToast);
  const [loading, setLoading] = useState(true);
  const [imports, setImports] = useState<any[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [lines, setLines] = useState<any[]>([]);
  const [busy, setBusy] = useState(false);

  const cc = () => (!isGlobalView && selectedCountry?.code ? selectedCountry.code : "");

  const loadSummary = useCallback(async () => {
    setLoading(true);
    try {
      const c = cc();
      const res = await apiFetch(`${ACCOUNT_BASE}/reconciliation-summary${c ? "?country_code=" + c : ""}`);
      if (res.ok) { const d = await res.json(); setImports(d.imports || []); }
      else toast("Failed to load reconciliation", "error");
    } catch { toast("Network error", "error"); }
    finally { setLoading(false); }
  }, [selectedCountry?.code, isGlobalView, toast]);

  useEffect(() => { loadSummary(); }, [loadSummary]);

  const openImport = async (id: number) => {
    setSelected(id); setBusy(true);
    try {
      const res = await apiFetch(`${ACCOUNT_BASE}/reconciliation/${id}`);
      if (res.ok) { const d = await res.json(); setLines(d.lines || []); }
    } finally { setBusy(false); }
  };

  const autoMatch = async (id: number) => {
    setBusy(true);
    try {
      const res = await apiFetch(`${ACCOUNT_BASE}/reconciliation/${id}/auto-match`, { method: "POST" });
      if (res.ok) { const d = await res.json(); toast(`Auto-matched ${d.matched || 0} lines`, "success"); openImport(id); }
      else toast("Auto-match failed", "error");
    } finally { setBusy(false); }
  };

  const matchLine = async (lineId: number, jeId: number) => {
    if (!selected) return;
    const res = await apiFetch(`${ACCOUNT_BASE}/reconciliation/${selected}/lines/${lineId}/match`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ journal_entry_id: jeId }),
    });
    if (res.ok) { toast("Line matched", "success"); openImport(selected); }
    else toast("Match failed", "error");
  };

  if (loading) return <PanelLoadingState count={3} />;

  return (
    <PanelContent className="space-y-4">
      <div className="flex items-center gap-2 text-xs text-text-faint"><Split className="h-3 w-3" /> Bank Reconciliation — match statement lines to GL journal entries</div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="theme-card rounded-xl border p-4 space-y-2">
          <h3 className="text-sm font-bold flex items-center gap-2"><ListChecks className="h-4 w-4 text-primary" /> Imported Statements</h3>
          {imports.length === 0 ? <p className="text-xs text-text-faint text-center py-4">No statements imported. Use Bank Mapping → Import to upload a CSV.</p>
            : imports.map((imp) => (
              <div key={imp.import_id} className={`flex items-center justify-between rounded-lg border p-2 cursor-pointer ${selected === imp.import_id ? "border-primary bg-primary/5" : ""}`} onClick={() => openImport(imp.import_id)}>
                <div>
                  <div className="text-sm font-semibold">#{imp.import_id} {imp.bank_name || "—"}</div>
                  <div className="text-xs text-text-faint">{imp.matched}/{imp.total} reconciled · {imp.status}</div>
                </div>
                <Button variant="primary" className="text-xs rounded-lg px-2 py-1 disabled:opacity-50" onClick={(e) => { e.stopPropagation(); autoMatch(imp.import_id); }} disabled={busy}>Auto-match</Button>
              </div>
            ))}
        </div>

        <div className="theme-card rounded-xl border p-4 space-y-2">
          <h3 className="text-sm font-bold flex items-center gap-2"><CircleDollarSign className="h-4 w-4 text-primary" /> Statement Lines {selected ? `· #${selected}` : ""}</h3>
          {!selected && <p className="text-xs text-text-faint text-center py-4">Select a statement to view lines.</p>}
          {selected && lines.length === 0 && <p className="text-xs text-text-faint text-center py-4">No lines.</p>}
          {lines.map((ln) => (
            <div key={ln.id} className="rounded-lg border p-2 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-sm">{ln.description}</span>
                <span className="font-mono text-sm">{ln.amount}</span>
              </div>
              <div className="flex items-center gap-2 flex-wrap text-xs">
                <span className={`px-1.5 py-0.5 rounded-full ${ln.status === "reconciled" ? "bg-success/20 text-success" : "bg-surface-2 text-text-faint"}`}>{ln.status}</span>
                {ln.suggestions?.slice(0, 3).map((s: any) => (
                  <Button variant="info" className="px-1.5 py-0.5 rounded text-info disabled:opacity-50" key={s.journal_entry_id} onClick={() => matchLine(ln.id, s.journal_entry_id)}
                    disabled={busy || ln.status === "reconciled"}>
                    ↳ JE #{s.journal_entry_id} ({s.amount})
                  </Button>
                ))}
                {(!ln.suggestions || ln.suggestions.length === 0) && ln.status !== "reconciled" && <span className="text-text-faint">no suggestions</span>}
              </div>
            </div>
          ))}
        </div>
      </div>
    </PanelContent>
  );
}

/* ───────────────────────── Budgets & Variance ───────────────────────── */

export function BudgetsPanel() {
  const formatMoney = useCurrencyStore((s) => s.format);
  const { selectedCountry, isGlobalView } = useAdminCountry();
  const toast = useToastStore((s) => s.addToast);
  const [loading, setLoading] = useState(true);
  const [budgets, setBudgets] = useState<any[]>([]);
  const [variance, setVariance] = useState<any>(null);
  const [fiscalPeriodId, setFiscalPeriodId] = useState(1);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ account_code: "5030", amount: "", currency: "OMR" });

  const cc = () => (!isGlobalView && selectedCountry?.code ? selectedCountry.code : "");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const c = cc();
      const p = new URLSearchParams(); p.set("fiscal_period_id", String(fiscalPeriodId)); if (c) p.set("country_code", c);
      const [b, v] = await Promise.all([
        apiFetch(`${ACCOUNT_BASE}/budgets?${p.toString()}`),
        apiFetch(`${ACCOUNT_BASE}/budgets/variance?fiscal_period_id=${fiscalPeriodId}${c ? "&country_code=" + c : ""}`),
      ]);
      if (b.ok) setBudgets((await b.json()).items || []);
      if (v.ok) setVariance(await v.json());
    } catch { toast("Network error", "error"); }
    finally { setLoading(false); }
  }, [fiscalPeriodId, selectedCountry?.code, isGlobalView, toast]);

  useEffect(() => { load(); }, [load]);

  const setBudget = async () => {
    const res = await apiFetch(`${ACCOUNT_BASE}/budgets`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        account_code: form.account_code, fiscal_period_id: fiscalPeriodId,
        amount: parseFloat(form.amount || "0"), currency: form.currency, country_code: cc(),
      }),
    });
    if (res.ok) { toast("Budget set", "success"); setShowForm(false); setForm({ account_code: "5030", amount: "", currency: "OMR" }); load(); }
    else { const e = await res.json().catch(() => ({})); toast(e.detail || "Failed", "error"); }
  };

  if (loading) return <PanelLoadingState count={3} />;

  const rows = variance?.items || [];
  return (
    <PanelContent className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-text-faint"><PiggyBank className="h-3 w-3" /> Budgets & Variance — Period #{fiscalPeriodId}</div>
        <Button variant="primary" className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold" onClick={() => setShowForm((s) => !s)}><Plus className="h-3.5 w-3.5" /> Set Budget</Button>
      </div>

      <Field label="Fiscal Period ID"><input type="number" className="fin-input w-32" value={fiscalPeriodId} onChange={(e) => setFiscalPeriodId(parseInt(e.target.value || "1"))} /></Field>

      {showForm && (
        <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} className="theme-card rounded-xl border p-4 grid gap-3 sm:grid-cols-3">
          <Field label="Account"><input className="fin-input" value={form.account_code} onChange={(e) => setForm({ ...form, account_code: e.target.value })} /></Field>
          <Field label="Amount"><input type="number" className="fin-input" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} /></Field>
          <div className="flex items-end"><button onClick={setBudget} disabled={!form.amount} className="theme-btn-primary px-4 py-1.5 text-sm rounded-lg disabled:opacity-50">Save</button></div>
        </motion.div>
      )}

      <div className="theme-card rounded-xl border overflow-hidden">
        <div className="max-h-[55vh] overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="bg-surface-2 sticky top-0"><tr><th className="text-left p-2">Account</th><th className="text-right p-2">Budget</th><th className="text-right p-2">Actual</th><th className="text-right p-2">Variance</th><th className="text-center p-2">Status</th></tr></thead>
            <tbody>
              {rows.length === 0 ? <tr><td colSpan={5} className="p-6 text-center text-text-muted text-xs">No budget data for this period.</td></tr>
                : rows.map((r: any) => (
                  <tr key={r.account_code} className="border-b border-border last:border-0">
                    <td className="p-2 font-mono text-xs">{r.account_code}</td>
                    <td className="p-2 text-right">{formatMoney(r.budget || 0)}</td>
                    <td className="p-2 text-right">{formatMoney(r.actual || 0)}</td>
                    <td className={`p-2 text-right ${r.variance < 0 ? "text-danger" : "text-success"}`}>{formatMoney(r.variance || 0)}</td>
                    <td className="p-2 text-center text-xs">{r.status}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </PanelContent>
  );
}

/* ───────────────────────── Finance Audit ───────────────────────── */

export function FinanceAuditPanel() {
  const { selectedCountry, isGlobalView } = useAdminCountry();
  const toast = useToastStore((s) => s.addToast);
  const [loading, setLoading] = useState(true);
  const [rows, setRows] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [action, setAction] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const p = new URLSearchParams();
      if (action) p.set("action", action);
      if (!isGlobalView && selectedCountry?.code) p.set("country_code", selectedCountry.code);
      p.set("limit", "100");
      const res = await apiFetch(`${ACCOUNT_BASE}/audit?${p.toString()}`);
      if (res.ok) { const d = await res.json(); setRows(d.items || []); setTotal(d.total || 0); }
      else toast("Failed to load audit log", "error");
    } catch { toast("Network error", "error"); }
    finally { setLoading(false); }
  }, [action, selectedCountry?.code, isGlobalView, toast]);

  useEffect(() => { const t = setTimeout(load, 200); return () => clearTimeout(t); }, [load]);

  const doExport = () => csvExport("finance_audit.csv", rows, [
    { key: "id", header: "ID" }, { key: "action", header: "Action" }, { key: "actor_id", header: "Actor" },
    { key: "entity_type", header: "Entity" }, { key: "entity_id", header: "Entity ID" },
    { key: "country_code", header: "Country" }, { key: "created_at", header: "At" },
  ]);

  if (loading) return <PanelLoadingState count={3} />;

  return (
    <PanelContent className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-text-faint"><FileSearch className="h-3 w-3" /> Finance Audit Trail — {total} events</div>
        <div className="flex items-center gap-2">
          <input className="fin-input w-40" placeholder="filter by action" value={action} onChange={(e) => setAction(e.target.value)} />
          <button onClick={doExport} className="flex items-center gap-1.5 rounded-lg bg-surface-2 px-3 py-1.5 text-xs hover:bg-surface-3"><Download className="h-3.5 w-3.5" /> Export CSV</button>
        </div>
      </div>

      <div className="theme-card rounded-xl border overflow-hidden">
        <div className="max-h-[60vh] overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="bg-surface-2 sticky top-0"><tr><th className="text-left p-2">Action</th><th className="text-left p-2">Actor</th><th className="text-left p-2">Entity</th><th className="text-left p-2">Detail</th><th className="text-center p-2">Country</th><th className="text-left p-2">At</th></tr></thead>
            <tbody>
              {rows.length === 0 ? <tr><td colSpan={6} className="p-6 text-center text-text-muted text-xs">No audit events.</td></tr>
                : rows.map((a) => (
                  <tr key={a.id} className="border-b border-border last:border-0">
                    <td className="p-2"><span className="text-[10px] bg-success/20 text-success px-1.5 py-0.5 rounded-full font-mono">{a.action}</span></td>
                    <td className="p-2 text-xs">{a.actor_id}</td>
                    <td className="p-2 text-xs text-text-faint">{a.entity_type || "—"}{a.entity_id ? ` #${a.entity_id}` : ""}</td>
                    <td className="p-2 text-xs text-text-faint max-w-[280px] truncate">{a.detail ? JSON.stringify(a.detail).slice(0, 80) : "—"}</td>
                    <td className="p-2 text-center text-xs text-text-faint">{a.country_code || "—"}</td>
                    <td className="p-2 text-xs text-text-faint">{a.created_at?.slice(0, 19)?.replace("T", " ")}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </PanelContent>
  );
}
