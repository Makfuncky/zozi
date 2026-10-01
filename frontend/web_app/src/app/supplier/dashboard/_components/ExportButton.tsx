"use client";

import { Download } from "@/lib/icons";
import { useToastStore } from "@/stores/toastStore";
import { apiFetch } from "@/lib/api";
import type { DashboardPeriod } from "@/lib/supplierDashboardConfig";

interface ExportButtonProps {
  period: DashboardPeriod;
  variant?: "primary" | "secondary";
  label?: string;
}

export function ExportButton({ period, variant = "secondary", label = "Export CSV" }: ExportButtonProps) {
  const addToast = useToastStore((s) => s.addToast);

  const handleExport = async () => {
    try {
      const res = await apiFetch(`/supplier/analytics/export/csv?period=${period}`);
      if (!res.ok) {
        addToast("Failed to export data", "error");
        return;
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `supplier-analytics-${period}-${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      addToast("Report downloaded successfully", "success");
    } catch {
      addToast("Network error during export", "error");
    }
  };

  const baseClass = "inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold";
  const variantClass =
    variant === "primary"
      ? "theme-btn-primary"
      : "theme-btn-secondary border border-border bg-surface-2 text-text-muted hover:text-text";

  return (
    <button onClick={handleExport} className={`${baseClass} ${variantClass}`}>
      <Download className="h-3.5 w-3.5" />
      {label}
    </button>
  );
}
