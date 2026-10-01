"use client";

import Link from "next/link";
import { AlertTriangle, Home, RefreshCw } from "lucide-react";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function Error({ error, reset }: ErrorProps) {
  return (
    <div className="min-h-screen bg-surface-0 flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <div className="w-20 h-20 rounded-full bg-error/10 flex items-center justify-center mx-auto mb-6">
          <AlertTriangle className="w-10 h-10 text-error" />
        </div>
        <h1 className="text-2xl font-display font-bold text-text-primary mb-3">
          Something went wrong
        </h1>
        <p className="text-text-secondary mb-2">
          We apologize for the inconvenience. Please try again.
        </p>
        {error?.message && (
          <p className="text-xs text-text-faint mb-6 font-mono bg-surface-1 rounded-lg p-3">
            {error.message}
          </p>
        )}
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={reset}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-primary text-white font-medium hover:bg-primary-dark transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Try Again
          </button>
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border border-border text-text-primary font-medium hover:bg-surface-1 transition-colors"
          >
            <Home className="w-4 h-4" />
            Go Home
          </Link>
        </div>
      </div>
    </div>
  );
}
