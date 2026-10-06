"use client";

/**
 * Shared <ErrorState /> / <Skeleton /> + simple data-fetching helpers.
 *
 * Per ARCHITECTURE_DIAGRAM.md §11, pages should render `<ErrorState />` on
 * query failure and a `<Skeleton />` (or `<ProductCardSkeleton />` etc.) on
 * loading. The `useApiQuery` hook below wraps native fetch in a React-friendly
 * interface so callers can render the shared states consistently.
 */

import { useState, useEffect, useCallback } from "react";

import { apiFetch, parseJsonResponse } from "./client";

export { Skeleton } from "@/components/LoadingSkeleton";
export { ErrorState } from "@/components/ui/ErrorState";

export type ApiQueryKey = readonly unknown[];

export type ApiQueryOptions<TData> = {
  queryKey: ApiQueryKey;
  path: string;
  init?: RequestInit;
};

export type ApiQueryResult<TData> = {
  data: TData | null;
  error: Error | null;
  isLoading: boolean;
  refetch: () => void;
};

export function useApiQuery<TData = unknown>({
  path,
  init,
}: ApiQueryOptions<TData>): ApiQueryResult<TData> {
  const [data, setData] = useState<TData | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refetch = useCallback(() => {
    setIsLoading(true);
    setError(null);
    apiFetch(path, init)
      .then(parseJsonResponse)
      .then(setData)
      .catch(setError)
      .finally(() => setIsLoading(false));
  }, [path, init]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { data, error, isLoading, refetch };
}
