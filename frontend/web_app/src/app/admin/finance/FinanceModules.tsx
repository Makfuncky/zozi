"use client";

import { Button } from "@/components/ui/Button";

import { useCallback, useEffect, useState } from "react";
import {
  Building2, Coins, PiggyBank, FileSpreadsheet, UploadCloud, Cpu, Layers,
  Wallet, BadgeCheck, ShieldCheck, ListChecks, ArrowDownUp, Split, CircleDollarSign,
  Banknote, Calculator, FileText, Plus, Trash2, Pencil, RefreshCw, Search,
  CheckCircle2, XCircle, Receipt, ScanLine, Landmark,
} from "@/lib/icons";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useAdminCountry } from "@/lib/useAdminCountry";
import { useToastStore } from "@/lib/toastStore";
import { motion } from "framer-motion";

const ACCOUNT_BASE = "/accounting";

/* ───────────────────────── Chart of Accounts (dynamic CRUD) ───────────────────────── */

export function ChartOfAccountsPanel() {
  const formatMoney = useCurrencyStore((s) => s.format);
  const { selectedCountry } = useAdminCountry();
  const toast = useToastStore((s) => s.addToast);
  const [loading, setLoading] = useState(true);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ code: "", name: "", group_code: "1.1", normal_side: "debit", currency: "OMR" });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch(`${ACCOUNT_BASE}/accounts`);
      if (res.ok) setAccounts(await res.json());
    } catch { toast("Network error", "error"); }
    finally { setLoading(false); }
  }, [toast]);

  useEffect(() => { load(); }, [load]);

  const create = async () => {
    const res = await apiFetch(`${ACCOUNT_BASE}/accounts`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...form, country_code: selectedCountry?.code }),
    });
    if (res.ok) { toast("Account created", "success"); setShowForm(false); setForm({ code: "", name: "", group_code: "1.1", normal_side: "debit", currency: "OMR" }); load(); }
    else { const e = await res.json().catch(() => ({})); toast(e.detail || "Create failed", "error"); }
  };

  const deactivate = async (code: string) => {
    const res = await apiFetch(`${ACCOUNT_BASE}/accounts/${code}/deactivate`, { method: "POST" });
    if (res.ok) { toast("Account deactivated", "success"); load(); }
    else toast("Failed", "error");
  };

  if (loading) return <PanelLoadingState count={3} blockClassName="h-16 rounded-xl bg-surface-2 animate-pulse" />;

  return (
    <PanelContent className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-text-faint">
          <Landmark className="h-3 w-3" /> Dynamic Chart of Accounts — {accounts.length} accounts
        </div>
        <Button variant="primary" className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold" onClick={() => setShowForm((s) => !s)}>
          <Plus className="h-3.5 w-3.5" /> New Account
        </Button>
      </div>

      {showForm && (
        <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} className="theme-card rounded-xl border p-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <Field label="Code"><input className="fin-input" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} placeholder="e.g. 5090" /></Field>
          <Field label="Name"><input className="fin-input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="e.g. Training Expense" /></Field>
          <Field label="Group Code"><input className="fin-input" value={form.group_code} onChange={(e) => setForm({ ...form, group_code: e.target.value })} placeholder="1.1 / 2.1 / 5.2" /></Field>
          <Field label="Normal Side">
            <select className="fin-input" value={form.normal_side} onChange={(e) => setForm({ ...form, normal_side: e.target.value })}>
              <option value="debit">Debit</option><option value="credit">Credit</option>
            </select>
          </Field>
          <Field label="Currency"><input className="fin-input" value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} /></Field>
          <div className="flex items-end">
            <button onClick={create} className="theme-btn-primary px-4 py-1.5 text-sm rounded-lg">Create</button>
          </div>
        </motion.div>
      )}

      <div className="theme-card rounded-xl border overflow-hidden">
        <div className="max-h-[60vh] overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="bg-surface-2 sticky top-0">
              <tr>
                <th className="text-left p-2 font-semibold">Code</th>
                <th className="text-left p-2 font-semibold">Name</th>
                <th className="text-left p-2 font-semibold">Group</th>
                <th className="text-center p-2 font-semibold">Side</th>
                <th className="text-center p-2 font-semibold">Active</th>
                <th className="text-center p-2 font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {accounts.map((a) => (
                <tr key={a.code} className="border-b border-border last:border-0">
                  <td className="p-2 font-mono text-xs">{a.code}</td>
                  <td className="p-2">{a.name}</td>
                  <td className="p-2 text-text-faint text-xs">{a.group_name}</td>
                  <td className="p-2 text-center text-xs uppercase">{a.normal_side}</td>
                  <td className="p-2 text-center">{a.is_active
                    ? <CheckCircle2 className="h-4 w-4 mx-auto text-success" />
                    : <XCircle className="h-4 w-4 mx-auto text-warning" />}</td>
                  <td className="p-2 text-center">
                    {a.is_active && <button onClick={() => deactivate(a.code)} title="Deactivate" className="text-warning hover:text-danger"><Trash2 className="h-3.5 w-3.5 inline" /></button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </PanelContent>
  );
}

/* ───────────────────────── Expense Scanning (OCR → GL) ───────────────────────── */

export function ExpenseScanPanel() {
  const { selectedCountry } = useAdminCountry();
  const toast = useToastStore((s) => s.addToast);
  const [loading, setLoading] = useState(true);
  const [list, setList] = useState<any[]>([]);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    vendor_name: "", amount: "", tax_amount: "0", expense_account_code: "5030",
    description: "", image_url: "", category: "office", ocr_raw_text: "",
  });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch(`${ACCOUNT_BASE}/expenses/scanned`);
      if (res.ok) setList(await res.json());
    } catch { toast("Network error", "error"); }
    finally { setLoading(false); }
  }, [toast]);

  useEffect(() => { load(); }, [load]);

  const scan = async () => {
    setBusy(true);
    try {
      const res = await apiFetch(`${ACCOUNT_BASE}/expenses/scan`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...form, amount: parseFloat(form.amount || "0"),
          tax_amount: parseFloat(form.tax_amount || "0"),
          ocr_confidence: 0.95, country_code: selectedCountry?.code,
        }),
      });
      if (res.ok) { toast("Bill scanned & posted to GL", "success"); setForm({ vendor_name: "", amount: "", tax_amount: "0", expense_account_code: "5030", description: "", image_url: "", category: "office", ocr_raw_text: "" }); load(); }
      else { const e = await res.json().catch(() => ({})); toast(e.detail || "Scan failed", "error"); }
    } finally { setBusy(false); }
  };

  // OCR file upload -> /expenses/scan-upload (multipart, server-side parse).
  const [file, setFile] = useState<File | null>(null);
  const uploadScan = async () => {
    if (!file) return;
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      if (selectedCountry?.code) fd.append("country_code", selectedCountry.code);
      fd.append("expense_account_code", form.expense_account_code);
      const res = await apiFetch(`${ACCOUNT_BASE}/expenses/scan-upload`, { method: "POST", body: fd });
      if (res.ok) { const d = await res.json(); toast(`OCR parsed: ${d.parsed?.vendor_name || "vendor"} — ${d.parsed?.amount} (conf ${(d.parsed?.confidence ?? 0) * 100 | 0}%)`, "success"); setFile(null); load(); }
      else { const e = await res.json().catch(() => ({})); toast(e.detail || "Upload failed", "error"); }
    } finally { setBusy(false); }
  };

  if (loading) return <PanelLoadingState count={2} blockClassName="h-20 rounded-xl bg-surface-2 animate-pulse" />;

  return (
    <PanelContent className="space-y-4">
      <div className="flex items-center gap-2 text-xs text-text-faint"><ScanLine className="h-3 w-3" /> OCR Bill Scanning → auto expense → double-entry GL posting</div>

      <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="theme-card rounded-xl border p-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <Field label="Vendor"><input className="fin-input" value={form.vendor_name} onChange={(e) => setForm({ ...form, vendor_name: e.target.value })} placeholder="Supplier name" /></Field>
        <Field label="Amount"><input type="number" className="fin-input" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} /></Field>
        <Field label="VAT"><input type="number" className="fin-input" value={form.tax_amount} onChange={(e) => setForm({ ...form, tax_amount: e.target.value })} /></Field>
        <Field label="GL Account">
          <select className="fin-input" value={form.expense_account_code} onChange={(e) => setForm({ ...form, expense_account_code: e.target.value })}>
            <option value="5030">5030 Operating Expenses</option>
            <option value="5040">5040 Salaries & Wages</option>
            <option value="5050">5050 Rent & Utilities</option>
            <option value="5060">5060 Marketing</option>
            <option value="5080">5080 Other Expenses</option>
          </select>
        </Field>
        <Field label="Category"><input className="fin-input" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} /></Field>
        <Field label="Receipt URL"><input className="fin-input" value={form.image_url} onChange={(e) => setForm({ ...form, image_url: e.target.value })} placeholder="https://..." /></Field>
        <div className="sm:col-span-2 lg:col-span-3">
          <Field label="Description"><textarea className="fin-input" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={2} /></Field>
        </div>
        <div className="sm:col-span-2 lg:col-span-3 flex">
          <button disabled={busy || !form.vendor_name || !form.amount} onClick={scan}
            className="theme-btn-primary px-4 py-1.5 text-sm rounded-lg disabled:opacity-50 flex items-center gap-1.5">
            {busy ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <ScanLine className="h-3.5 w-3.5" />} Scan & Post to GL
          </button>
          <label className="ml-3 flex items-center gap-1.5 rounded-lg bg-surface-2 px-3 py-1.5 text-xs cursor-pointer hover:bg-surface-3">
            <UploadCloud className="h-3.5 w-3.5" /> Upload Bill (OCR)
            <input type="file" accept=".txt,.csv,.png,.jpg,.pdf" className="hidden" onChange={(e) => setFile(e.target.files?.[0] || null)} />
          </label>
          {file && (
            <Button variant="primary" onClick={uploadScan} disabled={busy}>
              {busy ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <ScanLine className="h-3.5 w-3.5" />} Parse & Post
            </Button>
          )}
        </div>
      </motion.div>

      <div className="theme-card rounded-xl border overflow-hidden">
        <div className="max-h-[50vh] overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="bg-surface-2 sticky top-0">
              <tr>
                <th className="text-left p-2 font-semibold">Vendor</th>
                <th className="text-right p-2 font-semibold">Amount</th>
                <th className="text-left p-2 font-semibold">Account</th>
                <th className="text-center p-2 font-semibold">Status</th>
                <th className="text-left p-2 font-semibold">Date</th>
              </tr>
            </thead>
            <tbody>
              {list.length === 0 ? <tr><td colSpan={5} className="p-6 text-center text-text-muted text-xs">No scanned expenses yet.</td></tr>
                : list.map((e) => (
                  <tr key={e.id} className="border-b border-border last:border-0">
                    <td className="p-2">{e.vendor_name}</td>
                    <td className="p-2 text-right">{e.amount}</td>
                    <td className="p-2 font-mono text-xs">{e.account_code}</td>
                    <td className="p-2 text-center"><span className="text-[10px] bg-success/20 text-success px-1.5 py-0.5 rounded-full">{e.status}</span></td>
                    <td className="p-2 text-xs text-text-faint">{e.created_at?.slice(0, 10)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </PanelContent>
  );
}

/* ───────────────────────── Bank Mapping & Reconciliation ───────────────────────── */

export function BankMappingPanel() {
  const { selectedCountry } = useAdminCountry();
  const toast = useToastStore((s) => s.addToast);
  const [rules, setRules] = useState<any[]>([]);
  const [lines, setLines] = useState<{ import_id: number | null; rows: any[] }>({ import_id: null, rows: [] });
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [ruleForm, setRuleForm] = useState({ name: "", match_pattern: "", account_code: "5030", normal_side: "debit", category: "" });
  const [statementText, setStatementText] = useState("Office Supplies Vendor 55.00\nStripe Payout 1200.00\nLandlord Rent 800.00\nSalary Payroll 3000.00");

  const loadRules = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch(`${ACCOUNT_BASE}/mapping-rules`);
      if (res.ok) setRules(await res.json());
    } catch { toast("Network error", "error"); }
    finally { setLoading(false); }
  }, [toast]);

  useEffect(() => { loadRules(); }, [loadRules]);

  const addRule = async () => {
    const res = await apiFetch(`${ACCOUNT_BASE}/mapping-rules`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...ruleForm, country_code: selectedCountry?.code, priority: 100 }),
    });
    if (res.ok) { toast("Mapping rule added", "success"); setRuleForm({ name: "", match_pattern: "", account_code: "5030", normal_side: "debit", category: "" }); loadRules(); }
    else { const e = await res.json().catch(() => ({})); toast(e.detail || "Failed", "error"); }
  };

  const importStatement = async () => {
    setBusy(true);
    try {
      const rows = statementText.split("\n").map((l) => l.trim()).filter(Boolean).map((l) => {
        const m = l.match(/^(.*?)\s+([\d.]+)\s*$/);
        return m ? { description: m[1], amount: parseFloat(m[2]) } : { description: l, amount: 0 };
      }).filter((r) => r.amount > 0);
      const res = await apiFetch(`${ACCOUNT_BASE}/statements/import`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bank_name: "Demo Bank", currency: "OMR", country_code: selectedCountry?.code, lines: rows }),
      });
      if (res.ok) {
        const data = await res.json();
        toast(`Imported ${data.total_lines} lines (${data.matched_lines} auto-mapped)`, "success");
        const lr = await apiFetch(`${ACCOUNT_BASE}/statements/${data.import_id}/lines`);
        if (lr.ok) setLines({ import_id: data.import_id, rows: await lr.json() });
      } else { const e = await res.json().catch(() => ({})); toast(e.detail || "Import failed", "error"); }
    } finally { setBusy(false); }
  };

  // CSV file upload -> /statements/import-csv (server-side parse + auto-map).
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const importCsv = async () => {
    if (!csvFile) return;
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("file", csvFile);
      fd.append("currency", "OMR");
      if (selectedCountry?.code) fd.append("country_code", selectedCountry.code);
      const res = await apiFetch(`${ACCOUNT_BASE}/statements/import-csv`, { method: "POST", body: fd });
      if (res.ok) { const d = await res.json(); toast(`Imported ${d.total_lines} lines (${d.matched_lines} auto-mapped)`, "success"); setCsvFile(null); }
      else { const e = await res.json().catch(() => ({})); toast(e.detail || "CSV import failed", "error"); }
    } finally { setBusy(false); }
  };

  const postMapped = async () => {
    if (!lines.import_id) return;
    setBusy(true);
    try {
      const res = await apiFetch(`${ACCOUNT_BASE}/statements/${lines.import_id}/post`, { method: "POST" });
      if (res.ok) { const d = await res.json(); toast(`Posted ${d.posted}/${d.lines} lines to GL`, "success"); setLines({ import_id: null, rows: [] }); }
      else toast("Post failed", "error");
    } finally { setBusy(false); }
  };

  if (loading) return <PanelLoadingState count={2} blockClassName="h-16 rounded-xl bg-surface-2 animate-pulse" />;

  return (
    <PanelContent className="space-y-4">
      <div className="flex items-center gap-2 text-xs text-text-faint"><Split className="h-3 w-3" /> Configurable bank-statement → GL mapping & auto-posting</div>

      <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="theme-card rounded-xl border p-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Field label="Rule Name"><input className="fin-input" value={ruleForm.name} onChange={(e) => setRuleForm({ ...ruleForm, name: e.target.value })} placeholder="e.g. Office Supplies" /></Field>
        <Field label="Match Text"><input className="fin-input" value={ruleForm.match_pattern} onChange={(e) => setRuleForm({ ...ruleForm, match_pattern: e.target.value })} placeholder="contains 'office'" /></Field>
        <Field label="GL Account">
          <select className="fin-input" value={ruleForm.account_code} onChange={(e) => setRuleForm({ ...ruleForm, account_code: e.target.value })}>
            <option value="5030">5030 Operating Expenses</option>
            <option value="5040">5040 Salaries</option>
            <option value="5050">5050 Rent</option>
            <option value="5060">5060 Marketing</option>
            <option value="4010">4010 Commission Revenue</option>
            <option value="1010">1010 Cash</option>
          </select>
        </Field>
        <Field label="Side"><select className="fin-input" value={ruleForm.normal_side} onChange={(e) => setRuleForm({ ...ruleForm, normal_side: e.target.value })}><option value="debit">Debit</option><option value="credit">Credit</option></select></Field>
        <div className="lg:col-span-4"><button onClick={addRule} disabled={!ruleForm.name || !ruleForm.match_pattern} className="theme-btn-primary px-4 py-1.5 text-sm rounded-lg disabled:opacity-50 flex items-center gap-1.5"><Plus className="h-3.5 w-3.5" /> Add Mapping Rule</button></div>
      </motion.div>

      <div className="theme-card rounded-xl border p-4 space-y-3">
        <h3 className="text-sm font-bold flex items-center gap-2"><FileSpreadsheet className="h-4 w-4 text-primary" /> Import Bank Statement</h3>
        <textarea className="fin-input w-full" rows={4} value={statementText} onChange={(e) => setStatementText(e.target.value)} />
        <div className="flex gap-2 items-center flex-wrap">
          <button onClick={importStatement} disabled={busy} className="theme-btn-primary px-4 py-1.5 text-sm rounded-lg disabled:opacity-50 flex items-center gap-1.5"><UploadCloud className="h-3.5 w-3.5" /> Parse & Map</button>
          <label className="flex items-center gap-1.5 rounded-lg bg-surface-2 px-3 py-1.5 text-xs cursor-pointer hover:bg-surface-3">
            <UploadCloud className="h-3.5 w-3.5" /> Upload CSV
            <input type="file" accept=".csv" className="hidden" onChange={(e) => setCsvFile(e.target.files?.[0] || null)} />
          </label>
          {csvFile && <Button variant="primary" onClick={importCsv} disabled={busy}>{busy ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <UploadCloud className="h-3.5 w-3.5" />} Import CSV</Button>}
          {lines.import_id && <Button variant="primary" onClick={postMapped} disabled={busy}><CheckCircle2 className="h-3.5 w-3.5" /> Post Mapped to GL</Button>}
        </div>
        {lines.rows.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b"><th className="text-left p-2">Description</th><th className="text-right p-2">Amount</th><th className="text-left p-2">Maps To</th><th className="text-center p-2">Status</th></tr></thead>
              <tbody>
                {lines.rows.map((r) => (
                  <tr key={r.id} className="border-b border-border last:border-0">
                    <td className="p-2">{r.description}</td>
                    <td className="p-2 text-right">{r.amount}</td>
                    <td className="p-2 font-mono text-xs">{r.mapped_account_code || "—"}</td>
                    <td className="p-2 text-center"><span className={`text-[10px] px-1.5 py-0.5 rounded-full ${r.status === "mapped" ? "bg-info/20 text-info" : "bg-surface-2 text-text-faint"}`}>{r.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="theme-card rounded-xl border p-4">
        <h3 className="text-sm font-bold mb-2 flex items-center gap-2"><ListChecks className="h-4 w-4 text-primary" /> Active Mapping Rules</h3>
        <div className="flex flex-wrap gap-2">
          {rules.length === 0 && <p className="text-xs text-text-faint">No rules yet.</p>}
          {rules.map((r) => (
            <span key={r.id} className="text-[11px] bg-surface-2 rounded-lg px-2 py-1 flex items-center gap-1.5">
              <BadgeCheck className="h-3 w-3 text-success" /> "{r.match_pattern}" → <span className="font-mono">{r.account_code}</span>
            </span>
          ))}
        </div>
      </div>
    </PanelContent>
  );
}

/* ───────────────────────── Fixed Assets & Depreciation ───────────────────────── */

export function FixedAssetsPanel() {
  const { selectedCountry } = useAdminCountry();
  const toast = useToastStore((s) => s.addToast);
  const [assets, setAssets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ name: "", category: "vehicles", purchase_cost: "", useful_life_months: "60", salvage_value: "0" });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch(`${ACCOUNT_BASE}/fixed-assets?country_code=${selectedCountry?.code || ""}`);
      if (res.ok) setAssets(await res.json());
    } catch { /* fallback below */ }
    finally { setLoading(false); }
  }, [toast, selectedCountry?.code]);

  useEffect(() => { load(); }, [load]);

  const add = async () => {
    const res = await apiFetch(`${ACCOUNT_BASE}/fixed-assets`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: form.name, category: form.category,
        purchase_date: new Date().toISOString(),
        purchase_cost: parseFloat(form.purchase_cost || "0"),
        salvage_value: parseFloat(form.salvage_value || "0"),
        useful_life_months: parseInt(form.useful_life_months || "60"),
        country_code: selectedCountry?.code,
      }),
    });
    if (res.ok) { toast("Asset registered", "success"); setForm({ name: "", category: "vehicles", purchase_cost: "", useful_life_months: "60", salvage_value: "0" }); load(); }
    else { const e = await res.json().catch(() => ({})); toast(e.detail || "Failed", "error"); }
  };

  const depreciate = async () => {
    setBusy(true);
    try {
      const res = await apiFetch(`${ACCOUNT_BASE}/fixed-assets/depreciate?country_code=${selectedCountry?.code || ""}`, { method: "POST" });
      if (res.ok) { const d = await res.json(); toast(`Depreciated ${d.depreciated}/${d.processed} assets`, "success"); }
      else toast("Failed", "error");
    } finally { setBusy(false); }
  };

  if (loading) return <PanelLoadingState count={2} />;

  return (
    <PanelContent className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-text-faint"><Coins className="h-3 w-3" /> Fixed Asset Register & Straight-line Depreciation</div>
        <Button variant="primary" onClick={depreciate} disabled={busy}><RefreshCw className={`h-3.5 w-3.5 ${busy ? "animate-spin" : ""}`} /> Run Depreciation</Button>
      </div>

      <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="theme-card rounded-xl border p-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <Field label="Asset Name"><input className="fin-input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></Field>
        <Field label="Category"><input className="fin-input" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} /></Field>
        <Field label="Cost"><input type="number" className="fin-input" value={form.purchase_cost} onChange={(e) => setForm({ ...form, purchase_cost: e.target.value })} /></Field>
        <Field label="Salvage"><input type="number" className="fin-input" value={form.salvage_value} onChange={(e) => setForm({ ...form, salvage_value: e.target.value })} /></Field>
        <Field label="Life (months)"><input type="number" className="fin-input" value={form.useful_life_months} onChange={(e) => setForm({ ...form, useful_life_months: e.target.value })} /></Field>
        <div className="flex items-end"><button onClick={add} disabled={!form.name || !form.purchase_cost} className="theme-btn-primary px-4 py-1.5 text-sm rounded-lg disabled:opacity-50"><Plus className="h-3.5 w-3.5 inline" /> Register</button></div>
      </motion.div>

      {assets.length === 0
        ? <p className="text-xs text-text-muted text-center py-6">No fixed assets recorded. Register one above and run depreciation.</p>
        : (
          <div className="theme-card rounded-xl border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-surface-2"><tr><th className="text-left p-2">Name</th><th className="text-right p-2">Cost</th><th className="text-right p-2">Accum. Depr.</th><th className="text-center p-2">Status</th></tr></thead>
              <tbody>
                {assets.map((a: any) => (
                  <tr key={a.id} className="border-b border-border last:border-0">
                    <td className="p-2">{a.name}</td>
                    <td className="p-2 text-right">{a.purchase_cost}</td>
                    <td className="p-2 text-right">{a.accumulated_depreciation}</td>
                    <td className="p-2 text-center"><span className="text-[10px] bg-surface-2 rounded-full px-1.5 py-0.5">{a.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
    </PanelContent>
  );
}

/* ───────────────────────── Accruals ───────────────────────── */

export function AccrualsPanel() {
  const { selectedCountry } = useAdminCountry();
  const toast = useToastStore((s) => s.addToast);
  const [list, setList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ accrual_type: "expense", amount: "", expense_account_code: "5040", accrual_account_code: "2080", description: "" });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch(`${ACCOUNT_BASE}/accruals?country_code=${selectedCountry?.code || ""}`);
      if (res.ok) setList(await res.json());
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, [selectedCountry?.code]);
  useEffect(() => { load(); }, [load]);

  const create = async () => {
    const res = await apiFetch(`${ACCOUNT_BASE}/accruals`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...form, amount: parseFloat(form.amount || "0"),
        accrual_date: new Date().toISOString(), country_code: selectedCountry?.code,
      }),
    });
    if (res.ok) { toast("Accrual posted", "success"); setForm({ accrual_type: "expense", amount: "", expense_account_code: "5040", accrual_account_code: "2080", description: "" }); load(); }
    else { const e = await res.json().catch(() => ({})); toast(e.detail || "Failed", "error"); }
  };

  const reverse = async (id: number) => {
    const res = await apiFetch(`${ACCOUNT_BASE}/accruals/${id}/reverse`, { method: "POST" });
    if (res.ok) { toast("Accrual reversed", "success"); load(); } else toast("Failed", "error");
  };

  if (loading) return <PanelLoadingState count={2} />;

  return (
    <PanelContent className="space-y-4">
      <div className="flex items-center gap-2 text-xs text-text-faint"><ArrowDownUp className="h-3 w-3" /> Accruals Engine — recognize expense/revenue before cash, then reverse</div>
      <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="theme-card rounded-xl border p-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Field label="Type"><select className="fin-input" value={form.accrual_type} onChange={(e) => setForm({ ...form, accrual_type: e.target.value })}><option value="expense">Expense</option><option value="revenue">Revenue</option></select></Field>
        <Field label="Amount"><input type="number" className="fin-input" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} /></Field>
        <Field label="Expense/Rev Acct"><input className="fin-input" value={form.expense_account_code} onChange={(e) => setForm({ ...form, expense_account_code: e.target.value })} /></Field>
        <Field label="Accrual Acct"><input className="fin-input" value={form.accrual_account_code} onChange={(e) => setForm({ ...form, accrual_account_code: e.target.value })} /></Field>
        <div className="lg:col-span-3"><Field label="Description"><input className="fin-input" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></Field></div>
        <div className="flex items-end"><button onClick={create} disabled={!form.amount} className="theme-btn-primary px-4 py-1.5 text-sm rounded-lg disabled:opacity-50"><Plus className="h-3.5 w-3.5 inline" /> Post Accrual</button></div>
      </motion.div>

      <div className="theme-card rounded-xl border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-surface-2"><tr><th className="text-left p-2">Type</th><th className="text-right p-2">Amount</th><th className="text-left p-2">Description</th><th className="text-center p-2">Status</th><th className="text-center p-2">Action</th></tr></thead>
          <tbody>
            {list.length === 0 ? <tr><td colSpan={5} className="p-6 text-center text-text-muted text-xs">No accruals yet.</td></tr>
              : list.map((a: any) => (
                <tr key={a.id} className="border-b border-border last:border-0">
                  <td className="p-2 uppercase text-xs">{a.accrual_type}</td>
                  <td className="p-2 text-right">{a.amount}</td>
                  <td className="p-2">{a.description}</td>
                  <td className="p-2 text-center"><span className="text-[10px] bg-surface-2 rounded-full px-1.5 py-0.5">{a.status}</span></td>
                  <td className="p-2 text-center">{a.status === "open" && <button onClick={() => reverse(a.id)} className="text-warning hover:text-danger text-xs">Reverse</button>}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </PanelContent>
  );
}

/* ───────────────────────── FX Revaluation ───────────────────────── */

export function FxPanel() {
  const formatMoney = useCurrencyStore((s) => s.format);
  const { selectedCountry } = useAdminCountry();
  const toast = useToastStore((s) => s.addToast);
  const cc = selectedCountry?.code;
  const [rates, setRates] = useState<any[]>([]);
  const [form, setForm] = useState({ base: "USD", quote: "OMR", rate: "", as_of: new Date().toISOString().slice(0, 10) });

  const load = useCallback(async () => {
    const res = await apiFetch(`${ACCOUNT_BASE}/fx/rates${cc ? `?country_code=${cc}` : ""}`);
    if (res.ok) setRates(await res.json());
  }, [cc]);
  useEffect(() => { load(); }, [load]);

  const saveRate = async () => {
    const res = await apiFetch(`${ACCOUNT_BASE}/fx/rates`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...form, rate: parseFloat(form.rate), country_code: cc }),
    });
    if (res.ok) { toast("FX rate saved", "success"); setForm({ ...form, rate: "" }); load(); }
    else { const e = await res.json().catch(() => ({})); toast(e.detail || "Failed", "error"); }
  };
  const revalue = async () => {
    const res = await apiFetch(`${ACCOUNT_BASE}/fx/revalue${cc ? `?country_code=${cc}` : ""}`, { method: "POST" });
    if (res.ok) { const d = await res.json(); toast(d.journal_entry_id ? "FX revaluation posted" : "No open positions", "success"); }
    else toast("Revaluation failed", "error");
  };

  return (
    <PanelContent className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 items-end">
        <input className="input" placeholder="Base" value={form.base} onChange={(e) => setForm({ ...form, base: e.target.value })} />
        <input className="input" placeholder="Quote" value={form.quote} onChange={(e) => setForm({ ...form, quote: e.target.value })} />
        <input className="input" placeholder="Rate" value={form.rate} onChange={(e) => setForm({ ...form, rate: e.target.value })} />
        <input className="input" type="date" value={form.as_of} onChange={(e) => setForm({ ...form, as_of: e.target.value })} />
      </div>
      <div className="flex gap-2">
        <button onClick={saveRate} className="btn-primary text-xs px-3 py-1.5">Save Rate</button>
        <button onClick={revalue} className="btn-ghost text-xs px-3 py-1.5">Run Revaluation</button>
      </div>
      <table className="w-full text-xs">
        <thead><tr className="text-text-faint"><th className="p-2 text-left">Base</th><th className="p-2 text-left">Quote</th><th className="p-2 text-right">Rate</th><th className="p-2 text-left">As Of</th></tr></thead>
        <tbody>
          {rates.map((r: any) => (
            <tr key={r.id} className="border-b border-border">
              <td className="p-2">{r.base}</td><td className="p-2">{r.quote}</td>
              <td className="p-2 text-right">{r.rate}</td><td className="p-2">{r.as_of}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </PanelContent>
  );
}

/* ───────────────────────── Deferred Revenue ───────────────────────── */

export function DeferredRevenuePanel() {
  const { selectedCountry } = useAdminCountry();
  const toast = useToastStore((s) => s.addToast);
  const cc = selectedCountry?.code;
  const [contracts, setContracts] = useState<any[]>([]);
  const [form, setForm] = useState({ description: "", total_amount: "", start_date: new Date().toISOString().slice(0, 10), end_date: "", period_months: 12 });

  const load = useCallback(async () => {
    const res = await apiFetch(`${ACCOUNT_BASE}/deferred-revenue${cc ? `?country_code=${cc}` : ""}`);
    if (res.ok) setContracts(await res.json());
  }, [cc]);
  useEffect(() => { load(); }, [load]);

  const create = async () => {
    const res = await apiFetch(`${ACCOUNT_BASE}/deferred-revenue`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...form, total_amount: parseFloat(form.total_amount), country_code: cc }),
    });
    if (res.ok) { toast("Contract created", "success"); setForm({ ...form, description: "", total_amount: "" }); load(); }
    else { const e = await res.json().catch(() => ({})); toast(e.detail || "Failed", "error"); }
  };
  const amortize = async () => {
    const res = await apiFetch(`${ACCOUNT_BASE}/deferred-revenue/amortize${cc ? `?country_code=${cc}` : ""}`, { method: "POST" });
    if (res.ok) { const d = await res.json(); toast(`Released ${formatMoneyCompact(d.released || 0)}`, "success"); load(); }
    else toast("Failed", "error");
  };

  return (
    <PanelContent className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-3 gap-2 items-end">
        <input className="input" placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        <input className="input" placeholder="Amount" value={form.total_amount} onChange={(e) => setForm({ ...form, total_amount: e.target.value })} />
        <input className="input" placeholder="Months" value={form.period_months} onChange={(e) => setForm({ ...form, period_months: parseInt(e.target.value) || 12 })} />
        <input className="input" type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} />
        <input className="input" type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} />
      </div>
      <div className="flex gap-2">
        <button onClick={create} className="btn-primary text-xs px-3 py-1.5">Create Contract</button>
        <button onClick={amortize} className="btn-ghost text-xs px-3 py-1.5">Run Amortization</button>
      </div>
      <table className="w-full text-xs">
        <thead><tr className="text-text-faint"><th className="p-2 text-left">Desc</th><th className="p-2 text-right">Total</th><th className="p-2 text-right">Recognized</th><th className="p-2 text-center">Status</th></tr></thead>
        <tbody>
          {contracts.map((c: any) => (
            <tr key={c.id} className="border-b border-border">
              <td className="p-2">{c.description}</td>
              <td className="p-2 text-right">{c.total_amount}</td>
              <td className="p-2 text-right">{c.recognized_to_date}</td>
              <td className="p-2 text-center"><span className="text-[10px] bg-surface-2 rounded-full px-1.5 py-0.5">{c.status}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </PanelContent>
  );
}

/* ───────────────────────── Email-to-Ledger ───────────────────────── */

export function EmailLedgerPanel() {
  const { selectedCountry } = useAdminCountry();
  const toast = useToastStore((s) => s.addToast);
  const cc = selectedCountry?.code;
  const [raw, setRaw] = useState("Invoice #INV-2024-001 from Acme Ltd\nDate: 2024-01-15\nAmount: 1,250.00 OMR\nVAT: 62.50");
  const [subject, setSubject] = useState("Invoice INV-2024-001");
  const [sender, setSender] = useState("billing@acme.com");
  const [result, setResult] = useState<any>(null);

  const parse = async () => {
    const res = await apiFetch(`${ACCOUNT_BASE}/email/parse`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ raw_text: raw, subject, sender, country_code: cc }),
    });
    if (res.ok) { const d = await res.json(); setResult(d); toast("Email parsed", "success"); }
    else { const e = await res.json().catch(() => ({})); toast(e.detail || "Failed", "error"); }
  };

  return (
    <PanelContent className="space-y-4">
      <textarea className="input h-40 w-full font-mono text-xs" value={raw} onChange={(e) => setRaw(e.target.value)} />
      <div className="grid grid-cols-2 gap-2">
        <input className="input" placeholder="Subject" value={subject} onChange={(e) => setSubject(e.target.value)} />
        <input className="input" placeholder="Sender" value={sender} onChange={(e) => setSender(e.target.value)} />
      </div>
      <button onClick={parse} className="btn-primary text-xs px-3 py-1.5">Parse & Draft</button>
      {result && (
        <pre className="text-[11px] bg-surface-2 rounded-lg p-3 overflow-auto">{JSON.stringify(result, null, 2)}</pre>
      )}
    </PanelContent>
  );
}

/* ───────────────────────── AI Reconciliation ───────────────────────── */

export function AiReconcilePanel() {
  const { selectedCountry } = useAdminCountry();
  const toast = useToastStore((s) => s.addToast);
  const cc = selectedCountry?.code;
  const [importId, setImportId] = useState("");
  const [result, setResult] = useState<any>(null);

  const run = async () => {
    if (!importId) { toast("Enter an import ID", "error"); return; }
    const res = await apiFetch(`${ACCOUNT_BASE}/reconciliation/${importId}/auto-ai${cc ? `?country_code=${cc}` : ""}`, { method: "POST" });
    if (res.ok) { const d = await res.json(); setResult(d); toast(`Auto-posted ${d.auto_posted}, queued ${d.queued}`, "success"); }
    else { const e = await res.json().catch(() => ({})); toast(e.detail || "Failed", "error"); }
  };

  return (
    <PanelContent className="space-y-4">
      <div className="flex gap-2 items-end">
        <input className="input" placeholder="Bank import ID" value={importId} onChange={(e) => setImportId(e.target.value)} />
        <button onClick={run} className="btn-primary text-xs px-3 py-1.5">Run AI Reconcile</button>
      </div>
      {result && (
        <pre className="text-[11px] bg-surface-2 rounded-lg p-3 overflow-auto">{JSON.stringify(result, null, 2)}</pre>
      )}
    </PanelContent>
  );
}

function formatMoneyCompact(v: number) {
  try { return new Intl.NumberFormat().format(v); } catch { return String(v); }
}

/* ───────────────────────── Shared Field helper ───────────────────────── */

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-[10px] uppercase text-text-faint font-semibold">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  );
}
