"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { History, RefreshCw, Search, Filter, Clock3 } from "@/lib/icons";
import { useAuth } from "@/lib/useAuth";
import { isAdminStaffRole } from "@shared/adminPermissions";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelHero, PanelLoadingState } from "@/components/PanelPage";
import { EnterpriseDataTable, type EnterpriseColumn } from "@shared/components/EnterpriseDataTable";
import { apiFetch } from "@/lib/api";
import { dc, useDensity } from "@/lib/densityContext";

interface AuditLogEntry {
  id: number;
  action: string;
  user_id: number | null;
  username: string | null;
  resource_type: string | null;
  resource_id: number | null;
  details: Record<string, unknown> | null;
  status: string | null;
  occurred_at: string;
}

interface AuditLogPageData {
  data: AuditLogEntry[];
  total: number;
  page: number;
  pageSize: number;
  unique_actions: string[];
}

const ACTION_COLOR: Record<string, string> = {
  LOGIN_SUCCESS: "text-success",
  LOGIN_FAILED: "text-danger",
  LOGOUT: "text-text-muted",
  PRODUCT_UPLOAD: "text-info",
  PRODUCT_UPDATE: "text-warning",
  PRODUCT_DELETE: "text-danger",
  ORDER_CREATED: "text-success",
  ORDER_STATUS_CHANGED: "text-warning",
  ORDER_REFUNDED: "text-danger",
  STAFF_CREATED: "text-primary",
  STAFF_DELETED: "text-danger",
  FRAUD_FLAG: "text-danger",
  PAYOUT_PROCESSED: "text-success",
  PAYOUT_REJECTED: "text-danger",
};

export default function AuditLogsPage() {
  const router = useRouter();
  const { user, isLoggedIn, isLoading } = useAuth();
  const { density } = useDensity();
  const role = user?.role ?? null;

  const [data, setData] = useState<AuditLogPageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [actionFilter, setActionFilter] = useState("");

  const bodyText = dc(density, "text-[10px]", "text-xs", "text-sm");

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search.trim()) params.set("search", search.trim());
      if (actionFilter) params.set("action", actionFilter);
      const res = await apiFetch(`/admin/audit-logs?${params}`);
      if (res.ok) setData(await res.json());
    } catch (err) {
      console.error("Failed to load audit logs:", err);
    } finally {
      setLoading(false);
    }
  }, [search, actionFilter]);

  const fetchActions = useCallback(async () => {
    try {
      const res = await apiFetch("/admin/audit-logs/actions");
      if (res.ok) {
        const actions: string[] = await res.json();
        setData((prev) => prev ? { ...prev, unique_actions: actions } : null);
      }
    } catch {}
  }, []);

  useEffect(() => {
    if (isLoading) return;
    if (!isLoggedIn || !isAdminStaffRole(role)) {
      router.push("/admin/login");
      return;
    }
    fetchLogs();
    fetchActions();
  }, [isLoading, isLoggedIn, role, fetchLogs, fetchActions, router]);

  const columns: EnterpriseColumn<AuditLogEntry>[] = [
    { key: "id", label: "#", width: "64px", sortable: true, render: (e) => <span className={`${bodyText} font-mono tabular-nums text-text-faint`}>#{e.id}</span> },
    { key: "action", label: "Action", width: "180px", sortable: true, render: (e) => (
      <span className={`inline-flex items-center gap-1.5 text-[11px] font-semibold ${ACTION_COLOR[e.action] || "text-text"}`}>
        <span className={`h-1.5 w-1.5 rounded-full ${e.status === "success" ? "bg-success" : e.status === "failed" ? "bg-danger" : "bg-warning"}`} />
        {e.action.replace(/_/g, " ")}
      </span>
    )},
    { key: "username", label: "User", width: "140px", render: (e) => (
      <div>
        <span className={`${bodyText} font-medium text-text`}>{e.username || "—"}</span>
        {e.user_id && <span className="ml-1 text-[10px] text-text-faint">#{e.user_id}</span>}
      </div>
    )},
    { key: "resource_type", label: "Resource", width: "120px", render: (e) => (
      <span className={`${bodyText} text-text-muted`}>{e.resource_type || "—"}{e.resource_id ? ` #${e.resource_id}` : ""}</span>
    )},
    { key: "status", label: "Status", width: "90px", render: (e) => {
      const s = e.status || "unknown";
      return (
        <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold ${
          s === "success" ? "bg-success/10 text-success" : s === "failed" ? "bg-danger/10 text-danger" : "bg-warning/10 text-warning"
        }`}>
          {s}
        </span>
      );
    }},
    { key: "occurred_at", label: "Date", width: "100px", sortable: true, render: (e) => (
      <span className={`${bodyText} inline-flex items-center gap-1 tabular-nums text-text-faint`}>
        <Clock3 className="h-3 w-3" />
        {e.occurred_at?.slice(0, 16).replace("T", " ")}
      </span>
    )},
  ];

  if (isLoading || !isLoggedIn || !isAdminStaffRole(role)) {
    return <AdminLayout title="Audit Logs"><PanelLoadingState count={3} /></AdminLayout>;
  }

  return (
    <AdminLayout title="Audit Logs" headerMode="compact">
      <PanelContent className="space-y-4">
        <PanelHero
          eyebrow="Security"
          title="Audit Trail"
          description="Track every security-sensitive and business-critical event across the platform"
          icon={<History className="h-5 w-5" />}
          actions={
            <button onClick={fetchLogs} disabled={loading}
              className="flex items-center gap-2 rounded-xl border border-border bg-surface-2 px-4 py-2 text-xs font-semibold text-text-muted hover:text-text disabled:opacity-50">
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </button>
          }
        />

        <EnterpriseDataTable
          columns={columns}
          rows={data?.data ?? []}
          rowKey={(e) => e.id}
          densityMode={density}
          enableExport
          initialRowsPerPage={50}
          emptyState={loading ? undefined : "No audit logs found"}
          toolbarSlot={
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative min-w-[14rem] flex-1 xl:w-56 xl:flex-none">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                <input value={search} onChange={(e) => setSearch(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && fetchLogs()}
                  placeholder="Search logs…"
                  className="h-9 w-full rounded-xl border border-border bg-surface-1 py-2 pl-9 pr-3 text-xs text-text placeholder:text-text-faint focus:border-primary focus:outline-none" />
              </div>
              <div className="relative">
                <Filter className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                <select value={actionFilter} onChange={(e) => setActionFilter(e.target.value)}
                  className="h-9 appearance-none rounded-xl border border-border bg-surface-1 py-2 pl-9 pr-8 text-xs text-text focus:border-primary focus:outline-none">
                  <option value="">All actions</option>
                  {(data?.unique_actions ?? []).map((a) => (
                    <option key={a} value={a}>{a.replace(/_/g, " ")}</option>
                  ))}
                </select>
              </div>
              <span className="text-[10px] text-text-faint tabular-nums">
                {data ? `${data.total} total` : ""}
              </span>
            </div>
          }
        />
      </PanelContent>
    </AdminLayout>
  );
}
