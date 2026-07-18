"use client";

import { Suspense, useEffect, useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  TrendingUp, Wallet, Building2, Shield as ShieldIcon, ListChecks, ScanLine, GitBranch,
  PiggyBank, Layers, BookOpen, Receipt, FileText, Split, Calculator, FileSearch,
  ArrowDownUp, CircleDollarSign, Cpu, Mail, DollarSign, RefreshCw, Calendar, RotateCcw,
} from "@/lib/icons";
import { useAuth } from "@/lib/useAuth";
import { isAdminStaffRole } from "@shared/adminPermissions";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelLoadingState, PanelTabs } from "@/components/PanelPage";
import FinanceTab from "../dashboard/tabs/FinanceTab";
import PayoutsTab from "../dashboard/tabs/PayoutsTab";
import BankAccountsPanel from "./BankAccountsPanel";
import { TreasuryContent } from "../treasury/treasury-content";
import { useAdminCountry } from "@/lib/useAdminCountry";
import { useToastStore } from "@/lib/toastStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { apiFetch } from "@/lib/api";
import {
  ChartOfAccountsPanel,
  ExpenseScanPanel,
  BankMappingPanel,
  FixedAssetsPanel,
  AccrualsPanel,
  FxPanel,
  DeferredRevenuePanel,
  EmailLedgerPanel,
  AiReconcilePanel,
} from "./FinanceModules";
import {
  JournalBrowserPanel,
  ARPanel,
  APPanel,
  PaymentsRegisterPanel,
  BankReconciliationPanel,
  BudgetsPanel,
  FinanceAuditPanel,
} from "./ErpPanels";
import {
  TrialBalanceTab,
  IncomeStatementTab,
  BalanceSheetTab,
  CashFlowTab,
  PeriodsTab,
  ReversalTab,
  ForecastTab,
  ReportsTab,
} from "./AccountingPanels";

const TABS = [
  { key: "finance", label: "Finance", icon: TrendingUp },
  { key: "payouts", label: "Payouts", icon: Wallet },
  { key: "bank-accounts", label: "Bank Accounts", icon: Building2 },
  { key: "treasury", label: "Treasury", icon: ShieldIcon },
  { key: "chart-of-accounts", label: "Chart of Accounts", icon: ListChecks },
  { key: "expense-scan", label: "Expense Scan", icon: ScanLine },
  { key: "bank-mapping", label: "Bank Mapping", icon: GitBranch },
  { key: "fixed-assets", label: "Fixed Assets", icon: PiggyBank },
  { key: "accruals", label: "Accruals", icon: Layers },
  { key: "ar", label: "Receivables", icon: Receipt },
  { key: "ap", label: "Payables", icon: FileText },
  { key: "journal", label: "Journal", icon: BookOpen },
  { key: "payments", label: "Payments Register", icon: Wallet },
  { key: "reconciliation", label: "Reconciliation", icon: Split },
  { key: "budgets", label: "Budgets", icon: Calculator },
  { key: "audit", label: "Audit Log", icon: FileSearch },
  { key: "fx", label: "FX Revaluation", icon: ArrowDownUp },
  { key: "deferred-revenue", label: "Deferred Revenue", icon: CircleDollarSign },
  { key: "email-ledger", label: "Email-to-Ledger", icon: Mail },
  { key: "ai-reconcile", label: "AI Reconcile", icon: Cpu },
  { key: "trial-balance", label: "Trial Balance", icon: FileText },
  { key: "pl", label: "P&L", icon: TrendingUp },
  { key: "balance-sheet", label: "Balance Sheet", icon: DollarSign },
  { key: "cash-flow", label: "Cash Flow", icon: RefreshCw },
  { key: "periods", label: "Periods", icon: Calendar },
  { key: "reversal", label: "Reversal", icon: RotateCcw },
  { key: "forecast", label: "Forecast", icon: TrendingUp },
  { key: "reports", label: "Reports", icon: FileText },
] as const;

function AdminFinanceInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const section = searchParams?.get("section") ?? "finance";
  const { user, isLoggedIn, isLoading } = useAuth();
  const role = user?.role ?? null;
  const { selectedCountry, isGlobalView } = useAdminCountry();
  const toast = useToastStore((s) => s.addToast);
  const formatMoney = useCurrencyStore((s) => s.format);
  const [tab, setTab] = useState<string>(section);
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(async (path: string) => {
    setLoading(true);
    try {
      const res = await apiFetch(`/accounting${path}`);
      if (res.ok) { const j = await res.json(); setData(j); return j; }
      toast(`API error: ${res.status}`, "error");
    } catch { toast("Network error", "error"); }
    finally { setLoading(false); }
    return null;
  }, [toast]);

  const postData = useCallback(async (path: string, body: any) => {
    setLoading(true);
    try {
      const res = await apiFetch(`/accounting${path}`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (res.ok) { const j = await res.json(); setData(j); toast("Success", "success"); return j; }
      const err = await res.json().catch(() => ({}));
      toast(err.detail || `Error ${res.status}`, "error");
    } catch { toast("Network error", "error"); }
    finally { setLoading(false); }
    return null;
  }, [toast]);

  useEffect(() => {
    if (isLoading) return;
    if (!isLoggedIn || !isAdminStaffRole(role)) {
      router.push("/admin/login");
    }
  }, [isLoading, isLoggedIn, role, router]);

  useEffect(() => { setTab(section); }, [section]);

  if (isLoading || !isLoggedIn || !isAdminStaffRole(role)) {
    return (
      <AdminLayout title="Finance" headerMode="compact">
        <PanelLoadingState count={3} blockClassName="h-16 rounded-xl bg-surface-2 animate-pulse" />
      </AdminLayout>
    );
  }

  const render = () => {
    switch (tab) {
      case "finance": return <FinanceTab />;
      case "payouts": return <PayoutsTab />;
      case "bank-accounts": return <BankAccountsPanel />;
      case "treasury": return <TreasuryContent />;
      case "chart-of-accounts": return <ChartOfAccountsPanel />;
      case "expense-scan": return <ExpenseScanPanel />;
      case "bank-mapping": return <BankMappingPanel />;
      case "fixed-assets": return <FixedAssetsPanel />;
      case "accruals": return <AccrualsPanel />;
      case "ar": return <ARPanel />;
      case "ap": return <APPanel />;
      case "journal": return <JournalBrowserPanel />;
      case "payments": return <PaymentsRegisterPanel />;
      case "reconciliation": return <BankReconciliationPanel />;
      case "budgets": return <BudgetsPanel />;
      case "audit": return <FinanceAuditPanel />;
      case "fx": return <FxPanel />;
      case "deferred-revenue": return <DeferredRevenuePanel />;
      case "email-ledger": return <EmailLedgerPanel />;
      case "ai-reconcile": return <AiReconcilePanel />;
      case "trial-balance": return <TrialBalanceTab fetchData={fetchData} formatMoney={formatMoney} />;
      case "pl": return <IncomeStatementTab postData={postData} data={data} loading={loading} formatMoney={formatMoney} />;
      case "balance-sheet": return <BalanceSheetTab postData={postData} data={data} loading={loading} formatMoney={formatMoney} />;
      case "cash-flow": return <CashFlowTab postData={postData} data={data} loading={loading} formatMoney={formatMoney} />;
      case "periods": return <PeriodsTab fetchData={fetchData} postData={postData} data={data} loading={loading} />;
      case "reversal": return <ReversalTab postData={postData} data={data} loading={loading} />;
      case "forecast": return <ForecastTab postData={postData} data={data} loading={loading} formatMoney={formatMoney} />;
      case "reports": return <ReportsTab fetchData={fetchData} data={data} loading={loading} />;
      default: return <FinanceTab />;
    }
  };

  return (
    <AdminLayout title="Finance & Cash Management" headerMode="compact">
      <PanelContent className="space-y-3">
        <div className="flex items-center gap-2 text-[11px] text-text-faint bg-surface-2 rounded-lg px-3 py-1.5">
          <ShieldIcon className="h-3 w-3" />
          <span>{isGlobalView ? "Global View — All Countries" : `Country: ${selectedCountry?.name || selectedCountry?.code}`}</span>
        </div>

        <PanelTabs
          items={TABS as unknown as { key: string; label: string; icon: any }[]}
          value={tab}
          onChange={(next) => { setTab(next); router.replace(`/admin/finance?section=${next}`); }}
        />

        {render()}
      </PanelContent>
    </AdminLayout>
  );
}

export default function AdminFinancePage() {
  return (
    <Suspense>
      <AdminFinanceInner />
    </Suspense>
  );
}
