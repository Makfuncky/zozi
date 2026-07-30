"use client";
import { useEffect, useState } from "react";
import { Building2, CheckCircle2, XCircle, RefreshCw, Shield, CreditCard } from "@/lib/icons";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useAdminCountry } from "@/lib/useAdminCountry";
import { motion } from "framer-motion";

interface BankSettings {
  id: number;
  bank_name: string;
  account_name: string;
  account_number: string;
  iban: string;
  swift_bic: string;
  is_active: boolean;
  country_code?: string;
}

interface PendingBankAccount {
  id: number;
  supplier_name: string;
  bank_name: string;
  account_number: string;
  iban: string;
  status: string;
  created_at: string;
}

export default function BankAccountsPanel() {
  const formatMoney = useCurrencyStore((s) => s.format);
  const { selectedCountry, isGlobalView } = useAdminCountry();
  const [loading, setLoading] = useState(true);
  const [settings, setSettings] = useState<BankSettings | null>(null);
  const [pendingAccounts, setPendingAccounts] = useState<PendingBankAccount[]>([]);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [settingsRes, pendingRes] = await Promise.all([
          apiFetch("/cash-management/admin/bank-settings"),
          apiFetch("/admin/bank-accounts/pending"),
        ]);
        if (settingsRes.ok) setSettings(await settingsRes.json());
        if (pendingRes.ok) {
          const data = await pendingRes.json();
          setPendingAccounts(Array.isArray(data) ? data : data.accounts ?? []);
        }
      } catch (err) {
        console.error("Failed to load bank data:", err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return (
      <PanelContent title="Bank Accounts">
        <PanelLoadingState count={2} blockClassName="h-20 rounded-xl bg-surface-2 animate-pulse" />
      </PanelContent>
    );
  }

  return (
    <PanelContent title="Bank Accounts" className="space-y-4">
      <div className="flex items-center gap-2 text-xs text-text-faint">
        <Shield className="h-3 w-3" />
        <span>{isGlobalView ? "Global View" : `Country: ${selectedCountry?.name || selectedCountry?.code}`}</span>
      </div>

      {/* Bank Settings */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="theme-card rounded-xl border p-4">
        <h3 className="text-sm font-bold text-text mb-3 flex items-center gap-2">
          <Building2 className="h-4 w-4 text-primary" />
          Finance Bank Settings
        </h3>
        {settings ? (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <p className="text-[10px] text-text-faint uppercase">Bank Name</p>
              <p className="text-sm font-semibold">{settings.bank_name}</p>
            </div>
            <div>
              <p className="text-[10px] text-text-faint uppercase">Account Name</p>
              <p className="text-sm font-semibold">{settings.account_name}</p>
            </div>
            <div>
              <p className="text-[10px] text-text-faint uppercase">Account Number</p>
              <p className="text-sm font-mono">{settings.account_number}</p>
            </div>
            <div>
              <p className="text-[10px] text-text-faint uppercase">IBAN</p>
              <p className="text-sm font-mono">{settings.iban}</p>
            </div>
            <div>
              <p className="text-[10px] text-text-faint uppercase">SWIFT/BIC</p>
              <p className="text-sm font-mono">{settings.swift_bic}</p>
            </div>
            <div>
              <p className="text-[10px] text-text-faint uppercase">Status</p>
              <span className={`inline-flex items-center gap-1 text-xs font-semibold ${settings.is_active ? "text-success" : "text-warning"}`}>
                {settings.is_active ? <CheckCircle2 className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                {settings.is_active ? "Active" : "Inactive"}
              </span>
            </div>
          </div>
        ) : (
          <p className="text-sm text-text-muted text-center py-4">No bank settings configured</p>
        )}
      </motion.div>

      {/* Pending Bank Account Verifications */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="theme-card rounded-xl border p-4">
        <h3 className="text-sm font-bold text-text mb-3 flex items-center gap-2">
          <CreditCard className="h-4 w-4 text-warning" />
          Pending Verifications
          {pendingAccounts.length > 0 && (
            <span className="ml-auto text-[10px] bg-warning/20 text-warning px-2 py-0.5 rounded-full">{pendingAccounts.length}</span>
          )}
        </h3>
        {pendingAccounts.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left p-2 font-semibold text-[11px]">Supplier</th>
                  <th className="text-left p-2 font-semibold text-[11px]">Bank</th>
                  <th className="text-left p-2 font-semibold text-[11px]">Account</th>
                  <th className="text-left p-2 font-semibold text-[11px]">Status</th>
                  <th className="text-left p-2 font-semibold text-[11px]">Date</th>
                </tr>
              </thead>
              <tbody>
                {pendingAccounts.map((acc) => (
                  <tr key={acc.id} className="border-b border-border last:border-0">
                    <td className="p-2 text-sm">{acc.supplier_name}</td>
                    <td className="p-2 text-sm">{acc.bank_name}</td>
                    <td className="p-2 font-mono text-xs">{acc.account_number}</td>
                    <td className="p-2">
                      <span className="text-[10px] bg-warning/20 text-warning px-1.5 py-0.5 rounded-full">{acc.status}</span>
                    </td>
                    <td className="p-2 text-xs text-text-faint">{acc.created_at?.slice(0, 10)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-6 text-text-muted">
            <CheckCircle2 className="h-6 w-6 mx-auto mb-2 opacity-40" />
            <p className="text-xs">No pending bank account verifications</p>
          </div>
        )}
      </motion.div>
    </PanelContent>
  );
}
