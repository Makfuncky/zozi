/**
 * Frontend RBAC runtime.
 * Fetches the catalog from /api/v1/rbac/catalog and gates UI on the resolved
 * feature set (Law 167).
 */
import { FEATURE_CATALOG, FEATURE_SET, isKnownFeature } from "@zozi/shared/permissions";

let cached: { catalog: string[]; fetchedAt: number } | null = null;
let userFeatures: Set<string> = new Set();

const CACHE_TTL_MS = 60_000;

export async function fetchRbacCatalog(force = false): Promise<string[]> {
  if (!force && cached && Date.now() - cached.fetchedAt < CACHE_TTL_MS) {
    return cached.catalog;
  }
  const resp = await fetch("/api/v1/rbac/catalog", { credentials: "include" });
  if (!resp.ok) throw new Error(`RBAC catalog fetch failed: ${resp.status}`);
  const data = await resp.json();
  const list: string[] = Array.isArray(data.features) ? data.features : Object.keys(data.FEATURE_CATALOG || data);
  cached = { catalog: list, fetchedAt: Date.now() };
  return list;
}

export function setUserFeatures(features: string[] | Set<string>): void {
  userFeatures = features instanceof Set ? new Set(features) : new Set(features);
}

export function hasFeature(feature: string): boolean {
  if (userFeatures.has("*")) return true;
  return userFeatures.has(feature);
}

export function clearRbacCache(): void {
  cached = null;
}

export { FEATURE_CATALOG, FEATURE_SET, isKnownFeature };
