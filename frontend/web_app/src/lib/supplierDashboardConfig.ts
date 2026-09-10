/**
 * Supplier Dashboard Configuration — Enterprise Level
 *
 * Centralized configuration for dashboard tabs, period selectors, and
 * card definitions. Following the admin panel config pattern from
 * `lib/adminPanelConfig.ts` for architectural consistency.
 *
 * Law 14 (file placement): shared config lives under `lib/`, not in pages.
 */

import {
  DollarSign,
  TrendingUp,
  BarChart3,
  ShoppingCart,
  Package,
  Eye,
  FileText,
  AlertTriangle,
  Clock,
  Sparkles,
  Truck,
  CheckCircle,
  Download,
  XCircle,
  TrendingDown,
  type LucideIcon,
} from "@/lib/icons";

export type DashboardTabKey = "overview" | "analytics" | "operations" | "reports";
export type DashboardPeriod = "7d" | "30d" | "90d" | "1y";

export interface DashboardTabConfig {
  key: DashboardTabKey;
  label: string;
  icon: LucideIcon;
  description: string;
}

export const DASHBOARD_TABS: DashboardTabConfig[] = [
  { key: "overview", label: "Overview", icon: Eye, description: "Real-time business health snapshot" },
  { key: "analytics", label: "Analytics", icon: BarChart3, description: "Deep performance metrics and trends" },
  { key: "operations", label: "Operations", icon: Truck, description: "Fulfillment, inventory, and parcels" },
  { key: "reports", label: "Reports", icon: FileText, description: "Exports, AI audit, and insights" },
];

export const DASHBOARD_PERIODS: Array<{ value: DashboardPeriod; label: string; short: string }> = [
  { value: "7d", label: "Last 7 days", short: "7D" },
  { value: "30d", label: "Last 30 days", short: "30D" },
  { value: "90d", label: "Last 90 days", short: "90D" },
  { value: "1y", label: "Last 12 months", short: "1Y" },
];

export interface OverviewStatConfig {
  key: keyof OverviewData;
  label: string;
  icon: LucideIcon;
  color: string;
  subtitle: string;
  format: "money" | "number" | "percent";
  showGrowth: boolean;
}

export const OVERVIEW_STATS: OverviewStatConfig[] = [
  { key: "total_revenue", label: "Total Revenue", icon: DollarSign, color: "bg-primary/10 text-primary", subtitle: "All-time", format: "money", showGrowth: true },
  { key: "recent_revenue", label: "Period Revenue", icon: TrendingUp, color: "bg-info/10 text-info", subtitle: "Current period", format: "money", showGrowth: true },
  { key: "total_orders", label: "Total Orders", icon: ShoppingCart, color: "bg-warning/10 text-warning", subtitle: "All-time", format: "number", showGrowth: true },
  { key: "pending_orders", label: "Pending Orders", icon: Clock, color: "bg-danger/10 text-danger", subtitle: "Awaiting fulfillment", format: "number", showGrowth: false },
  { key: "total_products", label: "Active Products", icon: Package, color: "bg-success/10 text-success", subtitle: "Listed", format: "number", showGrowth: false },
  { key: "average_order_value", label: "Avg Order Value", icon: BarChart3, color: "bg-primary/10 text-primary", subtitle: "Per order", format: "money", showGrowth: false },
];

export interface AnalyticsStatConfig {
  key: string;
  label: string;
  icon: LucideIcon;
  format: "money" | "number" | "percent";
  growth: boolean;
}

export const ANALYTICS_STATS: AnalyticsStatConfig[] = [
  { key: "total_revenue", label: "Revenue", icon: DollarSign, format: "money", growth: true },
  { key: "total_orders", label: "Orders", icon: ShoppingCart, format: "number", growth: true },
  { key: "average_order_value", label: "Avg Order", icon: TrendingUp, format: "money", growth: false },
  { key: "total_products", label: "Products", icon: Package, format: "number", growth: false },
];

// Type contracts
export interface OverviewData {
  total_products: number;
  total_orders: number;
  total_revenue: number;
  recent_revenue: number;
  previous_revenue: number;
  average_order_value: number;
  pending_orders: number;
  low_stock_count: number;
  conversion_rate: number;
  return_rate: number;
}

export interface GrowthData {
  revenue_growth: number;
  order_growth: number;
  previous_revenue: number;
  previous_orders: number;
}

export interface TopProductData {
  id: number;
  name: string;
  sales: number;
  revenue: number;
  image_url?: string;
  stock?: number;
  category?: string;
}

export interface RecentOrderData {
  id: number;
  order_number: string;
  total: number;
  status: string;
  customer_name: string;
  customer_email?: string;
  created_at?: string;
  item_count?: number;
}

export interface RevenueTrendPoint {
  date: string;
  amount: number;
}

export interface InventoryAlertData {
  product_id: number;
  product_name: string;
  stock: number;
  low_stock_threshold: number;
  category?: string;
}

export interface AiAuditData {
  groupCount: number;
  curatedGroupCount: number;
  errorCount: number;
  warningCount: number;
  attentionCount: number;
  attentionGroups: Array<{ id?: string; label?: string; status?: string }>;
  generatedAt?: string;
}

export interface DashboardResponse {
  overview: OverviewData;
  growth: GrowthData;
  top_products: TopProductData[];
  recent_orders: RecentOrderData[];
  revenue_trend: RevenueTrendPoint[];
  inventory_alerts: InventoryAlertData[];
  order_status_breakdown: Record<string, number>;
  ai_audit: AiAuditData | null;
  period: string;
  period_start?: string;
  generated_at: string;
}

// Status color mapping
export const ORDER_STATUS_TONE: Record<string, string> = {
  completed: "text-success",
  delivered: "text-success",
  shipped: "text-info",
  processing: "text-info",
  confirmed: "text-info",
  pending: "text-warning",
  cancelled: "text-danger",
  returned: "text-danger",
};

export const ORDER_STATUS_BG: Record<string, string> = {
  completed: "bg-success/15 text-success",
  delivered: "bg-success/15 text-success",
  shipped: "bg-info/15 text-info",
  processing: "bg-info/15 text-info",
  confirmed: "bg-info/15 text-info",
  pending: "bg-warning/15 text-warning",
  cancelled: "bg-danger/15 text-danger",
  returned: "bg-danger/15 text-danger",
};

// Quick actions config
export const QUICK_ACTIONS: Array<{ label: string; description: string; route: string; icon: LucideIcon; tone: string }> = [
  { label: "Add Product", description: "Create a new listing", route: "/supplier/products/add", icon: Package, tone: "bg-primary/10 text-primary" },
  { label: "View Orders", description: "Manage customer orders", route: "/supplier/orders", icon: ShoppingCart, tone: "bg-info/10 text-info" },
  { label: "Payouts", description: "View settlements", route: "/supplier/payouts", icon: DollarSign, tone: "bg-success/10 text-success" },
  { label: "Inventory", description: "Stock management", route: "/supplier/inventory", icon: AlertTriangle, tone: "bg-warning/10 text-warning" },
];

// Operations metrics
export interface OperationsMetricConfig {
  key: keyof OverviewData;
  label: string;
  icon: LucideIcon;
  tone: string;
}

export const OPERATIONS_METRICS: OperationsMetricConfig[] = [
  { key: "pending_orders", label: "Pending Orders", icon: Truck, tone: "bg-warning/10 text-warning" },
  { key: "low_stock_count", label: "Low Stock Items", icon: AlertTriangle, tone: "bg-danger/10 text-danger" },
  { key: "total_products", label: "Active Listings", icon: Package, tone: "bg-success/10 text-success" },
  { key: "return_rate", label: "Return Rate", icon: CheckCircle, tone: "bg-info/10 text-info" },
];

// Operations links
export const OPERATION_LINKS = [
  { label: "View Orders", route: "/supplier/orders", description: "Process pending orders" },
  { label: "Inventory", route: "/supplier/inventory", description: "Stock health" },
  { label: "Documents", route: "/supplier/documents", description: "KYC compliance" },
  { label: "Returns", route: "/supplier/returns", description: "Return approvals" },
];

// AI Audit metrics
export const AUDIT_METRICS = [
  { key: "groupCount", label: "Groups", tone: "text-text" },
  { key: "curatedGroupCount", label: "Curated", tone: "text-text" },
  { key: "attentionCount", label: "Need Attention", tone: "text-warning" },
  { key: "errorCount", label: "Errors", tone: "text-danger" },
  { key: "warningCount", label: "Warnings", tone: "text-warning" },
] as const;

// Report nav links
export const REPORT_NAV_LINKS = [
  { label: "Open Payouts", route: "/supplier/payouts", icon: DollarSign },
  { label: "View Orders", route: "/supplier/orders", icon: ShoppingCart },
  { label: "Export CSV", route: "/supplier/analytics/export/csv", icon: Download, isExport: true },
] as const;
