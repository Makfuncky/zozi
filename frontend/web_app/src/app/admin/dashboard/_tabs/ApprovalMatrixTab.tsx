"use client";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  AlertCircle,
  CheckCircle2,
  GitBranch,
  ListChecks,
  Search,
  ShieldCheck,
  UserCheck,
  XCircle,
} from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { useToastStore } from "@/lib/toastStore";
import { hasAdminPermission } from "@shared/adminPermissions";
import { dc, useDensity, type Density } from "@/lib/densityContext";
import {
  ApprovalChainItem,
  ApprovalChainResponse,
  ApprovalEligibility,
  ApprovalMatrixResponse,
  ApprovalMatrixRules,
  ApproverSummary,
} from "@shared/types";
import {
  checkApprovalEligibility,
  getApprovalMatrixRules,
  getResourceApprovers,
  getUserApprovalChain,
} from "@/lib/approvalMatrixApi";
import { EnterpriseDataTable, type EnterpriseColumn } from "@shared/components/EnterpriseDataTable";
import { PanelContent } from "@/components/PanelPage";

type Tab = "rules" | "check" | "approvers" | "chain";

const RESOURCE_TYPES = [
  { value: "product", label: "Product" },
  { value: "supplier", label: "Supplier" },
  { value: "payout", label: "Payout" },
] as const;

const DENSITY_TEXT = (mode: Density) => dc(mode, "text-[11px]", "text-xs", "text-sm");

function ApprovalMatrixInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const tab = (searchParams?.get("tab") || "rules") as Tab;
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();
  const role = user?.role ?? null;
  const addToast = useToastStore((state) => state.addToast);
  const { density } = useDensity();

  const [rules, setRules] = useState<ApprovalMatrixRules | null>(null);
  const [eligibility, setEligibility] = useState<ApprovalEligibility | null>(null);
  const [approvers, setApprovers] = useState<ApprovalMatrixResponse | null>(null);
  const [chain, setChain] = useState<ApprovalChainResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const [checkUserId, setCheckUserId] = useState("1");
  const [checkResourceType, setCheckResourceType] = useState("product");
  const [checkAmount, setCheckAmount] = useState("");
  const [approverResourceType, setApproverResourceType] = useState("product");
  const [approverOrgUnitId, setApproverOrgUnitId] = useState("");
  const [chainUserId, setChainUserId] = useState("1");
  const [chainResourceType, setChainResourceType] = useState("product");

  const canView = hasAdminPermission(role, "hierarchy.view");

  useEffect(() => {
    if (!canView) {
      router.replace("/admin/dashboard");
    }
  }, [canView, router]);

  const switchTab = useCallback(
    (next: Tab) => {
      router.replace(`/admin/dashboard?tab=approval-matrix&section=${next}`, { scroll: false });
    },
    [router],
  );

  const loadRules = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getApprovalMatrixRules();
      setRules(data);
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Unable to load approval rules", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  const loadApprovers = useCallback(async () => {
    setLoading(true);
    try {
      const orgId = approverOrgUnitId.trim() ? Number(approverOrgUnitId.trim()) : undefined;
      const data = await getResourceApprovers(approverResourceType, orgId);
      setApprovers(data);
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Unable to load approvers", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast, approverOrgUnitId, approverResourceType]);

  const loadChain = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getUserApprovalChain(Number(chainUserId), chainResourceType);
      setChain(data);
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Unable to load approval chain", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast, chainResourceType, chainUserId]);

  const runEligibilityCheck = useCallback(async () => {
    setSaving(true);
    try {
      const amount = checkAmount.trim() ? Number(checkAmount.trim()) : null;
      const data = await checkApprovalEligibility(Number(checkUserId), checkResourceType, amount);
      setEligibility(data);
      addToast(
        data.can_approve
          ? "User is eligible to approve this resource"
          : "User is NOT eligible to approve this resource",
        data.can_approve ? "success" : "warning",
      );
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Failed to check eligibility", "error");
    } finally {
      setSaving(false);
    }
  }, [addToast, checkAmount, checkResourceType, checkUserId]);

  useEffect(() => {
    if (!isLoggedIn) return;
    if (tab === "rules") loadRules();
    if (tab === "approvers") loadApprovers();
    if (tab === "chain") loadChain();
  }, [isLoggedIn, tab, loadRules, loadApprovers, loadChain]);

  const eligibilityColumns = useMemo<Array<EnterpriseColumn<ApprovalEligibility>>>(() => {
    if (!eligibility) return [];
    const rows: ApprovalEligibility[] = [eligibility];
    return [
      { key: "user_id", label: "User ID", width: "120px", render: (r) => <span className="font-mono text-xs">{r.user_id}</span> },
      { key: "resource_type", label: "Resource", render: (r) => <span className="text-xs font-semibold uppercase">{r.resource_type}</span> },
      {
        key: "can_approve",
        label: "Eligible",
        render: (r) => (
          <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold ${r.can_approve ? "bg-success/10 text-success" : "bg-danger/10 text-danger"}`}>
            {r.can_approve ? <CheckCircle2 className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
            {r.can_approve ? "Yes" : "No"}
          </span>
        ),
      },
      { key: "authority_level", label: "Authority Level", render: (r) => <span className="font-mono text-xs">{r.authority_level ?? "—"}</span> },
      { key: "amount", label: "Amount", render: (r) => <span className="font-mono text-xs">{r.amount != null ? r.amount.toLocaleString() : "—"}</span> },
      { key: "reason", label: "Reason", render: (r) => <span className="text-xs text-text-muted">{r.reason || "—"}</span> },
    ];
  }, [eligibility]);

  const approverColumns = useMemo<Array<EnterpriseColumn<ApproverSummary>>>(() => {
    if (!approvers) return [];
    return [
      { key: "user_id", label: "User ID", width: "110px", sortable: true, sortValue: (r) => r.user_id, render: (r) => <span className="font-mono text-xs">{r.user_id}</span> },
      { key: "username", label: "Approver", width: "240px", sortable: true, sortValue: (r) => r.username.toLowerCase(), render: (r) => <span className="text-xs font-semibold text-text">{r.username}</span> },
      { key: "role", label: "Role", width: "160px", sortable: true, sortValue: (r) => r.role, render: (r) => <span className="inline-flex rounded-md border px-1.5 py-0.5 text-[10px] font-semibold capitalize">{r.role.replace("_", " ")}</span> },
      { key: "authority_level", label: "Level", width: "100px", sortable: true, sortValue: (r) => r.authority_level, align: "right", render: (r) => <span className="font-mono text-xs">{r.authority_level}</span> },
      { key: "org_unit_name", label: "Org Unit", width: "180px", render: (r) => <span className="text-xs text-text-muted">{r.org_unit_name || "—"}</span> },
      { key: "department", label: "Department", width: "180px", render: (r) => <span className="text-xs text-text-muted">{r.department || "—"}</span> },
      { key: "distance", label: "Distance", width: "120px", sortable: true, sortValue: (r) => r.distance ?? 0, align: "right", render: (r) => <span className="font-mono text-xs">{r.distance ?? "—"}</span> },
    ];
  }, [approvers]);

  const chainColumns = useMemo<Array<EnterpriseColumn<ApprovalChainItem>>>(() => {
    if (!chain) return [];
    return [
      { key: "user_id", label: "User ID", width: "110px", render: (r) => <span className="font-mono text-xs">{r.user_id}</span> },
      { key: "username", label: "Approver", width: "240px", render: (r) => <span className="text-xs font-semibold text-text">{r.username}</span> },
      { key: "role", label: "Role", width: "160px", render: (r) => <span className="inline-flex rounded-md border px-1.5 py-0.5 text-[10px] font-semibold capitalize">{r.role.replace("_", " ")}</span> },
      { key: "authority_level", label: "Level", width: "100px", align: "right", render: (r) => <span className="font-mono text-xs">{r.authority_level}</span> },
      { key: "org_unit_name", label: "Org Unit", width: "180px", render: (r) => <span className="text-xs text-text-muted">{r.org_unit_name || "—"}</span> },
      { key: "distance", label: "Distance", width: "120px", align: "right", render: (r) => <span className="font-mono text-xs">{r.distance}</span> },
    ];
  }, [chain]);

  if (!canView) {
    return (
      <AdminLayout title="Approval Matrix" headerMode="compact">
        <PanelContent>
          <div className="theme-card rounded-2xl border p-6 text-sm text-text-muted">You do not have permission to view the approval matrix.</div>
        </PanelContent>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout title="Approval Matrix" headerMode="compact">
      <PanelContent className="space-y-4">
        <div className="theme-card rounded-xl border p-2">
          <div className="flex flex-wrap gap-1">
            {[
              { key: "rules", label: "Rules", icon: ListChecks },
              { key: "check", label: "Check Eligibility", icon: ShieldCheck },
              { key: "approvers", label: "Approvers", icon: UserCheck },
              { key: "chain", label: "Approval Chain", icon: GitBranch },
            ].map((t) => (
              <button
                key={t.key}
                type="button"
                onClick={() => switchTab(t.key as Tab)}
                className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold transition-colors ${
                  tab === t.key ? "theme-btn-primary shadow-none" : "theme-btn-secondary border border-transparent text-text-muted hover:border-border/70 hover:text-text"
                }`}
              >
                <t.icon className="h-3.5 w-3.5" />
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {tab === "rules" && (
          <div className="theme-card rounded-2xl border p-5">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-text">Approval Rules</h2>
                <p className="mt-1 text-xs text-text-muted">Global approval matrix configuration by resource type.</p>
              </div>
              <button onClick={loadRules} disabled={loading} className="theme-btn-secondary rounded-lg border px-3 py-2 text-xs font-semibold text-text-muted disabled:opacity-50">
                {loading ? "Refreshing..." : "Refresh"}
              </button>
            </div>
            {loading && !rules ? (
              <div className="space-y-2">
                {Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-16 animate-pulse rounded-xl bg-surface-2" />)}
              </div>
            ) : rules ? (
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {Object.entries(rules.rules).map(([key, rule]) => (
                  <div key={key} className="rounded-xl border border-border bg-surface-2/60 p-4">
                    <div className="mb-2 flex items-center justify-between">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-text">{rule.label}</h3>
                      <span className="rounded-full border border-border px-2 py-0.5 text-[10px] font-semibold text-text-muted">{key}</span>
                    </div>
                    <div className="space-y-1.5 text-xs text-text-muted">
                      <p>Minimum authority level: <span className="font-mono font-semibold text-text">{rule.min_authority_level}</span></p>
                      {rule.department && <p>Department: <span className="font-semibold text-text">{rule.department}</span></p>}
                      <p>Org unit required: <span className="font-semibold text-text">{rule.org_unit_required ? "Yes" : "No"}</span></p>
                      <p className="pt-1 text-text-faint">{rule.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-text-muted">No rules loaded.</p>
            )}
          </div>
        )}

        {tab === "check" && (
          <div className="theme-card rounded-2xl border p-5">
            <h2 className="text-sm font-bold text-text">Check Approval Eligibility</h2>
            <p className="mt-1 mb-4 text-xs text-text-muted">Verify whether a specific user can approve a given resource type and amount.</p>

            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold text-text-muted">User ID</span>
                <input value={checkUserId} onChange={(e) => setCheckUserId(e.target.value)} className="theme-input w-full rounded-xl border px-3 py-2.5 text-xs" />
              </label>
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold text-text-muted">Resource Type</span>
                <select value={checkResourceType} onChange={(e) => setCheckResourceType(e.target.value)} className="theme-input w-full rounded-xl border px-3 py-2.5 text-xs">
                  {RESOURCE_TYPES.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
                </select>
              </label>
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold text-text-muted">Amount (optional)</span>
                <input value={checkAmount} onChange={(e) => setCheckAmount(e.target.value)} inputMode="decimal" className="theme-input w-full rounded-xl border px-3 py-2.5 text-xs" />
              </label>
              <div className="flex items-end">
                <button onClick={runEligibilityCheck} disabled={saving} className="theme-btn-primary w-full rounded-xl px-4 py-2.5 text-xs font-bold disabled:opacity-50">
                  {saving ? "Checking..." : "Check"}
                </button>
              </div>
            </div>

            {eligibility && (
              <div className={`mt-4 rounded-xl border p-4 ${eligibility.can_approve ? "border-success/30 bg-success/5" : "border-danger/30 bg-danger/5"}`}>
                <div className="flex flex-wrap items-center gap-3">
                  {eligibility.can_approve ? <CheckCircle2 className="h-5 w-5 text-success" /> : <XCircle className="h-5 w-5 text-danger" />}
                  <div>
                    <p className="text-xs font-bold text-text">{eligibility.can_approve ? "User is eligible" : "User is NOT eligible"}</p>
                    <p className="text-[11px] text-text-muted">User #{eligibility.user_id} on {eligibility.resource_type} {eligibility.amount != null ? `| amount ${eligibility.amount}` : ""}</p>
                    {eligibility.reason && <p className="text-[11px] text-text-faint">{eligibility.reason}</p>}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {tab === "approvers" && (
          <div className="theme-card rounded-2xl border p-5">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-sm font-bold text-text">Resolved Approvers</h2>
                <p className="mt-1 text-xs text-text-muted">Who can currently act on a given resource type and org unit.</p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <select value={approverResourceType} onChange={(e) => setApproverResourceType(e.target.value)} className="theme-input rounded-xl border px-3 py-2 text-xs">
                  {RESOURCE_TYPES.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
                </select>
                <input value={approverOrgUnitId} onChange={(e) => setApproverOrgUnitId(e.target.value)} placeholder="Org Unit ID (optional)" className="theme-input rounded-xl border px-3 py-2 text-xs w-32" />
                <button onClick={loadApprovers} disabled={loading} className="theme-btn-primary rounded-xl px-4 py-2 text-xs font-bold disabled:opacity-50">Load</button>
              </div>
            </div>

            {approvers && approvers.count === 0 && (
              <p className="text-xs text-text-muted">No approvers found for this resource type.</p>
            )}
            <EnterpriseDataTable
              columns={approverColumns}
              rows={approvers?.approvers ?? []}
              rowKey={(r) => r.user_id}
              densityMode={density}
              initialRowsPerPage={25}
              enableGlobalSearch={true}
              searchPlaceholder="Search approvers..."
              title={approvers ? `${approvers.count} approver(s)` : "Approvers"}
              emptyState={loading ? "Loading approvers..." : "Select a resource type and click Load."}
            />
          </div>
        )}

        {tab === "chain" && (
          <div className="theme-card rounded-2xl border p-5">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-sm font-bold text-text">Approval Chain</h2>
                <p className="mt-1 text-xs text-text-muted">Hierarchical chain of approvers for a user and resource type.</p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <input value={chainUserId} onChange={(e) => setChainUserId(e.target.value)} className="theme-input rounded-xl border px-3 py-2 text-xs w-24" />
                <select value={chainResourceType} onChange={(e) => setChainResourceType(e.target.value)} className="theme-input rounded-xl border px-3 py-2 text-xs">
                  {RESOURCE_TYPES.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
                </select>
                <button onClick={loadChain} disabled={loading} className="theme-btn-primary rounded-xl px-4 py-2 text-xs font-bold disabled:opacity-50">Load</button>
              </div>
            </div>

            {!chain || chain.count === 0 ? (
              <p className="text-xs text-text-muted">No chain entries. Enter a user ID and resource type, then click Load.</p>
            ) : (
              <>
                <p className="mb-3 text-xs text-text-muted">{chain.count} step(s) in chain</p>
                <div className="space-y-2">
                  {chain.chain.map((item, idx) => (
                    <div key={`${item.user_id}-${idx}`} className="flex items-center gap-3 rounded-xl border border-border bg-surface-2/60 p-3">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full theme-chip-brand text-[10px] font-bold text-white">
                        {item.distance}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-semibold text-text">{item.username}</p>
                        <p className="text-[11px] text-text-muted capitalize">{item.role.replace("_", " ")} • Level {item.authority_level} • {item.org_unit_name || "—"}</p>
                      </div>
                      <span className="shrink-0 rounded-full border border-border px-2 py-0.5 text-[10px] font-semibold text-text-muted">
                        Step {idx + 1}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        )}
      </PanelContent>
    </AdminLayout>
  );
}

export default function ApprovalMatrixPage() {
  return (
    <Suspense>
      <ApprovalMatrixInner />
    </Suspense>
  );
}
