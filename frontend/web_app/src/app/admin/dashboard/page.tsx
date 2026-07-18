"use client";

import React, { useEffect, useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";

const MotionDiv = motion.div as any;

import {
  Grid2x2, LayoutGrid, Rows3, Users, Package, ShoppingCart, TrendingUp, Store, Download,
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";

import { useAuth } from "@/lib/useAuth";
import { useLocaleStore } from "@/lib/localeStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useAdminCountry } from "@/lib/useAdminCountry";
import { ADMIN_DASHBOARD_FEATURED_ITEMS, ADMIN_LEGACY_DASHBOARD_REDIRECTS, ADMIN_NAV_ITEMS, canAccessAdminNavItem } from "@/lib/adminPanelConfig";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelLoadingState, PanelTabs } from "@/components/PanelPage";
import TranslatedText from "@/components/TranslatedText";
import ExportsPanel from "./ExportsPanel";
import { hasAdminPermission, isAdminStaffRole } from "@shared/adminPermissions";
import { isRtlLocale } from "@shared/localization";

// -- Types --

type Tab = "overview" | "insights" | "exports";
type DashboardGridMode = "compact" | "balanced" | "expanded";

const DASHBOARD_GRID_MODE_KEY = "admin-dashboard-grid-mode";

// -- Component --

function AdminDashboardInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();
  const locale = useLocaleStore((s) => s.locale);
  const isRtl = isRtlLocale(locale);
  const formatMoney = useCurrencyStore((s) => s.format);
  const { selectedCountry, assignedCountries } = useAdminCountry();
  const role: string | null = user?.role ?? null;
  const rawTab = searchParams?.get("tab") ?? "overview";
  const tab = rawTab as Tab;
  const legacyRedirectTarget = ADMIN_LEGACY_DASHBOARD_REDIRECTS[rawTab];
  const [loading, setLoading] = useState(true);
  const [gridMode, setGridMode] = useState<DashboardGridMode>("balanced");

  // Data states
  const [stats, setStats] = useState({ users: 0, suppliers: 0, products: 0, orders: 0, revenue: 0 });

  useEffect(() => {
    try {
      const stored = localStorage.getItem(DASHBOARD_GRID_MODE_KEY) as DashboardGridMode | null;
      if (stored === "compact" || stored === "balanced" || stored === "expanded") {
        setGridMode(stored);
      }
    } catch {}
  }, []);

  const updateGridMode = (nextMode: DashboardGridMode) => {
    setGridMode(nextMode);
    try {
      localStorage.setItem(DASHBOARD_GRID_MODE_KEY, nextMode);
    } catch {}
  };

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn || !isAdminStaffRole(role)) {
      router.push("/admin/login");
      return;
    }
    if (legacyRedirectTarget) {
      setLoading(false);
      router.replace(legacyRedirectTarget);
      return;
    }

    const fetchAll = async () => {
      try {
        const canViewAnalytics = hasAdminPermission(role, "analytics.view");
        const dashboardCountry = selectedCountry?.code || assignedCountries[0]?.code || null;
        const analyticsRes = canViewAnalytics && dashboardCountry
          ? await apiFetch(`/admin/${dashboardCountry}/dashboard`).then((r) => (r.ok ? r.json() : {})).catch(() => ({}))
          : {};

        if (analyticsRes && typeof analyticsRes === "object") {
          const ar = analyticsRes as any;
          setStats({
            users: ar.total_users ?? 0,
            suppliers: ar.total_suppliers ?? 0,
            products: ar.total_products ?? 0,
            orders: ar.total_orders ?? 0,
            revenue: ar.total_revenue ?? 0,
          });
        }
      } catch {}
      setLoading(false);
    };

    fetchAll();
  }, [authLoading, isLoggedIn, legacyRedirectTarget, role, router]);

  const operationalShortcuts = [
    "logistics",
    "countries",
    "finance",
    "promotions",
    "tickets",
    "moderation",
    "staff",
  ]
    .map((key) => ADMIN_NAV_ITEMS.find((item) => item.key === key) ?? null)
    .filter((item): item is NonNullable<typeof item> => item !== null)
    .filter((item) => canAccessAdminNavItem(item, role));
  const featuredItems = ADMIN_DASHBOARD_FEATURED_ITEMS.filter((item) => canAccessAdminNavItem(item, role));

  const statGridClass = gridMode === "compact"
    ? "grid grid-cols-2 gap-2 lg:grid-cols-5"
    : gridMode === "expanded"
      ? "grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5"
      : "grid grid-cols-2 gap-3 lg:grid-cols-5";
  const featuredGridClass = gridMode === "compact"
    ? "grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-5"
    : gridMode === "expanded"
      ? "grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3"
      : "grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-4";
  const cardPaddingClass = gridMode === "compact" ? "p-2.5" : gridMode === "expanded" ? "p-4" : "p-3";

  if (authLoading || loading) {
    return (
      <AdminLayout title="Dashboard">
        <PanelLoadingState count={4} />
      </AdminLayout>
    );
  }

  if (legacyRedirectTarget) {
    return (
      <AdminLayout title="Dashboard">
        <PanelContent>
          <div className="theme-card rounded-xl border p-6 text-xs text-text-muted">
            Opening the consolidated workspace for this admin area...
          </div>
        </PanelContent>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout title="Dashboard">
      <PanelContent className="space-y-4" dir={isRtl ? "rtl" : "ltr"}>

        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-text-faint">Workspace Density</p>
            <p className="mt-1 text-xs text-text-muted">Choose how many dashboard widgets fit in view.</p>
          </div>
          <div className="inline-flex overflow-hidden rounded-xl border border-border bg-surface-1 shadow-sm">
            {[
              { key: "compact", label: "Compact", icon: Rows3 },
              { key: "balanced", label: "Balanced", icon: LayoutGrid },
              { key: "expanded", label: "Expanded", icon: Grid2x2 },
            ].map((option) => (
              <button
                key={option.key}
                type="button"
                onClick={() => updateGridMode(option.key as DashboardGridMode)}
                aria-pressed={gridMode === option.key}
                className={`inline-flex items-center gap-1.5 border-l border-border px-3 py-2 text-xs font-medium transition-colors first:border-l-0 ${
                  gridMode === option.key ? "bg-primary/10 text-primary" : "text-text-muted hover:bg-surface-2 hover:text-text"
                }`}
              >
                <option.icon className="h-3.5 w-3.5" />
                {option.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab bar */}
        <PanelTabs
          value={tab}
          onChange={(k) =>
            router.replace(`/admin/dashboard${k === "overview" ? "" : `?tab=${k}`}`, { scroll: false })
          }
          items={[
            { key: "overview", label: "Overview", icon: TrendingUp },
            ...(role === "admin" ? [{ key: "exports" as const, label: "Exports", icon: Download }] : []),
          ]}
        />

        {/* Stats */}
        <div className={statGridClass}>
          {[
            { label: "Users", value: stats.users, icon: Users, bg: "theme-chip-info" },
            { label: "Suppliers", value: stats.suppliers, icon: Store, bg: "theme-chip-brand" },
            { label: "Products", value: stats.products, icon: Package, bg: "theme-chip-success" },
            { label: "Orders", value: stats.orders, icon: ShoppingCart, bg: "theme-chip-warning" },
            { label: "Revenue", value: formatMoney(stats.revenue), icon: TrendingUp, bg: "theme-chip-success" },
          ].map((s, i) => (
            <MotionDiv
              key={s.label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className={`theme-card theme-stat-card rounded-xl border ${cardPaddingClass}`}
            >
              <div className={`mb-2 flex h-8 w-8 items-center justify-center rounded-xl ${s.bg}`}>
                <s.icon className="w-3.5 h-3.5" />
              </div>
              <p className="text-base font-bold text-text">{s.value}</p>
              <p className="text-xs text-text-muted"><TranslatedText text={s.label} /></p>
            </MotionDiv>
          ))}
        </div>

        {tab === "overview" && (
          <>
            <div className={`theme-card rounded-xl border ${gridMode === "compact" ? "p-3" : "p-4"}`}>
              <h2 className="mb-4 text-xs font-bold text-text">Primary Workspaces</h2>
              <div className={featuredGridClass}>
                {featuredItems.map((item) => (
                  <Link
                    key={item.key}
                    href={item.href}
                    className={`theme-elevated group rounded-xl border border-border/80 transition-colors hover:bg-surface-2/70 ${cardPaddingClass}`}
                  >
                    <div className="mb-2 flex h-8 w-8 items-center justify-center rounded-xl theme-chip-brand">
                      <item.icon className="h-4 w-4 theme-status-info" />
                    </div>
                    <p className="text-xs font-semibold text-text">{item.name}</p>
                    <p className="mt-1 text-xs text-text-muted">{item.desc}</p>
                    <p className="mt-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-primary">
                      Open workspace
                    </p>
                  </Link>
                ))}
              </div>
            </div>

            <div className={`theme-card rounded-xl border ${gridMode === "compact" ? "p-3" : "p-4"}`}>
              <h2 className="mb-3 text-xs font-bold text-text">Operational Hubs</h2>
              <div className="flex flex-wrap gap-2">
                {operationalShortcuts.map((item) =>
                  item ? (
                    <Link
                      key={item.key}
                      href={item.href}
                      className="theme-elevated inline-flex items-center gap-2 rounded-full border border-border/80 px-3 py-2 text-xs font-medium text-text-muted transition-colors hover:text-text"
                    >
                      <item.icon className="h-3.5 w-3.5" />
                      <span>{item.name}</span>
                    </Link>
                  ) : null
                )}
              </div>
            </div>
          </>
        )}

        {tab === "exports" && role === "admin" && <ExportsPanel />}
      </PanelContent>
    </AdminLayout>
  );
}

export default function AdminDashboardPage() {
  return (
    <Suspense>
      <AdminDashboardInner />
    </Suspense>
  );
}