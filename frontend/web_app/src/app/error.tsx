"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { logFrontendError } from "@shared/errorLogging";

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorId: string;
}

function generateErrorId(): string {
  return `err_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

export default class RootErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, errorId: "" };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorId: generateErrorId() };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    logFrontendError(error, "react-error-boundary", {
      componentStack: errorInfo.componentStack,
      errorId: this.state.errorId,
    });
    try {
      const body = JSON.stringify({
        errors: [{
          message: error.message,
          source: "react-error-boundary",
          stack: error.stack,
          context: { componentStack: errorInfo.componentStack, errorId: this.state.errorId },
          timestamp: new Date().toISOString(),
        }],
        user_agent: navigator.userAgent,
        url: window.location.href,
      });
      if (typeof window !== "undefined" && navigator.sendBeacon) {
        navigator.sendBeacon("/api/frontend-errors", body);
      }
    } catch {
      // best-effort reporting
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined, errorId: "" });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center p-6 bg-background">
          <div className="max-w-md rounded-2xl border border-danger/40 bg-danger/10 p-8 text-center">
            <h2 className="text-xl font-bold text-danger">Something went wrong</h2>
            <p className="mt-3 text-sm text-muted-foreground">
              {this.state.error?.message || "An unexpected error occurred. Please try again."}
            </p>
            <p className="mt-2 text-xs text-muted-foreground/60">Error ID: {this.state.errorId}</p>
            <button
              onClick={this.handleReset}
              className="mt-6 rounded-xl theme-btn-primary px-6 py-2.5 text-sm font-semibold"
            >
              Try again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}