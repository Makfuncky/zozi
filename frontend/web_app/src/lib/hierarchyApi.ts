/**
 * hierarchyApi.ts — typed wrappers for admin hierarchy endpoints.
 */
import { apiFetch } from "@/lib/api";

export interface OrgUnit {
  id: number;
  name: string;
  parent_id?: number | null;
  path?: string | null;
  is_active: boolean;
}

export interface EmployeeRecord {
  id: number;
  user_id: number;
  username?: string;
  email?: string;
  full_name?: string;
  role?: string;
  org_unit_id?: number | null;
  org_unit_name?: string | null;
  authority_level?: number | null;
  reporting_manager_id?: number | null;
  manager_name?: string | null;
  department?: string | null;
  job_title?: string | null;
}

export interface HierarchyChainNode {
  user_id: number;
  username: string;
  role: string;
  authority_level?: number | null;
  org_unit_name?: string | null;
}

export async function getAuthorityLevel(db: number | string): Promise<{ user_id: number; authority_level: number | null }> {
  const res = await apiFetch(`/admin/hierarchy/authority-level?user_id=${encodeURIComponent(String(db))}`);
  if (!res.ok) throw new Error("Failed to load authority level");
  return res.json();
}

export async function getUserChain(db: number | string): Promise<{ user_id: number; chain: HierarchyChainNode[] }> {
  const res = await apiFetch(`/admin/hierarchy/chain/${encodeURIComponent(String(db))}`);
  if (!res.ok) throw new Error("Failed to load hierarchy chain");
  return res.json();
}

export async function getAllSubordinates(db: number | string): Promise<{ user_id: number; subordinates: HierarchyChainNode[] }> {
  const res = await apiFetch(`/admin/hierarchy/subordinates/${encodeURIComponent(String(db))}`);
  if (!res.ok) throw new Error("Failed to load subordinates");
  return res.json();
}

export async function getTeamMembers(db: number | string): Promise<{ user_id: number; team_members: HierarchyChainNode[] }> {
  const res = await apiFetch(`/admin/hierarchy/team-members/${encodeURIComponent(String(db))}`);
  if (!res.ok) throw new Error("Failed to load team members");
  return res.json();
}

export async function checkInChain(
  upperUserId: number | string,
  lowerUserId: number | string,
): Promise<{ upper_user_id: number; lower_user_id: number; in_chain: boolean }> {
  const res = await apiFetch(`/admin/hierarchy/in-chain?upper_user_id=${encodeURIComponent(String(upperUserId))}&lower_user_id=${encodeURIComponent(String(lowerUserId))}`);
  if (!res.ok) throw new Error("Failed to check chain relationship");
  return res.json();
}

export async function getOrgChart(orgUnitId?: number | null): Promise<Record<string, unknown>> {
  const qs = orgUnitId != null ? `?org_unit_id=${encodeURIComponent(String(orgUnitId))}` : "";
  const res = await apiFetch(`/admin/hierarchy/org-chart${qs}`);
  if (!res.ok) throw new Error("Failed to load org chart");
  return res.json();
}

export async function reassignManager(
  userId: number | string,
  newManagerId: number | string | null,
): Promise<{ updated: boolean; user_id: number; manager_id: number | null }> {
  const res = await apiFetch("/admin/hierarchy/reassign-manager", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: Number(userId), new_manager_id: newManagerId == null ? null : Number(newManagerId) }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to reassign manager");
  }
  return res.json();
}

export async function backfillAuthorityLevels(): Promise<{ updated: number }> {
  const res = await apiFetch("/admin/hierarchy/backfill-authority-levels", { method: "POST" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to backfill authority levels");
  }
  return res.json();
}
