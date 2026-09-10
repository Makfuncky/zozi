"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Plus,
  X,
  Check,
  AlertCircle,
  Search,
  ListTodo,
  Calendar,
  User,
  Flag,
} from "lucide-react";
import { apiFetch } from "@/lib/api";
import { useToastStore } from "@/stores/toastStore";

interface Employee {
  id: number;
  full_name: string;
  email: string;
  department: string | null;
}

interface Task {
  id: number;
  title: string;
  description: string | null;
  task_type: string;
  status: string;
  priority: string;
  due_date: string | null;
  assigned_to_id: number;
  assigned_to_name: string;
}

const TASK_TYPES = [
  { id: "review", label: "Review", icon: "📝" },
  { id: "ticket", label: "Ticket", icon: "🎫" },
  { id: "order", label: "Order", icon: "📦" },
  { id: "content", label: "Content", icon: "✍️" },
  { id: "quality", label: "Quality", icon: "🔍" },
  { id: "data_entry", label: "Data Entry", icon: "📊" },
  { id: "other", label: "Other", icon: "📌" },
];

const PRIORITIES = [
  { id: "high", label: "High", color: "bg-danger/10 text-danger" },
  { id: "medium", label: "Medium", color: "bg-warning/10 text-warning" },
  { id: "low", label: "Low", color: "bg-success/10 text-success" },
];

export default function TaskAssignmentPanel() {
  const { addToast } = useToastStore();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // Form state
  const [newTask, setNewTask] = useState({
    title: "",
    description: "",
    task_type: "other",
    priority: "medium",
    assigned_to_id: "",
    due_date: "",
  });

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch("/api/v1/admin/hr/tasks");
      if (res.ok) setTasks(await res.json());
    } catch {
      setTasks([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchEmployees = useCallback(async () => {
    try {
      const res = await apiFetch("/api/v1/admin/hr/employees");
      if (res.ok) {
        const data = await res.json();
        setEmployees(data.employees || data || []);
      }
    } catch {
      setEmployees([]);
    }
  }, []);

  useEffect(() => {
    fetchTasks();
    fetchEmployees();
  }, [fetchTasks, fetchEmployees]);

  const handleCreateTask = async () => {
    if (!newTask.title || !newTask.assigned_to_id) {
      addToast("Please fill in all required fields", "error");
      return;
    }
    setSaving(true);
    try {
      const res = await apiFetch("/api/v1/admin/hr/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...newTask,
          assigned_to_id: parseInt(newTask.assigned_to_id),
          due_date: newTask.due_date || null,
        }),
      });
      if (res.ok) {
        addToast("Task assigned successfully", "success");
        setShowCreateModal(false);
        setNewTask({
          title: "",
          description: "",
          task_type: "other",
          priority: "medium",
          assigned_to_id: "",
          due_date: "",
        });
        fetchTasks();
      } else {
        addToast("Failed to create task", "error");
      }
    } catch {
      addToast("Failed to create task", "error");
    } finally {
      setSaving(false);
    }
  };

  const filteredTasks = tasks.filter((task) =>
    task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    task.assigned_to_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-text">Task Assignment</h2>
          <p className="text-sm text-text-muted mt-1">
            Assign tasks to your team members and track progress
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          Assign Task
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
        <input
          type="text"
          placeholder="Search tasks..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full rounded-lg border border-border bg-surface-2 pl-10 pr-4 py-2 text-sm"
        />
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 rounded-xl bg-surface-2 animate-pulse" />
          ))}
        </div>
      ) : filteredTasks.length === 0 ? (
        <div className="rounded-xl border border-border bg-surface p-8 text-center">
          <ListTodo className="h-12 w-12 mx-auto mb-3 text-text-muted" />
          <p className="text-sm font-medium text-text">No tasks assigned</p>
          <p className="text-xs text-text-muted mt-1">Click &quot;Assign Task&quot; to get started</p>
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-3"
        >
          {filteredTasks.map((task) => (
            <div
              key={task.id}
              className="rounded-xl border border-border bg-surface p-4 hover:border-primary/30 transition-colors"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      PRIORITIES.find((p) => p.id === task.priority)?.color || "bg-gray-100 text-gray-500"
                    }`}>
                      {task.priority}
                    </span>
                    <span className="rounded-full bg-surface-2 px-2 py-0.5 text-xs font-medium text-text-muted">
                      {task.task_type}
                    </span>
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      task.status === "completed" ? "bg-success/10 text-success" :
                      task.status === "in_progress" ? "bg-info/10 text-info" :
                      "bg-warning/10 text-warning"
                    }`}>
                      {task.status.replace(/_/g, " ")}
                    </span>
                  </div>
                  <h3 className="text-sm font-semibold text-text">{task.title}</h3>
                  {task.description && (
                    <p className="text-xs text-text-muted mt-1">{task.description}</p>
                  )}
                  <div className="flex items-center gap-4 mt-2 text-xs text-text-muted">
                    <span className="flex items-center gap-1">
                      <User className="h-3 w-3" />
                      {task.assigned_to_name}
                    </span>
                    {task.due_date && (
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {new Date(task.due_date).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </motion.div>
      )}

      {/* Create Task Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-full max-w-lg rounded-xl bg-surface p-6 shadow-xl"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text">Assign Task</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="rounded-lg p-1.5 text-text-muted hover:bg-surface-2"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              {/* Title */}
              <div>
                <label className="block text-xs font-medium text-text-muted mb-1">Title *</label>
                <input
                  type="text"
                  value={newTask.title}
                  onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                  placeholder="Task title..."
                  className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-xs font-medium text-text-muted mb-1">Description</label>
                <textarea
                  value={newTask.description}
                  onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
                  placeholder="Task description..."
                  rows={3}
                  className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm"
                />
              </div>

              {/* Assign To */}
              <div>
                <label className="block text-xs font-medium text-text-muted mb-1">Assign To *</label>
                <select
                  value={newTask.assigned_to_id}
                  onChange={(e) => setNewTask({ ...newTask, assigned_to_id: e.target.value })}
                  className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm"
                >
                  <option value="">Select employee...</option>
                  {employees.map((emp) => (
                    <option key={emp.id} value={emp.id}>
                      {emp.full_name} ({emp.department || "No dept"})
                    </option>
                  ))}
                </select>
              </div>

              {/* Task Type & Priority */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">Type</label>
                  <select
                    value={newTask.task_type}
                    onChange={(e) => setNewTask({ ...newTask, task_type: e.target.value })}
                    className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm"
                  >
                    {TASK_TYPES.map((type) => (
                      <option key={type.id} value={type.id}>
                        {type.icon} {type.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">Priority</label>
                  <select
                    value={newTask.priority}
                    onChange={(e) => setNewTask({ ...newTask, priority: e.target.value })}
                    className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm"
                  >
                    {PRIORITIES.map((p) => (
                      <option key={p.id} value={p.id}>{p.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Due Date */}
              <div>
                <label className="block text-xs font-medium text-text-muted mb-1">Due Date</label>
                <input
                  type="date"
                  value={newTask.due_date}
                  onChange={(e) => setNewTask({ ...newTask, due_date: e.target.value })}
                  className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm"
                />
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-2 pt-2">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text-muted hover:bg-surface-2"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateTask}
                  disabled={saving}
                  className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:opacity-50"
                >
                  {saving ? "Assigning..." : "Assign Task"}
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
