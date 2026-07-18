"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Activity,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Loader2,
  TriangleAlert,
  X,
} from "@/lib/icons";

import { isBackgroundJobTracked, trackBackgroundJob } from "@/lib/backgroundJobs";
import { useBackgroundJobStore } from "@/lib/backgroundJobStore";

function formatTimestamp(value?: string | null): string {
  if (!value) return "Just now";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Just now";
  return date.toLocaleString();
}

function statusLabel(status: string): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}

function statusIcon(status: string) {
  if (status === "completed") {
    return <CheckCircle2 className="h-4 w-4 text-success" />;
  }
  if (status === "failed") {
    return <TriangleAlert className="h-4 w-4 text-danger" />;
  }
  return <Loader2 className="h-4 w-4 animate-spin text-primary" />;
}

export default function BackgroundJobCenter() {
  const jobs = useBackgroundJobStore((state) => state.jobs);
  const removeJob = useBackgroundJobStore((state) => state.removeJob);
  const clearFinishedJobs = useBackgroundJobStore((state) => state.clearFinishedJobs);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    jobs.forEach((job) => {
      if ((job.status === "queued" || job.status === "running") && !isBackgroundJobTracked(job.id)) {
        void trackBackgroundJob(job, {
          label: job.label,
          description: job.description ?? undefined,
          route: job.route ?? undefined,
          queuedToast: false,
          successToast: false,
          errorToast: false,
        }).catch(() => undefined);
      }
    });
  }, [jobs]);

  const sortedJobs = useMemo(
    () => [...jobs].sort((left, right) => Date.parse(right.updated_at_local) - Date.parse(left.updated_at_local)),
    [jobs],
  );

  const activeCount = sortedJobs.filter((job) => job.status === "queued" || job.status === "running").length;

  if (sortedJobs.length === 0) {
    return null;
  }

  return (
    <div className="pointer-events-none fixed bottom-3 right-3 z-50 flex w-[min(22rem,calc(100vw-1.5rem))] flex-col items-end gap-2">
      <button
        onClick={() => setOpen((current) => !current)}
        className="pointer-events-auto flex items-center gap-2 rounded-full border border-border bg-surface-base/95 px-3 py-1.5 text-left shadow-lg backdrop-blur-xl transition-colors hover:bg-surface-2"
      >
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/12 text-primary">
          <Activity className="h-3.5 w-3.5" />
        </div>
        <span className="text-xs font-semibold text-text">
          {activeCount > 0 ? `${activeCount} active` : `${sortedJobs.length} jobs`}
        </span>
        {open ? <ChevronDown className="h-3.5 w-3.5 text-text-faint" /> : <ChevronUp className="h-3.5 w-3.5 text-text-faint" />}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 16 }}
            className="pointer-events-auto w-full rounded-2xl border border-border bg-surface-base/96 p-3 shadow-lg backdrop-blur-2xl"
          >
            <div className="mb-3 flex items-center justify-between px-1">
              <div>
                <p className="text-sm font-semibold text-text">Progress & History</p>
                <p className="text-xs text-text-faint">Queued jobs keep updating even when you switch pages.</p>
              </div>
              <button
                onClick={() => clearFinishedJobs()}
                className="rounded-full border border-border px-2.5 py-1 text-[11px] font-medium text-text-muted transition-colors hover:bg-surface-1 hover:text-text"
              >
                Clear done
              </button>
            </div>

            <div className="max-h-64 space-y-2 overflow-y-auto pr-1">
              {sortedJobs.map((job) => (
                <div key={job.id} className="rounded-2xl border border-border bg-surface-1/80 p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        {statusIcon(job.status)}
                        <p className="truncate text-sm font-semibold text-text">{job.label}</p>
                      </div>
                      {job.description && (
                        <p className="mt-1 text-xs text-text-faint">{job.description}</p>
                      )}
                      <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-text-faint">
                        <span className="rounded-full border border-border px-2 py-0.5">{statusLabel(job.status)}</span>
                        <span>{job.kind}</span>
                        {job.route && (
                          <Link
                            href={job.route}
                            className="inline-flex items-center gap-1 rounded-full border border-border px-2 py-0.5 text-text-muted transition-colors hover:bg-surface-2 hover:text-text"
                          >
                            Open
                            <ExternalLink className="h-3 w-3" />
                          </Link>
                        )}
                      </div>
                      {job.error && <p className="mt-2 text-xs text-danger">{job.error}</p>}
                      {typeof job.result === "object" && job.result && "filename" in job.result && typeof job.result.filename === "string" && (
                        <p className="mt-2 text-xs text-text-faint">Artifact: {job.result.filename}</p>
                      )}
                      <p className="mt-2 text-[11px] text-text-faint">Updated {formatTimestamp(job.updated_at_local)}</p>
                    </div>
                    <button
                      onClick={() => removeJob(job.id)}
                      className="rounded-full p-1 text-text-faint transition-colors hover:bg-surface-2 hover:text-text"
                      aria-label={`Dismiss ${job.label}`}
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}


