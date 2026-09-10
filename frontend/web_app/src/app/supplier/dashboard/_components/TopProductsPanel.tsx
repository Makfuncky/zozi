"use client";

import { Eye, Package } from "@/lib/icons";
import { useCurrencyStore } from "@/stores/currencyStore";
import type { TopProductData } from "@/lib/supplierDashboardConfig";

interface TopProductsPanelProps {
  products: TopProductData[];
  limit?: number;
}

export function TopProductsPanel({ products, limit = 5 }: TopProductsPanelProps) {
  const formatMoney = useCurrencyStore((s) => s.format);
  const items = products.slice(0, limit);

  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-text flex items-center gap-2">
          <Eye className="h-4 w-4 text-primary" />
          Top Selling Products
        </h2>
        <button
          onClick={() => { window.location.href = "/supplier/products"; }}
          className="text-xs font-semibold text-primary hover:underline"
        >
          View All
        </button>
      </div>
      {items.length > 0 ? (
        <div className="space-y-2">
          {items.map((product, i) => (
            <div key={product.id} className="flex items-center gap-3 rounded-lg bg-surface-2 px-3 py-2">
              <span className="w-5 text-xs font-bold text-text-faint tabular-nums">#{i + 1}</span>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium text-text truncate">{product.name}</p>
                <p className="text-xs text-text-faint">{product.sales} sales</p>
              </div>
              <span className="text-xs font-semibold text-text tabular-nums">
                {formatMoney(product.revenue)}
              </span>
            </div>
          ))}
        </div>
      ) : (
        <div className="py-8 text-center text-xs text-text-faint">
          <Package className="h-8 w-8 mx-auto mb-2 text-text-faint/50" />
          <p>No sales data yet</p>
          <p className="mt-1">Top products appear as you make sales</p>
        </div>
      )}
    </div>
  );
}
