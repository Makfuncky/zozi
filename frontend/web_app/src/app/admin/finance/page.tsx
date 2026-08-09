"use client";

import { Suspense, useEffect, useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  TrendingUp, Wallet, Building2, Shield as ShieldIcon, Receipt, FileText, DollarSign, BookOpen,
} from "@/lib/icons";
import { useAuth } from "@/lib/useAuth";
import { isAdminStaffRole } from "@shared/adminPermissions";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelLoadingState, PanelTabs } from "@/components/PanelPage";
import { useAdminCountry } from "@/lib/useAdminCountry";
import { useToastStore } from "@/lib/toastStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { apiFetch } from "@/lib/api";
import dynamic from "next/dynamic";

const loadingFallback = () => <PanelLoadingState count={3} blockClassName="h-24 rounded-xl bg-surface-2 animate-pulse" />;

const FinanceTab = dynamic(() => import("../dashboard/_tabs/FinanceTab"), { loading: loadingFallback });
const PayoutsTab = dynamic(() => import("../dashboard/_tabs/PayoutsTab"), { loading: loadingFallback });
const BankAccountsPanel = dynamic(() => import("./_components/BankAccountsPanel"), { loading: loadingFallback });
const TreasuryContent = dynamic(() => import("../treasury/_components/treasury-content").then(m => ({ default: m.TreasuryContent })), { loading: loadingFallback });
const CashFlowCycleTab = dynamic(() => import("./_components/CashFlowCycleTab"), { loading: loadingFallback });
const JournalBrowserPanel = dynamic(() => import("./_components/ErpPanels").then(m => ({ default: m.JournalBrowserPanel })), { loading: loadingFallback });
const ARPanel = dynamic(() => import("./_components/ErpPanels").then(m => ({ default: m.ARPanel })), { loading: loadingFallback });
const APPanel = dynamic(() => import("./_components/ErpPanels").then(m => ({ default: m.APPanel })), { loading: loadingFallback });
const TrialBalanceTab = dynamic(() => import("./_components/AccountingPanels").then(m => ({ default: m.TrialBalanceTab })), { loading: loadingFallback });
const IncomeStatementTab = dynamic(() => import("./_components/AccountingPanels").then(m => ({ default: m.IncomeStatementTab })), { loading: loadingFallback });
const BalanceSheetTab = dynamic(() => import("./_components/AccountingPanels").then(m => ({ default: m.BalanceSheetTab })), { loading: loadingFallback });
const ReportsTab = dynamic(() => import("./_components/AccountingPanels").then(m => ({ default: m.ReportsTab })), { loading: loadingFallback });

const TABS = [
  { key: "finance", label: "Cash Flow & Cycle", icon: TrendingUp },
  { key: "payouts", label: "Payouts", icon: Wallet },
  { key: "bank-accounts", label: "Bank Accounts", icon: Building2 },
  { key: "treasury", label: "Treasury", icon: ShieldIcon },
  { key: "ar", label: "Receivables", icon: Receipt },
  { key: "ap", label: "Payables", icon: FileText },
  { key: "journal", label: "Journal", icon: BookOpen },
  { key: "trial-balance", label: "Trial Balance", icon: FileText },
  { key: "pl", label: "P&L", icon: TrendingUp },
  { key: "balance-sheet", label: "Balance Sheet", icon: DollarSign },
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
      case "finance": return <CashFlowCycleTab />;
      case "payouts": return <PayoutsTab />;
      case "bank-accounts": return <BankAccountsPanel />;
      case "treasury": return <TreasuryContent />;
      case "ar": return <ARPanel />;
      case "ap": return <APPanel />;
      case "journal": return <JournalBrowserPanel />;
      case "trial-balance": return <TrialBalanceTab fetchData={fetchData} formatMoney={formatMoney} />;
      case "pl": return <IncomeStatementTab postData={postData} data={data} loading={loading} formatMoney={formatMoney} />;
      case "balance-sheet": return <BalanceSheetTab postData={postData} data={data} loading={loading} formatMoney={formatMoney} />;
      case "reports": return <ReportsTab fetchData={fetchData} data={data} loading={loading} />;
      default: return <CashFlowCycleTab />;
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
