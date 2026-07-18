"use client";

/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { Component, ErrorInfo, ReactNode } from "react";
import { getFrontendErrorLogs, logFrontendError, type FrontendErrorLogEntry } from "../../errorLogging";

export interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  errorMessage: string;
  recentLogs: FrontendErrorLogEntry[];
}

/**
 * Simple Error Boundary component
 */
export default class ErrorBoundary extends Component<ErrorBoundaryProps, State> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, errorMessage: "", recentLogs: [] };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      errorMessage: error.message,
      recentLogs: getFrontendErrorLogs().slice(0, 5),
    };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    this.props.onError?.(error, info);
    logFrontendError(error, "web-error-boundary", {
      componentStack: info.componentStack,
    });
    console.error("[ErrorBoundary]", error, info);
    this.setState({ recentLogs: getFrontendErrorLogs().slice(0, 5) });
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default fallback
      return (
        <div style={{ padding: 24, maxWidth: 720, margin: "48px auto", border: "1px solid #fecaca", borderRadius: 20, background: "#fff7f7", color: "#7f1d1d" }}>
          <h2 style={{ margin: "0 0 8px", fontSize: 24 }}>Something went wrong</h2>
          <p style={{ margin: "0 0 16px" }}>{this.state.errorMessage}</p>
          <details style={{ marginBottom: 16, textAlign: "left", background: "#ffffff", borderRadius: 12, padding: 12 }}>
            <summary style={{ cursor: "pointer", fontWeight: 600 }}>Error handling window</summary>
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
          <button onClick={() => this.setState({ hasError: false, errorMessage: "", recentLogs: [] })}>
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}