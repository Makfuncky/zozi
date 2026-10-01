"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  BookOpen,
  Award,
  CheckCircle,
  Clock,
  Play,
  RefreshCw,
  GraduationCap,
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";
import { Progress } from "@/components/ui/Progress";
import { useToastStore } from "@/stores/toastStore";
import { ErrorState } from "@/components/employee/ErrorBoundary";

interface TrainingModule {
  id: number;
  title: string;
  description: string;
  duration_minutes: number;
  progress: number;
  status: string;
  completed_at: string | null;
  category: string;
}

interface Certification {
  id: number;
  name: string;
  issuer: string;
  issued_at: string;
  expires_at: string | null;
  credential_id: string;
  status: string;
}

export default function EmployeeTrainingPage() {
  const { addToast } = useToastStore();
  const [modules, setModules] = useState<TrainingModule[]>([]);
  const [certifications, setCertifications] = useState<Certification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [modulesRes, certsRes] = await Promise.all([
        apiFetch("/api/v1/employee/hr/training/modules").catch(() => null),
        apiFetch("/api/v1/employee/hr/training/certifications").catch(() => null),
      ]);
      if (modulesRes?.ok) {
        const data = await modulesRes.json();
        setModules(Array.isArray(data) ? data : data?.modules ?? data?.data ?? []);
      }
      if (certsRes?.ok) {
        const data = await certsRes.json();
        setCertifications(Array.isArray(data) ? data : data?.certifications ?? data?.data ?? []);
      }
    } catch {
      setError("Failed to load training data");
      addToast("Failed to load training data", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const completedModules = modules.filter((m) => m.status === "completed").length;
  const inProgressModules = modules.filter((m) => m.status === "in_progress").length;

  return (
    <PanelContent className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-text">Training</h1>
          <p className="text-sm text-text-muted mt-1">Learning modules and certifications</p>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="flex items-center gap-2 rounded-xl border border-border bg-surface-2 px-4 py-2 text-xs font-semibold text-text-muted hover:text-text disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {loading ? (
        <PanelLoadingState count={3} blockClassName="h-24 rounded-xl bg-surface-2 animate-pulse" />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchData} />
      ) : (
        <>
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-1 gap-4 sm:grid-cols-3"
          >
            <div className="rounded-xl border border-border bg-surface p-4 text-center">
              <BookOpen className="h-6 w-6 text-primary mx-auto mb-2" />
              <p className="text-2xl font-bold text-text">{modules.length}</p>
              <p className="text-xs text-text-muted">Total Modules</p>
            </div>
            <div className="rounded-xl border border-border bg-surface p-4 text-center">
              <CheckCircle className="h-6 w-6 text-success mx-auto mb-2" />
              <p className="text-2xl font-bold text-text">{completedModules}</p>
              <p className="text-xs text-text-muted">Completed</p>
            </div>
            <div className="rounded-xl border border-border bg-surface p-4 text-center">
              <Clock className="h-6 w-6 text-warning mx-auto mb-2" />
              <p className="text-2xl font-bold text-text">{inProgressModules}</p>
              <p className="text-xs text-text-muted">In Progress</p>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="rounded-xl border border-border bg-surface p-5"
          >
            <h2 className="text-sm font-semibold text-text mb-4 flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-primary" />
              Training Modules
            </h2>
            {modules.length > 0 ? (
              <div className="space-y-3">
                {modules.map((module) => (
                  <div key={module.id} className="rounded-lg bg-surface-2 p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {module.status === "completed" ? (
                          <CheckCircle className="h-4 w-4 text-success" />
                        ) : module.status === "in_progress" ? (
                          <Play className="h-4 w-4 text-primary" />
                        ) : (
                          <Clock className="h-4 w-4 text-text-faint" />
                        )}
                        <p className="text-sm font-medium text-text">{module.title}</p>
                      </div>
                      <span className="text-xs text-text-muted">{module.duration_minutes} min</span>
                    </div>
                    {module.description && (
                      <p className="text-xs text-text-muted mb-3">{module.description}</p>
                    )}
                    <div className="flex items-center gap-3">
                      <Progress value={module.progress} className="flex-1" />
                      <span className="text-xs font-medium text-text tabular-nums shrink-0">
                        {module.progress}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-text-muted text-center py-4">No training modules available</p>
            )}
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="rounded-xl border border-border bg-surface p-5"
          >
            <h2 className="text-sm font-semibold text-text mb-4 flex items-center gap-2">
              <GraduationCap className="h-4 w-4 text-warning" />
              Certifications
            </h2>
            {certifications.length > 0 ? (
              <div className="space-y-3">
                {certifications.map((cert) => (
                  <div key={cert.id} className="flex items-center justify-between rounded-lg bg-surface-2 p-4">
                    <div className="flex items-center gap-3">
                      <Award className="h-5 w-5 text-warning" />
                      <div>
                        <p className="text-sm font-medium text-text">{cert.name}</p>
                        <p className="text-xs text-text-muted">{cert.issuer}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                        cert.status === "active" ? "bg-success/10 text-success" : "bg-warning/10 text-warning"
                      }`}>
                        {cert.status}
                      </span>
                      {cert.expires_at && (
                        <p className="text-xs text-text-faint mt-1">Expires: {cert.expires_at}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-text-muted text-center py-4">No certifications earned</p>
            )}
          </motion.div>
        </>
      )}
    </PanelContent>
  );
}
