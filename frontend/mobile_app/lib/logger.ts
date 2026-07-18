type LogLevel = "debug" | "info" | "warn" | "error" | "silent";

const LEVEL_ORDER: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
  silent: 4,
};

let currentLevel: LogLevel = __DEV__ ? "debug" : "warn";

export function setLogLevel(level: LogLevel) {
  currentLevel = level;
}

function shouldLog(level: LogLevel) {
  return LEVEL_ORDER[level] >= LEVEL_ORDER[currentLevel];
}

function formatTimestamp() {
  return new Date().toISOString();
}

export const logger = {
  debug: (...args: any[]) => {
    if (!shouldLog("debug")) return;
    console.debug(`[DEBUG] [${formatTimestamp()}]`, ...args);
  },
  info: (...args: any[]) => {
    if (!shouldLog("info")) return;
    console.info(`[INFO] [${formatTimestamp()}]`, ...args);
  },
  warn: (...args: any[]) => {
    if (!shouldLog("warn")) return;
    console.warn(`[WARN] [${formatTimestamp()}]`, ...args);
  },
  error: (...args: any[]) => {
    if (!shouldLog("error")) return;
    console.error(`[ERROR] [${formatTimestamp()}]`, ...args);
  },
};

export { LogLevel };
