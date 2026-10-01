import { Platform } from "react-native";
import { logFrontendError, type FrontendErrorLogEntry } from "@shared/errorLogging";
import { API_BASE } from "@/lib/api";

const MAX_QUEUE_SIZE = 50;
const FLUSH_INTERVAL_MS = 30000;
const REPORT_PATH = "/api/frontend-errors";

interface QueuedError {
  message: string;
  source: string;
  stack?: string;
  context?: Record<string, unknown>;
  timestamp: string;
}

const queue: QueuedError[] = [];

async function flushQueue(): Promise<void> {
  if (queue.length === 0) return;

  const batch = queue.splice(0, queue.length);

  try {
    const url = `${API_BASE}${REPORT_PATH}`;
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        errors: batch,
        user_agent: `${Platform.OS}/${Platform.Version}`,
        url: "",
      }),
    });

    if (!res.ok) {
      queue.unshift(...batch);
    }
  } catch {
    queue.unshift(...batch);
  }
}

let flushTimer: ReturnType<typeof setInterval> | null = null;

export function initErrorReporter() {
  flushTimer = setInterval(flushQueue, FLUSH_INTERVAL_MS);
}

export function stopErrorReporter() {
  if (flushTimer) {
    clearInterval(flushTimer);
    flushTimer = null;
  }
}

export function reportErrorToBackend(entry: FrontendErrorLogEntry) {
  const queued: QueuedError = {
    message: entry.message,
    source: entry.source,
    stack: entry.stack,
    context: entry.context as Record<string, unknown> | undefined,
    timestamp: entry.timestamp,
  };

  queue.push(queued);
  if (queue.length > MAX_QUEUE_SIZE) {
    queue.shift();
  }
}
