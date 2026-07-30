"use client";

import { handleApiError } from "@/lib/api";
import { logFrontendError } from "@shared/errorLogging";
import { logger } from "@/lib/logger";

type Breadcrumb = {
  category: string;
  message: string;
  level: "debug" | "info" | "warn" | "error";
  timestamp: number;
  data?: Record<string, unknown>;
};

export class GlobalErrorHandler {
  private static instance: GlobalErrorHandler;
  private isInitialized = false;
  private breadcrumbs: Breadcrumb[] = [];
  private maxBreadcrumbs = 50;

  private onUnhandledRejection = (event: PromiseRejectionEvent) => {
    const reason = event.reason;
    this.addBreadcrumb("unhandled_promise", "Unhandled promise rejection", "error", {
      reason: this._normalizeMessage(reason),
    });
    logFrontendError(reason, "web-unhandled-promise-rejection");
    logger.error("[Unhandled Promise Rejection]", reason);
    handleApiError(reason, "unhandled-promise-rejection", {
      showToast: true,
      source: "unhandled-promise",
    });
    event.preventDefault();
  };

  private onWindowError = (event: ErrorEvent) => {
    const error = event.error || event.message;
    this.addBreadcrumb("window_error", "Uncaught window error", "error", {
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
    });
    logFrontendError(error, "web-window-error", {
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
    });
    logger.error("[Uncaught Error]", error);
    handleApiError(error, "uncaught-error", {
      showToast: false,
      source: "window-error",
    });
  };

  static getInstance(): GlobalErrorHandler {
    if (!GlobalErrorHandler.instance) {
      GlobalErrorHandler.instance = new GlobalErrorHandler();
    }
    return GlobalErrorHandler.instance;
  }

  initialize() {
    if (this.isInitialized || typeof window === "undefined") return;
    this.isInitialized = true;

    window.addEventListener("unhandledrejection", this.onUnhandledRejection);
    window.addEventListener("error", this.onWindowError);

    logger.info("[GlobalErrorHandler] Initialized");
  }

  private _normalizeMessage(error: unknown): string {
    if (error instanceof Error) return error.message;
    if (typeof error === "string") return error;
    try { return JSON.stringify(error); } catch { return "Unknown error"; }
  }

  private addBreadcrumb(category: string, message: string, level: Breadcrumb["level"], data?: Record<string, unknown>) {
    this.breadcrumbs.push({
      category,
      message,
      level,
      timestamp: Date.now(),
      data,
    });
    if (this.breadcrumbs.length > this.maxBreadcrumbs) {
      this.breadcrumbs = this.breadcrumbs.slice(-this.maxBreadcrumbs);
    }
  }

  addBreadcrumbPublic(category: string, message: string, data?: Record<string, unknown>) {
    this.addBreadcrumb(category, message, "info", data);
  }

  reportError(error: Error, context?: Record<string, any>) {
    this.addBreadcrumb("manual_report", "Manual error report", "error", context);
    logFrontendError(error, "web-manual-report", context);
    logger.error("[Manual Error Report]", { error, context });
    handleApiError(error, context?.source || "manual-report", {
      showToast: true,
      source: "manual",
    });
  }

  reportIssue(message: string, level: "info" | "warn" | "error" = "info", context?: Record<string, any>) {
    const mappedLevel = level === "warn" ? "warn" : level === "error" ? "error" : "info";
    if (mappedLevel === "error") {
      this.addBreadcrumb("issue", message, "error", context);
      logFrontendError(message, "web-issue", context);
    } else {
      this.addBreadcrumb("issue", message, mappedLevel, context);
    }
    const logMethod = mappedLevel === "error" ? logger.error : mappedLevel === "warn" ? logger.warn : logger.info;
    logMethod(`[${mappedLevel.toUpperCase()}] ${message}`, context);
  }

  getBreadcrumbs(): Breadcrumb[] {
    return [...this.breadcrumbs];
  }

  clearBreadcrumbs() {
    this.breadcrumbs = [];
  }
}

export const globalErrorHandler = GlobalErrorHandler.getInstance();
