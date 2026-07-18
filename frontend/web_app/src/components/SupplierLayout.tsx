"use client";

import { usePathname } from "next/navigation";
import { useAuth, useRequireSupplier } from "@/lib/useAuth";
import PanelShell from "@/components/PanelShell";
import { useLocaleStore } from "@/lib/localeStore";
import { useTranslateTexts } from "@/lib/useTranslate";
import { Package } from "@/lib/icons";
import { SUPPLIER_NAV_ITEMS, SUPPLIER_NAV_SECTIONS } from "@/lib/panelNavigation";

export default function SupplierLayout({ children, title }: { children: React.ReactNode; title?: string }) {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  useRequireSupplier();

  const locale = useLocaleStore((s) => s.locale);
  const dir = ["ar", "fa", "ur"].includes(locale) ? "rtl" : "ltr";
  const isRtl = dir === "rtl";
  const [dashboardLabel, translatedTitleValue, zoziSupplierLabel, supplierWorkspaceLabel, supplierFallbackLabel, premiumSellerLabel, logoutLabel, manageBusinessLabel] = useTranslateTexts([
    "Dashboard",
    title || "Dashboard",
    "ZOZI Supplier",
    "Supplier Workspace",
    "Supplier",
    "Premium Seller",
    "Logout",
    "Manage your business",
  ]);
  const translatedTitle = title ? translatedTitleValue : undefined;
  const translatedGroupLabels = useTranslateTexts(SUPPLIER_NAV_SECTIONS.map((section) => section.label));
  const translatedItemTexts = useTranslateTexts(SUPPLIER_NAV_ITEMS.flatMap((item) => [item.name, item.desc]));
  const translatedItems = SUPPLIER_NAV_ITEMS.map((item, index) => ({
    ...item,
    name: translatedItemTexts[index * 2] || item.name,
    desc: translatedItemTexts[index * 2 + 1] || item.desc,
  }));
  const translatedSections = SUPPLIER_NAV_SECTIONS.map((section, sectionIndex) => ({
    ...section,
    label: translatedGroupLabels[sectionIndex] || section.label,
    items: translatedItems.filter((item) => item.group === section.key && !item.hideFromNav),
  }));
  const isActiveItem = (item: (typeof translatedItems)[number]): boolean => !!(pathname === item.href || pathname?.startsWith(`${item.href}/`));

  return (
    <PanelShell
      title={translatedTitle || dashboardLabel}
      panelClassName="supplier"
      brandLabel={zoziSupplierLabel}
      panelBadgeLabel={supplierWorkspaceLabel}
      panelBadgeClassName="border-primary/30 bg-primary/10 text-primary"
      defaultTitle={dashboardLabel}
      defaultDescription={manageBusinessLabel}
      sections={translatedSections}
      allItems={translatedItems}
      isActiveItem={isActiveItem}
      onLogout={logout}
      logoutLabel={logoutLabel}
      userName={user?.username}
      fallbackUserLabel={supplierFallbackLabel}
      userSecondaryLabel={premiumSellerLabel}
      avatarIcon={Package}
      avatarClassName="bg-primary"
      shortcutScope="supplier"
      dir={dir}
      isRtl={isRtl}
    >
      {children}
    </PanelShell>
  );
}
