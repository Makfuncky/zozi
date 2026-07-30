import { Alert, Platform } from "react-native";
import { logger, setLogLevel } from "@/lib/logger";
import { logFrontendError } from "@shared/errorLogging";
import { reportErrorToBackend } from "@/lib/errorReporter";

export class GlobalErrorHandler {
  private static instance: GlobalErrorHandler;
  private isInitialized = false;
  private previousHandler: ((error: any, isFatal?: boolean) => void) | null = null;

  static getInstance(): GlobalErrorHandler {
    if (!GlobalErrorHandler.instance) {
      GlobalErrorHandler.instance = new GlobalErrorHandler();
    }
    return GlobalErrorHandler.instance;
  }

  initialize() {
    if (this.isInitialized) return;
    this.isInitialized = true;

    const errorUtils = (global as any).ErrorUtils;
    setLogLevel(__DEV__ ? "debug" : "warn");

    if (errorUtils && typeof errorUtils.setGlobalHandler === "function") {
      this.previousHandler = errorUtils.getGlobalHandler?.();

      errorUtils.setGlobalHandler((error: any, isFatal?: boolean) => {
        const entry = logFrontendError(error, "mobile-global-error", { isFatal });
        reportErrorToBackend(entry);
        logger.error("[GlobalErrorHandler] Mobile uncaught error:", error, { isFatal });

        if (Platform.OS !== "web") {
          Alert.alert("Unexpected error", "An unexpected error occurred. Please restart the app.");
        }

        this.previousHandler?.(error, isFatal);
      });

      logger.info("[GlobalErrorHandler] Initialized");
    } else {
      logger.warn("[GlobalErrorHandler] ErrorUtils not available on this platform");
    }
  }

  reportError(error: Error, context?: Record<string, any>) {
    const entry = logFrontendError(error, "mobile-manual-report", context);
    reportErrorToBackend(entry);
    logger.error("[Manual Error Report]", { error, context });
  }

  reportIssue(message: string, level: "info" | "warning" | "error" = "info", context?: Record<string, any>) {
    if (level === "error") {
      const entry = logFrontendError(message, "mobile-issue", context);
      reportErrorToBackend(entry);
    }
    if (level === "error") logger.error(`[${level.toUpperCase()}] ${message}`, context);
    else if (level === "warning") logger.warn(`[${level.toUpperCase()}] ${message}`, context);
    else logger.info(`[${level.toUpperCase()}] ${message}`, context);
  }
}

export const globalErrorHandler = GlobalErrorHandler.getInstance();
