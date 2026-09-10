"use client";

import { StatCard } from "@/components/ui/StatCard";
import { useCurrencyStore } from "@/stores/currencyStore";
import { useRouter } from "next/navigation";
import {
  OVERVIEW_STATS,
  type DashboardPeriod,
  type GrowthData,
  type InventoryAlertData,
  type OverviewData,
  type RecentOrderData,
  type RevenueTrendPoint,
  type TopProductData,
} from "@/lib/supplierDashboardConfig";
import { RevenueChart } from "./RevenueChart";
import { QuickActionsPanel } from "./QuickActionsPanel";
import { RecentOrdersPanel } from "./RecentOrdersPanel";
import { TopProductsPanel } from "./TopProductsPanel";
import { InventoryAlertsPanel } from "./InventoryAlertsPanel";
import { OrderStatusBreakdown } from "./OrderStatusBreakdown";
import { GrowthIndicator } from "./GrowthIndicator";

interface OverviewTabProps {
  overview: OverviewData;
  growth: GrowthData;
  recentOrders: RecentOrderData[];
  topProducts: TopProductData[];
  inventoryAlerts: InventoryAlertData[];
  revenueTrend: RevenueTrendPoint[];
  orderStatusBreakdown: Record<string, number>;
  periodLabel: string;
  period: DashboardPeriod;
}

export function OverviewTab({
  overview,
  growth,
  recentOrders,
  topProducts,
  inventoryAlerts,
  revenueTrend,
  orderStatusBreakdown,
  periodLabel,
  period,
}: OverviewTabProps) {
  const formatMoney = useCurrencyStore((s) => s.format);
  const router = useRouter();

  const renderStatValue = (config: typeof OVERVIEW_STATS[number], value: number) => {
    if (config.format === "money") return formatMoney(value);
    return String(value);
  };

  return (
    <div className="space-y-6">
      {/* Stat Cards with Growth Indicators */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {OVERVIEW_STATS.slice(0, 4).map((stat) => {
          const value = (overview[stat.key as keyof OverviewData] as number) ?? 0;
          const growthValue = stat.key === "total_revenue"
            ? growth.revenue_growth
            : stat.key === "recent_revenue"
            ? growth.revenue_growth
            : stat.key === "total_orders"
            ? growth.order_growth
            : null;

          return (
            <div key={stat.key} className="relative">
              <StatCard
                label={stat.label}
                value={renderStatValue(stat, value)}
                icon={stat.icon}
                color={stat.color}
                subtitle={stat.subtitle}
              />
              {growthValue !== null && stat.showGrowth && (
                <div className="absolute top-2 right-2">
                  <GrowthIndicator value={growthValue} size="sm" showLabel={false} />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Revenue Chart + Quick Actions */}
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          <RevenueChart data={revenueTrend} periodLabel={periodLabel} />
          <OrderStatusBreakdown
            breakdown={orderStatusBreakdown}
            totalOrders={overview.total_orders}
          />
        </div>
        <QuickActionsPanel />
      </div>

      {/* Recent Orders & Top Products */}
      <div className="grid gap-4 lg:grid-cols-2">
        <RecentOrdersPanel orders={recentOrders} />
        <TopProductsPanel products={topProducts} />
      </div>

      {/* Inventory Alerts */}
      <InventoryAlertsPanel alerts={inventoryAlerts} />
    </div>
  );
}
