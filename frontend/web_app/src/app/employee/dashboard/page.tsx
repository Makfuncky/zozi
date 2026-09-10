"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Calendar,
  Clock,
  DollarSign,
  FileText,
  TrendingUp,
  User,
  RefreshCw,
  Briefcase,
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { StatCard } from "@/components/ui/StatCard";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";
import { Spinner } from "@/components/ui/Spinner";

interface TaskStats {
  total: number;
  pending: number;
  in_progress: number;
  completed: number;
  blocked: number;
  cancelled: number;
  overdue: number;
}

interface WorkspaceInfo {
  role: string;
  all_roles: string[];
  features: string[];
  widgets: string[];
  primary_role: string | null;
}

interface LeaveBalance {
  annual: number;
  sick: number;
  personal: number;
  used: number;
}

interface Payslip {
  id: number;
  period: string;
  net_pay: number;
  currency: string;
  status: string;
}

interface AttendanceStatus {
  today_hours: number;
  week_hours: number;
  status: string;
}

interface OkrProgress {
  total: number;
  completed: number;
  in_progress: number;
}

interface DashboardData {
  leave_balance: LeaveBalance;
  recent_payslips: Payslip[];
  attendance: AttendanceStatus;
  okr_progress: OkrProgress;
}

export default function EmployeeDashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [taskStats, setTaskStats] = useState<TaskStats | null>(null);
  const [workspace, setWorkspace] = useState<WorkspaceInfo | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    try {
      const [leaveRes, payslipsRes, attendanceRes, okrsRes, taskStatsRes, workspaceRes] = await Promise.all([
        apiFetch("/api/v1/employee/hr/leave/balance").catch(() => null),
        apiFetch("/api/v1/employee/hr/payroll/payslips?limit=5").catch(() => null),
        apiFetch("/api/v1/employee/hr/attendance").catch(() => null),
        apiFetch("/api/v1/employee/hr/performance/okrs").catch(() => null),
        apiFetch("/api/v1/employee/hr/tasks/stats").catch(() => null),
        apiFetch("/api/v1/employee/hr/workspace").catch(() => null),
      ]);

      setData({
        leave_balance: leaveRes?.ok ? await leaveRes.json() : { annual: 0, sick: 0, personal: 0, used: 0 },
        recent_payslips: payslipsRes?.ok ? await payslipsJson(payslipsRes) : [],
        attendance: attendanceRes?.ok ? await attendanceRes.json() : { today_hours: 0, week_hours: 0, status: "unknown" },
        okr_progress: okrsRes?.ok ? await okrsRes.json() : { total: 0, completed: 0, in_progress: 0 },
      });

      if (taskStatsRes?.ok) setTaskStats(await taskStatsRes.json());
      if (workspaceRes?.ok) setWorkspace(await workspaceRes.json());
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const leave = data?.leave_balance;
  const attendance = data?.attendance;
  const okrs = data?.okr_progress;
  const totalLeave = (leave?.annual ?? 0) + (leave?.sick ?? 0) + (leave?.personal ?? 0);
  const leaveUsedPercent = totalLeave > 0 ? Math.round(((leave?.used ?? 0) / totalLeave) * 100) : 0;
  const okrPercent = okrs?.total ? Math.round((okrs.completed / okrs.total) * 100) : 0;

  return (
    <PanelContent className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-text">Dashboard</h1>
          <p className="text-sm text-text-muted mt-1">
            Welcome back, {user?.full_name || user?.email}
          </p>
        </div>
        <button
          onClick={fetchDashboard}
          disabled={loading}
          className="flex items-center gap-2 rounded-xl border border-border bg-surface-2 px-4 py-2 text-xs font-semibold text-text-muted hover:text-text disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {loading ? (
        <PanelLoadingState
          count={4}
          className="!mt-0 grid grid-cols-2 gap-3 lg:grid-cols-4"
          blockClassName="h-28 rounded-xl bg-surface-2 animate-pulse"
        />
      ) : (
        <>
          {/* Role Badge */}
          {workspace?.role && (
            <div className="rounded-xl border border-border bg-surface p-3 flex items-center gap-3">
              <div className="rounded-lg bg-emerald-100 p-2">
                <Briefcase className="h-4 w-4 text-emerald-600" />
              </div>
              <div>
                <p className="text-sm font-semibold text-text capitalize">
                  {workspace.role.replace(/_/g, " ")}
                </p>
                <p className="text-xs text-text-muted">
                  {workspace.all_roles.length > 1
                    ? `${workspace.all_roles.length} roles assigned`
                    : "Primary role"}
                </p>
              </div>
            </div>
          )}

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-2 gap-3 lg:grid-cols-4"
          >
            <StatCard
              label="Pending Tasks"
              value={String(taskStats?.pending ?? 0)}
              icon={Clock}
              color="bg-warning/10 text-warning"
              sub={`${taskStats?.overdue ?? 0} overdue`}
            />
            <StatCard
              label="Hours This Week"
              value={`${attendance?.week_hours ?? 0}h`}
              icon={Clock}
              color="bg-info/10 text-info"
              sub={`${attendance?.today_hours ?? 0}h today`}
            />
            <StatCard
              label="OKR Progress"
              value={`${okrPercent}%`}
              icon={TrendingUp}
              color="bg-success/10 text-success"
              sub={`${okrs?.completed ?? 0} of ${okrs?.total ?? 0} goals`}
            />
            <StatCard
              label="Leave Balance"
              value={`${totalLeave - (leave?.used ?? 0)} days`}
              icon={Calendar}
              color="bg-primary/10 text-primary"
              sub={`${leaveUsedPercent}% used`}
            />
          </motion.div>

          <div className="grid gap-4 lg:grid-cols-2">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="rounded-xl border border-border bg-surface p-4"
            >
              <h2 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
                <Calendar className="h-4 w-4 text-primary" />
                Leave Balance
              </h2>
              <div className="space-y-3">
                {[
                  { label: "Annual", value: leave?.annual ?? 0, total: totalLeave },
                  { label: "Sick", value: leave?.sick ?? 0, total: totalLeave },
                  { label: "Personal", value: leave?.personal ?? 0, total: totalLeave },
                ].map((item) => (
                  <div key={item.label}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-text-muted">{item.label}</span>
                      <span className="text-xs font-medium text-text">{item.value} days</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-surface-2 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-primary transition-all"
                        style={{ width: `${item.total > 0 ? (item.value / item.total) * 100 : 0}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 }}
              className="rounded-xl border border-border bg-surface p-4"
            >
              <h2 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
                <FileText className="h-4 w-4 text-info" />
                Recent Payslips
              </h2>
              {data?.recent_payslips && data.recent_payslips.length > 0 ? (
                <div className="divide-y divide-border">
                  {data.recent_payslips.slice(0, 5).map((payslip) => (
                    <div key={payslip.id} className="flex items-center justify-between py-2.5">
                      <div>
                        <p className="text-xs font-medium text-text">{payslip.period}</p>
                        <p className="text-xs text-text-muted capitalize">{payslip.status}</p>
                      </div>
                      <span className="text-xs font-semibold text-text tabular-nums">
                        {payslip.currency === "OMR"
                          ? `${(payslip.net_pay / 1000).toFixed(2)} OMR`
                          : `${payslip.net_pay} ${payslip.currency}`}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-text-muted">No payslips available</p>
              )}
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="rounded-xl border border-border bg-surface p-4"
          >
            <h2 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
              <User className="h-4 w-4 text-success" />
              Attendance Status
            </h2>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-lg font-bold text-text">{attendance?.status === "present" ? "Present" : attendance?.status === "absent" ? "Absent" : "—"}</p>
                <p className="text-xs text-text-muted">Today</p>
              </div>
              <div className="text-center">
                <p className="text-lg font-bold text-text">{attendance?.today_hours ?? 0}h</p>
                <p className="text-xs text-text-muted">Hours Today</p>
              </div>
              <div className="text-center">
                <p className="text-lg font-bold text-text">{attendance?.week_hours ?? 0}h</p>
                <p className="text-xs text-text-muted">This Week</p>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </PanelContent>
  );
}

async function payslipsJson(res: Response): Promise<any[]> {
  const data = await res.json().catch(() => []);
  return Array.isArray(data) ? data : data?.payslips ?? data?.data ?? [];
}
