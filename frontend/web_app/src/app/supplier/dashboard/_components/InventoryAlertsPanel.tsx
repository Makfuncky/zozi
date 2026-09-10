"use client";

import { AlertTriangle } from "@/lib/icons";
import type { InventoryAlertData } from "@/lib/supplierDashboardConfig";

interface InventoryAlertsPanelProps {
  alerts: InventoryAlertData[];
  limit?: number;
}

export function InventoryAlertsPanel({ alerts, limit = 6 }: InventoryAlertsPanelProps) {
  const items = alerts.slice(0, limit);
  const lowStockCount = alerts.filter((a) => a.stock <= a.low_stock_threshold).length;

  if (items.length === 0) {
    return null;
  }

  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <h2 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
        <AlertTriangle className="h-4 w-4 text-warning" />
        Inventory Alerts
        <span className="ml-auto text-xs text-text-faint">{lowStockCount} low stock</span>
      </h2>
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((item) => (
          <div key={item.product_id} className="flex items-center justify-between rounded-lg bg-surface-2 px-3 py-2">
            <span className="text-xs text-text truncate flex-1">{item.product_name}</span>
            <span
              className={`text-xs font-semibold tabular-nums shrink-0 ml-2 ${
                item.stock <= item.low_stock_threshold ? "text-danger" : "text-success"
              }`}
            >
              {item.stock}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
