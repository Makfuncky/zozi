"use client";

import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/useAuth";
import PanelShell from "@/components/PanelShell";
import { useLocaleStore } from "@/stores/localeStore";
import { useTranslateTexts } from "@/lib/useTranslate";
import { Briefcase } from "@/lib/icons";
import type { PanelNavItem } from "@/lib/panelNavigation";

const EMPLOYEE_NAV_GROUPS = [
  { key: "overview", label: "Overview" },
  { key: "work", label: "My Work" },
  { key: "account", label: "Account" },
];

const EMPLOYEE_NAV_ITEMS = [
  { key: "dashboard", group: "overview", name: "Dashboard", href: "/employee/dashboard", desc: "Overview of tasks, schedule, and key metrics", icon: Briefcase },
  { key: "tasks", group: "work", name: "My Tasks", href: "/employee/workspace/tasks", desc: "Tasks assigned by manager", icon: Briefcase },
  { key: "workspace", group: "work", name: "Workspace", href: "/employee/workspace", desc: "Role-based work tools", icon: Briefcase },
  { key: "schedule", group: "work", name: "Schedule", href: "/employee/schedule", desc: "Work schedule and shifts", icon: Briefcase },
  { key: "notifications", group: "work", name: "Notifications", href: "/employee/notifications", desc: "Work alerts and updates", icon: Briefcase },
  { key: "profile", group: "account", name: "My Profile", href: "/employee/profile", desc: "View and update personal information", icon: Briefcase },
  { key: "attendance", group: "account", name: "Attendance", href: "/employee/attendance", desc: "Clock in/out and timesheets", icon: Briefcase },
  { key: "leaves", group: "account", name: "Leaves", href: "/employee/leaves", desc: "Leave balance and requests", icon: Briefcase },
  { key: "payroll", group: "account", name: "Payroll", href: "/employee/payroll", desc: "Salary history and payslips", icon: Briefcase },
  { key: "performance", group: "account", name: "Performance", href: "/employee/performance", desc: "Goals, reviews, and KPIs", icon: Briefcase },
  { key: "training", group: "account", name: "Training", href: "/employee/training", desc: "Learning modules and certifications", icon: Briefcase },
  { key: "documents", group: "account", name: "Documents", href: "/employee/documents", desc: "Contracts, policies, and document vault", icon: Briefcase },
];

const EMPLOYEE_NAV_SECTIONS = EMPLOYEE_NAV_GROUPS.map((group) => ({
  ...group,
  items: EMPLOYEE_NAV_ITEMS.filter((item) => item.group === group.key),
})).filter((group) => group.items.length > 0);

export default function EmployeeLayout({ children, title }: { children: React.ReactNode; title?: string }) {
  const { user, logout } = useAuth();
  const pathname = usePathname();

  const locale = useLocaleStore((s) => s.locale);
  const dir = ["ar", "fa", "ur"].includes(locale) ? "rtl" : "ltr";
  const isRtl = dir === "rtl";

  const [dashboardLabel, translatedTitleValue, zoziEmployeeLabel, employeeWorkspaceLabel, employeeFallbackLabel, staffMemberLabel, logoutLabel, manageWorkLabel] = useTranslateTexts([
    "Dashboard",
    title || "Dashboard",
    "ZOZI Employee",
    "Employee Workspace",
    "Employee",
    "Staff Member",
    "Logout",
    "Manage your work and career",
  ]);

  const translatedTitle = title ? translatedTitleValue : undefined;
  const translatedGroupLabels = useTranslateTexts(EMPLOYEE_NAV_SECTIONS.map((section) => section.label));
  const translatedItemTexts = useTranslateTexts(EMPLOYEE_NAV_ITEMS.flatMap((item) => [item.name, item.desc]));

  const translatedItems = EMPLOYEE_NAV_ITEMS.map((item, index) => ({
    ...item,
    name: translatedItemTexts[index * 2] || item.name,
    desc: translatedItemTexts[index * 2 + 1] || item.desc,
  }));

  const translatedSections = EMPLOYEE_NAV_SECTIONS.map((section, sectionIndex) => ({
    ...section,
    label: translatedGroupLabels[sectionIndex] || section.label,
    items: translatedItems.filter((item) => item.group === section.key),
  }));

  const isActiveItem = (item: PanelNavItem): boolean =>
    !!(pathname === item.href || pathname?.startsWith(`${item.href}/`));

  return (
    <PanelShell
      title={translatedTitle || dashboardLabel}
      panelClassName="employee"
      brandLabel={zoziEmployeeLabel}
      panelBadgeLabel={employeeWorkspaceLabel}
      panelBadgeClassName="border-emerald-300 bg-emerald-50 text-emerald-700"
      defaultTitle={dashboardLabel}
      defaultDescription={manageWorkLabel}
      sections={translatedSections}
      allItems={translatedItems}
      isActiveItem={isActiveItem}
      onLogout={logout}
      logoutLabel={logoutLabel}
      userName={user?.username}
      fallbackUserLabel={employeeFallbackLabel}
      userSecondaryLabel={staffMemberLabel}
      avatarIcon={Briefcase}
      avatarClassName="bg-emerald-600"
      shortcutScope="supplier"
      dir={dir}
      isRtl={isRtl}
    >
      {children}
    </PanelShell>
  );
}
