"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { BackgroundJob } from "@/lib/backgroundJobs";

export interface TrackedBackgroundJob<Result = unknown> extends BackgroundJob<Result> {
  label: string;
  description?: string | null;
  route?: string | null;
  queued_at_local: string;
  updated_at_local: string;
}

interface BackgroundJobStoreState {
  jobs: TrackedBackgroundJob[];
  upsertJob: (job: BackgroundJob & { label: string; description?: string | null; route?: string | null }) => void;
  removeJob: (jobId: string) => void;
  clearFinishedJobs: () => void;
}

function sortAndTrimJobs(jobs: TrackedBackgroundJob[]): TrackedBackgroundJob[] {
  return [...jobs]
    .sort((left, right) => {
      const rightTime = Date.parse(right.updated_at_local || right.finished_at || right.created_at || "") || 0;
      const leftTime = Date.parse(left.updated_at_local || left.finished_at || left.created_at || "") || 0;
      return rightTime - leftTime;
    })
    .slice(0, 20);
}

export const useBackgroundJobStore = create<BackgroundJobStoreState>()(
  persist(
    (set) => ({
      jobs: [],

      upsertJob: (incoming) => {
        const now = new Date().toISOString();
        set((state) => {
          const existing = state.jobs.find((job) => job.id === incoming.id);
          const nextJob: TrackedBackgroundJob = {
            ...(existing ?? {
              queued_at_local: incoming.created_at || now,
              updated_at_local: now,
            }),
            ...incoming,
            label: incoming.label || existing?.label || incoming.kind,
            description: incoming.description ?? existing?.description ?? null,
            route: incoming.route ?? existing?.route ?? null,
            metadata: {
              ...(existing?.metadata ?? {}),
              ...(incoming.metadata ?? {}),
            },
            queued_at_local: existing?.queued_at_local || incoming.created_at || now,
            updated_at_local: now,
          };

          const withoutCurrent = state.jobs.filter((job) => job.id !== incoming.id);
          return { jobs: sortAndTrimJobs([nextJob, ...withoutCurrent]) };
        });
      },

      removeJob: (jobId) => {
        set((state) => ({ jobs: state.jobs.filter((job) => job.id !== jobId) }));
      },

      clearFinishedJobs: () => {
        set((state) => ({
          jobs: state.jobs.filter((job) => job.status === "queued" || job.status === "running"),
        }));
      },
    }),
    {
      name: "zozi-background-jobs",
      partialize: (state) => ({ jobs: sortAndTrimJobs(state.jobs) }),
    },
  ),
);
