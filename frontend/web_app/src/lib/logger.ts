import { apiFetch } from "./api/client";

type LogLevel = "debug" | "info" | "warn" | "error" | "silent";

const LEVEL_ORDER: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
  silent: 4,
};

let currentLevel: LogLevel =
  (typeof process !== "undefined" && process.env.NODE_ENV === "production")
    ? "warn"
    : "debug";

let remoteEndpoint: string | null = null;
let remoteQueue: Array<{ level: LogLevel; message: string; args: any[]; timestamp: string }> = [];
let remoteFlushTimer: ReturnType<typeof setInterval> | null = null;

export function setLogLevel(level: LogLevel) {
  currentLevel = level;
}

export function setRemoteEndpoint(endpoint: string) {
  remoteEndpoint = endpoint;
  if (remoteFlushTimer) clearInterval(remoteFlushTimer);
  remoteFlushTimer = setInterval(flushRemote, 10000);
}

function shouldLog(level: LogLevel) {
  return LEVEL_ORDER[level] >= LEVEL_ORDER[currentLevel];
}

function formatTimestamp() {
  return new Date().toISOString();
}

function serializeArgs(args: any[]): any[] {
  return args.map((a) => {
    if (a instanceof Error) {
      return { name: a.name, message: a.message, stack: a.stack };
    }
    if (typeof a === "object" && a !== null) {
      try { return JSON.parse(JSON.stringify(a)); } catch { return String(a); }
    }
    return a;
  });
}

async function flushRemote() {
  if (remoteQueue.length === 0 || !remoteEndpoint) return;
  const batch = [...remoteQueue];
  remoteQueue = [];
  try {
    await apiFetch(remoteEndpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ logs: batch }),
    });
  } catch {
    remoteQueue.unshift(...batch);
  }
}

function pushRemoteLog(level: LogLevel, message: string, args: any[]) {
  if (!remoteEndpoint) return;
  remoteQueue.push({
    level,
    message,
    args: serializeArgs(args),
    timestamp: formatTimestamp(),
  });
}

export const logger = {
  debug: (...args: any[]) => {
    if (!shouldLog("debug")) return;
    const message = args[0] ?? "";
    console.debug(`[DEBUG] [${formatTimestamp()}]`, ...args);
    pushRemoteLog("debug", String(message), args);
  },
  info: (...args: any[]) => {
    if (!shouldLog("info")) return;
    const message = args[0] ?? "";
    console.info(`[INFO] [${formatTimestamp()}]`, ...args);
    pushRemoteLog("info", String(message), args);
  },
  warn: (...args: any[]) => {
    if (!shouldLog("warn")) return;
    const message = args[0] ?? "";
    console.warn(`[WARN] [${formatTimestamp()}]`, ...args);
    pushRemoteLog("warn", String(message), args);
  },
  error: (...args: any[]) => {
    if (!shouldLog("error")) return;
    const message = args[0] ?? "";
    console.error(`[ERROR] [${formatTimestamp()}]`, ...args);
    pushRemoteLog("error", String(message), args);
  },
};

export type { LogLevel };
