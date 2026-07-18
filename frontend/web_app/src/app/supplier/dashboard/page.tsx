"use client";

import { useCallback, useEffect, useState } from "react";
import {
  DollarSign,
  ShoppingCart,
  Package,
  TrendingUp,
  AlertTriangle,
  RefreshCw,
  Eye,
  Truck,
} from "@/lib/icons";
import SupplierLayout from "@/components/SupplierLayout";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";
import { StatCard } from "@/components/ui/StatCard";
import { apiFetch } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";

interface Overview {
  totalRevenue: number;
  totalOrders: number;
  totalProducts: number;
  averageOrderValue: number;
  conversionRate: number;
}

interface TopProduct {
  id: number;
  name: string;
  sales: number;
  revenue: number;
  image_url?: string;
}

interface AnalyticsData {
  overview: Overview;
  products: { topSelling: TopProduct[] };
  trends: { revenueGrowth: number; orderGrowth: number };
}

interface InventoryItem {
  product_id: number;
  product_name: string;
  stock: number;
  low_stock_threshold: number;
}

export default function SupplierDashboardPage() {
  const formatMoney = useCurrencyStore((s) => s.format);
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [inventoryAlerts, setInventoryAlerts] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    const [analyticsRes, inventoryRes] = await Promise.all([
      apiFetch("/supplier/analytics?period=30d").catch(() => null),
      apiFetch("/supplier/inventory/alerts").catch(() => null),
    ]);
    if (analyticsRes?.ok) setData(await analyticsRes.json());
    if (inventoryRes?.ok) {
      const inv = await inventoryRes.json().catch(() => ({ alerts: [] }));
      const rawAlerts = Array.isArray(inv) ? inv : (inv?.alerts ?? []);
      setInventoryAlerts(
        rawAlerts.map((a: Record<string, any>) => ({
          product_id: a.product_id,
          product_name: a.product_name,
          stock: a.current_stock ?? 0,
          low_stock_threshold: a.reorder_point ?? 0,
        }))
      );
    }
    setLoading(false);
  }, []);

  useEffect(() => { fetchDashboard(); }, [fetchDashboard]);

  const overview = data?.overview;
  const trends = data?.trends;
  const topSelling = data?.products?.topSelling ?? [];
  const lowStockCount = inventoryAlerts.filter((i) => i.stock <= i.low_stock_threshold).length;

  return (
    <SupplierLayout title="Dashboard">
      <PanelContent className="space-y-5">
        <div className="flex items-center justify-between">
          <p className="text-xs text-text-muted">Business performance at a glance</p>
          <button onClick={fetchDashboard} disabled={loading}
            className="flex items-center gap-2 rounded-xl border border-border bg-surface-2 px-4 py-2 text-xs font-semibold text-text-muted hover:text-text disabled:opacity-50">
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        {loading ? (
          <PanelLoadingState
            count={4}
            className="!mt-0 grid grid-cols-2 gap-3 lg:grid-cols-4"
            blockClassName="h-28 rounded-xl bg-surface-2 animate-pulse"
          />
        ) : (
          <>
            {overview && (
              <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                <StatCard label="Revenue" value={formatMoney(overview.totalRevenue)} icon={DollarSign}
                  color="bg-primary/10 text-primary"
                  trend={trends ? { value: trends.revenueGrowth, positive: trends.revenueGrowth >= 0 } : undefined} />
                <StatCard label="Orders" value={String(overview.totalOrders)} icon={ShoppingCart}
                  color="bg-info/10 text-info"
                  trend={trends ? { value: trends.orderGrowth, positive: trends.orderGrowth >= 0 } : undefined} />
                <StatCard label="Products" value={String(overview.totalProducts)} icon={Package}
                  color="bg-success/10 text-success" />
                <StatCard label="Avg Order" value={formatMoney(overview.averageOrderValue)} icon={TrendingUp}
                  color="bg-warning/10 text-warning" />
              </div>
            )}

            <div className="grid gap-4 lg:grid-cols-3">
              {inventoryAlerts.length > 0 && (
                <div className="rounded-xl border border-border bg-surface p-4">
                  <h2 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-warning" />
                    Inventory Alerts
                    <span className="ml-auto text-xs text-text-faint">{lowStockCount} low stock</span>
                  </h2>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {inventoryAlerts.slice(0, 10).map((item) => (
                      <div key={item.product_id} className="flex items-center justify-between rounded-lg bg-surface-2 px-3 py-2">
                        <span className="text-xs text-text truncate">{item.product_name}</span>
                        <span className={`text-xs font-semibold tabular-nums shrink-0 ml-2 ${
                          item.stock <= item.low_stock_threshold ? "text-danger" : "text-success"
                        }`}>{item.stock}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {topSelling.length > 0 && (
                <div className="lg:col-span-2 rounded-xl border border-border bg-surface p-4">
                  <h2 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
                    <Eye className="h-4 w-4 text-primary" />
                    Top Selling Products
                  </h2>
                  <div className="divide-y divide-border">
                    {topSelling.slice(0, 8).map((product, i) => (
                      <div key={product.id} className="flex items-center gap-3 py-2.5">
                        <span className="w-5 text-xs font-bold text-text-faint tabular-nums">#{i + 1}</span>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-medium text-text truncate">{product.name}</p>
                          <p className="text-[10px] text-text-muted">{product.sales} sales</p>
                        </div>
                        <span className="text-xs font-semibold text-text tabular-nums">{formatMoney(product.revenue)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </PanelContent>
    </SupplierLayout>
  );
}
