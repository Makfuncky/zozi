"use client";

import { Suspense, useEffect, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ShieldCheck, MessageSquare, ShieldAlert, AlertTriangle } from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelLoadingState, PanelTabs } from "@/components/PanelPage";
import { useAuth } from "@/lib/useAuth";
import { isAdminStaffRole, hasAdminPermission } from "@shared/adminPermissions";
import { useAdminCountry } from "@/lib/useAdminCountry";

import ModerationPage from "../dashboard/_tabs/ModerationTab";
import TicketsPage from "../dashboard/_tabs/TicketsTab";
import AdminDisputesPage from "../disputes/_components/DisputesPanel";

function ResolutionInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const section = searchParams?.get("section") ?? "moderation";
  const { user, isLoggedIn, isLoading } = useAuth();
  const role = user?.role ?? null;
  const { selectedCountry, isGlobalView } = useAdminCountry();

  const roleInst = role ?? "";
  const tabs = useMemo(() => {
    const items = [
      { key: "moderation", label: "Moderation", icon: ShieldCheck },
      { key: "tickets", label: "Tickets", icon: MessageSquare },
      { key: "disputes", label: "Disputes", icon: ShieldAlert },
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
      <AdminLayout title="Resolution Center" headerMode="compact">
        <PanelLoadingState count={3} blockClassName="h-14 rounded-xl bg-surface-2 animate-pulse" />
      </AdminLayout>
    );
  }

  return (
    <AdminLayout title="Resolution Center" headerMode="compact">
      <PanelContent className="space-y-4">
        <div className="theme-card rounded-xl border p-2">
          <PanelTabs
            items={tabs}
            value={section}
            onChange={(next) => router.push(`/admin/resolution?section=${next}`)}
            className="border-0 bg-transparent p-0"
          />
        </div>

        {section === "moderation" && <ModerationPage />}
        {section === "tickets" && <TicketsPage />}
        {section === "disputes" && <AdminDisputesPage />}
      </PanelContent>
    </AdminLayout>
  );
}

export default function ResolutionPage() {
  return (
    <Suspense fallback={<PanelLoadingState count={3} />}>
      <ResolutionInner />
    </Suspense>
  );
}
