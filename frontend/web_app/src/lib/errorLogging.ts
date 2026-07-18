export interface FrontendErrorLogEntry {
  id: string;
  source: string;
  message: string;
  stack?: string;
  context?: Record<string, unknown>;
  timestamp: string;
}

type ErrorListener = (entries: FrontendErrorLogEntry[]) => void;

const MAX_ERROR_LOGS = 20;
const entries: FrontendErrorLogEntry[] = [];
const listeners = new Set<ErrorListener>();

function notifyListeners() {
  const snapshot = [...entries];
  listeners.forEach((listener) => listener(snapshot));
}

function normalizeErrorMessage(error: unknown): { message: string; stack?: string } {
  if (error instanceof Error) {
    return {
      message: error.message || "Unknown error",
      stack: error.stack,
    };
  }

  if (typeof error === "string") {
    return { message: error };
  }

  try {
    return { message: JSON.stringify(error) };
  } catch {
    return { message: "Unserializable error payload" };
  }
}

export function logFrontendError(
  error: unknown,
  source: string,
  context?: Record<string, unknown>
): FrontendErrorLogEntry {
  const normalized = normalizeErrorMessage(error);
  const entry: FrontendErrorLogEntry = {
    id: `${Date.now()}-${entries.length + 1}`,
    source,
    message: normalized.message,
    stack: normalized.stack,
    context,
    timestamp: new Date().toISOString(),
  };

  entries.unshift(entry);
  if (entries.length > MAX_ERROR_LOGS) {
    entries.length = MAX_ERROR_LOGS;
  }

  notifyListeners();
  return entry;
}

export function getFrontendErrorLogs(): FrontendErrorLogEntry[] {
  return [...entries];
}

export function subscribeFrontendErrorLogs(listener: ErrorListener): () => void {
  listeners.add(listener);
  listener([...entries]);
  return () => {
    listeners.delete(listener);
  };
}

export function clearFrontendErrorLogs(): void {
  entries.length = 0;
  notifyListeners();
}
