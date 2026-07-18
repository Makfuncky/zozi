import type { ComponentType } from "react";
import {
  BadgeCheck,
  BarChart3,
  Bell,
  BookOpen,
  FileText,
  Film,
  Globe2,
  LayoutDashboard,
  Map,
  MessageSquare,
  Package,
  ShieldAlert,
  ScanLine,
  ShoppingCart,
  Truck,
  Upload,
  User,
  Wallet,
} from "@/lib/icons";

export type PanelNavIcon = ComponentType<{ className?: string }>;

export interface PanelNavGroup {
  key: string;
  label: string;
}

export interface PanelNavItem {
  key: string;
  group: string;
  name: string;
  href: string;
  desc: string;
  icon: PanelNavIcon;
  hideFromNav?: boolean;
}

export interface PanelNavSection extends PanelNavGroup {
  items: PanelNavItem[];
}

export const SUPPLIER_NAV_GROUPS: PanelNavGroup[] = [
  { key: "overview", label: "Overview" },
  { key: "operations", label: "Operations" },
  { key: "finance", label: "Finance" },
  { key: "account", label: "Account" },
];

export const SUPPLIER_NAV_ITEMS: PanelNavItem[] = [
  {
    key: "dashboard",
    group: "overview",
    name: "Dashboard",
    href: "/supplier/dashboard",
    desc: "Overview, momentum, and fulfillment health",
    icon: LayoutDashboard,
  },
  {
    key: "analytics",
    group: "overview",
    name: "Analytics",
    href: "/supplier/analytics",
    desc: "Sales, conversion, and product performance",
    icon: BarChart3,
  },
  {
    key: "reports",
    group: "overview",
    name: "Reports",
    href: "/supplier/reports",
    desc: "Exports, summaries, and scheduled insights",
    icon: FileText,
  },
  {
    key: "products",
    group: "operations",
    name: "Products",
    href: "/supplier/products",
    desc: "Catalog, pricing, stock, and returns policy",
    icon: Package,
  },
  {
    key: "videos",
    group: "operations",
    name: "Videos",
    href: "/supplier/videos/upload",
    desc: "Upload and manage product videos",
    icon: Film,
  },
  {
    key: "orders",
    group: "operations",
    name: "Orders",
    href: "/supplier/orders",
    desc: "Order handling, returns, and shipment prep",
    icon: ShoppingCart,
  },
  {
    key: "returns",
    group: "operations",
    name: "Returns",
    href: "/supplier/returns",
    desc: "Return approvals and dispute handling",
    icon: FileText,
    hideFromNav: true,
  },
  {
    key: "disputes",
    group: "operations",
    name: "Disputes",
    href: "/supplier/disputes",
    desc: "Submit evidence and track dispute arbitration status",
    icon: ShieldAlert,
    hideFromNav: true,
  },
  {
    key: "logistics",
    group: "operations",
    name: "Logistics",
    href: "/supplier/logistics",
    desc: "Carrier coordination and delivery coverage",
    icon: Truck,
    hideFromNav: true,
  },
  {
    key: "payouts",
    group: "finance",
    name: "Payouts",
    href: "/supplier/payouts",
    desc: "Earnings, holds, and withdrawal requests",
    icon: Wallet,
  },
  {
    key: "invoices",
    group: "finance",
    name: "Invoices",
    href: "/supplier/invoices",
    desc: "Invoice history and settlement paperwork",
    icon: FileText,
    hideFromNav: true,
  },
  {
    key: "support",
    group: "account",
    name: "Support",
    href: "/supplier/support",
    desc: "Admin messaging, disputes, and issue tracking",
    icon: MessageSquare,
  },
  {
    key: "notification-preferences",
    group: "account",
    name: "Notifications",
    href: "/supplier/notification-preferences",
    desc: "Control event and channel notification preferences",
    icon: Bell,
  },
  {
    key: "credibility",
    group: "account",
    name: "Credibility",
    href: "/supplier/credibility",
    desc: "Trust score, badges, and store reputation",
    icon: BadgeCheck,
  },
  {
    key: "documents",
    group: "account",
    name: "Documents",
    href: "/supplier/documents",
    desc: "Compliance documents and uploads",
    icon: FileText,
    hideFromNav: true,
  },
  {
    key: "profile",
    group: "account",
    name: "Profile",
    href: "/supplier/profile",
    desc: "Business identity, KYC, and storefront info",
    icon: User,
  },
  {
    key: "guide",
    group: "account",
    name: "Guide",
    href: "/supplier/guide",
    desc: "Policies, onboarding, and operational playbooks",
    icon: BookOpen,
    hideFromNav: true,
  },
  {
    key: "bulk",
    group: "operations",
    name: "Bulk Upload",
    href: "/supplier/bulk",
    desc: "Mass product import and CSV workflows",
    icon: Upload,
    hideFromNav: true,
  },
  {
    key: "inventory",
    group: "operations",
    name: "Inventory",
    href: "/supplier/inventory",
    desc: "Inventory health and warehouse visibility",
    icon: Package,
    hideFromNav: true,
  },
  {
    key: "labels",
    group: "operations",
    name: "Parcel Labels",
    href: "/supplier/labels",
    desc: "Packing slips and printable parcel labels",
    icon: FileText,
    hideFromNav: true,
  },
  {
    key: "regions",
    group: "account",
    name: "Regions",
    href: "/supplier/regions",
    desc: "Country and regional delivery configuration",
    icon: Globe2,
    hideFromNav: true,
  },
  {
    key: "terms",
    group: "account",
    name: "Terms",
    href: "/supplier/terms",
    desc: "Supplier agreement and policy reference",
    icon: BookOpen,
    hideFromNav: true,
  },
];

export const SUPPLIER_NAV_SECTIONS: PanelNavSection[] = SUPPLIER_NAV_GROUPS.map((group) => ({
  ...group,
  items: SUPPLIER_NAV_ITEMS.filter((item) => item.group === group.key && !item.hideFromNav),
})).filter((group) => group.items.length > 0);

export const LOGISTICS_NAV_GROUPS: PanelNavGroup[] = [
  { key: "overview", label: "Overview" },
  { key: "operations", label: "Operations" },
  { key: "finance", label: "Finance" },
  { key: "account", label: "Account" },
];

export const LOGISTICS_NAV_ITEMS: PanelNavItem[] = [
  {
    key: "dashboard",
    group: "overview",
    name: "Dashboard",
    href: "/logistics-partner/dashboard",
    desc: "Live network health, SLA, and route activity",
    icon: LayoutDashboard,
  },
  {
    key: "analytics",
    group: "overview",
    name: "Analytics",
    href: "/logistics-partner/analytics",
    desc: "Delivery KPIs, scan coverage, and SLA trends",
    icon: BarChart3,
  },
  {
    key: "shipments",
    group: "operations",
    name: "Shipments",
    href: "/logistics-partner/shipments",
    desc: "Pickup acceptance, delivery flow, and exceptions",
    icon: Package,
  },
  {
    key: "scan",
    group: "operations",
    name: "Scan",
    href: "/logistics-partner/scan",
    desc: "Barcode scans and field confirmation tools",
    icon: ScanLine,
  },
  {
    key: "payouts",
    group: "finance",
    name: "Payouts",
    href: "/logistics-partner/payouts",
    desc: "Earnings, balances, and payout requests",
    icon: Wallet,
  },
  {
    key: "support",
    group: "account",
    name: "Support",
    href: "/tickets",
    desc: "Admin messaging and issue escalation",
    icon: MessageSquare,
  },
  {
    key: "profile",
    group: "account",
    name: "Profile",
    href: "/logistics-partner/profile",
    desc: "Business identity, rates, and operating settings",
    icon: User,
  },
  {
    key: "routes",
    group: "operations",
    name: "Coverage",
    href: "/logistics-partner/routes",
    desc: "Route planning and territory configuration",
    icon: Map,
    hideFromNav: true,
  },
];

export const LOGISTICS_NAV_SECTIONS: PanelNavSection[] = LOGISTICS_NAV_GROUPS.map((group) => ({
  ...group,
  items: LOGISTICS_NAV_ITEMS.filter((item) => item.group === group.key && !item.hideFromNav),
})).filter((group) => group.items.length > 0);
