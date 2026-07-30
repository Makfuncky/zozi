"use client";

import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Layers3, Network } from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelLoadingState, PanelTabs } from "@/components/PanelPage";
import { useAuth } from "@/lib/useAuth";
import { isAdminStaffRole } from "@shared/adminPermissions";
import dynamic from "next/dynamic";

const LogisticsPartnersPanel = dynamic(() => import("./_components/LogisticsPartnersPanel"), {
  loading: () => <PanelLoadingState count={3} blockClassName="h-24 rounded-xl bg-surface-2 animate-pulse" />
});

const SECTIONS = [
  { key: "partners", label: "Coverage & Routes", icon: Network },
  { key: "pricing", label: "Cost Drivers", icon: Layers3 },
] as const;

type Section = (typeof SECTIONS)[number]["key"];

function LogisticsHubInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isLoggedIn, isLoading } = useAuth();
  const requestedSection = searchParams?.get("section");
  const section = (SECTIONS.some((item) => item.key === requestedSection) ? requestedSection : "partners") as Section;

  useEffect(() => {
    if (!isLoading && (!isLoggedIn || !isAdminStaffRole(user?.role))) {
      router.replace("/admin/login");
    }
  }, [isLoading, isLoggedIn, router, user?.role]);

  if (isLoading) {
    return (
      <AdminLayout title="Logistics" headerMode="compact">
        <PanelLoadingState count={4} blockClassName="h-24 rounded-2xl bg-surface-2 animate-pulse" />
      </AdminLayout>
    );
  }

  if (!isLoggedIn || !isAdminStaffRole(user?.role)) {
    return null;
  }

  return (
    <AdminLayout title="Logistics" headerMode="compact">
      <PanelContent width="full" className="space-y-3">
        <div className="theme-card rounded-xl border p-2">
          <PanelTabs
            items={SECTIONS}
            value={section}
            onChange={(nextSection) => router.replace(`/admin/logistics?section=${nextSection}`, { scroll: false })}
            className="border-0 bg-transparent p-0"
          />
        </div>

        <section className="theme-card rounded-xl border p-3">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-text-faint">Logistics Admin Cycle</p>
          <h2 className="mt-1 text-sm font-semibold text-text">Coverage first, one simple charge model second</h2>
          <p className="mt-1 text-[11px] text-text-muted">Approve mapped service areas and route rows first, then manage one customer-charge story: base fee, weight, distance when needed, extra stops, and the highest approved handling fee. Vehicle fit stays operational only.</p>
        </section>

        <section className="theme-card rounded-xl border p-3">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-text-faint">Cost Drivers</p>
          <h2 className="mt-1 text-sm font-semibold text-text">Partner registry and service-area review</h2>
          <p className="mt-1 text-[11px] text-text-muted">Review pricing profiles, handling rules and vehicle fit per partner and service area before they go live.</p>
        </section>

        {section === "partners" ? <LogisticsPartnersPanel key="partners-scope" scope="partners" /> : null}
        {section === "pricing" ? <LogisticsPartnersPanel key="cost-drivers-scope" scope="pricing" /> : null}
      </PanelContent>
    </AdminLayout>
  );
}

export default function LogisticsHubPage() {
  return (
    <Suspense>
      <LogisticsHubInner />
    </Suspense>
  );
}
