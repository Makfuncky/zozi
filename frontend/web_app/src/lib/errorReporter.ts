import { logFrontendError, getFrontendErrorLogs, type FrontendErrorLogEntry } from "@shared/errorLogging";
import { apiFetch } from "./api/client";
import { logger } from "@/lib/logger";


const QUEUE_KEY = "zozi_error_report_queue";
const MAX_QUEUE_SIZE = 100;
const FLUSH_INTERVAL_MS = 15000;
const MAX_RETRIES = 3;
const BASE_RETRY_DELAY_MS = 1000;
const REPORT_ENDPOINT = "/api/frontend-errors";
const DEDUP_WINDOW_MS = 60000;

interface QueuedError {
  id: string;
  message: string;
  source: string;
  stack?: string;
  context?: Record<string, unknown>;
  timestamp: string;
  retryCount: number;
  lastRetryAt?: string;
  fingerprint: string;
}

interface ErrorFingerprint {
  message: string;
  source: string;
}

function generateId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function loadQueue(): QueuedError[] {
  if (typeof localStorage === "undefined") return [];
  try {
    const raw = localStorage.getItem(QUEUE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function persistQueue(queue: QueuedError[]) {
  if (typeof localStorage === "undefined") return;
  try {
    localStorage.setItem(QUEUE_KEY, JSON.stringify(queue.slice(0, MAX_QUEUE_SIZE)));
  } catch {
    localStorage.removeItem(QUEUE_KEY);
  }
}

function getFingerprint(entry: FrontendErrorLogEntry): string {
  return `${entry.source}:${entry.message}`;
}

function isDuplicate(queue: QueuedError[], entry: FrontendErrorLogEntry): boolean {
  const fingerprint = getFingerprint(entry);
  const now = Date.now();
  return queue.some(
    (q) =>
      q.fingerprint === fingerprint &&
      now - new Date(q.timestamp).getTime() < DEDUP_WINDOW_MS
  );
}

let queue: QueuedError[] = loadQueue();
let flushTimer: ReturnType<typeof setInterval> | null = null;
let isFlushing = false;

async function flushQueue(): Promise<void> {
  if (queue.length === 0 || isFlushing) return;
  isFlushing = true;

  const batch = [...queue];
  queue = [];
  persistQueue(queue);

  try {
    const res = await apiFetch(REPORT_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        errors: batch,
        user_agent: navigator.userAgent,
        url: window.location.href,
      }),
    });

    if (!res.ok) {
      const remaining = batch.filter((entry) => entry.retryCount < MAX_RETRIES);
      for (const entry of remaining) {
        entry.retryCount++;
        entry.lastRetryAt = new Date().toISOString();
        queue.push(entry);
      }
      persistQueue(queue);
    }
  } catch {
    for (const entry of batch) {
      if (entry.retryCount < MAX_RETRIES) {
        entry.retryCount++;
        entry.lastRetryAt = new Date().toISOString();
        queue.push(entry);
      }
    }
    persistQueue(queue);
  } finally {
    isFlushing = false;
  }
}

function scheduleFlush() {
  if (flushTimer) clearInterval(flushTimer);
  flushTimer = setInterval(() => {
    flushQueue();
  }, FLUSH_INTERVAL_MS);
}

function getContext(): Record<string, unknown> {
  const ctx: Record<string, unknown> = {
    url: window.location.href,
    user_agent: navigator.userAgent,
    platform: navigator.platform,
    language: navigator.language,
    screen_width: window.screen.width,
    screen_height: window.screen.height,
    viewport_width: window.innerWidth,
    viewport_height: window.innerHeight,
  };

  const countryCode = document.cookie
    .split("; ")
    .find((row) => row.startsWith("zozi_country="));
  if (countryCode) {
    ctx.country_code = countryCode.split("=")[1];
  }

  return ctx;
}

export function initErrorReporter() {
  if (typeof window === "undefined") return;
  scheduleFlush();

  window.addEventListener("beforeunload", () => {
    if (queue.length > 0) {
      navigator.sendBeacon(REPORT_ENDPOINT, JSON.stringify({
        errors: queue,
        user_agent: navigator.userAgent,
        url: window.location.href,
      }));
      queue = [];
      persistQueue(queue);
    }
  });

  logger.info("[ErrorReporter] Initialized", { queueSize: queue.length });
}

export function reportErrorToBackend(entry: FrontendErrorLogEntry) {
  if (isDuplicate(queue, entry)) {
    logger.debug("[ErrorReporter] Duplicate error suppressed", { fingerprint: getFingerprint(entry) });
    return;
  }

  const fingerprint = getFingerprint(entry);
  const queued: QueuedError = {
    id: entry.id || generateId(),
    message: entry.message,
    source: entry.source,
    stack: entry.stack,
    context: {
      ...entry.context,
      ...getContext(),
    } as Record<string, unknown> | undefined,
    timestamp: entry.timestamp,
    retryCount: 0,
    fingerprint,
  };

  queue.push(queued);
  if (queue.length >= MAX_QUEUE_SIZE) {
    queue.shift();
  }
  persistQueue(queue);
}
