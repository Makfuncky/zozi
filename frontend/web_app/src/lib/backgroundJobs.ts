import { apiFetch, getErrorMessage, parseJsonResponse } from "@/lib/api";
import { useBackgroundJobStore } from "@/lib/backgroundJobStore";
import { useToastStore, type ToastType } from "@/lib/toastStore";

export type BackgroundJobStatus = "queued" | "running" | "completed" | "failed";

export interface BackgroundJob<Result = unknown> {
  id: string;
  kind: string;
  status: BackgroundJobStatus | string;
  owner_user_id?: number | null;
  owner_role?: string | null;
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

export function isBackgroundJobTracked(jobId: string): boolean {
  return activeBackgroundJobMonitors.has(jobId);
}

function createAbortError(): Error {
  const error = new Error("Background job polling aborted");
  error.name = "AbortError";
  return error;
}

async function delay(ms: number, signal?: AbortSignal): Promise<void> {
  if (signal?.aborted) {
    throw createAbortError();
  }

  await new Promise<void>((resolve, reject) => {
    const timer = setTimeout(() => {
      signal?.removeEventListener("abort", onAbort);
      resolve();
    }, ms);

    const onAbort = () => {
      clearTimeout(timer);
      signal?.removeEventListener("abort", onAbort);
      reject(createAbortError());
    };

    signal?.addEventListener("abort", onAbort, { once: true });
  });
}

export function isAbortError(error: unknown): boolean {
  return error instanceof Error && error.name === "AbortError";
}

export function isBackgroundJobTerminal(job: BackgroundJob | null | undefined): boolean {
  return job?.status === "completed" || job?.status === "failed";
}

export async function fetchBackgroundJob<Result = unknown>(jobId: string): Promise<BackgroundJob<Result>> {
  const response = await apiFetch(`/jobs/${jobId}`);
  const payload = (await parseJsonResponse(response)) ?? {};
  if (!response.ok) {
    throw new Error(getErrorMessage(payload));
  }
  return payload as BackgroundJob<Result>;
}

export async function waitForBackgroundJob<Result = unknown>(
  jobOrId: string | BackgroundJob<Result>,
  options: {
    intervalMs?: number;
    signal?: AbortSignal;
    onUpdate?: (job: BackgroundJob<Result>) => void;
  } = {},
): Promise<BackgroundJob<Result>> {
  const { intervalMs = 1200, signal, onUpdate } = options;

  let job = typeof jobOrId === "string"
    ? await fetchBackgroundJob<Result>(jobOrId)
    : jobOrId;
  let attempt = 0;

  onUpdate?.(job);

  while (!isBackgroundJobTerminal(job)) {
    const isHidden = typeof document !== "undefined" && document.visibilityState === "hidden";
    let nextInterval = intervalMs;

    if (job.status === "queued") {
      nextInterval = Math.max(intervalMs * 2, 2000);
    }

    if (attempt > 8) {
      nextInterval = Math.min(nextInterval + (attempt - 8) * 400, 8000);
    }

    if (isHidden) {
      nextInterval = Math.min(Math.max(nextInterval * 3, 4000), 15000);
    }

    await delay(nextInterval, signal);
    job = await fetchBackgroundJob<Result>(job.id);
    onUpdate?.(job);
    attempt += 1;
  }

  return job;
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

function pushTrackedJob<Result>(job: BackgroundJob<Result>, options: TrackBackgroundJobOptions<Result>) {
  useBackgroundJobStore.getState().upsertJob({
    ...job,
    label: options.label,
    description: options.description ?? null,
    route: options.route ?? null,
  });
}

function addTrackedToast(message: string | false, type: ToastType) {
  if (!message) return;
  useToastStore.getState().addToast(message, type);
}

export function trackBackgroundJob<Result = unknown>(
  job: BackgroundJob<Result>,
  options: TrackBackgroundJobOptions<Result>,
): Promise<BackgroundJob<Result>> {
  const existing = activeBackgroundJobMonitors.get(job.id) as Promise<BackgroundJob<Result>> | undefined;
  if (existing) {
    return existing;
  }

  pushTrackedJob(job, options);

  addTrackedToast(
    resolveToastMessage(options.queuedToast, `${options.label} queued`, job),
    "info",
  );

  const monitor = waitForBackgroundJob(job, {
    onUpdate: (update) => {
      pushTrackedJob(update, options);
      options.onUpdate?.(update);
    },
  })
    .then((finalJob) => {
      pushTrackedJob(finalJob, options);

      if (finalJob.status === "completed") {
        addTrackedToast(
          resolveToastMessage(options.successToast, `${options.label} completed`, finalJob),
          "success",
        );
      } else {
        const failureMessage = finalJob.error || `${options.label} failed`;
        addTrackedToast(
          options.errorToast === false
            ? false
            : typeof options.errorToast === "function"
              ? options.errorToast(failureMessage, finalJob)
              : options.errorToast || failureMessage,
          "error",
        );
      }

      return finalJob;
    })
    .catch((error) => {
      if (isAbortError(error)) {
        throw error;
      }

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
      addTrackedToast(
        options.errorToast === false
          ? false
          : typeof options.errorToast === "function"
            ? options.errorToast(message, job)
            : options.errorToast || message,
        "error",
      );
      throw error;
    })
    .finally(() => {
      activeBackgroundJobMonitors.delete(job.id);
    });

  activeBackgroundJobMonitors.set(job.id, monitor as Promise<BackgroundJob<unknown>>);
  return monitor;
}

export async function downloadBackgroundJobResult(jobId: string, filename: string): Promise<void> {
  const response = await apiFetch(`/admin/export/jobs/${jobId}/download`);
  if (!response.ok) {
    const payload = await parseJsonResponse(response);
    throw new Error(getErrorMessage(payload ?? {}));
  }

  const blob = await response.blob();
  const blobUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = blobUrl;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(blobUrl);
}
