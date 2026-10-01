"use client";

/**
 * Shared <ErrorState /> / <Skeleton /> + TanStack Query helpers.
 *
 * Per ARCHITECTURE_DIAGRAM.md §11, pages should render `<ErrorState />` on
 * query failure and a `<Skeleton />` (or `<ProductCardSkeleton />` etc.) on
 * loading. The `useApiQuery` hook below wraps `useQuery` and is the
 * recommended replacement for ad-hoc `useEffect` + `useState` + `apiFetch`
 * data fetching. It produces a standard `{ data, error, isLoading, refetch }`
 * tuple so callers can render the shared states consistently.
 */

import { useQuery, type UseQueryOptions, type UseQueryResult } from "@tanstack/react-query";
import { apiFetch, parseJsonResponse } from "./client";

export { Skeleton } from "@/components/LoadingSkeleton";
export { ErrorState } from "@/components/ui/ErrorState";

export type ApiQueryKey = readonly unknown[];

export type ApiQueryOptions<TData> = Omit<
  UseQueryOptions<TData, Error, TData, ApiQueryKey>,
  "queryKey" | "queryFn"
> & {
  queryKey: ApiQueryKey;
  path: string;
  init?: RequestInit;
};

export function useApiQuery<TData = unknown>({
  path,
  init,
  ...options
}: ApiQueryOptions<TData>): UseQueryResult<TData, Error> {
  return useQuery<TData, Error, TData, ApiQueryKey>({
    ...options,
    queryKey: options.queryKey,
    queryFn: async () => {
      const res = await apiFetch(path, init);
      if (!res.ok) {
        const body = await res.text().catch(() => "");
        throw new Error(`API ${res.status} ${res.statusText}: ${body.slice(0, 200)}`);
      }
      return (await parseJsonResponse(res)) as TData;
    },
  });
}