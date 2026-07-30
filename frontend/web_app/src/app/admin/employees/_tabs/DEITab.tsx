"use client";

import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import {
  BarChart3,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  Users,
  DollarSign,
  Download,
} from "@/lib/icons";

interface EquityMetric {
  category: string;
  avg_male: number;
  avg_female: number;
  disparity_percent: number;
  flagged: boolean;
}

import type { ToastType } from "@/lib/toastStore";
import { apiFetch } from "@/lib/api";

interface DEITabProps {
  addToast: (message: string, type?: ToastType, duration?: number) => void;
}

export default function DEITab({ addToast }: DEITabProps) {
  const [metrics, setMetrics] = useState<EquityMetric[]>([]);
  const [loading, setLoading] = useState(false);

const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch("/admin/treasury/payroll/equity");
      if (res.ok) {
        const data = await res.json().catch(() => ({}));
        setMetrics(Array.isArray(data) ? data : data?.metrics ?? []);
      }
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, []);

  const handleExport = async () => {
    try {
      const res = await apiFetch("/admin/export/pay-equity");
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `pay-equity-${new Date().toISOString().split("T")[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
        addToast("Equity report exported", "success");
      } else {
        addToast("Failed to export equity report", "error");
      }
    } catch {
      addToast("Network error", "error");
    }
  };

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text">Diversity, Equity & Inclusion (DEI)</h3>
        <button
          onClick={handleExport}
          className="flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-xs font-semibold text-text-muted hover:text-text hover:border-primary/40 transition-colors"
        >
          <Download className="h-3.5 w-3.5" />
          Export Report
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { label: "Gender Pay Gap", value: metrics.length > 0 ? `${metrics[0]?.disparity_percent ?? 0}%` : "—", sub: "Average across all roles" },
          { label: "Flagged Categories", value: metrics.filter((m) => m.flagged).length, sub: "Require immediate review" },
          { label: "Total Employees Audited", value: "—", sub: "Latest automated run" },
        ].map((item) => (
          <div key={item.label} className="rounded-xl border border-border bg-surface-1 p-4 hover:border-primary/30 transition-colors">
            <div className="flex items-center gap-2 mb-3">
              <BarChart3 className="h-4 w-4 text-primary" />
              <span className="text-[11px] text-text-muted font-medium">{item.label}</span>
            </div>
            <p className="text-2xl font-bold text-text">{item.value}</p>
            {item.sub && <p className="mt-1 text-[10px] text-text-faint">{item.sub}</p>}
          </div>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-5 w-5 animate-spin text-text-faint" />
        </div>
      ) : metrics.length === 0 ? (
        <div className="rounded-xl border border-border bg-surface-1 p-8 text-center">
          <BarChart3 className="h-8 w-8 mx-auto mb-2 text-text-faint/40" />
          <p className="text-sm text-text-muted">No equity metrics available</p>
          <p className="text-xs text-text-faint mt-1">Nightly automated audit populates this panel</p>
        </div>
      ) : (
        <div className="rounded-xl border border-border bg-surface-1 overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border bg-surface-2 text-text-muted">
                <th className="px-4 py-2.5 font-semibold">Category</th>
                <th className="px-4 py-2.5 font-semibold">Avg Male</th>
                <th className="px-4 py-2.5 font-semibold">Avg Female</th>
                <th className="px-4 py-2.5 font-semibold">Disparity</th>
                <th className="px-4 py-2.5 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {metrics.map((m) => (
                <tr key={m.category} className="hover:bg-surface-2/50 transition-colors">
                  <td className="px-4 py-3 text-text font-semibold">{m.category}</td>
                  <td className="px-4 py-3 text-text-muted">{m.avg_male.toLocaleString()}</td>
                  <td className="px-4 py-3 text-text-muted">{m.avg_female.toLocaleString()}</td>
                  <td className="px-4 py-3">
                    <span className={m.disparity_percent > 10 ? "text-danger font-semibold" : "text-text"}>{m.disparity_percent}%</span>
                  </td>
                  <td className="px-4 py-3">
                    {m.flagged ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-danger/10 text-danger text-[10px] font-semibold px-2 py-0.5 border border-danger/20">
                        <AlertTriangle className="h-3 w-3" />
                        Flagged
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-full bg-success/10 text-success text-[10px] font-semibold px-2 py-0.5 border border-success/20">
                        <CheckCircle2 className="h-3 w-3" />
                        Compliant
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}


