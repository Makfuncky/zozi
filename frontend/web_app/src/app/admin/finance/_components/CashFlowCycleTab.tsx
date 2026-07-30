"use client";
import { useEffect, useState } from "react";
import {
  Wallet, TrendingUp, DollarSign, RefreshCw, Shield, Truck, CreditCard,
  ArrowRight, Building2, CheckCircle2, Clock,
} from "@/lib/icons";
import { useAuth } from "@/lib/useAuth";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useAdminCountry } from "@/lib/useAdminCountry";
import { motion } from "framer-motion";

interface FinanceMetrics {
  free_cash: number;
  total_liabilities: number;
  total_revenue: number;
  net_income: number;
  pending_payouts: number;
  total_pending_settlements: number;
  total_paid_out: number;
}

interface CashPositionItem {
  slug: string;
  name: string;
  account_type: string;
  balance: number;
  currency: string;
  gl_account_code: string;
}

export default function CashFlowCycleTab() {
  const { user } = useAuth();
  const formatMoney = useCurrencyStore((s) => s.format);
  const { selectedCountry, isGlobalView } = useAdminCountry();
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState<FinanceMetrics | null>(null);
  const [cashPositions, setCashPositions] = useState<CashPositionItem[]>([]);

  useEffect(() => {
    const loadFinanceData = async () => {
      setLoading(true);
      try {
        const metricsUrl = isGlobalView || !selectedCountry?.code
          ? "/finance/dashboard/metrics"
          : `/finance/dashboard/metrics?country_code=${selectedCountry.code}`;
        const cashUrl = isGlobalView || !selectedCountry?.code
          ? "/finance/cash-position"
          : `/finance/cash-position?country_code=${selectedCountry.code}`;

        const [metricsRes, cashRes] = await Promise.all([
          apiFetch(metricsUrl),
          apiFetch(cashUrl),
        ]);

        if (metricsRes.ok) setMetrics(await metricsRes.json());
        if (cashRes.ok) {
          const cashData = await cashRes.json();
          setCashPositions(Array.isArray(cashData) ? cashData : cashData.buckets ?? []);
        }
      } catch (err) {
        console.error("Failed to load finance data:", err);
      } finally {
        setLoading(false);
      }
    };
    loadFinanceData();
  }, [selectedCountry, isGlobalView]);

  if (loading) {
    return (
      <PanelContent title="Cash Flow & Cycle">
        <PanelLoadingState count={4} blockClassName="h-24 rounded-xl bg-surface-2 animate-pulse" />
      </PanelContent>
    );
  }

  return (
    <PanelContent title="Cash Flow & Cycle" className="space-y-6">
      {/* Country Scope Indicator */}
      <div className="flex items-center gap-2 text-xs text-text-faint">
        <Shield className="h-3 w-3" />
        <span>{isGlobalView ? "Global View — All Countries" : `Country: ${selectedCountry?.name || selectedCountry?.code}`}</span>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Free Cash", value: metrics?.free_cash ?? 0, icon: Wallet, color: "text-primary" },
          { label: "Revenue", value: metrics?.total_revenue ?? 0, icon: TrendingUp, color: "text-success" },
          { label: "Pending Payouts", value: metrics?.pending_payouts ?? metrics?.total_pending_settlements ?? 0, icon: Clock, color: "text-warning" },
          { label: "Total Paid Out", value: metrics?.total_paid_out ?? 0, icon: CheckCircle2, color: "text-info" },
        ].map((card, idx) => (
          <motion.div key={card.label} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.05 }} className="theme-card rounded-xl border p-4">
            <div className="flex items-center gap-2 mb-1">
              <card.icon className={`h-4 w-4 ${card.color}`} />
              <span className="text-[11px] font-semibold text-text-faint uppercase">{card.label}</span>
            </div>
            <p className="text-2xl font-bold tabular-nums text-text">{formatMoney(card.value)}</p>
          </motion.div>
        ))}
      </div>

      {/* ── Cash Flow Cycle: Pay by Card ───────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="theme-card rounded-xl border overflow-hidden">
        <div className="bg-primary/10 px-5 py-3 border-b border-border">
          <h3 className="text-sm font-bold text-text flex items-center gap-2">
            <CreditCard className="h-4 w-4 text-primary" />
            Pay by Card — Collection & Payout Cycle
          </h3>
        </div>
        <div className="p-5">
          <div className="relative grid gap-4 md:grid-cols-5">
            {[
              { step: "1", label: "Customer Pays Online", detail: "Payment captured via Stripe/Tap gateway", icon: CreditCard, color: "bg-primary/15 text-primary border-primary/30" },
              { step: "2", label: "Gateway Settlement", detail: "Funds arrive in Zozi merchant account (T+1–3)", icon: Building2, color: "bg-info/15 text-info border-info/30" },
              { step: "3", label: "Zozi Revenue Split", detail: "Deduct gateway fee (2.5%) + VAT (5%) + Zozi commission (varies)", icon: DollarSign, color: "bg-warning/15 text-warning border-warning/30" },
              { step: "4", label: "Supplier Payout (T+10)", detail: "Net amount sent to supplier bank account after 10-day hold", icon: Wallet, color: "bg-success/15 text-success border-success/30" },
              { step: "5", label: "Logistics Payout", detail: "Pickup + delivery charges settled to logistics partner", icon: Truck, color: "bg-accent/15 text-accent border-accent/30" },
            ].map((item, idx) => (
              <div key={item.step} className="relative">
                <div className={`rounded-xl border-2 p-4 ${item.color}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-background/80 text-xs font-bold">{item.step}</span>
                    <span className="text-[10px] font-semibold uppercase text-text-faint">{item.label}</span>
                  </div>
                  <p className="text-[11px] text-text-muted leading-5">{item.detail}</p>
                </div>
                {idx < 4 && (
                  <div className="hidden md:block absolute -right-3 top-1/2 -translate-y-1/2 z-10">
                    <ArrowRight className="h-5 w-5 text-text-faint" />
                  </div>
                )}
              </div>
            ))}
          </div>
          <div className="mt-4 rounded-lg bg-surface-2 p-3 text-xs text-text-muted">
            <span className="font-semibold text-text">Breakdown:</span> Customer pays <span className="font-semibold text-text">Product Price + VAT + Delivery</span> →
            Gateway takes 2.5% + fixed fee → Zozi deducts commission (supplier or product-based) →
            Supplier receives net amount after 10 days → Logistics partner receives delivery fees
          </div>
        </div>
      </motion.div>

      {/* ── Cash Flow Cycle: Cash on Delivery ────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }} className="theme-card rounded-xl border overflow-hidden">
        <div className="bg-accent/10 px-5 py-3 border-b border-border">
          <h3 className="text-sm font-bold text-text flex items-center gap-2">
            <Truck className="h-4 w-4 text-accent" />
            Cash on Delivery — Collection & Payout Cycle
          </h3>
        </div>
        <div className="p-5">
          <div className="relative grid gap-4 md:grid-cols-5">
            {[
              { step: "1", label: "Customer Pays COD", detail: "Cash collected by logistics partner at delivery", icon: Truck, color: "bg-accent/15 text-accent border-accent/30" },
              { step: "2", label: "Logistics Remits to Zozi", detail: "Partner deposits collected amount to Zozi bank (T+3–7)", icon: Building2, color: "bg-warning/15 text-warning border-warning/30" },
              { step: "3", label: "Zozi Revenue Split", detail: "Deduct VAT (5%) + Zozi commission + logistics delivery fee", icon: DollarSign, color: "bg-warning/15 text-warning border-warning/30" },
              { step: "4", label: "Supplier Payout (T+10)", detail: "Product net amount sent after 10-day hold", icon: Wallet, color: "bg-success/15 text-success border-success/30" },
              { step: "5", label: "Logistics Settlement", detail: "Delivery charges released after remittance confirmed", icon: CheckCircle2, color: "bg-info/15 text-info border-info/30" },
            ].map((item, idx) => (
              <div key={item.step} className="relative">
                <div className={`rounded-xl border-2 p-4 ${item.color}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-background/80 text-xs font-bold">{item.step}</span>
                    <span className="text-[10px] font-semibold uppercase text-text-faint">{item.label}</span>
                  </div>
                  <p className="text-[11px] text-text-muted leading-5">{item.detail}</p>
                </div>
                {idx < 4 && (
                  <div className="hidden md:block absolute -right-3 top-1/2 -translate-y-1/2 z-10">
                    <ArrowRight className="h-5 w-5 text-text-faint" />
                  </div>
                )}
              </div>
            ))}
          </div>
          <div className="mt-4 rounded-lg bg-surface-2 p-3 text-xs text-text-muted">
            <span className="font-semibold text-text">Breakdown:</span> Customer pays <span className="font-semibold text-text">Product Price + VAT + Delivery</span> to logistics partner →
            Partner remits total to Zozi → Zozi deducts VAT + commission + logistics fees →
            Supplier receives product net after 10 days → Logistics partner receives remaining delivery fees
          </div>
        </div>
      </motion.div>

      {/* ── Cash Position ─────────────────────────────────────────── */}
      {cashPositions.length > 0 && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="theme-card rounded-xl border p-4">
          <h3 className="text-sm font-bold text-text mb-3 flex items-center gap-2">
            <Building2 className="h-4 w-4 text-primary" />
            Cash Position by Account
          </h3>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {cashPositions.map((item) => (
              <div key={item.slug} className="rounded-lg border border-border bg-surface-2 p-3">
                <p className="text-[11px] text-text-faint uppercase">{item.name}</p>
                <p className="text-lg font-bold text-text tabular-nums">{formatMoney(item.balance)}</p>
                <p className="text-[10px] text-text-faint">{item.gl_account_code}</p>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* ── Info: How Payouts Work ────────────────────────────────── */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.35 }} className="theme-card rounded-xl border p-5">
        <h3 className="text-sm font-bold text-text mb-3">How the Payout Cycle Works</h3>
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-lg border border-border bg-surface-2 p-3">
            <p className="text-xs font-bold text-text mb-1">1. Order Completed</p>
            <p className="text-[11px] text-text-muted leading-5">When an order is delivered and marked completed, the system records the transaction in the ledger and creates a SupplierSettlement with gross amount, commission, VAT, and net amount.</p>
          </div>
          <div className="rounded-lg border border-border bg-surface-2 p-3">
            <p className="text-xs font-bold text-text mb-1">2. Holding Period (10 Days)</p>
            <p className="text-[11px] text-text-muted leading-5">A 10-day holding period starts from the completion date to allow for returns, disputes, and chargebacks. The settlement shows as "pending" with an `eligible_at` date.</p>
          </div>
          <div className="rounded-lg border border-border bg-surface-2 p-3">
            <p className="text-xs font-bold text-text mb-1">3. Payout Execution</p>
            <p className="text-[11px] text-text-muted leading-5">After the hold period, the settlement becomes eligible. A Payout record is created and transferred to the supplier's verified bank account. The payout status changes from pending → processing → completed.</p>
          </div>
        </div>
      </motion.div>

      {/* Empty State */}
      {!metrics && cashPositions.length === 0 && (
        <div className="theme-card rounded-xl border p-8 text-center text-text-muted">
          <RefreshCw className="h-8 w-8 mx-auto mb-2 opacity-40" />
          <p className="text-sm">No finance data available</p>
          <p className="text-xs text-text-faint mt-1">Try seeding the Chart of Accounts and placing test orders</p>
        </div>
      )}
    </PanelContent>
  );
}
