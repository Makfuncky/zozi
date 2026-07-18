/**
 * useApprovalCheck.ts – pre-flight approval-eligibility hook.
 *
 * Lets admin UI pages check whether the current user can approve a given
 * resource before firing the write request. Falls back gracefully when
 * the hierarchy/approval-matrix backend is unavailable or the user has
 * no Employee record (backward-compat mode: returns `eligible: true`).
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { UserInfo } from "@/lib/useAuth";

const CACHE_TTL_MS = 60_000;
let cachedAt = 0;
let cachedUserId: number | null = null;
let cachedEligibility: Record<string, boolean> = {};

export interface ApprovalEligibilityResult {
  eligible: boolean;
  reason?: string;
  authorityLevel?: number | null;
  requiredLevel?: number;
  approvers?: Array<{ user_id: number; username: string; role: string; authority_level: number }>;
}

function cacheKey(userId: number, resourceType: string, amount?: number | null): string {
  return `${userId}:${resourceType}:${amount ?? ""}`;
}

export function useApprovalCheck(user: UserInfo | null) {
  const [eligibilityMap, setEligibilityMap] = useState<Record<string, ApprovalEligibilityResult>>({});
  const [loading, setLoading] = useState(false);

  const canApprove = useCallback(
    async (resourceType: "product" | "supplier" | "payout", amount?: number | null): Promise<ApprovalEligibilityResult> => {
      if (!user?.id) return { eligible: true };
      const key = cacheKey(user.id, resourceType, amount);

      const isCached =
        cachedUserId === user.id &&
        Date.now() - cachedAt < CACHE_TTL_MS &&
        key in cachedEligibility;
      if (isCached) {
        return { eligible: cachedEligibility[key] };
      }

      setLoading(true);
      try {
        const qs = new URLSearchParams({ user_id: String(user.id), resource_type: resourceType });
        if (amount != null && !Number.isNaN(amount)) qs.set("amount", String(amount));

        const res = await apiFetch(`/admin/hierarchy/approval-matrix/check?${qs.toString()}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ resource_type: resourceType, amount: amount ?? null }),
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({} as any));
          const reason = typeof err?.detail === "string" ? err.detail : "Unable to verify approval eligibility";
          return { eligible: false, reason };
        }

        const payload = await res.json() as {
          can_approve: boolean;
          reason?: string;
          authority_level?: number | null;
          min_authority_level?: number;
          approvers?: Array<{ user_id: number; username: string; role: string; authority_level: number }>;
        };

        const result: ApprovalEligibilityResult = {
          eligible: payload.can_approve,
          reason: payload.reason,
          authorityLevel: payload.authority_level,
          requiredLevel: payload.min_authority_level,
          approvers: payload.approvers,
        };

        cachedUserId = user.id;
        cachedAt = Date.now();
        cachedEligibility[key] = payload.can_approve;

        setEligibilityMap((prev) => ({ ...prev, [key]: result }));
        return result;
      } catch {
        return { eligible: true };
      } finally {
        setLoading(false);
      }
    },
    [user?.id],
  );

  const invalidateCache = useCallback(() => {
    cachedAt = 0;
    cachedUserId = null;
    cachedEligibility = {};
    setEligibilityMap({});
  }, []);

  // Refresh cache on login
  useEffect(() => {
    if (user?.id) invalidateCache();
  }, [user?.id, invalidateCache]);

  const getEligibility = useCallback(
    (resourceType: "product" | "supplier" | "payout", amount?: number | null) => {
      const key = cacheKey(user?.id ?? 0, resourceType, amount);
      return eligibilityMap[key] ?? null;
    },
    [eligibilityMap, user?.id],
  );

  return {
    canApprove,
    getEligibility,
    invalidateCache,
    loading,
  };
}
