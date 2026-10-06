"use client";

/**
 * QueryErrorBoundary
 * ==================
 * Simple wrapper that renders children. Error handling is now done
 * via React error boundaries or per-component try/catch.
 */

import { type ReactNode } from "react";

export default function QueryErrorBoundary({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
