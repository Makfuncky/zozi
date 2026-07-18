"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import SupplierLayout from "@/components/SupplierLayout";
import { PanelContent, PanelHero, PanelLoadingState } from "@/components/PanelPage";
import { apiFetch, getErrorMessage, parseJsonResponse } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";
import { BadgeCheck, ArrowRight, Loader2, ShieldCheck } from "@/lib/icons";

type BadgeTier = {
  badge_level: string;
  commission_rate: number;
  min_fulfilled_orders: number;
  min_monthly_revenue: number;
  is_current?: boolean;
  is_eligible?: boolean;
  is_recommended?: boolean;
};

type BadgeCatalog = {
  current_badge_level?: string;
  eligible_badge_level?: string;
  fulfilled_orders?: number;
  monthly_revenue?: number;
  month_label?: string;
  tiers?: BadgeTier[];
};

const LEVEL_LABELS: Record<string, string> = {
  gold: "Gold",
  silver: "Silver",
  bronze: "Bronze",
  membership: "Membership",
  verified: "Verified",
  none: "Unbadged",
};

function levelLabel(level?: string | null): string {
  if (!level) return "Unbadged";
  return LEVEL_LABELS[level.toLowerCase()] ?? level;
}

export default function SupplierCredibilityPage() {
  const [data, setData] = useState<BadgeCatalog | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const addToast = useToastStore((state) => state.addToast);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const res = await apiFetch("/supplier/badge/catalog");
      const json = (await parseJsonResponse(res)) as BadgeCatalog;
      if (!res.ok) {
        throw new Error(getErrorMessage(json || {}));
      }
      setData(json);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Failed to load credibility data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <SupplierLayout title="Credibility">
      {loading ? (
        <PanelLoadingState width="wide" count={3} />
      ) : (
        <PanelContent width="wide">
          <PanelHero
            eyebrow="Account"
            title="Credibility & Trust"
            description="Your credibility score reflects fulfilled orders, revenue, and verification. Higher tiers unlock better commission rates and stronger buyer trust."
            icon={<BadgeCheck className="h-5 w-5" />}
          />

          {loadError ? (
            <div className="theme-card rounded-xl border border-danger/30 bg-danger/10 p-6 text-center">
              <p className="text-sm font-semibold text-text">{loadError}</p>
              <button
                onClick={() => void load()}
                className="theme-btn-primary mt-4 rounded-xl px-4 py-2 text-xs font-semibold"
              >
                Retry
              </button>
            </div>
          ) : (
            <>
              <div className="grid gap-4 sm:grid-cols-3">
                <div className="theme-card rounded-xl border p-5">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-text-faint">
                    Current Badge
                  </p>
                  <p className="mt-2 flex items-center gap-2 text-lg font-bold text-text">
                    <ShieldCheck className="h-5 w-5 text-primary" />
                    {levelLabel(data?.current_badge_level)}
                  </p>
                </div>
                <div className="theme-card rounded-xl border p-5">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-text-faint">
                    Eligible For
                  </p>
                  <p className="mt-2 text-lg font-bold text-text">
                    {levelLabel(data?.eligible_badge_level)}
                  </p>
                </div>
                <div className="theme-card rounded-xl border p-5">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-text-faint">
                    Fulfilled Orders
                  </p>
                  <p className="mt-2 text-lg font-bold text-text">
                    {data?.fulfilled_orders ?? 0}
                  </p>
                  <p className="mt-1 text-xs text-text-muted">
                    {data?.month_label ? `Revenue ${data.month_label}` : "Last 30 days"}
                  </p>
                </div>
              </div>

              <div className="theme-card rounded-xl border p-5">
                <p className="text-sm font-semibold text-text">Badge Tiers</p>
                <p className="mt-1 text-xs text-text-muted">
                  Meet the thresholds below to unlock each tier and its commission rate.
                </p>
                <div className="mt-4 space-y-3">
                  {(data?.tiers ?? []).map((tier) => {
                    const label = levelLabel(tier.badge_level);
                    const status = tier.is_current
                      ? { text: "Current", cls: "theme-chip-brand" }
                      : tier.is_eligible
                        ? { text: "Eligible", cls: "theme-chip-success" }
                        : tier.is_recommended
                          ? { text: "Recommended", cls: "theme-chip-warning" }
                          : { text: "Locked", cls: "theme-chip-muted" };
                    return (
                      <div
                        key={tier.badge_level}
                        className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-surface-1 p-4"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="text-sm font-semibold text-text">{label}</p>
                            <span
                              className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${status.cls}`}
                            >
                              {status.text}
                            </span>
                          </div>
                          <p className="mt-1 text-xs text-text-muted">
                            {tier.min_fulfilled_orders} fulfilled orders · min{" "}
                            {tier.min_monthly_revenue.toLocaleString()} revenue ·{" "}
                            {(tier.commission_rate * 100).toFixed(1)}% commission
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <Link
                  href="/supplier/documents"
                  className="theme-btn-secondary inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold"
                >
                  Manage Verification Documents
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
                <Link
                  href="/supplier/profile"
                  className="theme-btn-secondary inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold"
                >
                  Complete Your Profile
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </>
          )}
        </PanelContent>
      )}
    </SupplierLayout>
  );
}
