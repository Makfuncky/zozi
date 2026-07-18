"use client";

import { handleApiError } from "@/lib/api";
import { logFrontendError } from "@shared/errorLogging";

/**
 * Global error handler for unhandled errors and promise rejections
 */
export class GlobalErrorHandler {
  private static instance: GlobalErrorHandler;
  private isInitialized = false;
  private onUnhandledRejection = (event: PromiseRejectionEvent) => {
    logFrontendError(event.reason, "web-unhandled-promise-rejection");
    console.error("[Unhandled Promise Rejection]", event.reason);
    handleApiError(event.reason, "unhandled-promise-rejection");
    event.preventDefault();
  };

  private onWindowError = (event: ErrorEvent) => {
    logFrontendError(event.error || event.message, "web-window-error", {
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
    });
    console.error("[Uncaught Error]", event.error || event.message);
    handleApiError(event.error || event.message, "uncaught-error");
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

    console.log("[GlobalErrorHandler] Initialized");
  }

  /**
   * Manually report an error
   */
  reportError(error: Error, context?: Record<string, any>) {
    logFrontendError(error, "web-manual-report", context);
    console.error("[Manual Error Report]", { error, context });
    handleApiError(error, context?.source || "manual-report");
  }

  /**
   * Report a non-error issue (warning, info)
   */
  reportIssue(message: string, level: "info" | "warning" | "error" = "info", context?: Record<string, any>) {
    if (level === "error") {
      logFrontendError(message, "web-issue", context);
    }
    const logMethod = level === "error" ? console.error : level === "warning" ? console.warn : console.info;
    logMethod(`[${level.toUpperCase()}] ${message}`, context);
  }
}

// Initialize the global error handler
export const globalErrorHandler = GlobalErrorHandler.getInstance();
