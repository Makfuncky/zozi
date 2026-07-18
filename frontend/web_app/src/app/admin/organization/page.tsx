"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Users, Crown, Lock, Network, Building2, Shield } from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelLoadingState, PanelTabs } from "@/components/PanelPage";
import { useAuth } from "@/lib/useAuth";
import { isAdminStaffRole, hasAdminPermission } from "@shared/adminPermissions";
import { useAdminCountry } from "@/lib/useAdminCountry";

import { StaffContent } from "../staff/staff-content";
import { PermissionsContent } from "../permissions/permissions-content";
import { EmployeesContent } from "../employees/employees-content";
import HierarchyTab from "../dashboard/tabs/HierarchyTab";

function OrganizationInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const section = searchParams?.get("section") ?? "staff";
  const { user, isLoggedIn, isLoading } = useAuth();
  const role = user?.role ?? null;
  const isAdmin = role === "admin";
  const { selectedCountry, isGlobalView } = useAdminCountry();

  const tabs = useMemo(() => {
    const items = [
      { key: "staff", label: "Staff Accounts", icon: Crown },
      { key: "employees", label: "Employees (HCM)", icon: Users },
      { key: "permissions", label: "Permissions", icon: Lock },
      { key: "hierarchy", label: "Hierarchy", icon: Network },
    ];
    return items;
  }, []);

  useEffect(() => {
    if (isLoading) return;
    if (!isLoggedIn || !isAdminStaffRole(role)) {
      router.push("/admin/login");
    }
  }, [isLoading, isLoggedIn, role, router]);

  if (isLoading || !isLoggedIn || !isAdminStaffRole(role)) {
    return (
      <AdminLayout title="Organization" headerMode="compact">
        <PanelLoadingState count={4} blockClassName="h-14 rounded-xl bg-surface-2 animate-pulse" />
      </AdminLayout>
    );
  }

  return (
    <AdminLayout title="Organization Management" headerMode="compact">
      <PanelContent className="space-y-4">
        <div className="flex items-center gap-2 text-[11px] text-text-faint bg-surface-2 rounded-lg px-3 py-1.5">
          <Shield className="h-3 w-3" />
          <span>{isGlobalView ? "Global View — All Countries" : `Country: ${selectedCountry?.name || selectedCountry?.code}`}</span>
        </div>

        <div className="theme-card rounded-xl border p-2">
          <PanelTabs
            items={tabs}
            value={section}
            onChange={(next) => router.push(`/admin/organization?section=${next}`)}
            className="border-0 bg-transparent p-0"
          />
        </div>

        {section === "staff" && isAdmin && <StaffContent />}
        {section === "employees" && isAdmin && <EmployeesContent />}
        {section === "permissions" && isAdmin && <PermissionsContent />}
        {section === "hierarchy" && (
          <div className="theme-card rounded-xl border p-4">
            <HierarchyTab />
          </div>
        )}
      </PanelContent>
    </AdminLayout>
  );
}

export default function OrganizationPage() {
  return (
    <Suspense fallback={<PanelLoadingState count={4} />}>
      <OrganizationInner />
    </Suspense>
  );
}
