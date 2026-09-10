"use client";

import { Clock, ShoppingCart } from "@/lib/icons";
import { useCurrencyStore } from "@/stores/currencyStore";
import { ORDER_STATUS_TONE, type RecentOrderData } from "@/lib/supplierDashboardConfig";

interface RecentOrdersPanelProps {
  orders: RecentOrderData[];
  limit?: number;
}

export function RecentOrdersPanel({ orders, limit = 5 }: RecentOrdersPanelProps) {
  const formatMoney = useCurrencyStore((s) => s.format);
  const items = orders.slice(0, limit);

  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-text flex items-center gap-2">
          <Clock className="h-4 w-4 text-info" />
          Recent Orders
        </h2>
        <button
          onClick={() => { window.location.href = "/supplier/orders"; }}
          className="text-xs font-semibold text-primary hover:underline"
        >
          View All
        </button>
      </div>
      {items.length > 0 ? (
        <div className="space-y-2">
          {items.map((order) => (
            <div key={order.id} className="flex items-center justify-between rounded-lg bg-surface-2 px-3 py-2">
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium text-text truncate">
                  #{order.order_number || order.id}
                </p>
                <p className="text-xs text-text-faint truncate">{order.customer_name || "Customer"}</p>
              </div>
              <div className="text-right shrink-0 ml-2">
                <p className="text-xs font-semibold text-text">{formatMoney(order.total)}</p>
                <span className={`text-xs font-medium ${ORDER_STATUS_TONE[order.status] ?? "text-info"}`}>
                  {order.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="py-8 text-center text-xs text-text-faint">
          <ShoppingCart className="h-8 w-8 mx-auto mb-2 text-text-faint/50" />
          <p>No recent orders</p>
          <p className="mt-1">Orders appear here when customers place them</p>
        </div>
      )}
    </div>
  );
}
