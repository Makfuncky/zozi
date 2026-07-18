"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useAuth } from "@/lib/useAuth";
import { isAdminStaffRole } from "@shared/adminPermissions";
import { useCurrencyStore } from "@/lib/currencyStore";

/* Shared table/cell helpers (mirror of the legacy /admin/accounting page). */
export function Table({ columns, rows }: any) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left">
            {columns.map((c: string) => <th key={c} className="py-2 px-3 font-medium">{c}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((row: any, i: number) => (
            <tr key={i} className="border-b last:border-0 hover:bg-surface-1/50">
              {columns.map((c: string) => <td key={c} className="py-2 px-3">{formatCell(row[c])}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function formatCell(v: any): string {
  if (v === null || v === undefined) return "-";
  if (typeof v === "number") return v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
}

export function MetricCard({ title, value, color }: any) {
  return (
    <div className="theme-card rounded-xl border p-4">
      <p className="text-sm text-muted-foreground">{title}</p>
      <p className={`text-2xl font-bold ${color ?? ""}`}>{typeof value === "number" ? value.toLocaleString() : value}</p>
    </div>
  );
}

export function TrialBalanceTab({ fetchData, formatMoney }: any) {
  const [tb, setTb] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => { fetchData("/trial-balance").then(setTb).finally(() => setLoading(false)); }, []);
  if (loading) return <p className="text-sm">Loading...</p>;
  if (!tb) return <p>No data</p>;
  return (
    <div className="space-y-3">
      <div className="theme-card rounded-xl border p-4">
        <h3 className="font-semibold mb-2">Trial Balance — {new Date(tb.as_of).toLocaleDateString()}</h3>
        <p>Total Debits: <strong>{formatMoney?.(tb.total_debit_balances) ?? tb.total_debit_balances}</strong></p>
        <p>Total Credits: <strong>{formatMoney?.(tb.total_credit_balances) ?? tb.total_credit_balances}</strong></p>
      </div>
      <div className="theme-card rounded-xl border p-4">
        <Table columns={["Code", "Account", "Group", "Side", "Balance"]} rows={(tb.accounts ?? []).map((a: any) => [a.account_code, a.account_name, a.group_name, a.normal_side, a.balance])} />
      </div>
    </div>
  );
}

export function IncomeStatementTab({ postData, data, loading, formatMoney }: any) {
  const [start, setStart] = useState(() => { const d = new Date(); d.setMonth(d.getMonth() - 1); return d.toISOString().slice(0, 16); });
  const [end, setEnd] = useState(() => new Date().toISOString().slice(0, 16));
  const generate = () => postData("/reports/income-statement", { period_start: new Date(start).toISOString(), period_end: new Date(end).toISOString(), currency: "OMR" });
  return (
    <div className="space-y-3">
      <div className="theme-card rounded-xl border p-4 flex gap-3 items-end flex-wrap">
        <div><label className="text-xs">From</label><input type="datetime-local" value={start} onChange={e => setStart(e.target.value)} className="block border rounded p-1 text-sm" /></div>
        <div><label className="text-xs">To</label><input type="datetime-local" value={end} onChange={e => setEnd(e.target.value)} className="block border rounded p-1 text-sm" /></div>
        <button onClick={generate} disabled={loading} className="theme-btn-primary px-4 py-1.5 text-sm rounded-lg">Generate P&amp;L</button>
      </div>
      {data && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
          <div className="theme-card rounded-xl border p-4">
            <h3 className="font-semibold mb-2 text-success">Revenue</h3>
            <Table columns={["Code", "Account", "Group", "Amount"]} rows={(data.revenue_lines ?? []).map((l: any) => [l.account_code, l.account_name, l.group_name, l.amount])} />
            <p className="text-right font-semibold mt-2">Total Revenue: {formatMoney?.(data.total_revenue) ?? data.total_revenue}</p>
          </div>
          <div className="theme-card rounded-xl border p-4">
            <h3 className="font-semibold mb-2 text-danger">Expenses</h3>
            <Table columns={["Code", "Account", "Group", "Amount"]} rows={(data.expense_lines ?? []).map((l: any) => [l.account_code, l.account_name, l.group_name, l.amount])} />
            <p className="text-right font-semibold mt-2">Total: {formatMoney?.(data.total_expenses) ?? data.total_expenses}</p>
          </div>
          <div className="theme-card rounded-xl border p-4 text-center">
            <strong className="text-lg">Net Income: {formatMoney?.(data.net_income) ?? data.net_income}</strong>
          </div>
        </motion.div>
      )}
    </div>
  );
}

export function BalanceSheetTab({ postData, data, loading, formatMoney }: any) {
  const generate = () => postData("/reports/balance-sheet", { as_of_date: new Date().toISOString(), currency: "OMR" });
  return (
    <div className="space-y-3">
      <div className="theme-card rounded-xl border p-4">
        <button onClick={generate} disabled={loading} className="theme-btn-primary px-4 py-1.5 text-sm rounded-lg">Generate Balance Sheet</button>
      </div>
      {data && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
          <div className="theme-card rounded-xl border p-4">
            <h3 className="font-semibold mb-2 text-info">Assets</h3>
            <Table columns={["Code", "Account", "Group", "Amount"]} rows={(data.asset_lines ?? []).map((l: any) => [l.account_code, l.account_name, l.group_name, l.amount])} />
            <p className="text-right font-semibold mt-2">Total Assets: {formatMoney?.(data.total_assets) ?? data.total_assets}</p>
          </div>
          <div className="theme-card rounded-xl border p-4">
            <h3 className="font-semibold mb-2 text-warning">Liabilities</h3>
            <Table columns={["Code", "Account", "Group", "Amount"]} rows={(data.liability_lines ?? []).map((l: any) => [l.account_code, l.account_name, l.group_name, l.amount])} />
            <p className="text-right font-semibold mt-2">Total Liabilities: {formatMoney?.(data.total_liabilities) ?? data.total_liabilities}</p>
          </div>
          <div className="theme-card rounded-xl border p-4">
            <h3 className="font-semibold mb-2 text-success">Equity</h3>
            <Table columns={["Code", "Account", "Group", "Amount"]} rows={(data.equity_lines ?? []).map((l: any) => [l.account_code, l.account_name, l.group_name, l.amount])} />
            <p className="text-right font-semibold mt-2">Total Equity: {formatMoney?.(data.total_equity) ?? data.total_equity}</p>
          </div>
        </motion.div>
      )}
    </div>
  );
}

export function CashFlowTab({ postData, data, loading, formatMoney }: any) {
  const [start, setStart] = useState(() => { const d = new Date(); d.setMonth(d.getMonth() - 1); return d.toISOString().slice(0, 16); });
  const [end, setEnd] = useState(() => new Date().toISOString().slice(0, 16));
  const generate = () => postData("/reports/cash-flow", { period_start: new Date(start).toISOString(), period_end: new Date(end).toISOString(), currency: "OMR" });
  return (
    <div className="space-y-3">
      <div className="theme-card rounded-xl border p-4 flex gap-3 items-end flex-wrap">
        <div><label className="text-xs">From</label><input type="datetime-local" value={start} onChange={e => setStart(e.target.value)} className="mt-1 border rounded p-1 text-sm" /></div>
        <div><label className="text-xs">To</label><input type="datetime-local" value={end} onChange={e => setEnd(e.target.value)} className="mt-1 border rounded p-1 text-sm" /></div>
        <button onClick={generate} disabled={loading} className="theme-btn-primary px-4 py-1.5 text-sm rounded-lg">Generate</button>
      </div>
      {data && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
          <div className="theme-card rounded-xl border p-4">
            <h3 className="font-semibold mb-2">Operating Activities</h3>
            <Table columns={["Item", "Amount"]} rows={(data.operating?.lines ?? []).map((l: any) => [l.label, l.amount])} />
            <p className="text-right font-semibold mt-2">Net: {formatMoney?.(data.net_operating) ?? data.net_operating}</p>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <MetricCard title="Opening Balance" value={data.opening_balance} />
            <MetricCard title="Net Change" value={data.net_change} />
            <MetricCard title="Closing Balance" value={data.closing_balance} />
          </div>
        </motion.div>
      )}
    </div>
  );
}

export function PeriodsTab({ fetchData, postData, data, loading }: any) {
  useEffect(() => { fetchData("/periods"); }, []);
  const [cc, setCc] = useState("OMN");
  const [yr, setYr] = useState("2026");
  const [mo, setMo] = useState("7");
  const createPeriod = () => postData("/periods/get-or-create", { country_code: cc, year: parseInt(yr), month: parseInt(mo) }).then(() => fetchData("/periods"));
  const [closePeriodId, setClosePeriodId] = useState<number | null>(null);
  const doClose = () => { if (closePeriodId) postData("/periods/close", { period_id: closePeriodId }).then(() => fetchData("/periods")); };
  return (
    <div className="space-y-3">
      <div className="theme-card rounded-xl border p-4 flex gap-3 items-end flex-wrap">
        <div><label className="text-xs">Country</label><input value={cc} onChange={e => setCc(e.target.value)} className="mt-1 border rounded p-1 text-sm w-16" /></div>
        <div><label className="text-xs">Year</label><input value={yr} onChange={e => setYr(e.target.value)} className="mt-1 border rounded p-1 text-sm w-20" /></div>
        <div><label className="text-xs">Month</label><input value={mo} onChange={e => setMo(e.target.value)} className="mt-1 border rounded p-1 text-sm w-16" /></div>
        <button onClick={createPeriod} disabled={loading} className="theme-btn-primary px-4 py-1.5 text-sm rounded-lg">Get/Create</button>
      </div>
      <div className="theme-card rounded-xl border p-4 flex gap-3 items-end flex-wrap">
        <div><label className="text-xs">Period ID to Close</label><input type="number" value={closePeriodId ?? ""} onChange={e => setClosePeriodId(parseInt(e.target.value) || null)} className="mt-1 border rounded p-1 text-sm w-24" /></div>
        <button onClick={doClose} disabled={loading} className="theme-btn-danger px-4 py-1.5 text-sm rounded-lg">Close Period</button>
      </div>
      <div className="theme-card rounded-xl border p-4">
        <Table columns={["ID", "Period", "Status", "Locked", "Start", "End"]} rows={(data ?? []).map((p: any) => [p.id, p.label, p.status, p.is_locked ? "Y" : "N", p.period_start?.slice(0, 10), p.period_end?.slice(0, 10)])} />
      </div>
    </div>
  );
}

export function ReversalTab({ postData, data, loading }: any) {
  const [entryId, setEntryId] = useState("");
  const [reason, setReason] = useState("");
  const doReverse = () => postData("/journal-entries/reverse", { entry_id: parseInt(entryId), reason });
  return (
    <div className="space-y-3">
      <div className="theme-card rounded-xl border p-4 flex gap-3 items-end flex-wrap">
        <div><label className="text-xs">Journal Entry ID</label><input type="number" value={entryId} onChange={e => setEntryId(e.target.value)} className="mt-1 border rounded p-1 text-sm w-28" /></div>
        <div><label className="text-xs">Reason</label><input value={reason} onChange={e => setReason(e.target.value)} className="mt-1 border rounded p-1 text-sm w-64" /></div>
        <button onClick={doReverse} disabled={loading} className="theme-btn-danger px-4 py-1.5 text-sm rounded-lg">Reverse Entry</button>
      </div>
      {data && (
        <div className="theme-card rounded-xl border p-4">
          <p>Reversal Entry ID: <strong>{data.reversal_entry_id}</strong></p>
          <p>Reference: {data.reference_number}</p>
          <p>Reason: {data.reason}</p>
          <p>Lines Reversed: {data.lines_reversed}</p>
        </div>
      )}
    </div>
  );
}

export function ForecastTab({ postData, data, loading, formatMoney }: any) {
  const [days, setDays] = useState("90");
  const generate = () => postData("/cash-flow-forecast", { days: parseInt(days), currency: "OMR" });
  return (
    <div className="space-y-3">
      <div className="theme-card rounded-xl border p-4 flex gap-3 items-end flex-wrap">
        <div><label className="text-xs">Days</label><input type="number" value={days} onChange={e => setDays(e.target.value)} className="mt-1 border rounded p-1 text-sm w-20" /></div>
        <button onClick={generate} disabled={loading} className="theme-btn-primary px-4 py-1.5 text-sm rounded-lg">Generate Forecast</button>
      </div>
      {data && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
          <div className="grid grid-cols-4 gap-3">
            <MetricCard title="Current Balance" value={formatMoney?.(data.current_balance) ?? data.current_balance} />
            <MetricCard title="Avg Daily Net" value={formatMoney?.(data.historical_avg_daily_net) ?? data.historical_avg_daily_net} />
            <MetricCard title="30d Projected" value={formatMoney?.(data.projected_balance_30d) ?? data.projected_balance_30d} />
            <MetricCard title="90d Projected" value={formatMoney?.(data.projected_balance_90d) ?? data.projected_balance_90d} />
          </div>
          <div className="theme-card rounded-xl border p-4 max-h-96 overflow-y-auto">
            <Table columns={["Date", "Opening", "Inflow", "Outflow", "Net", "Closing"]} rows={(data.forecast_days ?? []).map((d: any) => [d.date?.slice(0, 10), d.opening_balance, d.inflow, d.outflow, d.net_flow, d.closing_balance])} />
          </div>
        </motion.div>
      )}
    </div>
  );
}

export function ReportsTab({ fetchData, data, loading }: any) {
  useEffect(() => { fetchData("/reports"); }, []);
  return (
    <div className="theme-card rounded-xl border p-4">
      <Table columns={["Type", "Period", "Generated At"]} rows={(data ?? []).map((r: any) => [r.report_type, `${r.period_start?.slice(0, 10)} to ${r.period_end?.slice(0, 10)}`, r.generated_at?.slice(0, 16)])} />
    </div>
  );
}
