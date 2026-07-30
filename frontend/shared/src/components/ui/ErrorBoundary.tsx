"use client";

/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { Component, ErrorInfo, ReactNode } from "react";
import { getFrontendErrorLogs, logFrontendError, type FrontendErrorLogEntry } from "../../errorLogging";

export interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  onReset?: () => void;
  showReportButton?: boolean;
}

interface State {
  hasError: boolean;
  errorMessage: string;
  error?: Error;
  errorId: string;
  recentLogs: FrontendErrorLogEntry[];
}

function generateErrorId(): string {
  return `err_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

function tryReportToBackend(error: Error, info: ErrorInfo, errorId: string) {
  if (typeof window === "undefined") return;
  try {
    const reportEndpoint = "/api/frontend-errors";
    const body = JSON.stringify({
      errors: [{
        message: error.message,
        source: "react-error-boundary",
        stack: error.stack,
        context: {
          componentStack: info.componentStack,
          errorId,
          fingerprint: `${error.name}:${error.message}`,
        },
        timestamp: new Date().toISOString(),
      }],
      user_agent: navigator.userAgent,
      url: window.location.href,
    });
    if (navigator.sendBeacon) {
      navigator.sendBeacon(reportEndpoint, body);
    } else {
      fetch(reportEndpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body });
    }
  } catch {
    // silently fail - we're already in error state
  }
}

export default class ErrorBoundary extends Component<ErrorBoundaryProps, State> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, errorMessage: "", errorId: "", recentLogs: [] };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      errorMessage: error.message,
      error,
      errorId: generateErrorId(),
      recentLogs: getFrontendErrorLogs().slice(0, 5),
    };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    this.props.onError?.(error, info);
    logFrontendError(error, "react-error-boundary", {
      componentStack: info.componentStack,
      errorId: this.state.errorId,
    });
    tryReportToBackend(error, info, this.state.errorId);
    if (typeof console !== "undefined") {
      console.error("[ErrorBoundary]", error, info);
    }
    this.setState({ recentLogs: getFrontendErrorLogs().slice(0, 5) });
  }

  handleReset = () => {
    this.props.onReset?.();
    this.setState({ hasError: false, errorMessage: "", error: undefined, errorId: "", recentLogs: [] });
  };

  handleReport = () => {
    const { error } = this.state;
    if (!error) return;
    try {
      const details = `Error: ${error.message}\nStack: ${error.stack}\nComponent Stack: ${this.state.recentLogs.map(l => l.message).join("\n")}`;
      navigator.clipboard.writeText(details).catch(() => {});
    } catch {
      // silently fail
    }
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div style={{ padding: 24, maxWidth: 720, margin: "48px auto", border: "1px solid #fecaca", borderRadius: 20, background: "#fff7f7", color: "#7f1d1d", fontFamily: "system-ui, sans-serif" }}>
          <h2 style={{ margin: "0 0 8px", fontSize: 24 }}>Something went wrong</h2>
          <p style={{ margin: "0 0 8px", fontSize: 14, color: "#991b1b" }}>Error ID: {this.state.errorId}</p>
          <p style={{ margin: "0 0 16px" }}>{this.state.errorMessage}</p>
          <details style={{ marginBottom: 16, textAlign: "left", background: "#ffffff", borderRadius: 12, padding: 12 }}>
            <summary style={{ cursor: "pointer", fontWeight: 600 }}>Error details</summary>
            <div style={{ marginTop: 12, fontSize: 13 }}>
              {this.state.recentLogs.length === 0 ? (
                <p>No frontend error logs captured yet.</p>
              ) : (
                this.state.recentLogs.map((entry) => (
                  <div key={entry.id} style={{ marginBottom: 10, paddingBottom: 10, borderBottom: "1px solid #e5e7eb" }}>
                    <div><strong>{entry.source}</strong> at {entry.timestamp}</div>
                    <div>{entry.message}</div>
                  </div>
                ))
              )}
            </div>
          </details>
          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={this.handleReset} style={{ padding: "8px 16px", borderRadius: 8, border: "none", background: "#2563eb", color: "white", cursor: "pointer", fontWeight: 600 }}>
              Try again
            </button>
            {this.props.showReportButton && (
              <button onClick={this.handleReport} style={{ padding: "8px 16px", borderRadius: 8, border: "1px solid #dc2626", background: "white", color: "#dc2626", cursor: "pointer", fontWeight: 600 }}>
                Copy error details
              </button>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
