"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Target,
  TrendingUp,
  Award,
  Star,
  RefreshCw,
  BarChart3,
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";
import { Progress } from "@/components/ui/Progress";
import { useToastStore } from "@/stores/toastStore";
import { ErrorState } from "@/components/employee/ErrorBoundary";

interface Goal {
  id: number;
  title: string;
  description: string;
  progress: number;
  target: number;
  unit: string;
  due_date: string;
  status: string;
}

interface Review {
  id: number;
  period: string;
  rating: number;
  reviewer: string;
  comments: string;
  status: string;
}

interface PerformanceData {
  goals: Goal[];
  reviews: Review[];
  overall_rating: number;
}

export default function EmployeePerformancePage() {
  const { addToast } = useToastStore();
  const [data, setData] = useState<PerformanceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [okrsRes, reviewsRes] = await Promise.all([
        apiFetch("/api/v1/employee/hr/performance/okrs").catch(() => null),
        apiFetch("/api/v1/employee/hr/performance/reviews").catch(() => null),
      ]);
      const okrs = okrsRes?.ok ? await okrsRes.json() : { goals: [], overall_rating: 0 };
      const reviews = reviewsRes?.ok ? await reviewsRes.json() : [];
      setData({
        goals: okrs.goals ?? okrs.data ?? [],
        reviews: Array.isArray(reviews) ? reviews : reviews?.reviews ?? reviews?.data ?? [],
        overall_rating: okrs.overall_rating ?? 0,
      });
    } catch {
      setError("Failed to load performance data");
      addToast("Failed to load performance data", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <PanelContent className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-text">Performance</h1>
          <p className="text-sm text-text-muted mt-1">Track goals, OKRs, and performance reviews</p>
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
              <Target className="h-6 w-6 text-primary mx-auto mb-2" />
              <p className="text-2xl font-bold text-text">{data?.goals?.length ?? 0}</p>
              <p className="text-xs text-text-muted">Active Goals</p>
            </div>
            <div className="rounded-xl border border-border bg-surface p-4 text-center">
              <TrendingUp className="h-6 w-6 text-success mx-auto mb-2" />
              <p className="text-2xl font-bold text-text">
                {data?.goals?.filter((g) => g.status === "completed").length ?? 0}
              </p>
              <p className="text-xs text-text-muted">Completed</p>
            </div>
            <div className="rounded-xl border border-border bg-surface p-4 text-center">
              <Star className="h-6 w-6 text-warning mx-auto mb-2" />
              <p className="text-2xl font-bold text-text">{data?.overall_rating ?? "—"}</p>
              <p className="text-xs text-text-muted">Overall Rating</p>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="rounded-xl border border-border bg-surface p-5"
          >
            <h2 className="text-sm font-semibold text-text mb-4 flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-primary" />
              Goals & OKRs
            </h2>
            {data?.goals && data.goals.length > 0 ? (
              <div className="space-y-4">
                {data.goals.map((goal) => (
                  <div key={goal.id} className="rounded-lg bg-surface-2 p-4">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm font-medium text-text">{goal.title}</p>
                      <span className={`text-xs font-medium capitalize ${
                        goal.status === "completed" ? "text-success" :
                        goal.status === "in_progress" ? "text-primary" : "text-text-muted"
                      }`}>
                        {goal.status.replace("_", " ")}
                      </span>
                    </div>
                    {goal.description && (
                      <p className="text-xs text-text-muted mb-3">{goal.description}</p>
                    )}
                    <div className="flex items-center gap-3">
                      <Progress value={goal.progress} className="flex-1" />
                      <span className="text-xs font-medium text-text tabular-nums shrink-0">
                        {goal.progress}/{goal.target} {goal.unit}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-text-muted text-center py-4">No goals assigned</p>
            )}
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="rounded-xl border border-border bg-surface p-5"
          >
            <h2 className="text-sm font-semibold text-text mb-4 flex items-center gap-2">
              <Award className="h-4 w-4 text-warning" />
              Performance Reviews
            </h2>
            {data?.reviews && data.reviews.length > 0 ? (
              <div className="space-y-3">
                {data.reviews.map((review) => (
                  <div key={review.id} className="rounded-lg bg-surface-2 p-4">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm font-medium text-text">{review.period}</p>
                      <div className="flex items-center gap-1">
                        {Array.from({ length: 5 }).map((_, i) => (
                          <Star
                            key={i}
                            className={`h-3.5 w-3.5 ${
                              i < review.rating ? "text-warning fill-warning" : "text-text-faint"
                            }`}
                          />
                        ))}
                      </div>
                    </div>
                    <p className="text-xs text-text-muted">Reviewer: {review.reviewer}</p>
                    {review.comments && (
                      <p className="text-xs text-text mt-2">{review.comments}</p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-text-muted text-center py-4">No reviews available</p>
            )}
          </motion.div>
        </>
      )}
    </PanelContent>
  );
}
