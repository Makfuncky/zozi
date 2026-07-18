"use client";

import React from "react";

interface StatCardProps {
  label: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  trend?: { value: number; positive: boolean };
  sub?: string;
  className?: string;
}

/**
 * Shared metric card used across Supplier/Admin/Logistics dashboards.
 * Keeps stat visuals consistent (surface, border, icon chip, trend).
 */
export function StatCard({ label, value, icon: Icon, color, trend, sub, className }: StatCardProps) {
  return (
    <div className={`rounded-xl border border-border bg-surface p-4 ${className ?? ""}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[11px] font-semibold uppercase tracking-[0.15em] text-text-muted">{label}</p>
          <p className="mt-1.5 text-2xl font-bold text-text truncate">{value}</p>
          {trend && (
            <p className={`mt-0.5 text-xs flex items-center gap-1 ${trend.positive ? "text-success" : "text-danger"}`}>
              {trend.positive ? "+" : ""}{trend.value.toFixed(1)}%
            </p>
          )}
          {sub && <p className="mt-0.5 text-xs text-text-muted">{sub}</p>}
        </div>
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${color}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
}
