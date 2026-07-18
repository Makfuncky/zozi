import { Platform } from "react-native";
import * as FileSystem from "@/lib/fileSystem";
import * as Sharing from "@/lib/sharing";

import { API_BASE, apiFetch, getCurrentAccessToken } from "@/lib/api";
import { toast } from "@/lib/toastStore";
import { useBackgroundJobStore, type BackgroundJobStatus } from "@/lib/backgroundJobStore";

export interface BackgroundJob<Result = unknown> {
  id: string;
  kind: string;
  status: BackgroundJobStatus | string;
  metadata?: Record<string, unknown>;
  result?: Result | null;
  error?: string | null;
  created_at?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
}

export interface TrackBackgroundJobOptions<Result = unknown> {
  label: string;
  description?: string;
  route?: string;
  queuedToast?: string | false;
  successToast?: string | ((job: BackgroundJob<Result>) => string) | false;
  errorToast?: string | ((message: string, job: BackgroundJob<Result>) => string) | false;
  onUpdate?: (job: BackgroundJob<Result>) => void;
}

const activeBackgroundJobMonitors = new Map<string, Promise<BackgroundJob<unknown>>>();

export function isBackgroundJobTerminal(job: BackgroundJob | null | undefined): boolean {
  return job?.status === "completed" || job?.status === "failed";
}

export async function fetchBackgroundJob<Result = unknown>(jobId: string): Promise<BackgroundJob<Result>> {
  return apiFetch<BackgroundJob<Result>>(`/jobs/${jobId}`);
}

async function delay(ms: number): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

export async function waitForBackgroundJob<Result = unknown>(
  jobOrId: string | BackgroundJob<Result>,
  options: {
    intervalMs?: number;
    onUpdate?: (job: BackgroundJob<Result>) => void;
  } = {},
): Promise<BackgroundJob<Result>> {
  const { intervalMs = 1200, onUpdate } = options;
  let job = typeof jobOrId === "string"
    ? await fetchBackgroundJob<Result>(jobOrId)
    : jobOrId;

  onUpdate?.(job);

  while (!isBackgroundJobTerminal(job)) {
    await delay(intervalMs);
    job = await fetchBackgroundJob<Result>(job.id);
    onUpdate?.(job);
  }

  return job;
}

function pushTrackedJob<Result>(job: BackgroundJob<Result>, options: TrackBackgroundJobOptions<Result>) {
  useBackgroundJobStore.getState().upsertJob({
    ...job,
    label: options.label,
    description: options.description ?? null,
    route: options.route ?? null,
    updated_at_local: new Date().toISOString(),
  });
}

function resolveToastMessage<Result>(
  value: string | ((job: BackgroundJob<Result>) => string) | false | undefined,
  fallback: string,
  job: BackgroundJob<Result>,
): string | false {
  if (value === false) return false;
  if (typeof value === "function") return value(job);
  return value || fallback;
}

export function trackBackgroundJob<Result = unknown>(
  job: BackgroundJob<Result>,
  options: TrackBackgroundJobOptions<Result>,
): Promise<BackgroundJob<Result>> {
  pushTrackedJob(job, options);

  const existing = activeBackgroundJobMonitors.get(job.id) as Promise<BackgroundJob<Result>> | undefined;
  if (existing) {
    return existing;
  }

  const queuedToast = resolveToastMessage(options.queuedToast, `${options.label} queued`, job);
  if (queuedToast) {
    toast.info(queuedToast);
  }

  const monitor = waitForBackgroundJob(job, {
    onUpdate: (update) => {
      pushTrackedJob(update, options);
      options.onUpdate?.(update);
    },
  })
    .then((finalJob) => {
      pushTrackedJob(finalJob, options);

      if (finalJob.status === "completed") {
        const successToast = resolveToastMessage(options.successToast, `${options.label} completed`, finalJob);
        if (successToast) {
          toast.success(successToast);
        }
      } else {
        const message = finalJob.error || `${options.label} failed`;
        const errorToast = options.errorToast === false
          ? false
          : typeof options.errorToast === "function"
            ? options.errorToast(message, finalJob)
            : options.errorToast || message;
        if (errorToast) {
          toast.error(errorToast);
        }
      }

      return finalJob;
    })
    .catch((error) => {
      const message = error instanceof Error ? error.message : `${options.label} failed`;
      pushTrackedJob(
        {
          ...job,
          status: "failed",
          error: message,
          finished_at: new Date().toISOString(),
        },
        options,
      );

      const errorToast = options.errorToast === false
        ? false
        : typeof options.errorToast === "function"
          ? options.errorToast(message, job)
          : options.errorToast || message;
      if (errorToast) {
        toast.error(errorToast);
      }
      throw error;
    })
    .finally(() => {
      activeBackgroundJobMonitors.delete(job.id);
    });

  activeBackgroundJobMonitors.set(job.id, monitor as Promise<BackgroundJob<unknown>>);
  return monitor;
}

function getDownloadUrl(jobId: string): string {
  return `${API_BASE.replace(/\/$/, "")}/admin/export/jobs/${jobId}/download`;
}

function sanitizeFilename(filename: string): string {
  return filename.replace(/[^a-zA-Z0-9._-]/g, "_");
}

async function parseDownloadError(response: Response): Promise<string> {
  try {
    const json = await response.json();
    if (json && typeof json.detail === "string") {
      return json.detail;
    }
  } catch {
    try {
      const text = await response.text();
      if (text) return text;
    } catch {
      return "Download failed";
    }
  }
  return "Download failed";
}

export async function downloadBackgroundJobResult(jobId: string, filename: string): Promise<string> {
  const url = getDownloadUrl(jobId);
  const token = getCurrentAccessToken();
  const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

  if (Platform.OS === "web" && typeof window !== "undefined") {
    const response = await fetch(url, { headers });
    if (!response.ok) {
      throw new Error(await parseDownloadError(response));
    }

    const blob = await response.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = blobUrl;
    anchor.download = sanitizeFilename(filename);
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.URL.revokeObjectURL(blobUrl);
    return filename;
  }

  const directory = FileSystem.cacheDirectory || FileSystem.documentDirectory;
  if (!directory) {
    throw new Error("File download directory is unavailable on this device");
  }

  const targetPath = `${directory}${sanitizeFilename(filename)}`;
  const download = await FileSystem.downloadAsync(url, targetPath);
  if (!download?.uri) {
    throw new Error("Failed to save export file");
  }

  const canShare = await Sharing.isAvailableAsync();
  if (canShare) {
    await Sharing.shareAsync(download.uri, { dialogTitle: filename });
  }

  return download.uri;
}