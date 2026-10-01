"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { fetchRbacCatalog } from "@shared/adminPermissions";
import QueryErrorBoundary from "@/components/QueryErrorBoundary";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            gcTime: 5 * 60 * 1000, // 5 minutes
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  useEffect(() => {
    // ARCHITECTURE_DIAGRAM.md §7 — fetch the live RBAC catalog once at app boot
    // so getAvailablePermissions() reflects the server's authoritative feature
    // atoms (with namespace wildcards). Failures are non-fatal; the hardcoded
    // ADMIN_PERMISSION_MAP fallback remains in place until the catalog arrives.
    void fetchRbacCatalog();
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <QueryErrorBoundary>
        {children}
      </QueryErrorBoundary>
    </QueryClientProvider>
  );
}
