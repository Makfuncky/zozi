"use client";

import { usePathname, useSearchParams, useRouter } from "next/navigation";
import { useAuth } from "@/lib/useAuth";
import PanelShell from "@/components/PanelShell";
import { Crown, Globe } from "@/lib/icons";
import { useLocaleStore } from "@/lib/localeStore";
import { ADMIN_NAV_ITEMS, ADMIN_NAV_SECTIONS, canAccessAdminNavItem } from "@/lib/adminPanelConfig";
import { useAdminCountry } from "@/lib/useAdminCountry";

export default function AdminLayout({
  children,
  title,
  headerMode,
}: {
  children: React.ReactNode;
  title?: string;
  headerMode?: "default" | "compact";
}) {
  const { user, logout } = useAuth();
  const locale = useLocaleStore((s) => s.locale);
  const dir = ["ar", "fa", "ur"].includes(locale) ? "rtl" : "ltr";
  const isRtl = dir === "rtl";
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const router = useRouter();

  const currentRole = user?.role ?? null;
  const { selectedCountry, assignedCountries, setAdminCountry, loading } = useAdminCountry();

  const isCountryScopedRole = !!currentRole && (currentRole === "admin" || currentRole === "country_head" || currentRole === "country_manager");

  const canAccessAdminItem = (item: (typeof ADMIN_NAV_ITEMS)[number]) => canAccessAdminNavItem(item, currentRole);

  const visibleSections = ADMIN_NAV_SECTIONS.map((section) => ({
    ...section,
    items: section.items.filter(canAccessAdminItem),
  })).filter((section) => section.items.length > 0);
  const accessibleNavItems = ADMIN_NAV_ITEMS.filter(canAccessAdminItem);

  const isMenuItemActive = (item: (typeof ADMIN_NAV_ITEMS)[number]) => {
    const [path, query] = item.href.split("?");
    const pathMatches = pathname === path || pathname?.startsWith(`${path}/`);
    if (!pathMatches) {
      if (item.key === "barcode" && pathname === "/admin/barcode") return true;
      if (item.key === "product-verification" && pathname === "/admin/product-verification") return true;
      if (item.key === "returns" && pathname === "/admin/returns") return true;
      return false;
    }
    if (query) {
      const queryParams = new URLSearchParams(query);
      for (const [key, value] of queryParams.entries()) {
        if (searchParams?.get(key) !== value) {
          return false;
        }
      }
    }
    return true;
  };

  const handleLogout = async () => {
    await logout();
    router.push("/admin/login");
  };

  return (
    <PanelShell
      title={title}
      headerMode={headerMode}
      panelClassName="admin"
      brandLabel="ZOZI Admin"
      panelBadgeLabel="Admin Workspace"
      panelBadgeClassName="border-warning/35 bg-warning/10 text-warning"
      defaultTitle="Admin Dashboard"
      defaultDescription="Platform management and operational control"
      sections={visibleSections}
      allItems={accessibleNavItems}
      isActiveItem={isMenuItemActive}
      onLogout={handleLogout}
      logoutLabel="Logout"
      userName={user?.username}
      fallbackUserLabel="Admin"
      userSecondaryLabel={user?.role || "admin"}
      avatarIcon={Crown}
      avatarClassName="bg-warning"
      shortcutScope="admin"
      dir={dir}
      isRtl={isRtl}
    >
      {isCountryScopedRole && !loading && assignedCountries.length > 0 && (
        <div className="flex items-center gap-2 border-b border-border/60 bg-surface-2 px-3 py-2">
          <Globe className="h-3.5 w-3.5 text-text-muted" />
          <span className="text-[10px] font-semibold text-text-muted uppercase tracking-wider">Country:</span>
          <select
            data-testid="country-select-dropdown"
            className="rounded border border-border bg-surface px-2 py-1 text-xs text-text font-medium"
            value={selectedCountry?.code || ""}
            onChange={(e) => setAdminCountry(e.target.value)}
          >
            {!selectedCountry && <option value="">Select country...</option>}
            {assignedCountries.map((c) => (
              <option key={c.code} value={c.code}>{c.name} ({c.code})</option>
            ))}
          </select>
        </div>
      )}
      {children}
    </PanelShell>
  );
}
