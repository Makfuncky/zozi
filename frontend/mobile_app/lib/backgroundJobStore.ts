import { create } from "zustand";

export type BackgroundJobStatus = "queued" | "running" | "completed" | "failed";

export interface TrackedBackgroundJob<Result = unknown> {
  id: string;
  kind: string;
  status: BackgroundJobStatus | string;
  label: string;
  description?: string | null;
  route?: string | null;
  metadata?: Record<string, unknown>;
  result?: Result | null;
  error?: string | null;
  created_at?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  updated_at_local: string;
}

interface BackgroundJobStoreState {
  jobs: TrackedBackgroundJob[];
  upsertJob: (job: Omit<TrackedBackgroundJob, "updated_at_local"> & { updated_at_local?: string }) => void;
  removeJob: (jobId: string) => void;
  clearFinishedJobs: () => void;
  reset: () => void;
}

function sortJobs(jobs: TrackedBackgroundJob[]): TrackedBackgroundJob[] {
  return [...jobs]
    .sort((left, right) => {
      const rightTime = Date.parse(right.updated_at_local || right.finished_at || right.created_at || "") || 0;
      const leftTime = Date.parse(left.updated_at_local || left.finished_at || left.created_at || "") || 0;
      return rightTime - leftTime;
    })
    .slice(0, 20);
}

export const useBackgroundJobStore = create<BackgroundJobStoreState>((set) => ({
  jobs: [],

  upsertJob: (incoming) => {
    const updatedAt = incoming.updated_at_local || new Date().toISOString();
    set((state) => {
      const existing = state.jobs.find((job) => job.id === incoming.id);
      const nextJob: TrackedBackgroundJob = {
        ...(existing ?? {}),
        ...incoming,
        updated_at_local: updatedAt,
      };
      return {
        jobs: sortJobs([
          nextJob,
          ...state.jobs.filter((job) => job.id !== incoming.id),
        ]),
      };
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

  reset: () => set({ jobs: [] }),
}));