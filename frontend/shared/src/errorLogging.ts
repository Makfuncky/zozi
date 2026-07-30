export interface FrontendErrorLogEntry {
  id: string;
  source: string;
  message: string;
  stack?: string;
  context?: Record<string, unknown>;
  timestamp: string;
}

type ErrorListener = (entries: FrontendErrorLogEntry[]) => void;

const MAX_ERROR_LOGS = 50;
const STORAGE_KEY = "zozi_error_logs";

const entries: FrontendErrorLogEntry[] = [];
const listeners = new Set<ErrorListener>();

function loadPersisted(): FrontendErrorLogEntry[] {
  if (typeof sessionStorage === "undefined") return [];
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as FrontendErrorLogEntry[];
    return Array.isArray(parsed) ? parsed.slice(0, MAX_ERROR_LOGS) : [];
  } catch {
    return [];
  }
}

function persist(entries: FrontendErrorLogEntry[]) {
  if (typeof sessionStorage === "undefined") return;
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(entries.slice(0, MAX_ERROR_LOGS)));
  } catch {
    // storage full — silently ignore
  }
}

const persisted = loadPersisted();
entries.push(...persisted);

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
  const id = typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const entry: FrontendErrorLogEntry = {
    id,
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

  persist(entries);
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
  persist(entries);
  notifyListeners();
}
