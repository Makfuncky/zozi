"use client";

import { Truck, Package, AlertTriangle, CheckCircle } from "@/lib/icons";
import {
  type OverviewData,
  type InventoryAlertData,
  type TopProductData,
} from "@/lib/supplierDashboardConfig";

interface OperationsTabProps {
  overview: OverviewData;
  inventoryAlerts: InventoryAlertData[];
  topProducts: TopProductData[];
}

interface OperationsMetricConfig {
  key: keyof OverviewData;
  label: string;
  icon: typeof Truck;
  tone: string;
}

const OPERATIONS_METRICS: OperationsMetricConfig[] = [
  { key: "pending_orders", label: "Pending Orders", icon: Truck, tone: "bg-warning/10 text-warning" },
  { key: "low_stock_count", label: "Low Stock Items", icon: AlertTriangle, tone: "bg-danger/10 text-danger" },
  { key: "total_products", label: "Active Listings", icon: Package, tone: "bg-success/10 text-success" },
  { key: "return_rate", label: "Return Rate", icon: CheckCircle, tone: "bg-info/10 text-info" },
];

const OPERATION_LINKS = [
  { label: "View Orders", route: "/supplier/orders", description: "Process pending orders" },
  { label: "Inventory", route: "/supplier/inventory", description: "Stock health" },
  { label: "Documents", route: "/supplier/documents", description: "KYC compliance" },
  { label: "Returns", route: "/supplier/returns", description: "Return approvals" },
];

export function OperationsTab({ overview, inventoryAlerts, topProducts }: OperationsTabProps) {
  return (
    <div className="space-y-6">
      {/* Operations Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {OPERATIONS_METRICS.map((m) => (
          <div key={m.key} className="p-4 rounded-xl border border-border bg-surface">
            <div className="flex items-center justify-between mb-2">
              <m.icon className="w-5 h-5 text-primary" />
            </div>
            <p className="text-xl font-bold text-text">
              {String((overview[m.key] as number | undefined) ?? 0)}
            </p>
            <p className="text-xs text-text-faint">{m.label}</p>
          </div>
        ))}
      </div>

      {/* Inventory Alerts + Top Products */}
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-border bg-surface p-4">
          <h2 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-warning" />
            Stock Health
          </h2>
          {inventoryAlerts.length > 0 ? (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {inventoryAlerts.slice(0, 10).map((item) => (
                <div
                  key={item.product_id}
                  className="flex items-center justify-between rounded-lg bg-surface-2 px-3 py-2"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium text-text truncate">{item.product_name}</p>
                    <p className="text-xs text-text-faint">Threshold: {item.low_stock_threshold}</p>
                  </div>
                  <span
                    className={`text-xs font-semibold tabular-nums shrink-0 ml-2 ${
                      item.stock <= item.low_stock_threshold ? "text-danger" : "text-success"
                    }`}
                  >
                    {item.stock} in stock
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-text-muted py-6 text-center">All products are well stocked.</p>
          )}
        </div>

        <div className="rounded-xl border border-border bg-surface p-4">
          <h2 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
            <Package className="h-4 w-4 text-primary" />
            Top Performers
          </h2>
          {topProducts.length > 0 ? (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {topProducts.slice(0, 10).map((product, i) => (
                <div
                  key={product.id}
                  className="flex items-center gap-3 rounded-lg bg-surface-2 px-3 py-2"
                >
                  <span className="w-5 text-xs font-bold text-text-faint tabular-nums shrink-0">#{i + 1}</span>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium text-text truncate">{product.name}</p>
                    <p className="text-xs text-text-faint">{product.sales} sold</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-text-muted py-6 text-center">No sales data yet.</p>
          )}
        </div>
      </div>

      {/* Operations Navigation */}
      <div className="rounded-xl border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
          <Truck className="h-4 w-4 text-primary" />
          Operations
        </h2>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {OPERATION_LINKS.map((link) => (
            <button
              key={link.route}
              onClick={() => { window.location.href = link.route; }}
              className="rounded-lg bg-surface-2 px-3 py-2.5 text-left hover:bg-surface-3 transition-colors"
            >
              <p className="text-xs font-semibold text-text">{link.label}</p>
              <p className="text-xs text-text-faint">{link.description}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
