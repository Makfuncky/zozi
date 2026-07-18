/**
 * Mock LogBox to avoid React module resolution issues on Windows
 */

export const LogBox = {
  ignoreLogs: () => {},
  ignoreAllLogs: () => {},
  show: () => {},
  hide: () => {},
};

export const LogBoxLog = class {
  constructor() {}
};

export const LogContext = {
  Provider: ({ children }: { children: React.ReactNode }) => children,
};

export function useLogs() {
  return {
    selectedLogIndex: 0,
    isDisabled: false,
    logs: [],
  };
}

// Mock for other LogBox exports
export const LogBoxLogData = {};
export const LogBoxLogItem = {};