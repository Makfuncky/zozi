"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  FileText,
  Download,
  DollarSign,
  Calendar,
  RefreshCw,
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";
import { useToastStore } from "@/stores/toastStore";
import { ErrorState } from "@/components/employee/ErrorBoundary";

interface Payslip {
  id: number;
  period: string;
  gross_pay: number;
  deductions: number;
  net_pay: number;
  currency: string;
  status: string;
  issued_at: string;
  download_url?: string;
}

export default function EmployeePayrollPage() {
  const { addToast } = useToastStore();
  const [payslips, setPayslips] = useState<Payslip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchPayslips = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await apiFetch("/api/v1/employee/hr/payroll/payslips");
      if (res.ok) {
        const data = await res.json();
        setPayslips(Array.isArray(data) ? data : data?.payslips ?? data?.data ?? []);
      }
    } catch {
      setError("Failed to load payslips");
      addToast("Failed to load payslips", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    fetchPayslips();
  }, [fetchPayslips]);

  const formatCurrency = (amount: number, currency: string) => {
    if (currency === "OMR") return `${(amount / 1000).toFixed(3)} OMR`;
    return `${amount} ${currency}`;
  };

  return (
    <PanelContent className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-text">Payroll</h1>
          <p className="text-sm text-text-muted mt-1">View and download your payslips</p>
        </div>
        <button
          onClick={fetchPayslips}
          disabled={loading}
          className="flex items-center gap-2 rounded-xl border border-border bg-surface-2 px-4 py-2 text-xs font-semibold text-text-muted hover:text-text disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {loading ? (
        <PanelLoadingState count={4} blockClassName="h-20 rounded-xl bg-surface-2 animate-pulse" />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchPayslips} />
      ) : payslips.length > 0 ? (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl border border-border bg-surface overflow-hidden"
        >
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-surface-2">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-text-muted">Period</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-text-muted">Gross</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-text-muted">Deductions</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-text-muted">Net Pay</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-text-muted">Status</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-text-muted">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {payslips.map((payslip) => (
                  <tr key={payslip.id} className="hover:bg-surface-2 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Calendar className="h-3.5 w-3.5 text-text-faint" />
                        <span className="text-xs font-medium text-text">{payslip.period}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs text-text tabular-nums">
                      {formatCurrency(payslip.gross_pay, payslip.currency)}
                    </td>
                    <td className="px-4 py-3 text-xs text-danger tabular-nums">
                      -{formatCurrency(payslip.deductions, payslip.currency)}
                    </td>
                    <td className="px-4 py-3 text-xs font-semibold text-success tabular-nums">
                      {formatCurrency(payslip.net_pay, payslip.currency)}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize ${
                        payslip.status === "paid"
                          ? "bg-success/10 text-success"
                          : payslip.status === "pending"
                            ? "bg-warning/10 text-warning"
                            : "bg-surface-2 text-text-muted"
                      }`}>
                        {payslip.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      {payslip.download_url ? (
                        <a
                          href={payslip.download_url}
                          className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
                        >
                          <Download className="h-3.5 w-3.5" />
                          Download
                        </a>
                      ) : (
                        <span className="text-xs text-text-faint">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      ) : (
        <div className="rounded-xl border border-border bg-surface p-8 text-center">
          <FileText className="h-8 w-8 text-text-faint mx-auto mb-3" />
          <p className="text-sm text-text-muted">No payslips available</p>
        </div>
      )}
    </PanelContent>
  );
}
