"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Clock,
  CheckCircle,
  AlertTriangle,
  ChevronRight,
} from "lucide-react";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";

interface Task {
  id: number;
  title: string;
  description: string | null;
  task_type: string;
  status: string;
  priority: string;
  due_date: string | null;
  entity_type: string | null;
  entity_id: number | null;
  entity_url: string | null;
}

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-warning/10 text-warning",
  in_progress: "bg-info/10 text-info",
  completed: "bg-success/10 text-success",
  blocked: "bg-danger/10 text-danger",
  cancelled: "bg-gray-100 text-gray-500",
};

const PRIORITY_COLORS: Record<string, string> = {
  high: "bg-danger/10 text-danger",
  medium: "bg-warning/10 text-warning",
  low: "bg-success/10 text-success",
};

export default function EmployeeTasksPage() {
  const { user } = useAuth();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    try {
      const params = filter !== "all" ? `?status=${filter}` : "";
      const res = await apiFetch(`/api/v1/employee/hr/tasks${params}`);
      if (res.ok) setTasks(await res.json());
    } catch {
      setTasks([]);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const handleStatusUpdate = async (taskId: number, newStatus: string) => {
    try {
      await apiFetch(`/api/v1/employee/hr/tasks/${taskId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
      fetchTasks();
    } catch {
      // ignore
    }
  };

  return (
    <PanelContent className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-text">My Tasks</h1>
          <p className="text-sm text-text-muted mt-1">
            Tasks assigned to you by your manager
          </p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 overflow-x-auto">
        {["all", "pending", "in_progress", "completed", "blocked"].map((status) => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium whitespace-nowrap transition-colors ${
              filter === status
                ? "bg-primary text-white"
                : "bg-surface-2 text-text-muted hover:bg-surface-2/80"
            }`}
          >
            {status === "all" ? "All" : status.replace(/_/g, " ")}
          </button>
        ))}
      </div>

      {loading ? (
        <PanelLoadingState
          count={5}
          className="!mt-0 space-y-3"
          blockClassName="h-20 rounded-xl bg-surface-2 animate-pulse"
        />
      ) : tasks.length === 0 ? (
        <div className="rounded-xl border border-border bg-surface p-8 text-center">
          <CheckCircle className="h-12 w-12 mx-auto mb-3 text-success" />
          <p className="text-sm font-medium text-text">No tasks found</p>
          <p className="text-xs text-text-muted mt-1">
            {filter !== "all"
              ? "Try changing the filter"
              : "You have no assigned tasks"}
          </p>
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-3"
        >
          {tasks.map((task) => (
            <div
              key={task.id}
              className="rounded-xl border border-border bg-surface p-4 hover:border-primary/30 transition-colors"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        PRIORITY_COLORS[task.priority] || "bg-gray-100 text-gray-500"
                      }`}
                    >
                      {task.priority}
                    </span>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        STATUS_COLORS[task.status] || "bg-gray-100 text-gray-500"
                      }`}
                    >
                      {task.status.replace(/_/g, " ")}
                    </span>
                  </div>
                  <h3 className="text-sm font-semibold text-text truncate">
                    {task.title}
                  </h3>
                  {task.description && (
                    <p className="text-xs text-text-muted mt-1 line-clamp-2">
                      {task.description}
                    </p>
                  )}
                  {task.due_date && (
                    <p className="text-xs text-text-muted mt-2 flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      Due: {new Date(task.due_date).toLocaleDateString()}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {task.status === "pending" && (
                    <button
                      onClick={() => handleStatusUpdate(task.id, "in_progress")}
                      className="rounded-lg bg-info/10 px-2 py-1 text-xs font-medium text-info hover:bg-info/20"
                    >
                      Start
                    </button>
                  )}
                  {task.status === "in_progress" && (
                    <button
                      onClick={() => handleStatusUpdate(task.id, "completed")}
                      className="rounded-lg bg-success/10 px-2 py-1 text-xs font-medium text-success hover:bg-success/20"
                    >
                      Complete
                    </button>
                  )}
                  {task.entity_url && (
                    <a
                      href={task.entity_url}
                      className="rounded-lg bg-surface-2 p-1.5 hover:bg-surface-2/80"
                    >
                      <ChevronRight className="h-4 w-4 text-text-muted" />
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))}
        </motion.div>
      )}
    </PanelContent>
  );
}
