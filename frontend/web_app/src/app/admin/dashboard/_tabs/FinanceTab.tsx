"use client";
import { useEffect, useState } from "react";
import { Wallet, TrendingUp, DollarSign, PieChart, RefreshCw, Shield } from "@/lib/icons";
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
}

interface CashPositionItem {
  slug: string;
  name: string;
  account_type: string;
  balance: number;
  currency: string;
  gl_account_code: string;
}

export default function FinanceTab() {
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
      <PanelContent title="Finance">
        <PanelLoadingState count={4} blockClassName="h-24 rounded-xl bg-surface-2 animate-pulse" />
      </PanelContent>
    );
  }

  return (
    <PanelContent title="Finance" className="space-y-4">
      {/* Country Scope Indicator */}
      <div className="flex items-center gap-2 text-xs text-text-faint">
        <Shield className="h-3 w-3" />
        <span>{isGlobalView ? "Global View — All Countries" : `Country: ${selectedCountry?.name || selectedCountry?.code}`}</span>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="theme-card rounded-xl border p-4">
          <div className="flex items-center gap-2 mb-1">
            <Wallet className="h-4 w-4 text-primary" />
            <span className="text-[11px] font-semibold text-text-faint uppercase">Free Cash</span>
          </div>
          <p className="text-2xl font-bold text-text">{formatMoney(metrics?.free_cash ?? 0)}</p>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="theme-card rounded-xl border p-4">
          <div className="flex items-center gap-2 mb-1">
            <DollarSign className="h-4 w-4 text-warning" />
            <span className="text-[11px] font-semibold text-text-faint uppercase">Liabilities</span>
          </div>
          <p className="text-2xl font-bold text-text">{formatMoney(metrics?.total_liabilities ?? 0)}</p>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="theme-card rounded-xl border p-4">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp className="h-4 w-4 text-success" />
            <span className="text-[11px] font-semibold text-text-faint uppercase">Revenue</span>
          </div>
          <p className="text-2xl font-bold text-text">{formatMoney(metrics?.total_revenue ?? 0)}</p>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="theme-card rounded-xl border p-4">
          <div className="flex items-center gap-2 mb-1">
            <PieChart className="h-4 w-4 text-info" />
            <span className="text-[11px] font-semibold text-text-faint uppercase">Net Income</span>
          </div>
          <p className="text-2xl font-bold text-text">{formatMoney(metrics?.net_income ?? 0)}</p>
        </motion.div>
      </div>

      {/* Cash Position Breakdown */}
      {cashPositions.length > 0 && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }} className="theme-card rounded-xl border p-4">
          <h3 className="text-sm font-bold text-text mb-3">Cash Position by Account</h3>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {cashPositions.map((item) => (
              <div key={item.slug} className="rounded-lg border border-border bg-surface-2 p-3">
                <p className="text-[11px] text-text-faint uppercase">{item.name}</p>
                <p className="text-lg font-bold text-text">{formatMoney(item.balance)}</p>
                <p className="text-[10px] text-text-faint">{item.gl_account_code}</p>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Empty State */}
      {!metrics && cashPositions.length === 0 && (
        <div className="theme-card rounded-xl border p-8 text-center text-text-muted">
          <RefreshCw className="h-8 w-8 mx-auto mb-2 opacity-40" />
          <p className="text-sm">No finance data available</p>
          <p className="text-xs text-text-faint mt-1">Try seeding the Chart of Accounts</p>
        </div>
      )}
    </PanelContent>
  );
}
