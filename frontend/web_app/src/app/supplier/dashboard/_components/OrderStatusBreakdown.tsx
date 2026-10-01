"use client";

import { ShoppingCart } from "@/lib/icons";
import { ORDER_STATUS_BG } from "@/lib/supplierDashboardConfig";

interface OrderStatusBreakdownProps {
  breakdown: Record<string, number>;
  totalOrders: number;
}

const STATUS_ORDER = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled", "returned"];

export function OrderStatusBreakdown({ breakdown, totalOrders }: OrderStatusBreakdownProps) {
  const entries = Object.entries(breakdown).sort(
    (a, b) => STATUS_ORDER.indexOf(a[0]) - STATUS_ORDER.indexOf(b[0])
  );

  if (entries.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
          <ShoppingCart className="h-4 w-4 text-primary" />
          Order Status Breakdown
        </h2>
        <p className="text-xs text-text-faint py-6 text-center">No orders in this period</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <h2 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
        <ShoppingCart className="h-4 w-4 text-primary" />
        Order Status Breakdown
        <span className="ml-auto text-xs text-text-faint">{totalOrders} total</span>
      </h2>
      <div className="space-y-2">
        {entries.map(([status, count]) => {
          const pct = totalOrders > 0 ? (count / totalOrders) * 100 : 0;
          return (
            <div key={status}>
              <div className="flex items-center justify-between text-xs mb-1">
                <span
                  className={`px-2 py-0.5 rounded-full text-2xs font-semibold ${
                    ORDER_STATUS_BG[status] ?? "bg-surface-2 text-text"
                  }`}
                >
                  {status}
                </span>
                <span className="text-text-faint">
                  {count} ({pct.toFixed(0)}%)
                </span>
              </div>
              <div className="h-1.5 rounded-full bg-surface-3 overflow-hidden">
                <div
                  className="h-full rounded-full bg-primary transition-all"
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
