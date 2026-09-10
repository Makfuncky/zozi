"use client";

import { useCurrencyStore } from "@/stores/currencyStore";
import { BarChart3 } from "@/lib/icons";
import type { RevenueTrendPoint } from "@/lib/supplierDashboardConfig";

interface RevenueChartProps {
  data: RevenueTrendPoint[];
  periodLabel: string;
  height?: number;
}

export function RevenueChart({ data, periodLabel, height = 160 }: RevenueChartProps) {
  const formatMoney = useCurrencyStore((s) => s.format);
  const maxValue = Math.max(...data.map((d) => d.amount), 1);
  const points = data.slice(-14);

  if (points.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold text-text mb-4 flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-primary" />
          Revenue Trend
          <span className="ml-auto text-xs text-text-faint">{periodLabel}</span>
        </h2>
        <div style={{ height }} className="flex items-center justify-center text-xs text-text-faint">
          <div className="text-center">
            <BarChart3 className="h-8 w-8 mx-auto mb-2 text-text-faint/50" />
            <p>No revenue data for this period</p>
            <p className="mt-1">Data appears as orders are completed</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <h2 className="text-sm font-semibold text-text mb-4 flex items-center gap-2">
        <BarChart3 className="h-4 w-4 text-primary" />
        Revenue Trend
        <span className="ml-auto text-xs text-text-faint">{periodLabel}</span>
      </h2>
      <div style={{ height }} className="flex items-end gap-1">
        {points.map((point, i) => (
          <div key={`${point.date}-${i}`} className="flex-1 flex flex-col items-center gap-1">
            <div
              className="w-full rounded-t bg-primary/70 hover:bg-primary transition-colors cursor-pointer min-h-[4px]"
              style={{ height: `${Math.max((point.amount / maxValue) * 100, 4)}%` }}
              title={`${point.date}: ${formatMoney(point.amount)}`}
            />
          </div>
        ))}
      </div>
      <div className="mt-2 flex justify-between text-3xs text-text-faint">
        <span>{points[0]?.date.slice(5) ?? ""}</span>
        <span>{points[Math.floor(points.length / 2)]?.date.slice(5) ?? ""}</span>
        <span>{points[points.length - 1]?.date.slice(5) ?? ""}</span>
      </div>
    </div>
  );
}
