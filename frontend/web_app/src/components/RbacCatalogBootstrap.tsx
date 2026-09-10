"use client";

import { useEffect } from "react";

/**
 * Fetches `GET /api/v1/rbac/catalog` once on mount and pushes the result
 * into the in-memory permissions store so the admin UI reflects the
 * latest backend RBAC surface without a hard refresh.
 *
 * This is intentionally non-blocking: if the request fails (e.g. the user
 * is not authenticated yet, or the backend is unreachable), we simply fall
 * back to the build-time catalog baked into
 * ``frontend/shared/src/permissions.ts``. The component renders nothing.
 */
export default function RbacCatalogBootstrap() {
  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      try {
        const res = await fetch("/api/v1/rbac/catalog", {
          credentials: "include",
          cache: "no-store",
        });
        if (!res.ok) return;
        const body = (await res.json()) as { items?: string[] };
        const atoms = body.items ?? [];
        if (cancelled || atoms.length === 0) return;

        // Defer import so this component stays client-only and tiny.
        const { applyRbacCatalogAtoms } = await import("@zozi/shared/permissions");
        applyRbacCatalogAtoms(atoms);
      } catch {
        // Network or parse failure — fall back to the static catalog.
      }
    }

    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  return null;
}