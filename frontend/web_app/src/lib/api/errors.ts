/**
 * API error utilities — extraction, categorization, and toast-integrated handling.
 */

import { logFrontendError } from "@shared/errorLogging";
import { useToastStore } from "@/lib/toastStore";

export function getErrorMessage(data: any): string {
  if (typeof data.detail === "string") {
    return data.detail;
  }
  if (Array.isArray(data.detail) && data.detail.length > 0) {
    return data.detail[0].msg || "Validation error";
  }
  if (data.message) {
    return data.message;
  }
  if (typeof data.error === "string") {
    return "Too many attempts. Please wait a moment and try again.";
  }
  return "An error occurred";
}

function normalizeErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  if (typeof error === "string") return error;
  try { return JSON.stringify(error); } catch { return "Unknown error"; }
}

export function categorizeError(error: any): { category: string; retryable: boolean } {
  if (error instanceof TypeError && /failed to fetch/i.test(error.message)) {
    return { category: "network_error", retryable: true };
  }

  if (error instanceof DOMException && error.name === "AbortError") {
    return { category: "timeout_error", retryable: true };
  }

  const message = normalizeErrorMessage(error).toLowerCase();

  if (/timeout|networkrequestfailed/.test(message)) {
    return { category: "timeout_error", retryable: true };
  }

  if (error instanceof Response) {
    if (error.status >= 500) {
      return { category: "server_error", retryable: true };
    }
    if (error.status === 429) {
      return { category: "rate_limit_error", retryable: true };
    }
    if (error.status === 401) {
      return { category: "auth_error", retryable: false };
    }
    if (error.status === 403) {
      return { category: "forbidden_error", retryable: false };
    }
    if (error.status === 404) {
      return { category: "not_found_error", retryable: false };
    }
    if (error.status >= 400) {
      return { category: "client_error", retryable: false };
    }
  }

  if (typeof error === "object" && error !== null && "status" in error) {
    if (error.status >= 500) {
      return { category: "server_error", retryable: true };
    }
    if (error.status === 429) {
      return { category: "rate_limit_error", retryable: true };
    }
    return { category: "client_error", retryable: false };
  }

  return { category: "unknown_error", retryable: false };
}

/**
 * Enhanced error handler that integrates with toast notifications.
 */
export function handleApiError(
  error: any,
  context?: string,
  options?: { showToast?: boolean; source?: string }
): void {
  let message = "An unknown error occurred";
  let statusCode: number | undefined;

  if (error instanceof Response) {
    statusCode = error.status;
    message = `HTTP ${error.status}: ${error.statusText || "Request failed"}`;
  } else if (error instanceof TypeError && error.message.includes("Failed to fetch")) {
    message = "Network error. Please check your connection.";
  } else if (error instanceof Error) {
    message = error.message;
  } else if (typeof error === "string") {
    message = error;
  } else if (error && typeof error === "object") {
    message = getErrorMessage(error);
    if (error.status) statusCode = error.status;
  }

  const logSource = options?.source || context || "api";

  logFrontendError(error, `api-${logSource}`, {
    statusCode,
    message,
  });

  if (typeof console !== "undefined") {
    console.error(`[API Error${context ? ` - ${context}` : ""}]: ${message}`, error);
  }

  const showToast = options?.showToast !== false;
  if (showToast && statusCode !== 401 && typeof window !== "undefined") {
    const toastStore = useToastStore.getState?.();
    if (toastStore?.addToast) {
      const toastType = statusCode && statusCode >= 500 ? "error" : "warning";
      toastStore.addToast(message, toastType, 5000);
    }
  }
}
