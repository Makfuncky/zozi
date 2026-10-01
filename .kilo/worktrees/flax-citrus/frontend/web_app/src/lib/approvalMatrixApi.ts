/**
 * approvalMatrixApi.ts — typed wrappers for approval-matrix endpoints.
 */
import { apiFetch } from "./api";

export interface ApprovalRuleSummary {
  label: string;
  min_authority_level: number;
  department?: string | null;
  org_unit_required: boolean;
  description: string;
}

export interface ApprovalMatrixRules {
  rules: Record<string, ApprovalRuleSummary>;
}

export interface ApprovalEligibility {
  can_approve: boolean;
  user_id: number;
  resource_type: string;
  authority_level?: number | null;
  amount?: number | null;
  reason?: string;
  requiredLevel?: number | null;
  approvers?: ApproverSummary[];
}

export interface ApproverSummary {
  user_id: number;
  username: string;
  role: string;
  authority_level: number;
  org_unit_name?: string | null;
  department?: string | null;
  distance?: number;
}

export interface ApprovalMatrixResponse {
  resource_type: string;
  org_unit_id?: number | null;
  approvers: ApproverSummary[];
  count: number;
}

export interface ApprovalChainItem {
  user_id: number;
  username: string;
  role: string;
  authority_level: number;
  org_unit_name?: string | null;
  distance: number;
}

export interface ApprovalChainResponse {
  user_id: number;
  resource_type: string;
  chain: ApprovalChainItem[];
  count: number;
}

async function handleError(res: Response, fallback: string): Promise<never> {
  const err = await res.json().catch(() => ({}));
  throw new Error(err.detail || fallback);
}

export async function getApprovalMatrixRules(): Promise<ApprovalMatrixRules> {
  const res = await apiFetch("/admin/hierarchy/approval-matrix/rules");
  if (!res.ok) return handleError(res, "Failed to load approval rules");
  return res.json();
}

export async function checkApprovalEligibility(
  userId: number,
  resourceType: string,
  amount?: number | null,
): Promise<ApprovalEligibility> {
  const qs = new URLSearchParams({ user_id: String(userId), resource_type: resourceType });
  if (amount != null && !Number.isNaN(amount)) qs.set("amount", String(amount));
  const res = await apiFetch(`/admin/hierarchy/approval-matrix/check?${qs.toString()}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resource_type: resourceType, amount: amount ?? null }),
  });
  if (!res.ok) return handleError(res, "Failed to check approval eligibility");
  return res.json();
}

export async function getResourceApprovers(
  resourceType: string,
  orgUnitId?: number | null,
): Promise<ApprovalMatrixResponse> {
  const qs = new URLSearchParams();
  if (orgUnitId != null && !Number.isNaN(orgUnitId)) qs.set("org_unit_id", String(orgUnitId));
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  const res = await apiFetch(`/admin/hierarchy/approvers/${encodeURIComponent(resourceType)}${suffix}`);
  if (!res.ok) return handleError(res, "Failed to load approvers");
  return res.json();
}

export async function getUserApprovalChain(
  userId: number,
  resourceType: string,
): Promise<ApprovalChainResponse> {
  const res = await apiFetch(`/admin/hierarchy/approval-chain/${encodeURIComponent(String(userId))}/${encodeURIComponent(resourceType)}`);
  if (!res.ok) return handleError(res, "Failed to load approval chain");
  return res.json();
}
