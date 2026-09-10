"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  CheckCircle,
  Clock,
  AlertTriangle,
  ListTodo,
  Briefcase,
} from "lucide-react";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";
import { StatCard } from "@/components/ui/StatCard";

interface TaskStats {
  total: number;
  pending: number;
  in_progress: number;
  completed: number;
  blocked: number;
  cancelled: number;
  overdue: number;
}

interface WorkspaceConfig {
  role: string;
  all_roles: string[];
  features: string[];
  widgets: string[];
  primary_role: string | null;
}

export default function EmployeeWorkspacePage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<TaskStats | null>(null);
  const [workspace, setWorkspace] = useState<WorkspaceConfig | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [statsRes, workspaceRes] = await Promise.all([
        apiFetch("/api/v1/employee/hr/tasks/stats").catch(() => null),
        apiFetch("/api/v1/employee/hr/workspace").catch(() => null),
      ]);
      if (statsRes?.ok) setStats(await statsRes.json());
      if (workspaceRes?.ok) setWorkspace(await workspaceRes.json());
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const roleLabels: Record<string, string> = {
    moderator: "Content Moderator",
    supplier_coordinator: "Supplier Coordinator",
    customer_coordinator: "Customer Coordinator",
    promotion_manager: "Promotion Manager",
    order_fulfillment: "Order Fulfillment",
    delivery_coordinator: "Delivery Coordinator",
    finance_clerk: "Finance Clerk",
    hr_coordinator: "HR Coordinator",
    data_entry: "Data Entry",
    quality_analyst: "Quality Analyst",
    social_media: "Social Media Manager",
    inventory_manager: "Inventory Manager",
    returns_processor: "Returns Processor",
    content_writer: "Content Writer",
    photography_editor: "Photography Editor",
    accounts_payable: "Accounts Payable",
    accounts_receivable: "Accounts Receivable",
    general_employee: "General Employee",
  };

  return (
    <PanelContent className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-text">My Workspace</h1>
          <p className="text-sm text-text-muted mt-1">
            Welcome back, {user?.full_name || user?.email}
          </p>
        </div>
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
            <div className="rounded-xl border border-border bg-surface p-4">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-emerald-100 p-2">
                  <Briefcase className="h-5 w-5 text-emerald-600" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-text">
                    {roleLabels[workspace.role] || workspace.role}
                  </p>
                  <p className="text-xs text-text-muted">
                    {workspace.all_roles.length > 1
                      ? `Also: ${workspace.all_roles.filter((r) => r !== workspace.role).map((r) => roleLabels[r] || r).join(", ")}`
                      : "Primary role"}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Task Stats */}
          {stats && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="grid grid-cols-2 gap-3 lg:grid-cols-4"
            >
              <StatCard
                label="Pending"
                value={String(stats.pending)}
                icon={Clock}
                color="bg-warning/10 text-warning"
                sub={`${stats.overdue} overdue`}
              />
              <StatCard
                label="In Progress"
                value={String(stats.in_progress)}
                icon={ListTodo}
                color="bg-info/10 text-info"
              />
              <StatCard
                label="Completed"
                value={String(stats.completed)}
                icon={CheckCircle}
                color="bg-success/10 text-success"
              />
              <StatCard
                label="Blocked"
                value={String(stats.blocked)}
                icon={AlertTriangle}
                color="bg-danger/10 text-danger"
              />
            </motion.div>
          )}

          {/* Quick Actions */}
          <div className="rounded-xl border border-border bg-surface p-4">
            <h2 className="text-sm font-semibold text-text mb-3">Quick Actions</h2>
            <div className="grid grid-cols-2 gap-2 lg:grid-cols-4">
              <a
                href="/employee/workspace/tasks"
                className="rounded-lg border border-border bg-surface-2 p-3 text-center hover:bg-surface-2/80 transition-colors"
              >
                <ListTodo className="h-5 w-5 mx-auto mb-1 text-primary" />
                <span className="text-xs font-medium text-text">My Tasks</span>
              </a>
              <a
                href="/employee/attendance"
                className="rounded-lg border border-border bg-surface-2 p-3 text-center hover:bg-surface-2/80 transition-colors"
              >
                <Clock className="h-5 w-5 mx-auto mb-1 text-info" />
                <span className="text-xs font-medium text-text">Clock In/Out</span>
              </a>
              <a
                href="/employee/leaves"
                className="rounded-lg border border-border bg-surface-2 p-3 text-center hover:bg-surface-2/80 transition-colors"
              >
                <CheckCircle className="h-5 w-5 mx-auto mb-1 text-success" />
                <span className="text-xs font-medium text-text">Request Leave</span>
              </a>
              <a
                href="/employee/notifications"
                className="rounded-lg border border-border bg-surface-2 p-3 text-center hover:bg-surface-2/80 transition-colors"
              >
                <AlertTriangle className="h-5 w-5 mx-auto mb-1 text-warning" />
                <span className="text-xs font-medium text-text">Notifications</span>
              </a>
            </div>
          </div>

          {/* Role Features */}
          {workspace?.features && workspace.features.length > 0 && (
            <div className="rounded-xl border border-border bg-surface p-4">
              <h2 className="text-sm font-semibold text-text mb-3">Your Work Tools</h2>
              <div className="flex flex-wrap gap-2">
                {workspace.features.map((feature) => (
                  <span
                    key={feature}
                    className="rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary"
                  >
                    {feature.replace(/_/g, " ")}
                  </span>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </PanelContent>
  );
}
