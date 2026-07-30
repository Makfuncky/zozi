"use client";

import { Suspense, useEffect, useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Megaphone, Settings2, Tag, Zap, Globe } from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelLoadingState, PanelTabs } from "@/components/PanelPage";
import { useAuth } from "@/lib/useAuth";
import { isAdminStaffRole } from "@shared/adminPermissions";
import { useAdminCountry } from "@/lib/useAdminCountry";
import { apiFetch, parseJsonResponse } from "@/lib/api";

import dynamic from "next/dynamic";

const BannersPanel = dynamic(() => import("./_components/BannersPanel"), {
  loading: () => <PanelLoadingState count={2} blockClassName="h-32 rounded-xl bg-surface-2 animate-pulse" />
});
const CouponsPanel = dynamic(() => import("./_components/CouponsPanel"), {
  loading: () => <PanelLoadingState count={2} blockClassName="h-32 rounded-xl bg-surface-2 animate-pulse" />
});
const FlashSalesPanel = dynamic(() => import("./_components/FlashSalesPanel"), {
  loading: () => <PanelLoadingState count={2} blockClassName="h-32 rounded-xl bg-surface-2 animate-pulse" />
});
const PromotionBuilderPanel = dynamic(() => import("./_components/PromotionBuilderPanel"), {
  loading: () => <PanelLoadingState count={3} blockClassName="h-24 rounded-xl bg-surface-2 animate-pulse" />
});

const SECTIONS = [
  { key: "builder", label: "Promotion Builder", icon: Settings2 },
  { key: "banners", label: "Banners", icon: Megaphone },
  { key: "coupons", label: "Coupons", icon: Tag },
  { key: "flash-sales", label: "Flash Sales", icon: Zap },
] as const;

type Section = (typeof SECTIONS)[number]["key"];

interface PromoMetrics {
  banners: number;
  coupons: number;
  flash_sales: number;
  tiers: number;
}

function PromotionsHubInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isLoggedIn, isLoading } = useAuth();
  const { selectedCountry } = useAdminCountry();
  const countryCode = selectedCountry?.code || "*";
  const section = (searchParams?.get("section") || "builder") as Section;

  const [metrics, setMetrics] = useState<PromoMetrics | null>(null);
  const [metricsLoading, setMetricsLoading] = useState(true);

  const loadMetrics = useCallback(async () => {
    setMetricsLoading(true);
    try {
      const ccSuffix = countryCode && countryCode !== "*" ? `/${countryCode}` : "";
      const [bannersRes, couponsRes, flashRes, tiersRes] = await Promise.allSettled([
        apiFetch(`/admin/banners${ccSuffix}?page=1&page_size=1`),

        apiFetch(`/admin/promotions/coupons${ccSuffix}`),

        apiFetch(`/admin/promotions/flash-sales${ccSuffix}`),

        apiFetch(`/admin/promotions/tiers${ccSuffix}`),
      ]);

      const getCount = async (res: PromiseSettledResult<Response>, extractTotal?: (d: any) => number) => {
        if (res.status !== "fulfilled" || !res.value.ok) return 0;
        const data = await parseJsonResponse(res.value);
        if (extractTotal) return extractTotal(data);
        if (Array.isArray(data)) return data.length;
        return data?.total ?? data?.items?.length ?? 0;
      };

      setMetrics({
        banners: await getCount(bannersRes, (d) => d?.total ?? d?.items?.length ?? 0),
        coupons: await getCount(couponsRes),
        flash_sales: await getCount(flashRes),
        tiers: await getCount(tiersRes),
      });
    } catch {
      setMetrics(null);
    } finally {
      setMetricsLoading(false);
    }
  }, [countryCode]);

  useEffect(() => { loadMetrics(); }, [loadMetrics]);

  if (isLoading) {
    return (
      <AdminLayout title="Promotions" headerMode="compact">
        <PanelLoadingState count={4} />
      </AdminLayout>
    );
  }

  if (!isLoggedIn || !isAdminStaffRole(user?.role)) {
    router.push("/admin/login");
    return null;
  }

  return (
    <AdminLayout title="Promotions" headerMode="compact">
      <PanelContent className="space-y-4">
        {/* Country badge */}
        {selectedCountry && selectedCountry.code !== "*" && (
          <div className="flex items-center gap-2 rounded-lg border border-glass-border bg-glass-panel px-3 py-2">
            <Globe className="h-4 w-4 text-primary" />
            <span className="text-xs font-medium text-text">{selectedCountry.name}</span>
            <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-mono font-semibold text-primary">{selectedCountry.code}</span>
          </div>
        )}

        {/* Metrics summary */}
        {!metricsLoading && metrics && (
          <div className="grid grid-cols-4 gap-3">
            {[
              { label: "Banners", value: metrics.banners, icon: Megaphone, color: "text-info" },
              { label: "Coupons", value: metrics.coupons, icon: Tag, color: "text-success" },
              { label: "Flash Sales", value: metrics.flash_sales, icon: Zap, color: "text-amber-400" },
              { label: "Tiers", value: metrics.tiers, icon: Settings2, color: "text-purple-400" },
            ].map((m) => (
              <div key={m.label} className="theme-card rounded-xl border p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-text-faint">{m.label}</p>
                    <p className="mt-0.5 text-xl font-bold text-text">{m.value}</p>
                  </div>
                  <div className={`${m.color} opacity-60`}>
                    <m.icon className="h-6 w-6" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        <PanelTabs
          items={SECTIONS}
          value={section}
          onChange={(nextSection) => router.replace(`/admin/promotions?section=${nextSection}`, { scroll: false })}
        />

        {section === "builder" && <PromotionBuilderPanel />}
        {section === "banners" && <BannersPanel />}
        {section === "coupons" && <CouponsPanel />}
        {section === "flash-sales" && <FlashSalesPanel />}
      </PanelContent>
    </AdminLayout>
  );
}

export default function PromotionsHubPage() {
  return (
    <Suspense>
      <PromotionsHubInner />
    </Suspense>
  );
}
