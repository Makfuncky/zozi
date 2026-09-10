"use client";

import { DASHBOARD_PERIODS, type DashboardPeriod } from "@/lib/supplierDashboardConfig";
import { RefreshCw } from "@/lib/icons";

interface PeriodSelectorProps {
  period: DashboardPeriod;
  onPeriodChange: (period: DashboardPeriod) => void;
  onRefresh: () => void;
  loading: boolean;
}

export function PeriodSelector({ period, onPeriodChange, onRefresh, loading }: PeriodSelectorProps) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex rounded-xl border border-border bg-surface-2 p-0.5">
        {DASHBOARD_PERIODS.map((p) => (
          <button
            key={p.value}
            onClick={() => onPeriodChange(p.value)}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
              period === p.value
                ? "bg-primary text-white"
                : "text-text-muted hover:text-text"
            }`}
          >
            {p.short}
          </button>
        ))}
      </div>
      <button
        onClick={onRefresh}
        disabled={loading}
        className="rounded-xl border border-border bg-surface-2 p-2 text-text-muted hover:text-text disabled:opacity-50"
        aria-label="Refresh data"
      >
        <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
      </button>
    </div>
  );
}
