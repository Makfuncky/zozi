"use client";

import { Button } from "@/components/ui/Button";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Wallet, TrendingUp, Users, DollarSign, RefreshCw, FileText, PieChart, BarChart3, Shield, Download, Calendar, Filter, CreditCard, AlertTriangle, ListChecks, ShieldCheck, History, Banknote, Search, Truck, Building, Layers, Clock, ChevronDown, Percent, Scale, Target, Globe2, Hash, Package2, PackageCheck, Grid2x2, LayoutGrid, CheckCircle, ArrowDownUp, BadgeCheck, Inbox, Coins, Receipt, Landmark, CircleDollarSign, Columns, Rows, FileSpreadsheet, PiggyBank, ListFilter, Workflow, CircleCheck, Split } from "@/lib/icons";
import { useAuth } from "@/lib/useAuth";
import { isAdminStaffRole } from "@shared/adminPermissions";
import AdminRouteRedirect from "@/components/AdminRouteRedirect";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useAdminCountry } from "@/lib/useAdminCountry";
import { useToastStore } from "@/lib/toastStore";
import { motion, AnimatePresence } from "framer-motion";

interface TreasuryMetrics {
  total_credits: number;
  total_debits: number;
  net_balance: number;
  total_entries: number;
}

interface TrialBalanceItem {
  account_code: string;
  account_name: string;
  balance: number;
  normal_side: string;
}

interface JournalEntry {
  id: number;
  reference_number: string;
  entry_date: string;
  description: string;
  source: string;
  total_debit: number;
  total_credit: number;
}

interface CashPosition {
  account_name: string;
  balance: number;
  gl_code: string;
}

interface PayoutBatch {
  id: number;
  batch_number: string;
  country_code: string;
  total_amount: number;
  status: string;
  created_at: string;
  created_by?: number;
  created_by_name?: string;
  approved_by?: number;
  approved_by_name?: string;
}

interface VATLiability {
  output_vat: number;
  input_vat: number;
  net_vat_due: number;
  country_code?: string;
  period?: string;
}

interface CODRemittance {
  id: number;
  logistics_partner_id: number;
  logistics_partner_name: string;
  amount_remitted: number;
  amount_expected: number;
  status: string;
  remitted_at: string;
  bank_reference?: string;
  proof_url?: string;
}

interface GatewayReconciliationItem {
  gateway_code: string;
  total_settled: number;
  total_expected: number;
  discrepancy: number;
  count: number;
  last_settlement_date: string;
}

interface PaymentTxn {
  id: number;
  order_id: number | null;
  amount: number;
  payment_method: string | null;
  provider: string | null;
  status: string | null;
  created_at: string | null;
  country_code: string | null;
}

interface LiabilityExposure {
  supplier_payables: number;
  logistics_payables: number;
  vat_payable: number;
}

interface PendingEntry {
  id: number;
  description: string | null;
  source: string | null;
  country_code: string | null;
  amount_threshold_triggered: boolean;
  status: string;
  created_by: number;
  created_at: string;
}

interface GatewayException {
  id: number;
  gateway_id: number;
  settlement_date: string | null;
  amount: number;
  currency: string | null;
  status: string;
  country_code: string | null;
}

interface SupplierPayout {
  id: number;
  supplier_id: number;
  supplier_name: string;
  amount: number;
  currency: string | null;
  method: string | null;
  status: string;
  reference: string | null;
  created_at: string | null;
  country_code: string | null;
}

interface LogisticsPayout {
  id: number;
  partner_id: number;
  amount: number;
  currency: string | null;
  status: string;
  reference_id: string | null;
  period_start: string | null;
  period_end: string | null;
  created_at: string | null;
  country_code: string | null;
}

type TabType = "dashboard" | "ledger" | "trial-balance" | "cash-position" | "payments" | "payouts" | "vat" | "gateway-recon" | "cod" | "reconciliation" | "liabilities" | "pending";

export function TreasuryContent() {
  const router = useRouter();
  const { isLoggedIn, user } = useAuth();
  const role = user?.role ?? null;
  const formatMoney = useCurrencyStore((s) => s.format);
  const { selectedCountry, assignedCountries } = useAdminCountry();
  const [activeTab, setActiveTab] = useState<TabType>("dashboard");
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState<TreasuryMetrics | null>(null);
  const [trialBalance, setTrialBalance] = useState<TrialBalanceItem[]>([]);
  const [journalEntries, setJournalEntries] = useState<JournalEntry[]>([]);
  const [cashPosition, setCashPosition] = useState<CashPosition[]>([]);
  const [payoutBatches, setPayoutBatches] = useState<PayoutBatch[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>("2026-06-29");
  const [filterCountry, setFilterCountry] = useState<string>(() => selectedCountry?.code || "*");
  const [vatLiability, setVatLiability] = useState<VATLiability | null>(null);
  const [codRemittances, setCODRemittances] = useState<CODRemittance[]>([]);
  const [gatewayRecon, setGatewayRecon] = useState<GatewayReconciliationItem[]>([]);
  const [currentUser, setCurrentUser] = useState<{ id: number; full_name: string } | null>(null);
  const [showMakerChecker, setShowMakerChecker] = useState(false);
  const [makerCheckerBatch, setMakerCheckerBatch] = useState<PayoutBatch | null>(null);
  const [makerCheckerAction, setMakerCheckerAction] = useState<"approve" | "dispatch" | null>(null);
  const [paymentTxns, setPaymentTxns] = useState<PaymentTxn[]>([]);
  const [paymentStart, setPaymentStart] = useState<string>(() => {
    const d = new Date(); d.setDate(1); return d.toISOString().slice(0, 10);
  });
  const [liabilities, setLiabilities] = useState<LiabilityExposure | null>(null);
  const [pendingEntries, setPendingEntries] = useState<PendingEntry[]>([]);
  const [gatewayExceptions, setGatewayExceptions] = useState<GatewayException[]>([]);
  const [supplierPayouts, setSupplierPayouts] = useState<SupplierPayout[]>([]);
  const [logisticsPayouts, setLogisticsPayouts] = useState<LogisticsPayout[]>([]);
  const [showGenerateBatch, setShowGenerateBatch] = useState(false);
  const [showVatRemit, setShowVatRemit] = useState(false);
  const [detectingOrphans, setDetectingOrphans] = useState(false);
  const [orphanResult, setOrphanResult] = useState<{ alerts: unknown[]; count: number } | null>(null);

  useEffect(() => {
    if (selectedCountry && filterCountry === "*" && assignedCountries.length > 0) {
      setFilterCountry(selectedCountry.code);
    }
  }, [selectedCountry, filterCountry, assignedCountries.length]);

  useEffect(() => {
    if (!isLoggedIn || !isAdminStaffRole(role)) {
      router.push("/admin/login");
      return;
    }

    const loadData = async () => {
      setLoading(true);
      try {
        const useConsolidated = filterCountry === "*" || !filterCountry;
        const cc = useConsolidated ? "consolidated" : filterCountry;

        const buildUrl = (path: string) =>
          `/admin/treasury/${useConsolidated ? `consolidated` : `${cc}`}${path}`;
        const b = (path: string) =>
          useConsolidated ? `/admin/treasury${path}` : `/admin/treasury/${cc}${path}`;

        const [metricsRes, trialRes, ledgerRes, cashRes, payoutRes, vatRes, codRes, gatewayRes, payRes, liabRes, pendingRes, excRes, supPayRes, logPayRes] = await Promise.all([
          apiFetch(buildUrl("/metrics")),
          apiFetch(buildUrl(`/reports/trial-balance?as_of_date=${selectedDate}`)),
          apiFetch(buildUrl(`/ledger?start_date=2026-01-01&end_date=${selectedDate}&limit=50`)),
          apiFetch(buildUrl("/cash-position")),
          apiFetch(buildUrl("/payouts/batches")),
          apiFetch(buildUrl(`/reports/vat-liability?period=current`)),
          apiFetch(buildUrl(`/cod-remittances?status=pending`)),
          apiFetch(buildUrl("/reconciliation/gateway-summary")),
          apiFetch(b(`/payments/transactions?start_date=${paymentStart}&end_date=${selectedDate}`)),
          apiFetch(b("/liabilities/exposure")),
          apiFetch(b("/ledger/pending")),
          apiFetch(b("/reconciliation/gateway-exceptions")),
          apiFetch(b("/supplier-payouts")),
          apiFetch(b("/logistics-payouts")),
        ]);

        if (metricsRes.ok) setMetrics(await metricsRes.json());
        if (trialRes.ok) setTrialBalance(await trialRes.json());
        if (ledgerRes.ok) setJournalEntries(await ledgerRes.json());
        if (cashRes.ok) {
          const raw = await cashRes.json();
          const arr: any[] = Array.isArray(raw)
            ? raw
            : (raw?.accounts ?? raw?.cash_position ?? raw?.buckets ?? []);
          setCashPosition(
            arr.map((item: any) => ({
              account_name: item.account_name ?? item.name ?? "—",
              balance: Number(item.balance ?? 0),
              gl_code: item.gl_code ?? item.gl_account_code ?? item.slug ?? "",
            }))
          );
        }
        if (payoutRes.ok) setPayoutBatches(await payoutRes.json());
        if (vatRes.ok) setVatLiability(await vatRes.json());
        if (codRes.ok) {
          const codData = await codRes.json();
          setCODRemittances(Array.isArray(codData) ? codData : codData.remittances ?? []);
        }
        if (gatewayRes.ok) {
          const gwData = await gatewayRes.json();
          setGatewayRecon(Array.isArray(gwData) ? gwData : gwData.gateways ?? []);
        }
        if (payRes.ok) setPaymentTxns(await payRes.json());
        if (liabRes.ok) setLiabilities(await liabRes.json());
        if (pendingRes.ok) {
          const pData = await pendingRes.json();
          setPendingEntries(Array.isArray(pData) ? pData : pData.entries ?? []);
        }
        if (excRes.ok) setGatewayExceptions(await excRes.json());
        if (supPayRes.ok) setSupplierPayouts(await supPayRes.json());
        if (logPayRes.ok) setLogisticsPayouts(await logPayRes.json());
        if (user) {
          setCurrentUser({ id: user.id, full_name: user.full_name ?? `User ${user.id}` });
        }
      } catch (error) {
        console.error("Failed to load treasury data:", error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [isLoggedIn, role, router, selectedDate, filterCountry, paymentStart, user]);

  if (!isLoggedIn || !isAdminStaffRole(role)) {
    return <PanelLoadingState count={3} blockClassName="h-16 rounded-xl bg-surface-2 animate-pulse" />;
  }

  const handleDetectOrphans = async () => {
    setDetectingOrphans(true);
    setOrphanResult(null);
    try {
      const seg = filterCountry === "*" ? "" : `${filterCountry}/`;
      const res = await apiFetch(`/admin/treasury/${seg}detect-orphans`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setOrphanResult({ alerts: data.alerts ?? [], count: data.count ?? 0 });
      }
    } catch {
      /* ignore */
    } finally {
      setDetectingOrphans(false);
    }
  };

  const TabButton = ({ tab, label, icon: Icon }: { tab: TabType; label: string; icon: React.ElementType }) => (
    <button
      onClick={() => setActiveTab(tab)}
      className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
        activeTab === tab 
          ? "bg-primary text-primary-foreground" 
          : "bg-surface-2 text-text-faint hover:bg-surface-3"
      }`}
    >
      <Icon className="h-4 w-4" />
      {label}
    </button>
  );

  return (
    <PanelContent className="space-y-4">
        {/* Tabs */}
        <div className="flex flex-wrap gap-2">
          <TabButton tab="dashboard" label="Dashboard" icon={Wallet} />
          <TabButton tab="ledger" label="General Ledger" icon={FileText} />
          <TabButton tab="trial-balance" label="Trial Balance" icon={BarChart3} />
          <TabButton tab="cash-position" label="Cash Position" icon={PieChart} />
          <TabButton tab="payments" label="Payments" icon={CreditCard} />
          <TabButton tab="payouts" label="Payout Batches" icon={Download} />
          <TabButton tab="vat" label="VAT Remittance" icon={Shield} />
          <TabButton tab="gateway-recon" label="Gateway Recon" icon={RefreshCw} />
          <TabButton tab="cod" label="COD Remittance" icon={DollarSign} />
          <TabButton tab="reconciliation" label="Reconciliation" icon={RefreshCw} />
          <TabButton tab="liabilities" label="Liabilities" icon={Banknote} />
          <TabButton tab="pending" label="Pending Entries" icon={ListChecks} />
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
              {activeTab === "dashboard" && (
                <DashboardView
                  metrics={metrics}
                  cashPosition={cashPosition}
                  codRemittances={codRemittances}
                  liabilities={liabilities}
                  gatewayRecon={gatewayRecon}
                  gatewayExceptions={gatewayExceptions}
                  onDetectOrphans={handleDetectOrphans}
                  detectingOrphans={detectingOrphans}
                  orphanResult={orphanResult}
                />
              )}
            {activeTab === "ledger" && (
              <LedgerView 
                entries={journalEntries} 
                onDateChange={setSelectedDate} 
                onCountryChange={setFilterCountry}
                selectedDate={selectedDate}
                filterCountry={filterCountry}
                assignedCountries={assignedCountries}
              />
            )}
            {activeTab === "trial-balance" && (
              <TrialBalanceView data={trialBalance} formatMoney={formatMoney} />
            )}
            {activeTab === "cash-position" && (
              <CashPositionView data={cashPosition} formatMoney={formatMoney} />
            )}
            {activeTab === "payouts" && (
              <PayoutsView 
                batches={payoutBatches} 
                supplierPayouts={supplierPayouts}
                logisticsPayouts={logisticsPayouts}
                formatMoney={formatMoney} 
                currentUser={currentUser}
                filterCountry={filterCountry}
                onShowMakerChecker={(batch, action) => {
                  setMakerCheckerBatch(batch);
                  setMakerCheckerAction(action);
                  setShowMakerChecker(true);
                }}
                onGenerateBatch={() => setShowGenerateBatch(true)}
              />
            )}
              {activeTab === "payments" && (
                <PaymentsView
                  txns={paymentTxns}
                  gatewayRecon={gatewayRecon}
                  gatewayExceptions={gatewayExceptions}
                  formatMoney={formatMoney}
                  startDate={paymentStart}
                  endDate={selectedDate}
                  onStartChange={setPaymentStart}
                  onEndChange={setSelectedDate}
                />
              )}
             {activeTab === "vat" && <VATView formatMoney={formatMoney} vatLiability={vatLiability} onMarkRemitted={() => setShowVatRemit(true)} />}
             {activeTab === "gateway-recon" && <GatewayReconView data={gatewayRecon} exceptions={gatewayExceptions} formatMoney={formatMoney} />}
             {activeTab === "cod" && <CODView remittances={codRemittances} formatMoney={formatMoney} />}
              {activeTab === "reconciliation" && <ReconciliationView filterCountry={filterCountry} formatMoney={formatMoney} forceRefresh={loading} exceptions={gatewayExceptions} supplierPayouts={supplierPayouts} />}
             {activeTab === "liabilities" && <LiabilitiesView liabilities={liabilities} formatMoney={formatMoney} />}
             {activeTab === "pending" && (
               <PendingEntriesView
                 entries={pendingEntries}
                 formatMoney={formatMoney}
                 currentUser={currentUser}
                 filterCountry={filterCountry}
                 onApproved={() => {
                   const cc = filterCountry === "*" ? "" : filterCountry;
                   apiFetch(`/admin/treasury/${cc}/ledger/pending`).then(async (r) => {
                     if (r.ok) { const d = await r.json(); setPendingEntries(Array.isArray(d) ? d : d.entries ?? []); }
                   });
                 }}
               />
             )}

            {/* Maker-Checker Modal */}
            {showMakerChecker && makerCheckerBatch && makerCheckerAction && (
              <MakerCheckerModal
                batch={makerCheckerBatch}
                action={makerCheckerAction}
                currentUser={currentUser}
                onClose={() => { setShowMakerChecker(false); setMakerCheckerBatch(null); setMakerCheckerAction(null); }}
                onConfirmed={() => {
                  setShowMakerChecker(false);
                  setMakerCheckerBatch(null);
                  setMakerCheckerAction(null);
                }}
              />
            )}

            {/* Generate Payout Batch Modal */}
            {showGenerateBatch && (
              <GenerateBatchModal
                filterCountry={filterCountry}
                assignedCountries={assignedCountries}
                onClose={() => setShowGenerateBatch(false)}
                onGenerated={() => {
                  setShowGenerateBatch(false);
                  const seg = filterCountry === "*" ? "consolidated" : filterCountry;
                  apiFetch(`/admin/treasury/${seg}/payouts/batches`).then(async (r) => {
                    if (r.ok) setPayoutBatches(await r.json());
                  });
                }}
              />
            )}

            {/* VAT Remittance Modal */}
            {showVatRemit && (
              <VatRemitModal
                vatLiability={vatLiability}
                currentUser={currentUser}
                onClose={() => setShowVatRemit(false)}
                onRemitted={() => setShowVatRemit(false)}
              />
            )}
          </motion.div>
        </AnimatePresence>
      </PanelContent>
  );
}

function DashboardView({ metrics, cashPosition, codRemittances, liabilities, gatewayRecon, gatewayExceptions, onDetectOrphans, detectingOrphans, orphanResult }: {
  metrics: TreasuryMetrics | null;
  cashPosition: CashPosition[];
  codRemittances: CODRemittance[];
  liabilities: LiabilityExposure | null;
  gatewayRecon: GatewayReconciliationItem[];
  gatewayExceptions: GatewayException[];
  onDetectOrphans: () => void;
  detectingOrphans: boolean;
  orphanResult: { alerts: unknown[]; count: number } | null;
}) {
  const formatMoney = useCurrencyStore((s) => s.format);

  const totalCash = cashPosition.reduce((sum, item) => sum + item.balance, 0);
  const lockedCash = cashPosition.find((c) => c.gl_code === "1020")?.balance || 0;
  const codReceivable = cashPosition.find((c) => c.gl_code === "1030")?.balance || 0;
  const freeCash = totalCash - lockedCash;

  const supplierPayables = liabilities?.supplier_payables ?? 0;
  const logisticsPayables = liabilities?.logistics_payables ?? 0;
  const vatPayable = liabilities?.vat_payable ?? 0;

  // Treasury Engine buckets (legacy 4-tier model)
  const buckets = [
    { label: "Available Cash", value: freeCash, tone: "text-success", bar: "bg-success", hint: "Operating bank — free to use" },
    { label: "Locked / Settling", value: lockedCash, tone: "text-warning", bar: "bg-warning", hint: "Gateway T+ settlement clearing" },
    { label: "COD Receivable", value: codReceivable, tone: "text-info", bar: "bg-info", hint: "Cash collected by drivers, not yet remitted" },
    { label: "Supplier Payables", value: supplierPayables, tone: "text-primary", bar: "bg-primary", hint: "Owed to suppliers (payout reserve)" },
    { label: "Logistics Payables", value: logisticsPayables, tone: "text-primary", bar: "bg-primary", hint: "Owed to 3PL partners" },
    { label: "VAT Payable", value: vatPayable, tone: "text-danger", bar: "bg-danger", hint: "Held in trust for ZATCA / FTA" },
  ];
  const bucketMax = Math.max(...buckets.map((b) => Math.abs(b.value)), 1);

  const kpis = [
    { label: "Net Balance", value: formatMoney(metrics?.net_balance ?? 0), icon: Wallet, tone: "text-primary", hint: "Credits − Debits" },
    { label: "Total Credits", value: formatMoney(metrics?.total_credits ?? 0), icon: DollarSign, tone: "text-success", hint: "All-time inflows" },
    { label: "Total Debits", value: formatMoney(metrics?.total_debits ?? 0), icon: RefreshCw, tone: "text-warning", hint: "All-time outflows" },
    { label: "Journal Entries", value: String(metrics?.total_entries ?? 0), icon: FileText, tone: "text-info", hint: "Immutable ledger posts" },
  ];

  const pendingCod = codRemittances.reduce((s, r) => s + (r.amount_expected - r.amount_remitted), 0);
  const reconDiscrepancy = gatewayRecon.reduce((s, g) => s + g.discrepancy, 0);
  const reconHealth = gatewayExceptions.length === 0 && Math.abs(reconDiscrepancy) < 0.01;

  return (
    <div className="space-y-5">
      {/* Key Metrics */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {kpis.map((k) => (
          <div key={k.label} className="theme-card rounded-xl border p-4 relative overflow-hidden">
            <div className={`absolute -right-4 -top-4 h-16 w-16 rounded-full ${k.tone} opacity-5`} />
            <div className="flex items-center gap-2 mb-1">
              <k.icon className={`h-4 w-4 ${k.tone}`} />
              <span className="text-[11px] font-semibold text-text-faint uppercase">{k.label}</span>
            </div>
            <p className="text-2xl font-bold text-text tabular-nums">{k.value}</p>
            <p className="text-[10px] text-text-faint mt-0.5">{k.hint}</p>
          </div>
        ))}
      </div>

      {/* Treasury Engine — Bucket Allocation */}
      <div className="theme-card rounded-xl border p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <PieChart className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-bold text-text">Treasury Engine — Cash &amp; Reserve Position</h3>
          </div>
          <span className="text-[11px] text-text-faint">Free Cash: <strong className="text-success">{formatMoney(freeCash)}</strong></span>
        </div>
        <div className="space-y-2.5">
          {buckets.map((b) => (
            <div key={b.label} className="grid grid-cols-[10rem_1fr_auto] items-center gap-3">
              <div>
                <p className="text-[11px] font-semibold text-text">{b.label}</p>
                <p className="text-[10px] text-text-faint">{b.hint}</p>
              </div>
              <div className="h-2.5 w-full rounded-full bg-surface-2 overflow-hidden">
                <div className={`h-full rounded-full ${b.bar}`} style={{ width: `${Math.min(100, (Math.abs(b.value) / bucketMax) * 100)}%` }} />
              </div>
              <p className={`text-xs font-bold tabular-nums ${b.tone}`}>{formatMoney(b.value)}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Payment Channels + Reconciliation Health */}
      <div className="grid gap-3 lg:grid-cols-2">
        <div className="theme-card rounded-xl border p-4">
          <div className="flex items-center gap-2 mb-3">
            <CreditCard className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-bold text-text">Payment Channels</h3>
          </div>
          {gatewayRecon.length === 0 ? (
            <p className="text-xs text-text-faint">No gateway settlement activity recorded yet.</p>
          ) : (
            <div className="space-y-2">
              {gatewayRecon.map((gw) => {
                const pct = gw.total_expected > 0 ? Math.min(100, (gw.total_settled / gw.total_expected) * 100) : 0;
                return (
                  <div key={gw.gateway_code}>
                    <div className="flex items-center justify-between text-[11px] mb-1">
                      <span className="font-semibold text-text capitalize">{gw.gateway_code}</span>
                      <span className={Math.abs(gw.discrepancy) < 0.01 ? "text-success" : "text-warning"}>
                        {formatMoney(gw.total_settled)} / {formatMoney(gw.total_expected)}
                      </span>
                    </div>
                    <div className="h-2 rounded-full bg-surface-2 overflow-hidden">
                      <div className={`h-full ${Math.abs(gw.discrepancy) < 0.01 ? "bg-success" : "bg-warning"}`} style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="flex flex-col gap-3">
          <div className={`rounded-xl border p-3 flex items-center justify-between ${reconHealth ? "border-success/30 bg-success/5" : "border-warning/30 bg-warning/5"}`}>
            <div className="flex items-center gap-2">
              <ShieldCheck className={`h-4 w-4 ${reconHealth ? "text-success" : "text-warning"}`} />
              <div>
                <p className="text-xs font-bold text-text">Reconciliation Health</p>
                <p className="text-[10px] text-text-faint">
                  {gatewayExceptions.length} settlement exceptions · {formatMoney(reconDiscrepancy)} discrepancy
                </p>
              </div>
            </div>
            <span className={`text-[11px] font-semibold ${reconHealth ? "text-success" : "text-warning"}`}>
              {reconHealth ? "Balanced" : "Needs Review"}
            </span>
          </div>

          {codRemittances.length > 0 && (
            <div className="rounded-xl border border-warning/30 bg-warning/5 p-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <DollarSign className="h-4 w-4 text-warning" />
                <span className="text-xs text-text">
                  <strong>{codRemittances.length} pending COD remittance{codRemittances.length > 1 ? "s" : ""}</strong> awaiting reconciliation
                </span>
              </div>
              <span className="text-xs font-bold text-warning">{formatMoney(pendingCod)}</span>
            </div>
          )}

          <div className="rounded-xl border border-info/20 bg-info/5 p-3 flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-2">
              <History className="h-4 w-4 text-info" />
              <div>
                <p className="text-xs font-bold text-text">Ledger Integrity</p>
                <p className="text-[10px] text-text-faint">Detect delivered orders / paid payouts missing a journal entry</p>
              </div>
            </div>
            <Button variant="info" className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition disabled:opacity-50" onClick={onDetectOrphans}
              disabled={detectingOrphans}
            >
              {detectingOrphans ? <div className="animate-spin rounded-full h-3 w-3 border-2 border-white border-t-transparent" /> : <History className="h-3.5 w-3.5" />}
              Run Orphan Detector
            </Button>
          </div>
        </div>
      </div>

      {orphanResult && (
        <div className={`rounded-lg border p-3 text-xs ${orphanResult.count > 0 ? "border-warning/30 bg-warning/5 text-warning" : "border-success/30 bg-success/5 text-success"}`}>
          {orphanResult.count > 0
            ? `${orphanResult.count} orphaned records detected — review the General Ledger and reconciliation pipeline.`
            : "Ledger is balanced — no orphaned financial records found."}
        </div>
      )}

      {/* Cash Position Breakdown */}
      <div className="theme-card rounded-xl border p-4">
        <h3 className="text-sm font-bold text-text mb-3">Cash Position by GL Account</h3>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {cashPosition.map((item) => (
            <div key={item.gl_code} className="rounded-lg border border-border bg-surface-2 p-3">
              <p className="text-[11px] text-text-faint uppercase">{item.account_name}</p>
              <p className="text-lg font-bold text-text tabular-nums">{formatMoney(item.balance)}</p>
              <p className="text-[10px] text-text-faint">{item.gl_code}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function LedgerView({ 
  entries, 
  onDateChange, 
  onCountryChange,
  selectedDate,
  filterCountry,
  assignedCountries = []
}: {
  entries: JournalEntry[];
  onDateChange: (date: string) => void;
  onCountryChange: (country: string) => void;
  selectedDate: string;
  filterCountry: string;
  assignedCountries: {code:string;name:string}[];
}) {
  const formatMoney = useCurrencyStore((s) => s.format);
  
  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-text-faint" />
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => onDateChange(e.target.value)}
            className="rounded-lg border border-border bg-surface-2 px-3 py-1.5 text-sm text-text"
          />
        </div>
        <select
          value={filterCountry}
          onChange={(e) => onCountryChange(e.target.value)}
          className="rounded-lg border border-border bg-surface-2 px-3 py-1.5 text-sm text-text"
        >
          {(assignedCountries.length > 0 ? assignedCountries : [{code:"*",name:"Global"}]).map((c) => (
            <option key={c.code} value={c.code}>{c.code === "*" ? "All Countries" : c.name || c.code}</option>
          ))}
        </select>
        <button className="ml-auto flex items-center gap-2 rounded-lg border border-border bg-surface-2 px-3 py-1.5 text-sm text-text hover:bg-surface-3">
          <Filter className="h-4 w-4" />
          Filter
        </button>
      </div>

      {/* Ledger Table */}
      <div className="theme-card rounded-xl border overflow-hidden">
        <div className="max-h-96 overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-surface-2 border-b border-border">
              <tr>
                <th className="text-left p-3 font-semibold">Ref</th>
                <th className="text-left p-3 font-semibold">Date</th>
                <th className="text-left p-3 font-semibold">Description</th>
                <th className="text-right p-3 font-semibold">Debit</th>
                <th className="text-right p-3 font-semibold">Credit</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.id} className="border-b border-border last:border-0">
                  <td className="p-3 font-mono text-xs">{entry.reference_number}</td>
                  <td className="p-3 text-text-faint">{entry.entry_date?.slice(0, 10)}</td>
                  <td className="p-3">{entry.description}</td>
                  <td className="p-3 text-right">{formatMoney(entry.total_debit)}</td>
                  <td className="p-3 text-right">{formatMoney(entry.total_credit)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function TrialBalanceView({ data, formatMoney }: { data: TrialBalanceItem[]; formatMoney: (n: number) => string }) {
  const totalDebits = data.reduce((sum, item) => sum + (item.normal_side === "debit" ? item.balance : 0), 0);
  const totalCredits = data.reduce((sum, item) => sum + (item.normal_side === "credit" ? item.balance : 0), 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-text">Trial Balance</h3>
        <div className="flex items-center gap-4 text-sm">
          <div>
            <span className="text-text-faint">Total Debits:</span>
            <span className="font-bold text-text ml-2">{formatMoney(totalDebits)}</span>
          </div>
          <div>
            <span className="text-text-faint">Total Credits:</span>
            <span className="font-bold text-text ml-2">{formatMoney(totalCredits)}</span>
          </div>
          <div className="text-text-faint">
            {Math.abs(totalDebits - totalCredits) < 0.01 ? "✓ Balanced" : "✗ Unbalanced"}
          </div>
        </div>
      </div>

      <div className="theme-card rounded-xl border overflow-hidden">
        <div className="max-h-96 overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-surface-2 border-b border-border">
              <tr>
                <th className="text-left p-2 font-semibold">Account Code</th>
                <th className="text-left p-2 font-semibold">Account Name</th>
                <th className="text-right p-2 font-semibold">Balance</th>
                <th className="text-center p-2 font-semibold">Normal Side</th>
              </tr>
            </thead>
            <tbody>
              {data.map((item) => (
                <tr key={item.account_code} className="border-b border-border last:border-0">
                  <td className="p-2 font-mono text-xs">{item.account_code}</td>
                  <td className="p-2">{item.account_name}</td>
                  <td className="p-2 text-right font-medium">{formatMoney(item.balance)}</td>
                  <td className="p-2 text-center text-text-faint">{item.normal_side}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function CashPositionView({ data, formatMoney }: { data: CashPosition[]; formatMoney: (n: number) => string }) {
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-bold text-text">Cash Position Dashboard</h3>
      
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {data.map((item) => (
          <div key={item.gl_code} className="theme-card rounded-xl border p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[11px] text-text-faint uppercase">{item.account_name}</p>
                <p className="text-2xl font-bold text-text">{formatMoney(item.balance)}</p>
              </div>
              <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                <Wallet className="h-5 w-5 text-primary" />
              </div>
            </div>
            <p className="text-[10px] text-text-faint mt-2">{item.gl_code}</p>
          </div>
        ))}
      </div>

      {/* Simple Bar Chart Representation */}
      <div className="theme-card rounded-xl border p-4">
        <h4 className="text-sm font-bold text-text mb-3">Cash Distribution</h4>
        <div className="space-y-2">
          {data.map((item) => {
            const percentage = (item.balance / Math.max(1, data.reduce((sum, d) => sum + d.balance, 0))) * 100;
            return (
              <div key={item.gl_code}>
                <div className="flex justify-between text-[11px] mb-1">
                  <span>{item.account_name}</span>
                  <span>{formatMoney(item.balance)}</span>
                </div>
                <div className="h-2 bg-surface-2 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-primary rounded-full" 
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function statusPill(status: string | null | undefined, map: Record<string, string>): string {
  const key = (status || "").toLowerCase();
  return map[key] || "bg-surface-2 text-text-faint";
}

function PayoutsView({ batches, supplierPayouts, logisticsPayouts, formatMoney, currentUser, filterCountry, onShowMakerChecker, onGenerateBatch }: {
  batches: PayoutBatch[];
  supplierPayouts: SupplierPayout[];
  logisticsPayouts: LogisticsPayout[];
  formatMoney: (n: number) => string;
  currentUser: { id: number; full_name: string } | null;
  filterCountry: string;
  onShowMakerChecker: (batch: PayoutBatch, action: "approve" | "dispatch") => void;
  onGenerateBatch: () => void;
}) {
  const [sub, setSub] = useState<"batches" | "supplier" | "logistics">("batches");

  const batchStatus: Record<string, string> = {
    draft: "bg-surface-2 text-text-faint",
    pending_approval: "bg-warning/20 text-warning",
    approved: "bg-info/20 text-info",
    dispatched: "bg-success/20 text-success",
    settled: "bg-success/20 text-success",
  };
  const payStatus: Record<string, string> = {
    pending: "bg-warning/20 text-warning",
    processing: "bg-info/20 text-info",
    batched: "bg-surface-2 text-text-faint",
    approved: "bg-info/20 text-info",
    dispatched: "bg-primary/20 text-primary",
    paid: "bg-success/20 text-success",
    completed: "bg-success/20 text-success",
    failed: "bg-danger/20 text-danger",
    rejected: "bg-danger/20 text-danger",
  };

  const supplierTotals = {
    total: supplierPayouts.reduce((s, p) => s + p.amount, 0),
    pending: supplierPayouts.filter((p) => p.status === "pending" || p.status === "batched").length,
    paid: supplierPayouts.filter((p) => p.status === "paid" || p.status === "completed").length,
  };
  const logisticsTotals = {
    total: logisticsPayouts.reduce((s, p) => s + p.amount, 0),
    pending: logisticsPayouts.filter((p) => p.status === "pending" || p.status === "processing").length,
    paid: logisticsPayouts.filter((p) => p.status === "paid" || p.status === "completed").length,
  };
  const batchTotals = {
    total: batches.reduce((s, b) => s + b.total_amount, 0),
    pending: batches.filter((b) => b.status === "pending_approval").length,
    dispatched: batches.filter((b) => b.status === "dispatched" || b.status === "settled").length,
  };

  const subTabs = [
    { key: "batches" as const, label: "Batches", icon: Layers, count: batches.length },
    { key: "supplier" as const, label: "Supplier Payouts", icon: Users, count: supplierPayouts.length },
    { key: "logistics" as const, label: "Logistics Payouts", icon: Truck, count: logisticsPayouts.length },
  ];

  return (
    <div className="space-y-4">
      {/* Header + sub tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-1 rounded-lg border border-border p-0.5">
          {subTabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setSub(t.key)}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[11px] font-semibold transition ${
                sub === t.key ? "bg-primary text-primary-foreground" : "text-text-faint hover:text-text"
              }`}
            >
              <t.icon className="h-3.5 w-3.5" />
              {t.label}
              <span className={`rounded-full px-1.5 text-[9px] ${sub === t.key ? "bg-white/20" : "bg-surface-2"}`}>{t.count}</span>
            </button>
          ))}
        </div>
        {sub === "batches" && (
          <Button variant="primary" className="rounded-lg px-3 py-1.5 text-xs font-semibold transition flex items-center gap-1.5" onClick={() => onGenerateBatch()}
          >
            <Download className="h-3.5 w-3.5" /> Generate New Batch
          </Button>
        )}
      </div>

      {/* Summary cards */}
      {sub === "batches" && (
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="theme-card rounded-xl border p-4">
            <p className="text-[11px] uppercase text-text-faint font-semibold">Batch Value</p>
            <p className="text-2xl font-bold text-text">{formatMoney(batchTotals.total)}</p>
          </div>
          <div className="theme-card rounded-xl border p-4">
            <p className="text-[11px] uppercase text-text-faint font-semibold">Awaiting Approval</p>
            <p className="text-2xl font-bold text-warning">{batchTotals.pending}</p>
          </div>
          <div className="theme-card rounded-xl border p-4">
            <p className="text-[11px] uppercase text-text-faint font-semibold">Dispatched / Settled</p>
            <p className="text-2xl font-bold text-success">{batchTotals.dispatched}</p>
          </div>
        </div>
      )}
      {sub === "supplier" && (
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="theme-card rounded-xl border p-4">
            <p className="text-[11px] uppercase text-text-faint font-semibold">Supplier Exposure</p>
            <p className="text-2xl font-bold text-text">{formatMoney(supplierTotals.total)}</p>
          </div>
          <div className="theme-card rounded-xl border p-4">
            <p className="text-[11px] uppercase text-text-faint font-semibold">Pending / Batched</p>
            <p className="text-2xl font-bold text-warning">{supplierTotals.pending}</p>
          </div>
          <div className="theme-card rounded-xl border p-4">
            <p className="text-[11px] uppercase text-text-faint font-semibold">Paid Out</p>
            <p className="text-2xl font-bold text-success">{supplierTotals.paid}</p>
          </div>
        </div>
      )}
      {sub === "logistics" && (
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="theme-card rounded-xl border p-4">
            <p className="text-[11px] uppercase text-text-faint font-semibold">Logistics Exposure</p>
            <p className="text-2xl font-bold text-text">{formatMoney(logisticsTotals.total)}</p>
          </div>
          <div className="theme-card rounded-xl border p-4">
            <p className="text-[11px] uppercase text-text-faint font-semibold">Pending / Processing</p>
            <p className="text-2xl font-bold text-warning">{logisticsTotals.pending}</p>
          </div>
          <div className="theme-card rounded-xl border p-4">
            <p className="text-[11px] uppercase text-text-faint font-semibold">Paid Out</p>
            <p className="text-2xl font-bold text-success">{logisticsTotals.paid}</p>
          </div>
        </div>
      )}

      {/* Batches table */}
      {sub === "batches" && (
        <div className="theme-card rounded-xl border overflow-hidden">
          <div className="max-h-[60vh] overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="bg-surface-2 sticky top-0">
                <tr>
                  <th className="text-left p-2 font-semibold">Batch #</th>
                  <th className="text-left p-2 font-semibold">Country</th>
                  <th className="text-right p-2 font-semibold">Amount</th>
                  <th className="text-center p-2 font-semibold">Status</th>
                  <th className="text-left p-2 font-semibold">Created By</th>
                  <th className="text-center p-2 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {batches.length === 0 ? (
                  <tr><td colSpan={6} className="p-6 text-center text-text-muted text-xs">No payout batches yet. Generate one to group pending supplier payouts.</td></tr>
                ) : batches.map((batch) => {
                  const isMaker = currentUser && batch.created_by === currentUser.id;
                  return (
                    <tr key={batch.id} className="border-b border-border last:border-0">
                      <td className="p-2 font-mono text-xs">{batch.batch_number}</td>
                      <td className="p-2">{batch.country_code}</td>
                      <td className="p-2 text-right">{formatMoney(batch.total_amount)}</td>
                      <td className="p-2 text-center">
                        <span className={`px-2 py-0.5 rounded-full text-[11px] ${statusPill(batch.status, batchStatus)}`}>{batch.status.replace("_", " ")}</span>
                      </td>
                      <td className="p-2 text-text-faint text-xs">{batch.created_by_name ?? `User #${batch.created_by}`}</td>
                      <td className="p-2 text-center">
                        <div className="flex items-center justify-center gap-1">
                          {batch.status === "pending_approval" && (
                            <Button variant="primary" className="rounded px-2 py-1 text-[10px] font-semibold text-success transition disabled:opacity-40 disabled:cursor-not-allowed" onClick={() => onShowMakerChecker(batch, "approve")} disabled={isMaker === true}
                              title={isMaker ? "Cannot approve your own batch (Maker-Checker)" : "Approve batch"}>Approve</Button>
                          )}
                          {batch.status === "approved" && (
                            <Button variant="primary" className="rounded px-2 py-1 text-[10px] font-semibold text-primary transition disabled:opacity-40 disabled:cursor-not-allowed" onClick={() => onShowMakerChecker(batch, "dispatch")} disabled={isMaker === true}
                              title={isMaker ? "Cannot dispatch your own batch (Maker-Checker)" : "Dispatch batch"}>Dispatch</Button>
                          )}
                          {batch.status !== "pending_approval" && batch.status !== "approved" && (
                            <span className="text-[10px] text-text-faint">—</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Supplier payouts table */}
      {sub === "supplier" && (
        <div className="theme-card rounded-xl border overflow-hidden">
          <div className="max-h-[60vh] overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="bg-surface-2 sticky top-0">
                <tr>
                  <th className="text-left p-2 font-semibold">Payout #</th>
                  <th className="text-left p-2 font-semibold">Supplier</th>
                  <th className="text-right p-2 font-semibold">Amount</th>
                  <th className="text-center p-2 font-semibold">Method</th>
                  <th className="text-center p-2 font-semibold">Status</th>
                  <th className="text-left p-2 font-semibold">Reference</th>
                  <th className="text-left p-2 font-semibold">Country</th>
                </tr>
              </thead>
              <tbody>
                {supplierPayouts.length === 0 ? (
                  <tr><td colSpan={7} className="p-6 text-center text-text-muted text-xs">No supplier payouts recorded yet.</td></tr>
                ) : supplierPayouts.map((p) => (
                  <tr key={p.id} className="border-b border-border last:border-0">
                    <td className="p-2 font-mono text-xs">#{p.id}</td>
                    <td className="p-2">
                      <p className="font-medium text-text">{p.supplier_name}</p>
                      <p className="text-[10px] text-text-faint">Supplier #{p.supplier_id}</p>
                    </td>
                    <td className="p-2 text-right font-medium">{formatMoney(p.amount)}</td>
                    <td className="p-2 text-center capitalize text-xs">{p.method ?? "—"}</td>
                    <td className="p-2 text-center"><span className={`px-2 py-0.5 rounded-full text-[10px] ${statusPill(p.status, payStatus)}`}>{p.status}</span></td>
                    <td className="p-2 font-mono text-[10px] text-text-faint">{p.reference ?? "—"}</td>
                    <td className="p-2 text-xs">{p.country_code ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Logistics payouts table */}
      {sub === "logistics" && (
        <div className="theme-card rounded-xl border overflow-hidden">
          <div className="max-h-[60vh] overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="bg-surface-2 sticky top-0">
                <tr>
                  <th className="text-left p-2 font-semibold">Payout #</th>
                  <th className="text-left p-2 font-semibold">Partner #</th>
                  <th className="text-right p-2 font-semibold">Amount</th>
                  <th className="text-center p-2 font-semibold">Status</th>
                  <th className="text-left p-2 font-semibold">Period</th>
                  <th className="text-left p-2 font-semibold">Reference</th>
                  <th className="text-left p-2 font-semibold">Country</th>
                </tr>
              </thead>
              <tbody>
                {logisticsPayouts.length === 0 ? (
                  <tr><td colSpan={7} className="p-6 text-center text-text-muted text-xs">No logistics partner payouts recorded yet.</td></tr>
                ) : logisticsPayouts.map((p) => (
                  <tr key={p.id} className="border-b border-border last:border-0">
                    <td className="p-2 font-mono text-xs">#{p.id}</td>
                    <td className="p-2 text-xs">Partner #{p.partner_id}</td>
                    <td className="p-2 text-right font-medium">{formatMoney(p.amount)}</td>
                    <td className="p-2 text-center"><span className={`px-2 py-0.5 rounded-full text-[10px] ${statusPill(p.status, payStatus)}`}>{p.status}</span></td>
                    <td className="p-2 text-[10px] text-text-faint">
                      {p.period_start ? p.period_start.slice(0, 10) : "—"} → {p.period_end ? p.period_end.slice(0, 10) : "—"}
                    </td>
                    <td className="p-2 font-mono text-[10px] text-text-faint">{p.reference_id ?? "—"}</td>
                    <td className="p-2 text-xs">{p.country_code ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function VATView({ formatMoney, vatLiability, onMarkRemitted }: { formatMoney: (n: number) => string; vatLiability: VATLiability | null; onMarkRemitted: () => void }) {
  const outputVat = vatLiability?.output_vat ?? 0;
  const inputVat = vatLiability?.input_vat ?? 0;
  const netVatDue = vatLiability?.net_vat_due ?? (outputVat - inputVat);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-text">VAT Remittance Wizard</h3>
        {vatLiability?.period && (
          <span className="text-xs text-text-faint">Period: {vatLiability.period}</span>
        )}
      </div>
      
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="theme-card rounded-xl border p-4">
          <h4 className="text-sm font-bold text-text mb-3">VAT Summary</h4>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-xs">
                <span className="text-text-faint">Output VAT Collected</span>
                <span className="font-bold text-text">{formatMoney(outputVat)}</span>
              </div>
              {vatLiability?.country_code && (
                <p className="text-[9px] text-text-faint mt-0.5">Country: {vatLiability.country_code}</p>
              )}
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-text-faint">Input VAT Paid</span>
              <span className="font-bold text-text">{formatMoney(inputVat)}</span>
            </div>
            <div className="border-t border-border pt-3 flex justify-between">
              <span className="font-bold text-sm">Net VAT Due</span>
              <span className="font-bold text-sm text-primary">{formatMoney(netVatDue)}</span>
            </div>
          </div>
        </div>

        <div className="theme-card rounded-xl border p-4">
          <h4 className="text-sm font-bold text-text mb-3">Country Breakdown</h4>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-text-faint">Filter Country</span>
              <span className="font-medium">{vatLiability?.country_code ?? "All"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-faint">VAT Type</span>
              <span className="font-medium">Output / Input</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-faint">Data Source</span>
              <span className="font-medium text-success">Live Ledger</span>
            </div>
          </div>
        </div>

         <div className="theme-card rounded-xl border p-4">
           <h4 className="text-sm font-bold text-text mb-3">Actions</h4>
           <div className="space-y-2">
             <Button variant="primary" onClick={onMarkRemitted}>
               Mark as Remitted
             </Button>
             <button onClick={() => exportVatCsv(vatLiability)} className="w-full rounded-lg bg-surface-2 px-3 py-2 text-xs text-text hover:bg-surface-3 transition">
               Generate ZATCA CSV
             </button>
             <button onClick={() => exportVatCsv(vatLiability, "xls")} className="w-full rounded-lg border border-border px-3 py-2 text-xs text-text hover:bg-surface-2 transition">
               Download Excel Report
             </button>
           </div>
         </div>
      </div>
    </div>
  );
}

function GatewayReconView({ data, exceptions, formatMoney }: { data: GatewayReconciliationItem[]; exceptions: GatewayException[]; formatMoney: (n: number) => string }) {
  const totalDiscrepancy = data.reduce((s, g) => s + g.discrepancy, 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-text">Gateway Reconciliation</h3>
        <div className={`text-xs font-bold ${Math.abs(totalDiscrepancy) < 0.01 ? "text-success" : "text-warning"}`}>
          {Math.abs(totalDiscrepancy) < 0.01 ? "All Reconciled" : `${formatMoney(totalDiscrepancy)} Discrepancy`}
        </div>
      </div>

      <div className="theme-card rounded-xl border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-surface-2">
            <tr>
              <th className="text-left p-2 font-semibold">Gateway</th>
              <th className="text-right p-2 font-semibold">Expected</th>
              <th className="text-right p-2 font-semibold">Settled</th>
              <th className="text-right p-2 font-semibold">Discrepancy</th>
              <th className="text-center p-2 font-semibold">Txns</th>
              <th className="text-left p-2 font-semibold">Last Settlement</th>
            </tr>
          </thead>
          <tbody>
            {data.map((gw) => (
              <tr key={gw.gateway_code} className="border-b border-border last:border-0">
                <td className="p-2 font-medium">{gw.gateway_code}</td>
                <td className="p-2 text-right">{formatMoney(gw.total_expected)}</td>
                <td className="p-2 text-right">{formatMoney(gw.total_settled)}</td>
                <td className={`p-2 text-right font-medium ${Math.abs(gw.discrepancy) < 0.01 ? "text-success" : "text-warning"}`}>
                  {formatMoney(gw.discrepancy)}
                </td>
                <td className="p-2 text-center">{gw.count}</td>
                <td className="p-2 text-text-faint text-xs">{gw.last_settlement_date?.slice(0, 10) ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

      {/* Gateway Settlement Exceptions */}
      <div className="flex items-center gap-2">
        <AlertTriangle className={`h-4 w-4 ${exceptions.length ? "text-warning" : "text-success"}`} />
        <h4 className="text-sm font-bold text-text">Settlement Exceptions Queue</h4>
        <span className={`text-[11px] px-2 py-0.5 rounded-full ${exceptions.length ? "bg-warning/20 text-warning" : "bg-success/20 text-success"}`}>
          {exceptions.length} open
        </span>
      </div>

      {exceptions.length === 0 ? (
        <div className="theme-card rounded-xl border p-4 text-center text-text-muted text-xs">
          No pending or flagged gateway settlements — all settlements matched.
        </div>
      ) : (
        <div className="theme-card rounded-xl border overflow-hidden">
          <div className="max-h-72 overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="bg-surface-2">
                <tr>
                  <th className="text-left p-2 font-semibold">Schedule #</th>
                  <th className="text-left p-2 font-semibold">Gateway</th>
                  <th className="text-right p-2 font-semibold">Amount</th>
                  <th className="text-center p-2 font-semibold">Status</th>
                  <th className="text-left p-2 font-semibold">Settlement Date</th>
                  <th className="text-left p-2 font-semibold">Country</th>
                </tr>
              </thead>
              <tbody>
                {exceptions.map((e) => (
                  <tr key={e.id} className="border-b border-border last:border-0">
                    <td className="p-2 font-mono text-xs">#{e.id}</td>
                    <td className="p-2 font-medium">{e.gateway_id}</td>
                    <td className="p-2 text-right">{formatMoney(e.amount)}</td>
                    <td className="p-2 text-center">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] ${e.status === "flagged" ? "bg-danger/20 text-danger" : "bg-warning/20 text-warning"}`}>{e.status}</span>
                    </td>
                    <td className="p-2 text-text-faint text-xs">{e.settlement_date?.slice(0, 10) ?? "—"}</td>
                    <td className="p-2 text-text-faint text-xs">{e.country_code ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function CODView({ remittances, formatMoney }: { remittances: CODRemittance[]; formatMoney: (n: number) => string }) {
  const pendingTotal = remittances.reduce((s, r) => s + (r.amount_expected - r.amount_remitted), 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-text">COD Remittance Tracking</h3>
        <span className="text-xs text-text-faint">{remittances.length} pending</span>
      </div>

      {remittances.length === 0 ? (
        <div className="theme-card rounded-xl border p-8 text-center text-text-muted">
          <DollarSign className="h-8 w-8 mx-auto mb-2 opacity-40" />
          <p className="text-sm">All COD remittances reconciled</p>
          <p className="text-xs text-text-faint mt-1">No pending remittances from logistics partners</p>
        </div>
      ) : (
        <>
          <div className="rounded-xl border border-warning/30 bg-warning/5 p-3 flex items-center justify-between">
            <span className="text-xs text-text">Total pending COD reconciliation</span>
            <span className="text-sm font-bold text-warning">{formatMoney(pendingTotal)}</span>
          </div>
          <div className="theme-card rounded-xl border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-surface-2">
                <tr>
                  <th className="text-left p-2 font-semibold">Logistics Partner</th>
                  <th className="text-right p-2 font-semibold">Expected</th>
                  <th className="text-right p-2 font-semibold">Remitted</th>
                  <th className="text-right p-2 font-semibold">Shortfall</th>
                  <th className="text-center p-2 font-semibold">Status</th>
                  <th className="text-left p-2 font-semibold">Date</th>
                </tr>
              </thead>
              <tbody>
                {remittances.map((r) => (
                  <tr key={r.id} className="border-b border-border last:border-0">
                    <td className="p-2 font-medium">{r.logistics_partner_name}</td>
                    <td className="p-2 text-right">{formatMoney(r.amount_expected)}</td>
                    <td className="p-2 text-right">{formatMoney(r.amount_remitted)}</td>
                    <td className="p-2 text-right font-medium text-warning">{formatMoney(r.amount_expected - r.amount_remitted)}</td>
                    <td className="p-2 text-center">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] ${
                        r.status === "reconciled" ? "bg-success/20 text-success" : "bg-warning/20 text-warning"
                      }`}>
                        {r.status}
                      </span>
                    </td>
                    <td className="p-2 text-text-faint text-xs">{r.remitted_at?.slice(0, 10) ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

function MakerCheckerModal({ batch, action, currentUser, onClose, onConfirmed }: {
  batch: PayoutBatch;
  action: "approve" | "dispatch";
  currentUser: { id: number; full_name: string } | null;
  onClose: () => void;
  onConfirmed: () => void;
}) {
  const addToast = useToastStore((s) => s.addToast);
  const [processing, setProcessing] = useState(false);
  const isMaker = currentUser && batch.created_by === currentUser.id;

  const handleConfirm = async () => {
    if (isMaker) {
      addToast("Maker-Checker violation: You cannot approve your own batch", "error");
      return;
    }
    const batchCountry = batch.country_code || "";
    setProcessing(true);
    try {
      const endpoint = action === "approve"
        ? `/admin/treasury/${batchCountry}/payouts/batches/${batch.id}/approve`
        : `/admin/treasury/${batchCountry}/payouts/batches/${batch.id}/dispatch`;
      const res = await apiFetch(endpoint, { method: "POST" });
      if (res.ok) {
        addToast(`Batch ${action === "approve" ? "approved" : "dispatched"} successfully`, "success");
        onConfirmed();
      } else {
        const err = await res.json().catch(() => ({}));
        addToast(err?.detail ?? `Failed to ${action} batch`, "error");
      }
    } catch {
      addToast("Network error", "error");
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay" onClick={onClose}>
      <div className="theme-modal-card p-5 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-2 mb-4">
          <Shield className="h-5 w-5 text-primary" />
          <h3 className="text-sm font-bold text-text">Maker-Checker Confirmation</h3>
        </div>

        <div className="space-y-2 text-xs text-text mb-4">
          <div className="flex justify-between">
            <span className="text-text-faint">Batch</span>
            <span className="font-medium">{batch.batch_number}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-faint">Amount</span>
            <span className="font-medium">{useCurrencyStore.getState().format(batch.total_amount)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-faint">Created By</span>
            <span className="font-medium">{batch.created_by_name ?? `User #${batch.created_by}`}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-faint">Action</span>
            <span className={`font-medium uppercase ${action === "approve" ? "text-success" : "text-primary"}`}>{action}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-faint">Current User</span>
            <span className="font-medium">{currentUser?.full_name ?? "—"}</span>
          </div>
          <div className="border-t border-border pt-2">
            <span className={`text-xs font-semibold ${isMaker ? "text-danger" : "text-success"}`}>
              {isMaker
                ? "✗ Cannot approve your own batch (Maker-Checker protocol)"
                : "✓ Different user — eligible to act as Checker"}
            </span>
          </div>
        </div>

        <div className="flex items-center justify-end gap-2">
          <button onClick={onClose} className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-text-muted hover:text-text transition">
            Cancel
          </button>
          <Button variant="primary" onClick={handleConfirm}
            disabled={processing || isMaker === true}>
            {processing ? <div className="animate-spin rounded-full h-3 w-3 border-2 border-white border-t-transparent" /> : <Shield className="h-3.5 w-3.5" />}
            Confirm {action === "approve" ? "Approval" : "Dispatch"}
          </Button>
        </div>
      </div>
    </div>
  );
}

interface ReconciliationItem {
  order_id: number;
  order_status: string;
  order_total: number;
  supplier_id: number | null;
  supplier_name?: string | null;
  payment_method: string | null;
  payment_status: string | null;
  payment_amount: number | null;
  logistics_partner: string | null;
  cod_remitted: number | null;
  cod_remittance_status: string | null;
  supplier_settlement_id: number | null;
  supplier_settlement_status: string | null;
  supplier_net_amount: number | null;
  supplier_payout_status: string | null;
  supplier_payout_amount: number | null;
  commission: { rate: number; amount: number } | null;
  stage: string;
}

function DetailField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-text-faint uppercase tracking-wide">{label}</p>
      <p className="font-semibold text-text tabular-nums">{value}</p>
    </div>
  );
}

function ReconciliationView({ filterCountry, formatMoney, forceRefresh, exceptions, supplierPayouts }: {
  filterCountry: string;
  formatMoney: (v: number) => string;
  forceRefresh: boolean;
  exceptions: GatewayException[];
  supplierPayouts: SupplierPayout[];
}) {
  const addToast = useToastStore((s) => s.addToast);
  const [pipeline, setPipeline] = useState<ReconciliationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "unsettled" | "settled">("all");
  const [search, setSearch] = useState("");
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [showCOD, setShowCOD] = useState(false);
  const [showSettle, setShowSettle] = useState(false);
  const [codForm, setCodForm] = useState({ order_id: 0, partner_id: 0, amount: 0, bank_reference: "" });
  const [settleForm, setSettleForm] = useState({ order_id: 0, supplier_id: 0, gross_amount: 0, commission_amount: 0, net_amount: 0 });
  const [saving, setSaving] = useState(false);

  const loadPipeline = useCallback(async () => {
    setLoading(true);
    try {
      const cc = filterCountry === "*" ? "consolidated" : filterCountry;
      const res = await apiFetch(`/admin/treasury/${cc}/reconciliation/pipeline`);
      if (res.ok) {
        const data = await res.json();
        setPipeline(Array.isArray(data.pipeline) ? data.pipeline : []);
      }
    } catch (e) {
      console.error("Failed to load reconciliation pipeline:", e);
    } finally {
      setLoading(false);
    }
  }, [filterCountry]);

  useEffect(() => { loadPipeline(); }, [loadPipeline, forceRefresh]);

  const handleRecordCOD = async () => {
    if (!codForm.order_id || !codForm.partner_id || !codForm.amount || !codForm.bank_reference) {
      addToast("Fill all COD fields", "error"); return;
    }
    setSaving(true);
    try {
      const cc = filterCountry === "*" ? "consolidated" : filterCountry;
      const res = await apiFetch(`/admin/treasury/${cc}/reconciliation/record-cod-remittance`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(codForm),
      });
      if (res.ok) {
        addToast("COD remittance recorded", "success");
        setShowCOD(false);
        setCodForm({ order_id: 0, partner_id: 0, amount: 0, bank_reference: "" });
        loadPipeline();
      } else {
        const err = await res.json().catch(() => ({}));
        addToast(err?.detail ?? "Failed to record COD", "error");
      }
    } catch { addToast("Network error", "error"); }
    finally { setSaving(false); }
  };

  const handleSettleSupplier = async () => {
    if (!settleForm.order_id || !settleForm.supplier_id || !settleForm.gross_amount || !settleForm.net_amount) {
      addToast("Fill all settlement fields", "error"); return;
    }
    setSaving(true);
    try {
      const cc = filterCountry === "*" ? "consolidated" : filterCountry;
      const res = await apiFetch(`/admin/treasury/${cc}/reconciliation/settle-supplier`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settleForm),
      });
      if (res.ok) {
        addToast("Supplier settlement recorded", "success");
        setShowSettle(false);
        setSettleForm({ order_id: 0, supplier_id: 0, gross_amount: 0, commission_amount: 0, net_amount: 0 });
        loadPipeline();
      } else {
        const err = await res.json().catch(() => ({}));
        addToast(err?.detail ?? "Failed to settle supplier", "error");
      }
    } catch { addToast("Network error", "error"); }
    finally { setSaving(false); }
  };

  const handleApproveSettlement = async (item: ReconciliationItem) => {
    if (!item.supplier_settlement_id) {
      addToast("No settlement to approve", "error"); return;
    }
    setSaving(true);
    try {
      const cc = filterCountry === "*" ? "consolidated" : filterCountry;
      const res = await apiFetch(`/admin/treasury/${cc}/reconciliation/approve-settlement`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ settlement_id: item.supplier_settlement_id }),
      });
      if (res.ok) {
        addToast("Settlement approved — Treasury → Supplier payout posted", "success");
        loadPipeline();
      } else {
        const err = await res.json().catch(() => ({}));
        addToast(err?.detail ?? "Failed to approve settlement", "error");
      }
    } catch { addToast("Network error", "error"); }
    finally { setSaving(false); }
  };

  const prefillCOD = (order: ReconciliationItem) => {
    setCodForm({ order_id: order.order_id, partner_id: 0, amount: order.order_total, bank_reference: "" });
    setShowCOD(true);
  };

  const prefillSettle = (order: ReconciliationItem) => {
    const commAmount = order.commission?.amount ?? 0;
    setSettleForm({
      order_id: order.order_id, supplier_id: order.supplier_id ?? 0,
      gross_amount: order.order_total,
      commission_amount: commAmount,
      net_amount: order.order_total - commAmount,
    });
    setShowSettle(true);
  };

  // ── Pipeline stage helpers (Order → Payment → Logistics/COD → Treasury → Supplier) ──
  const buildSteps = (item: ReconciliationItem) => {
    const orderDone = ["shipped", "delivered", "completed", "dispatched"].includes(item.order_status);
    const isCod = item.payment_method === "cod";
    const paymentDone = isCod ? !!item.cod_remittance_status : item.payment_status === "completed";
    const logisticsDone = isCod ? item.cod_remittance_status === "remitted" : orderDone;
    const settleDone = item.supplier_settlement_status === "settled" || item.supplier_settlement_status === "paid";
    const payoutDone = item.supplier_payout_status === "paid";

    return [
      { key: "order", label: "Order", done: orderDone },
      { key: "payment", label: isCod ? "COD Collected" : "Payment", done: paymentDone },
      { key: "logistics", label: isCod ? "COD Remit" : "Logistics", done: logisticsDone },
      { key: "settlement", label: "Settlement", done: settleDone },
      { key: "payout", label: "Supplier Paid", done: payoutDone },
    ];
  };

  const resolveAction = (item: ReconciliationItem): { label: string; tone: "warning" | "info" | "success"; onClick: () => void } | null => {
    if (item.payment_method === "cod" && item.cod_remittance_status !== "remitted") {
      return { label: "Record COD", tone: "warning", onClick: () => prefillCOD(item) };
    }
    if (!item.supplier_settlement_status) {
      return { label: "Settle Supplier", tone: "info", onClick: () => prefillSettle(item) };
    }
    if (item.supplier_settlement_status === "settled") {
      return { label: "Approve Payout", tone: "success", onClick: () => handleApproveSettlement(item) };
    }
    return null;
  };

  const stageColor: Record<string, string> = {
    order_dispatched: "bg-warning/20 text-warning",
    payment_received: "bg-info/20 text-info",
    cod_pending: "bg-warning/20 text-warning",
    cod_remitted: "bg-info/20 text-info",
    payout_processing: "bg-warning/20 text-warning",
    supplier_settled: "bg-success/20 text-success",
    supplier_paid: "bg-success/20 text-success",
    pending: "bg-text-faint/20 text-text-faint",
  };
  const stageLabel: Record<string, string> = {
    order_dispatched: "Dispatched", payment_received: "Paid", cod_pending: "COD Pending",
    cod_remitted: "COD Remitted", payout_processing: "Processing", supplier_settled: "Settled",
    supplier_paid: "Paid Out", pending: "Pending",
  };

  const visible = pipeline.filter((p) => {
    const payoutDone = p.supplier_payout_status === "paid";
    if (filter === "settled") return payoutDone;
    if (filter === "unsettled") return !payoutDone;
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      const hay = `${p.order_id} ${p.supplier_id ?? ""} ${p.logistics_partner ?? ""} ${p.payment_method ?? ""}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });

  const settledCount = pipeline.filter((p) => p.supplier_payout_status === "paid").length;
  const unsettledExposure = pipeline
    .filter((p) => p.supplier_payout_status !== "paid")
    .reduce((s, p) => s + (p.supplier_net_amount ?? p.order_total), 0);

  const summary = [
    { label: "In Pipeline", value: String(pipeline.length), icon: RefreshCw, tone: "text-primary" },
    { label: "Settled / Paid Out", value: String(settledCount), icon: ShieldCheck, tone: "text-success" },
    { label: "Unsettled Orders", value: String(pipeline.length - settledCount), icon: AlertTriangle, tone: "text-warning" },
    { label: "Payout Exposure", value: formatMoney(unsettledExposure), icon: Banknote, tone: "text-info" },
  ];

  return (
    <div className="space-y-5">
      {/* Settlement Exceptions banner */}
      {exceptions.length > 0 && (
        <div className="rounded-xl border border-warning/30 bg-warning/5 p-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-warning" />
            <span className="text-xs text-text">
              <strong>{exceptions.length} gateway settlement exceptions</strong> need reconciliation in the Gateway Recon tab.
            </span>
          </div>
          <span className="text-[11px] font-semibold text-warning">{formatMoney(exceptions.reduce((s, e) => s + e.amount, 0))} unmatched</span>
        </div>
      )}

      {/* Action Bar */}
      <div className="flex flex-wrap items-center gap-2">
        <Button variant="primary" className="rounded-lg px-3 py-1.5 text-xs font-semibold" onClick={() => setShowCOD(true)}>
          Record COD Remittance
        </Button>
        <Button variant="info" className="rounded-lg px-3 py-1.5 text-xs font-semibold" onClick={() => setShowSettle(true)}>
          Settle Supplier
        </Button>
        <button onClick={loadPipeline} className="rounded-lg border border-border px-3 py-1.5 text-xs font-semibold text-text-muted hover:text-text">
          <RefreshCw className="inline h-3.5 w-3.5" /> Refresh
        </button>
        <div className="flex items-center gap-1 rounded-lg border border-border px-2 py-1">
          <Search className="h-3.5 w-3.5 text-text-faint" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search order / supplier / partner"
            className="bg-transparent text-xs outline-none w-44 placeholder:text-text-faint"
          />
        </div>
        <div className="flex items-center gap-1 rounded-lg border border-border p-0.5">
          {(["all", "unsettled", "settled"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`rounded-md px-2.5 py-1 text-[11px] font-semibold capitalize transition ${filter === f ? "bg-primary text-primary-foreground" : "text-text-faint hover:text-text"}`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {summary.map((s) => (
          <div key={s.label} className="theme-card rounded-xl border p-3">
            <div className="flex items-center gap-2 mb-1">
              <s.icon className={`h-4 w-4 ${s.tone}`} />
              <span className="text-[11px] font-semibold text-text-faint uppercase">{s.label}</span>
            </div>
            <p className="text-xl font-bold text-text tabular-nums">{s.value}</p>
          </div>
        ))}
      </div>

      <div>
        <h3 className="text-sm font-bold text-text">Reconciliation Pipeline</h3>
        <p className="text-xs text-text-muted">Order → Payment → Logistics/COD → Treasury Settlement → Supplier Payout</p>
      </div>

      {loading ? (
        <div className="space-y-2">
          {[1,2,3].map(i => <div key={i} className="h-20 rounded-lg bg-surface-2 animate-pulse" />)}
        </div>
      ) : visible.length === 0 ? (
        <div className="theme-card rounded-xl border p-8 text-center text-text-muted">
          <RefreshCw className="h-8 w-8 mx-auto mb-2 opacity-40" />
          <p>No reconciliation records in this view</p>
        </div>
      ) : (
        <div className="space-y-2">
          {visible.map((item) => {
            const steps = buildSteps(item);
            const action = resolveAction(item);
            const currentIdx = steps.findIndex((s) => !s.done);
            const expanded = expandedId === item.order_id;
            const matchedPayout = supplierPayouts.find((p) => p.supplier_id === item.supplier_id && p.status === "paid");
            return (
              <div key={item.order_id} className="theme-card rounded-xl border p-3">
                <div className="flex items-center justify-between gap-3 flex-wrap">
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setExpandedId(expanded ? null : item.order_id)}
                      className="flex items-center gap-1 min-w-[5rem] text-left"
                    >
                      <ChevronDown className={`h-3.5 w-3.5 text-text-faint transition-transform ${expanded ? "rotate-180" : ""}`} />
                      <div>
                        <p className="text-xs font-bold text-text">#{item.order_id}</p>
                        <p className="text-[10px] text-text-muted">{item.order_status}</p>
                      </div>
                    </button>
                    <div>
                      <p className="text-[11px] font-semibold text-text tabular-nums">{formatMoney(item.order_total)}</p>
                      <p className="text-[10px] text-text-faint">{item.payment_method || "—"}</p>
                    </div>
                    {item.logistics_partner && (
                      <p className="text-[10px] text-text-muted hidden sm:block">🚚 {item.logistics_partner}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {action && (
                      <button onClick={action.onClick} className={`rounded px-2.5 py-1 text-[10px] font-semibold ${
                        action.tone === "warning" ? "bg-warning/20 text-warning hover:bg-warning/30"
                        : action.tone === "info" ? "bg-info/20 text-info hover:bg-info/30"
                        : "bg-success/20 text-success hover:bg-success/30"
                      }`}>
                        {action.label}
                      </button>
                    )}
                    <span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold ${stageColor[item.stage] || "bg-text-faint/20 text-text-faint"}`}>
                      {stageLabel[item.stage] || item.stage}
                    </span>
                  </div>
                </div>

                {/* 5-stage stepper */}
                <div className="mt-3 flex items-center gap-1">
                  {steps.map((step, i) => (
                    <div key={step.key} className="flex flex-1 items-center gap-1">
                      <div className="flex flex-col items-center gap-1 flex-1">
                        <div className={`flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-bold border ${
                          step.done ? "bg-success/20 border-success text-success"
                          : i === currentIdx ? "bg-warning/20 border-warning text-warning animate-pulse"
                          : "bg-surface-2 border-border text-text-faint"
                        }`}>
                          {step.done ? "✓" : i + 1}
                        </div>
                        <span className={`text-[9px] text-center leading-tight ${step.done ? "text-success" : i === currentIdx ? "text-warning" : "text-text-faint"}`}>{step.label}</span>
                      </div>
                      {i < steps.length - 1 && (
                        <div className={`h-0.5 flex-1 rounded ${steps[i + 1].done || step.done ? "bg-success/40" : "bg-border"}`} />
                      )}
                    </div>
                  ))}
                </div>

                {/* Expandable detail */}
                {expanded && (
                  <div className="mt-3 grid gap-2 rounded-lg border border-border bg-surface-2 p-3 sm:grid-cols-2 lg:grid-cols-4 text-[11px]">
                    <DetailField label="Supplier" value={item.supplier_name ? `${item.supplier_name}` : `Supplier #${item.supplier_id ?? "—"}`} />
                    <DetailField label="Payment" value={`${item.payment_status ?? "—"}${item.payment_amount != null ? ` · ${formatMoney(item.payment_amount)}` : ""}`} />
                    <DetailField label="Commission" value={item.commission ? `${item.commission.rate}% · ${formatMoney(item.commission.amount)}` : "—"} />
                    <DetailField label="Supplier Net" value={item.supplier_net_amount != null ? formatMoney(item.supplier_net_amount) : "—"} />
                    <DetailField label="Settlement" value={item.supplier_settlement_status ? `#${item.supplier_settlement_id} · ${item.supplier_settlement_status}` : "Not settled"} />
                    <DetailField label="Payout" value={item.supplier_payout_status ? `${item.supplier_payout_status}${item.supplier_payout_amount != null ? ` · ${formatMoney(item.supplier_payout_amount)}` : ""}` : "—"} />
                    <DetailField label="COD Remittance" value={item.cod_remittance_status ? `${item.cod_remittance_status}${item.cod_remitted != null ? ` · ${formatMoney(item.cod_remitted)}` : ""}` : "—"} />
                    <DetailField label="Matched Payout" value={matchedPayout ? `#${matchedPayout.id} · ${matchedPayout.status}` : "No payout record"} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* COD Remittance Modal */}
      {showCOD && (
        <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay" onClick={() => setShowCOD(false)}>
          <div className="theme-modal-card p-5 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-2 mb-4">
              <DollarSign className="h-5 w-5 text-primary" />
              <h3 className="text-sm font-bold text-text">Record COD Remittance</h3>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-[11px] font-semibold text-text-faint">Order ID</label>
                <input type="number" value={codForm.order_id || ""} onChange={(e) => setCodForm(p => ({ ...p, order_id: parseInt(e.target.value) || 0 }))} className="theme-input w-full rounded-lg border px-3 py-2 text-xs" />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-text-faint">Logistics Partner ID</label>
                <input type="number" value={codForm.partner_id || ""} onChange={(e) => setCodForm(p => ({ ...p, partner_id: parseInt(e.target.value) || 0 }))} className="theme-input w-full rounded-lg border px-3 py-2 text-xs" />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-text-faint">Amount</label>
                <input type="number" step="0.01" value={codForm.amount || ""} onChange={(e) => setCodForm(p => ({ ...p, amount: parseFloat(e.target.value) || 0 }))} className="theme-input w-full rounded-lg border px-3 py-2 text-xs" />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-text-faint">Bank Reference</label>
                <input value={codForm.bank_reference} onChange={(e) => setCodForm(p => ({ ...p, bank_reference: e.target.value }))} className="theme-input w-full rounded-lg border px-3 py-2 text-xs" />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button onClick={() => setShowCOD(false)} className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-text-muted">Cancel</button>
                <Button variant="primary" onClick={handleRecordCOD} disabled={saving}>
                  {saving ? "Saving..." : "Record COD"}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Supplier Settlement Modal */}
      {showSettle && (
        <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay" onClick={() => setShowSettle(false)}>
          <div className="theme-modal-card p-5 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="h-5 w-5 text-info" />
              <h3 className="text-sm font-bold text-text">Settle Supplier</h3>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-[11px] font-semibold text-text-faint">Order ID</label>
                <input type="number" value={settleForm.order_id || ""} onChange={(e) => setSettleForm(p => ({ ...p, order_id: parseInt(e.target.value) || 0 }))} className="theme-input w-full rounded-lg border px-3 py-2 text-xs" />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-text-faint">Supplier ID</label>
                <input type="number" value={settleForm.supplier_id || ""} onChange={(e) => setSettleForm(p => ({ ...p, supplier_id: parseInt(e.target.value) || 0 }))} className="theme-input w-full rounded-lg border px-3 py-2 text-xs" />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-text-faint">Gross Amount</label>
                <input type="number" step="0.01" value={settleForm.gross_amount || ""} onChange={(e) => setSettleForm(p => ({ ...p, gross_amount: parseFloat(e.target.value) || 0 }))} className="theme-input w-full rounded-lg border px-3 py-2 text-xs" />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-text-faint">Commission Amount</label>
                <input type="number" step="0.01" value={settleForm.commission_amount || ""} onChange={(e) => setSettleForm(p => ({ ...p, commission_amount: parseFloat(e.target.value) || 0 }))} className="theme-input w-full rounded-lg border px-3 py-2 text-xs" />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-text-faint">Net Amount</label>
                <input type="number" step="0.01" value={settleForm.net_amount || ""} onChange={(e) => setSettleForm(p => ({ ...p, net_amount: parseFloat(e.target.value) || 0 }))} className="theme-input w-full rounded-lg border px-3 py-2 text-xs" />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button onClick={() => setShowSettle(false)} className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-text-muted">Cancel</button>
                <Button variant="info" className="rounded-lg px-3 py-1.5 text-xs font-semibold disabled:opacity-50" onClick={handleSettleSupplier} disabled={saving}>
                  {saving ? "Saving..." : "Settle Supplier"}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function exportVatCsv(vat: VATLiability | null, format: "csv" | "xls" = "csv") {
  if (!vat) return;
  const net = vat.net_vat_due ?? vat.output_vat - vat.input_vat;
  const rows = [
    ["Field", "Value"],
    ["Period", vat.period ?? "current"],
    ["Country", vat.country_code ?? "ALL"],
    ["Output VAT", String(vat.output_vat)],
    ["Input VAT", String(vat.input_vat)],
    ["Net VAT Due", String(net)],
  ];
  const content = rows.map((r) => r.join(",")).join("\n");
  const blob = new Blob([content], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `vat-${vat.period ?? "current"}-${vat.country_code ?? "all"}.${format === "xls" ? "csv" : "csv"}`;
  a.click();
  URL.revokeObjectURL(url);
}

function PaymentsView({ txns, gatewayRecon, gatewayExceptions, formatMoney, startDate, endDate, onStartChange, onEndChange }: {
  txns: PaymentTxn[];
  gatewayRecon: GatewayReconciliationItem[];
  gatewayExceptions: GatewayException[];
  formatMoney: (n: number) => string;
  startDate: string;
  endDate: string;
  onStartChange: (v: string) => void;
  onEndChange: (v: string) => void;
}) {
  const [methodFilter, setMethodFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const totalCollected = txns.filter((t) => t.status === "captured" || t.status === "paid").reduce((s, t) => s + t.amount, 0);
  const captured = txns.filter((t) => t.status === "captured" || t.status === "paid").length;
  const pending = txns.filter((t) => t.status === "pending" || t.status === "processing").length;
  const failed = txns.filter((t) => t.status === "failed" || t.status === "refunded" || t.status === "cancelled").length;

  const methods = Array.from(new Set(txns.map((t) => t.payment_method).filter(Boolean) as string[]));
  const providers = Array.from(new Set(txns.map((t) => t.provider).filter(Boolean) as string[]));

  const filtered = txns.filter((t) => {
    if (methodFilter !== "all" && (t.payment_method || "") !== methodFilter) return false;
    if (statusFilter !== "all" && (t.status || "") !== statusFilter) return false;
    return true;
  });

  const reconDiscrepancy = gatewayRecon.reduce((s, g) => s + g.discrepancy, 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h3 className="text-sm font-bold text-text">Payment Transactions</h3>
        <div className="flex items-center gap-2 text-xs">
          <input type="date" value={startDate} onChange={(e) => onStartChange(e.target.value)} className="theme-input rounded-lg border px-2 py-1" />
          <span className="text-text-faint">to</span>
          <input type="date" value={endDate} onChange={(e) => onEndChange(e.target.value)} className="theme-input rounded-lg border px-2 py-1" />
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="theme-card rounded-xl border p-4">
          <p className="text-[11px] uppercase text-text-faint font-semibold">Collected</p>
          <p className="text-2xl font-bold text-success">{formatMoney(totalCollected)}</p>
          <p className="text-[10px] text-text-faint">{txns.length} transactions</p>
        </div>
        <div className="theme-card rounded-xl border p-4">
          <p className="text-[11px] uppercase text-text-faint font-semibold">Captured</p>
          <p className="text-2xl font-bold text-text">{captured}</p>
        </div>
        <div className="theme-card rounded-xl border p-4">
          <p className="text-[11px] uppercase text-text-faint font-semibold">Pending / Processing</p>
          <p className="text-2xl font-bold text-warning">{pending}</p>
        </div>
        <div className="theme-card rounded-xl border p-4">
          <p className="text-[11px] uppercase text-text-faint font-semibold">Failed / Refunded</p>
          <p className="text-2xl font-bold text-danger">{failed}</p>
        </div>
      </div>

      {/* Gateway settlement reconciliation banner */}
      <div className={`rounded-xl border p-3 flex items-center justify-between flex-wrap gap-2 ${gatewayExceptions.length || Math.abs(reconDiscrepancy) >= 0.01 ? "border-warning/30 bg-warning/5" : "border-success/30 bg-success/5"}`}>
        <div className="flex items-center gap-2">
          <CreditCard className={`h-4 w-4 ${gatewayExceptions.length || Math.abs(reconDiscrepancy) >= 0.01 ? "text-warning" : "text-success"}`} />
          <span className="text-xs text-text">
            Gateway settlement reconciliation: <strong>{gatewayExceptions.length} exceptions</strong> · {formatMoney(reconDiscrepancy)} unmatched
          </span>
        </div>
        <span className={`text-[11px] font-semibold ${gatewayExceptions.length || Math.abs(reconDiscrepancy) >= 0.01 ? "text-warning" : "text-success"}`}>
          {gatewayExceptions.length || Math.abs(reconDiscrepancy) >= 0.01 ? "Review Gateway Recon tab" : "Settled"}
        </span>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex items-center gap-1 text-[11px] text-text-faint">
          <Filter className="h-3.5 w-3.5" /> Method:
        </div>
        <select value={methodFilter} onChange={(e) => setMethodFilter(e.target.value)} className="theme-input rounded-lg border px-2 py-1 text-xs">
          <option value="all">All</option>
          {methods.map((m) => <option key={m} value={m}>{m}</option>)}
        </select>
        <div className="flex items-center gap-1 text-[11px] text-text-faint">
          Status:
        </div>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="theme-input rounded-lg border px-2 py-1 text-xs">
          <option value="all">All</option>
          {Array.from(new Set(txns.map((t) => t.status).filter(Boolean) as string[])).map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        {providers.length > 0 && (
          <span className="text-[10px] text-text-faint ml-2">Providers: {providers.join(", ")}</span>
        )}
      </div>

      <div className="theme-card rounded-xl border overflow-hidden">
        <div className="max-h-[55vh] overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="bg-surface-2 sticky top-0">
              <tr>
                <th className="text-left p-2 font-semibold">#</th>
                <th className="text-left p-2 font-semibold">Order</th>
                <th className="text-left p-2 font-semibold">Method</th>
                <th className="text-left p-2 font-semibold">Provider</th>
                <th className="text-right p-2 font-semibold">Amount</th>
                <th className="text-center p-2 font-semibold">Status</th>
                <th className="text-left p-2 font-semibold">Date</th>
                <th className="text-left p-2 font-semibold">Country</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr><td colSpan={8} className="p-4 text-center text-text-muted text-xs">No payment transactions match the filters</td></tr>
              ) : filtered.map((t) => (
                <tr key={t.id} className="border-b border-border last:border-0">
                  <td className="p-2 font-mono text-xs">#{t.id}</td>
                  <td className="p-2">{t.order_id ?? "—"}</td>
                  <td className="p-2 capitalize">{t.payment_method ?? "—"}</td>
                  <td className="p-2">{t.provider ?? "—"}</td>
                  <td className="p-2 text-right font-medium">{formatMoney(t.amount)}</td>
                  <td className="p-2 text-center">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] ${(t.status === "captured" || t.status === "paid") ? "bg-success/20 text-success" : (t.status === "failed" || t.status === "refunded" || t.status === "cancelled") ? "bg-danger/20 text-danger" : "bg-warning/20 text-warning"}`}>{t.status ?? "—"}</span>
                  </td>
                  <td className="p-2 text-text-faint text-xs">{t.created_at?.slice(0, 10) ?? "—"}</td>
                  <td className="p-2 text-text-faint text-xs">{t.country_code ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function LiabilitiesView({ liabilities, formatMoney }: { liabilities: LiabilityExposure | null; formatMoney: (n: number) => string }) {
  const items = liabilities
    ? [
        { label: "Supplier Payables", value: liabilities.supplier_payables, color: "text-warning" },
        { label: "Logistics Payables", value: liabilities.logistics_payables, color: "text-info" },
        { label: "VAT Payable", value: liabilities.vat_payable, color: "text-danger" },
      ]
    : [];
  const total = items.reduce((s, i) => s + i.value, 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-text">Liability Exposure</h3>
        <span className="text-xs text-text-faint">Outstanding financial obligations</span>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {items.map((i) => (
          <div key={i.label} className="theme-card rounded-xl border p-4">
            <p className="text-[11px] uppercase text-text-faint font-semibold">{i.label}</p>
            <p className={`text-2xl font-bold ${i.color}`}>{formatMoney(i.value)}</p>
          </div>
        ))}
        <div className="theme-card rounded-xl border p-4">
          <p className="text-[11px] uppercase text-text-faint font-semibold">Total Exposure</p>
          <p className="text-2xl font-bold text-text">{formatMoney(total)}</p>
        </div>
      </div>
      <div className="theme-card rounded-xl border p-4 text-xs text-text-faint">
        Supplier &amp; logistics payables represent owed disbursements; VAT payable is the net tax obligation due to tax authorities. Reconcile against Payout Batches and the VAT Remittance tab.
      </div>
    </div>
  );
}

function PendingEntriesView({ entries, formatMoney, currentUser, filterCountry, onApproved }: {
  entries: PendingEntry[];
  formatMoney: (n: number) => string;
  currentUser: { id: number; full_name: string } | null;
  filterCountry: string;
  onApproved: () => void;
}) {
  const addToast = useToastStore((s) => s.addToast);
  const [busy, setBusy] = useState<number | null>(null);
  const [rejectId, setRejectId] = useState<number | null>(null);
  const [reason, setReason] = useState("");

  const base = filterCountry === "*" ? "/admin/treasury" : `/admin/treasury/${filterCountry}`;

  const handleApprove = async (id: number, createdBy: number) => {
    if (currentUser && currentUser.id === createdBy) {
      addToast("Maker-Checker: cannot approve your own entry", "error");
      return;
    }
    setBusy(id);
    try {
      const res = await apiFetch(`${base}/ledger/pending/${id}/approve`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ approver_id: currentUser?.id ?? 0 }),
      });
      if (res.ok) { addToast("Entry approved", "success"); onApproved(); }
      else { const err = await res.json().catch(() => ({})); addToast(err?.detail ?? "Approve failed", "error"); }
    } catch { addToast("Network error", "error"); }
    finally { setBusy(null); }
  };

  const handleReject = async (id: number) => {
    if (!reason.trim()) { addToast("Enter a reason", "error"); return; }
    setBusy(id);
    try {
      const res = await apiFetch(`${base}/ledger/pending/${id}/reject`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rejected_by: currentUser?.id ?? 0, reason }),
      });
      if (res.ok) { addToast("Entry rejected", "success"); setRejectId(null); setReason(""); onApproved(); }
      else { const err = await res.json().catch(() => ({})); addToast(err?.detail ?? "Reject failed", "error"); }
    } catch { addToast("Network error", "error"); }
    finally { setBusy(null); }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-text">Pending Journal Entries</h3>
        <span className="text-xs text-text-faint">Maker-Checker dual control</span>
      </div>
      <div className="theme-card rounded-xl border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-surface-2">
            <tr>
              <th className="text-left p-2 font-semibold">#</th>
              <th className="text-left p-2 font-semibold">Description</th>
              <th className="text-left p-2 font-semibold">Source</th>
              <th className="text-left p-2 font-semibold">Country</th>
              <th className="text-center p-2 font-semibold">Threshold</th>
              <th className="text-left p-2 font-semibold">Created By</th>
              <th className="text-center p-2 font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody>
            {entries.length === 0 ? (
              <tr><td colSpan={7} className="p-4 text-center text-text-muted text-xs">No pending entries</td></tr>
            ) : entries.map((e) => {
              const selfMade = currentUser ? currentUser.id === e.created_by : false;
              return (
                <tr key={e.id} className="border-b border-border last:border-0">
                  <td className="p-2 font-mono text-xs">#{e.id}</td>
                  <td className="p-2">{e.description ?? "—"}</td>
                  <td className="p-2 capitalize">{e.source ?? "—"}</td>
                  <td className="p-2 text-xs">{e.country_code ?? "—"}</td>
                  <td className="p-2 text-center">
                    {e.amount_threshold_triggered
                      ? <span className="px-2 py-0.5 rounded-full bg-warning/20 text-warning text-[10px]">High</span>
                      : <span className="text-text-faint text-[10px]">—</span>}
                  </td>
                  <td className="p-2 text-xs">{e.created_by}{selfMade ? " (you)" : ""}</td>
                  <td className="p-2">
                    <div className="flex items-center justify-center gap-1">
                      <Button variant="primary" className="rounded-lg px-2 py-1 text-[10px] font-medium disabled:opacity-40" onClick={() => handleApprove(e.id, e.created_by)} disabled={busy === e.id || selfMade}>
                        {busy === e.id ? "..." : "Approve"}
                      </Button>
                      <button onClick={() => setRejectId(rejectId === e.id ? null : e.id)} disabled={busy === e.id} className="rounded-lg border border-border px-2 py-1 text-[10px] font-medium text-text-muted disabled:opacity-40">
                        Reject
                      </button>
                    </div>
                    {rejectId === e.id && (
                      <div className="mt-2 flex gap-1">
                        <input value={reason} onChange={(ev) => setReason(ev.target.value)} placeholder="Reason" className="theme-input flex-1 rounded border px-2 py-1 text-[10px]" />
                        <Button variant="danger" className="rounded px-2 py-1 text-[10px] font-medium" onClick={() => handleReject(e.id)}>Send</Button>
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function GenerateBatchModal({ filterCountry, assignedCountries, onClose, onGenerated }: {
  filterCountry: string;
  assignedCountries: { code: string; name: string }[];
  onClose: () => void;
  onGenerated: () => void;
}) {
  const addToast = useToastStore((s) => s.addToast);
  const { selectedCountry } = useAdminCountry();
  const countries = assignedCountries.length ? assignedCountries : (selectedCountry ? [selectedCountry] : []);
  const [country, setCountry] = useState<string>(filterCountry !== "*" ? filterCountry : (countries[0]?.code ?? "AE"));
  const [cutoff, setCutoff] = useState<string>(new Date().toISOString().slice(0, 10));
  const [saving, setSaving] = useState(false);

  const handleGenerate = async () => {
    if (!country) { addToast("Select a country", "error"); return; }
    setSaving(true);
    try {
      const res = await apiFetch(`/admin/treasury/payouts/batches/generate`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ country_code: country, cutoff_date: cutoff }),
      });
      if (res.ok) { addToast("Payout batch generated", "success"); onGenerated(); }
      else { const err = await res.json().catch(() => ({})); addToast(err?.detail ?? "Generate failed", "error"); }
    } catch { addToast("Network error", "error"); }
    finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay" onClick={onClose}>
      <div className="theme-modal-card p-5 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-2 mb-4">
          <Download className="h-5 w-5 text-primary" />
          <h3 className="text-sm font-bold text-text">Generate Payout Batch</h3>
        </div>
        <div className="space-y-3">
          <div>
            <label className="text-[11px] font-semibold text-text-faint">Country</label>
            <select value={country} onChange={(e) => setCountry(e.target.value)} className="theme-input w-full rounded-lg border px-3 py-2 text-xs">
              {countries.map((c) => (<option key={c.code} value={c.code}>{c.name} ({c.code})</option>))}
            </select>
          </div>
          <div>
            <label className="text-[11px] font-semibold text-text-faint">Cutoff Date</label>
            <input type="date" value={cutoff} onChange={(e) => setCutoff(e.target.value)} className="theme-input w-full rounded-lg border px-3 py-2 text-xs" />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button onClick={onClose} className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-text-muted">Cancel</button>
            <Button variant="primary" onClick={handleGenerate} disabled={saving}>
              {saving ? "Generating..." : "Generate"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function VatRemitModal({ vatLiability, currentUser, onClose, onRemitted }: {
  vatLiability: VATLiability | null;
  currentUser: { id: number; full_name: string } | null;
  onClose: () => void;
  onRemitted: () => void;
}) {
  const addToast = useToastStore((s) => s.addToast);
  const formatMoney = useCurrencyStore((s) => s.format);
  const netDue = vatLiability?.net_vat_due ?? (vatLiability ? vatLiability.output_vat - vatLiability.input_vat : 0);
  const [amount, setAmount] = useState<string>(String(netDue));
  const [periodEnd, setPeriodEnd] = useState<string>(new Date().toISOString().slice(0, 10));
  const [notes, setNotes] = useState<string>("");
  const [saving, setSaving] = useState(false);

  const handleRemit = async () => {
    const amt = parseFloat(amount);
    if (!amt || amt <= 0) { addToast("Enter a valid amount", "error"); return; }
    setSaving(true);
    try {
      const res = await apiFetch(`/cash-management/admin/vat-remittances`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          amount_remitted: amt,
          amount: amt,
          period_end: periodEnd,
          notes: notes || `VAT remittance ${vatLiability?.period ?? "current"}`,
          country_code: vatLiability?.country_code,
        }),
      });
      if (res.ok) { addToast("VAT remittance recorded", "success"); onRemitted(); }
      else { const err = await res.json().catch(() => ({})); addToast(err?.detail ?? "Remit failed", "error"); }
    } catch { addToast("Network error", "error"); }
    finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay" onClick={onClose}>
      <div className="theme-modal-card p-5 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-2 mb-4">
          <Shield className="h-5 w-5 text-primary" />
          <h3 className="text-sm font-bold text-text">Record VAT Remittance</h3>
        </div>
        <div className="space-y-3">
          <div>
            <label className="text-[11px] font-semibold text-text-faint">Net VAT Due</label>
            <p className="text-lg font-bold text-text">{formatMoney(netDue)}</p>
          </div>
          <div>
            <label className="text-[11px] font-semibold text-text-faint">Amount Remitted</label>
            <input type="number" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} className="theme-input w-full rounded-lg border px-3 py-2 text-xs" />
          </div>
          <div>
            <label className="text-[11px] font-semibold text-text-faint">Period End</label>
            <input type="date" value={periodEnd} onChange={(e) => setPeriodEnd(e.target.value)} className="theme-input w-full rounded-lg border px-3 py-2 text-xs" />
          </div>
          <div>
            <label className="text-[11px] font-semibold text-text-faint">Notes</label>
            <input value={notes} onChange={(e) => setNotes(e.target.value)} className="theme-input w-full rounded-lg border px-3 py-2 text-xs" />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button onClick={onClose} className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-text-muted">Cancel</button>
            <Button variant="primary" onClick={handleRemit} disabled={saving}>
              {saving ? "Saving..." : "Record Remittance"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}


