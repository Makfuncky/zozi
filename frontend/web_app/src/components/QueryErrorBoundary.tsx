"use client";

/**
 * QueryErrorBoundary
 * ==================
 * Global fallback that catches unhandled query errors. TanStack Query does
 * not surface errors as React render errors by default, so we attach the
 * QueryCache.onError handler and force a re-render with a shared <ErrorState />
 * banner. This is the systematic solution to "page crashed on 4xx/5xx":
 *   - any `useQuery` / `useApiQuery` that throws will trip this once
 *   - pages that handle the error locally (e.g. via `if (q.isError) return
 *     <ErrorState />`) are unaffected because `q.error` never reaches the
 *     global cache.
 */

import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { ErrorState } from "@/components/ui/ErrorState";

export default function QueryErrorBoundary({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const [unhandled, setUnhandled] = useState<{ message: string; retry: () => void } | null>(null);

  useEffect(() => {
    const cache = queryClient.getQueryCache();
    const handler = (event: { type: string; query?: { queryKey: readonly unknown[]; state: { error: unknown; status: string } } }) => {
      if (event.type !== "updated") return;
      const q = event.query;
      if (!q || q.state.status !== "error") return;
      const err = q.state.error;
      const message = err instanceof Error ? err.message : "Request failed";
      setUnhandled({
        message,
        retry: () => {
          queryClient.invalidateQueries({ queryKey: q.queryKey });
          setUnhandled(null);
        },
      });
    };
    const unsubscribe = cache.subscribe(handler);
    return () => {
      unsubscribe();
    };
  }, [queryClient]);

  if (unhandled) {
    return (
      <div className="px-4 py-6">
        <ErrorState
          title="We couldn't load this section"
          message={unhandled.message}
          onRetry={unhandled.retry}
        />
      </div>
    );
  }
  return <>{children}</>;
}