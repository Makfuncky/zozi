"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  RefreshCw,
  Navigation,
  Clock,
  ShieldCheck,
  Map,
} from "@/lib/icons";
import { useRequireLogisticsPartner } from "@/lib/useAuth";
import LogisticsPartnerLayout from "@/components/LogisticsPartnerLayout";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";

const MotionDiv = motion.div as typeof motion.div;

interface ServiceArea {
  id: number;
  city: string;
  country_code: string;
  service_type: string;
  estimated_delivery_days: number;
  base_rate: number;
  is_active: boolean;
  approval_status?: string;
}

export default function LogisticsPartnerRoutesPage() {
  const { user, isLoading: authLoading } = useRequireLogisticsPartner();
  const router = useRouter();
  const { addToast } = useToastStore();
  const [areas, setAreas] = useState<ServiceArea[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAreas = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch("/logistics-partner/service-areas");
      const data = await res.json().catch(() => []);
      if (res.ok && Array.isArray(data)) {
        setAreas(data);
      }
    } catch {
      addToast("Failed to load coverage areas", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    if (authLoading) return;
    if (!user) return;
    fetchAreas();
  }, [authLoading, user, fetchAreas]);

  const activeAreas = areas.filter((a) => a.is_active);
  const pendingAreas = areas.filter((a) => a.approval_status === "pending");

  return (
    <LogisticsPartnerLayout title="Coverage Areas">
      <PanelContent className="space-y-4">
        <div className="flex items-center justify-between">
          <button
            onClick={() => router.push("/logistics-partner/dashboard")}
            className="theme-btn-secondary rounded-lg px-3 py-1.5 text-xs font-semibold flex items-center gap-2"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back
          </button>
          <button
            onClick={fetchAreas}
            className="theme-btn-secondary rounded-lg px-3 py-1.5 text-xs font-semibold flex items-center gap-2"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </button>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <div className="theme-card rounded-xl border p-4">
            <div className="flex items-center gap-2 mb-1">
              <Navigation className="h-4 w-4 text-primary" />
              <p className="text-xs font-semibold text-text-faint">Total Coverage</p>
            </div>
            <p className="text-2xl font-bold text-text">{areas.length}</p>
          </div>
          <div className="theme-card rounded-xl border p-4">
            <div className="flex items-center gap-2 mb-1">
              <ShieldCheck className="h-4 w-4 text-success" />
              <p className="text-xs font-semibold text-text-faint">Active Routes</p>
            </div>
            <p className="text-2xl font-bold text-text">{activeAreas.length}</p>
          </div>
          <div className="theme-card rounded-xl border p-4">
            <div className="flex items-center gap-2 mb-1">
              <Clock className="h-4 w-4 text-warning" />
              <p className="text-xs font-semibold text-text-faint">Pending Approval</p>
            </div>
            <p className="text-2xl font-bold text-text">{pendingAreas.length}</p>
          </div>
        </div>

        {loading ? (
          <PanelLoadingState count={4} blockClassName="h-24 animate-pulse rounded-xl bg-surface-2" />
        ) : areas.length === 0 ? (
          <div className="theme-card rounded-xl border p-8 text-center">
            <Map className="mx-auto h-8 w-8 text-text-faint mb-2" />
            <p className="text-sm text-text-muted">No coverage areas configured yet.</p>
            <p className="text-xs text-text-faint mt-1">
              Contact your administrator to set up delivery routes and territories.
            </p>
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {areas.map((area) => (
              <MotionDiv
                key={area.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="theme-card rounded-xl border p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-text">
                    {area.city}, {area.country_code}
                  </span>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded border ${
                      area.is_active
                        ? "text-success bg-success/10 border-success/20"
                        : "text-warning bg-warning/10 border-warning/20"
                    }`}
                  >
                    {area.is_active ? "Active" : area.approval_status ?? "Inactive"}
                  </span>
                </div>
                <div className="space-y-1 text-[11px] text-text-muted">
                  <p>Service: {area.service_type}</p>
                  <p>Delivery: {area.estimated_delivery_days} days</p>
                  <p>Base rate: {area.base_rate}</p>
                </div>
              </MotionDiv>
            ))}
          </div>
        )}
          </PanelContent>
    </LogisticsPartnerLayout>
  );
}


