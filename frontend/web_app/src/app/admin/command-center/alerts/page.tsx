"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  RefreshCw,
  AlertCircle,
  ShieldAlert,
  Info,
  CheckCircle2,
} from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { useToastStore } from "@/lib/toastStore";
import { isAdminStaffRole } from "@shared/adminPermissions";

const MotionDiv = motion.div as typeof motion.div;

interface Alert {
  id: number;
  type: string;
  severity: "critical" | "warning" | "info";
  title: string;
  message: string;
  country_code?: string;
  created_at: string;
}

const SEVERITY_CONFIG: Record<Alert["severity"], { icon: typeof AlertCircle; className: string }> = {
  critical: {
    icon: ShieldAlert,
    className: "border-danger/30 bg-danger/10 text-danger",
  },
  warning: {
    icon: AlertCircle,
    className: "border-warning/30 bg-warning/10 text-warning",
  },
  info: {
    icon: Info,
    className: "border-info/30 bg-info/10 text-info",
  },
};

export default function CommandCenterAlertsPage() {
  const router = useRouter();
  const { user, isLoggedIn, isLoading } = useAuth();
  const { addToast } = useToastStore();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<Alert["severity"] | "all">("all");

  const fetchAlerts = useCallback(async () => {
    setLoading(true);
    try {
      const url =
        filter === "all"
          ? "/admin/command-center/alerts?limit=50"
          : `/admin/command-center/alerts?limit=50&severity=${filter}`;
      const res = await apiFetch(url);
      const data = await res.json().catch(() => []);
      if (res.ok && Array.isArray(data)) {
        setAlerts(data);
      }
    } catch {
      addToast("Failed to load alerts", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast, filter]);

  useEffect(() => {
    if (isLoading) return;
    if (!isLoggedIn || !isAdminStaffRole(user?.role ?? null)) {
      router.push("/admin/login");
      return;
    }
    fetchAlerts();
  }, [isLoading, isLoggedIn, user, router, fetchAlerts]);

  const handleResolve = async (id: number) => {
    try {
      const res = await apiFetch(`/admin/command-center/alerts/${id}/resolve`, {
        method: "POST",
      });
      if (res.ok) {
        setAlerts((prev) => prev.filter((a) => a.id !== id));
        addToast("Alert resolved", "success");
      } else {
        addToast("Failed to resolve alert", "error");
      }
    } catch {
      addToast("Failed to resolve alert", "error");
    }
  };

  const filteredAlerts =
    filter === "all" ? alerts : alerts.filter((a) => a.severity === filter);

  return (
    <AdminLayout title="Active Alerts" headerMode="compact">
      <PanelContent className="space-y-4">
        <div className="flex items-center justify-between">
          <button
            onClick={() => router.push("/admin/command-center")}
            className="theme-btn-secondary rounded-lg px-3 py-1.5 text-xs font-semibold flex items-center gap-2"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back
          </button>
          <button
            onClick={fetchAlerts}
            className="theme-btn-secondary rounded-lg px-3 py-1.5 text-xs font-semibold flex items-center gap-2"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </button>
        </div>

        <div className="flex items-center gap-2">
          {( ["all", "critical", "warning", "info"] as const).map((severity) => (
            <button
              key={severity}
              onClick={() => setFilter(severity)}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold border transition-colors ${
                filter === severity
                  ? severity === "all"
                    ? "bg-primary text-on-primary border-primary"
                    : severity === "critical"
                    ? "bg-danger text-white border-danger"
                    : severity === "warning"
                    ? "bg-warning text-on-warning border-warning"
                    : "bg-info text-white border-info"
                  : "bg-surface-1 text-text-muted border-border hover:border-primary/40"
              }`}
            >
              {severity === "all" ? "All" : severity.charAt(0).toUpperCase() + severity.slice(1)}
            </button>
          ))}
        </div>

        {loading ? (
          <PanelLoadingState count={5} blockClassName="h-20 animate-pulse rounded-xl bg-surface-2" />
        ) : filteredAlerts.length === 0 ? (
          <div className="theme-card rounded-xl border p-8 text-center">
            <CheckCircle2 className="mx-auto h-8 w-8 text-success mb-2" />
            <p className="text-sm text-text-muted">No alerts match the selected filter.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredAlerts.map((alert) => {
              const config = SEVERITY_CONFIG[alert.severity] ?? SEVERITY_CONFIG.info;
              const Icon = config.icon;
              return (
                <MotionDiv
                  key={alert.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`theme-card rounded-xl border p-4 flex items-start gap-3 ${config.className}`}
                >
                  <Icon className="h-5 w-5 shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-semibold text-text truncate">{alert.title}</p>
                      <span className="text-[10px] px-2 py-0.5 rounded border border-current/20 shrink-0">
                        {alert.severity}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-text-muted">{alert.message}</p>
                    <div className="mt-2 flex items-center justify-between">
                      <span className="text-[10px] text-text-faint">
                        {new Date(alert.created_at).toLocaleString()}
                        {alert.country_code ? ` · ${alert.country_code}` : ""}
                      </span>
                      <button
                        onClick={() => handleResolve(alert.id)}
                        className="theme-btn-secondary rounded-md px-2 py-1 text-[10px] font-semibold"
                      >
                        Resolve
                      </button>
                    </div>
                  </div>
                </MotionDiv>
              );
            })}
          </div>
        )}
      </PanelContent>
    </AdminLayout>
  );
}


