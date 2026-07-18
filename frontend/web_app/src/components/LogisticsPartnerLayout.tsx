"use client";

import { usePathname } from "next/navigation";
import { useAuth, useRequireLogisticsPartner } from "@/lib/useAuth";
import PanelShell from "@/components/PanelShell";
import { useLocaleStore } from "@/lib/localeStore";
import { useTranslateTexts } from "@/lib/useTranslate";
import { Truck } from "@/lib/icons";
import { LOGISTICS_NAV_ITEMS, LOGISTICS_NAV_SECTIONS } from "@/lib/panelNavigation";

export default function LogisticsPartnerLayout({ children, title }: { children: React.ReactNode; title?: string }) {
  const { user, isLoading } = useRequireLogisticsPartner();
  const { logout } = useAuth();
  const pathname = usePathname();

  const locale = useLocaleStore((s) => s.locale);
  const dir = ["ar", "fa", "ur"].includes(locale) ? "rtl" : "ltr";
  const isRtl = dir === "rtl";
  const [dashboardLabel, translatedTitleValue, zoziLogisticsLabel, logisticsWorkspaceLabel, partnerFallbackLabel, logisticsPartnerLabel, logoutLabel, manageLogisticsLabel] = useTranslateTexts([
    "Dashboard",
    title || "Dashboard",
    "ZOZI Logistics",
    "Logistics Workspace",
    "Partner",
    "Logistics Partner",
    "Logout",
    "Manage your logistics",
  ]);
  const translatedTitle = title ? translatedTitleValue : undefined;
  const translatedGroupLabels = useTranslateTexts(LOGISTICS_NAV_SECTIONS.map((section) => section.label));
  const translatedItemTexts = useTranslateTexts(LOGISTICS_NAV_ITEMS.flatMap((item) => [item.name, item.desc]));
  const translatedItems = LOGISTICS_NAV_ITEMS.map((item, index) => ({
    ...item,
    name: translatedItemTexts[index * 2] || item.name,
    desc: translatedItemTexts[index * 2 + 1] || item.desc,
  }));
  const translatedSections = LOGISTICS_NAV_SECTIONS.map((section, sectionIndex) => ({
    ...section,
    label: translatedGroupLabels[sectionIndex] || section.label,
    items: translatedItems.filter((item) => item.group === section.key && !item.hideFromNav),
  }));
  const isActiveItem = (item: (typeof translatedItems)[number]): boolean => !!(pathname === item.href || pathname?.startsWith(`${item.href}/`));

  const hasAccess = !!user && user.role === "logistics_partner";

  if (isLoading || !hasAccess) {
    return (
      <div className="flex h-screen items-center justify-center bg-surface-base">
        <div className="h-8 w-8 rounded-full border-2 border-accent border-t-transparent animate-spin" />
      </div>
    );
  }

  return (
    <PanelShell
      title={translatedTitle || dashboardLabel}
      panelClassName="logistics-partner"
      brandLabel={zoziLogisticsLabel}
      panelBadgeLabel={logisticsWorkspaceLabel}
      panelBadgeClassName="border-info/30 bg-info/10 text-info"
      defaultTitle={dashboardLabel}
      defaultDescription={manageLogisticsLabel}
      sections={translatedSections}
      allItems={translatedItems}
      isActiveItem={isActiveItem}
      onLogout={logout}
      logoutLabel={logoutLabel}
      userName={user?.username}
      fallbackUserLabel={partnerFallbackLabel}
      userSecondaryLabel={logisticsPartnerLabel}
      avatarIcon={Truck}
      avatarClassName="bg-primary"
      shortcutScope="logistics"
      dir={dir}
      isRtl={isRtl}
    >
      {children}
    </PanelShell>
  );
}
