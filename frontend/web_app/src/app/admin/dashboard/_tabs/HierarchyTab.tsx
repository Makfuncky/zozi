"use client";

import {
  ArrowUpCircle,
  CheckCircle2,
  ChevronRight,
  GitBranch,
  Network,
  RefreshCw,
  Search,
  Users,
  XCircle,
} from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { useToastStore } from "@/lib/toastStore";
import { hasAdminPermission, setAdminPermissionOverrides } from "@shared/adminPermissions";
import { dc, useDensity, type Density } from "@/lib/densityContext";
import { PanelContent, PanelTabs } from "@/components/PanelPage";
import { EnterpriseDataTable, type EnterpriseColumn } from "@shared/components/EnterpriseDataTable";
import {
  backfillAuthorityLevels,
  getAllSubordinates,
  getAuthorityLevel,
  getOrgChart,
  getTeamMembers,
  getUserChain,
  reassignManager,
} from "@/lib/hierarchyApi";
import { ApprovalChainItem, ApprovalMatrixResponse, EmployeeRecord, HierarchyChainNode, OrgUnit } from "@shared/types";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

type Tab = "org-chart" | "authority" | "team" | "reassign" | "backfill";

const SECTION_OPTIONS = [
  { key: "org-chart", label: "Org Chart", icon: GitBranch },
  { key: "authority", label: "Authority Levels", icon: ArrowUpCircle },
  { key: "team", label: "Team Members", icon: Users },
  { key: "reassign", label: "Reassign Manager", icon: Network },
  { key: "backfill", label: "Backfill Levels", icon: RefreshCw },
] as const;

function HierarchyInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const tab = (searchParams?.get("section") || "org-chart") as Tab;
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();
  const role = user?.role ?? null;
  const addToast = useToastStore((state) => state.addToast);
  const { density } = useDensity();
  const textCls = DENSITY_TEXT(density);
  const canView = hasAdminPermission(role, "hierarchy.view");

  const [loading, setLoading] = useState(false);
  const [chain, setChain] = useState<HierarchyChainNode[]>([]);
  const [authorityLevel, setAuthorityLevel] = useState<number | null>(null);
  const [subordinates, setSubordinates] = useState<HierarchyChainNode[]>([]);
  const [teamMembers, setTeamMembers] = useState<HierarchyChainNode[]>([]);
  const [orgChart, setOrgChart] = useState<OrgUnit[]>([]);
  const [backfillCount, setBackfillCount] = useState<number | null>(null);

  const [authorityUserId, setAuthorityUserId] = useState("1");
  const [chainUserId, setChainUserId] = useState("1");
  const [subordinatesUserId, setSubordinatesUserId] = useState("1");
  const [teamUserId, setTeamUserId] = useState("1");
  const [reassignUserId, setReassignUserId] = useState("1");
  const [reassignNewManagerId, setReassignNewManagerId] = useState("");
  const [reassignSaving, setReassignSaving] = useState(false);
  const [backfillSaving, setBackfillSaving] = useState(false);

  useEffect(() => {
    if (!isLoggedIn) return;
    if (!canView) {
      router.replace("/admin/dashboard");
      return;
    }
    // Load permissions matrix for consistency with backend.
    apiFetch("/admin/hierarchy/permissions")
      .then((r) => r.ok ? r.json() : null)
      .then((data) => { if (data?.matrix) setAdminPermissionOverrides(data.matrix); })
      .catch(() => {});
  }, [isLoggedIn, canView, router]);

  const loadChain = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getUserChain(Number(chainUserId));
      setChain(data.chain);
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Failed to load chain", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast, chainUserId]);

  const loadAuthority = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getAuthorityLevel(Number(authorityUserId));
      setAuthorityLevel(data.authority_level);
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Failed to load authority level", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast, authorityUserId]);

  const loadSubordinates = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getAllSubordinates(Number(subordinatesUserId));
      setSubordinates(data.subordinates);
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Failed to load subordinates", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast, subordinatesUserId]);

  const loadTeamMembers = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getTeamMembers(Number(teamUserId));
      setTeamMembers(data.team_members);
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Failed to load team members", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast, teamUserId]);

  const loadOrgChart = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getOrgChart();
      const units = Array.isArray(data) ? (data as OrgUnit[]) : [];
      setOrgChart(units);
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Failed to load org chart", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  const doReassign = useCallback(async () => {
    if (!reassignUserId) return;
    setReassignSaving(true);
    try {
      const newId = reassignNewManagerId.trim() ? Number(reassignNewManagerId.trim()) : null;
      const result = await reassignManager(Number(reassignUserId), newId);
      addToast(`Manager reassigned for user #${result.user_id}`, "success");
      setReassignNewManagerId("");
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Failed to reassign manager", "error");
    } finally {
      setReassignSaving(false);
    }
  }, [addToast, reassignManager, reassignNewManagerId, reassignUserId]);

  const doBackfill = useCallback(async () => {
    setBackfillSaving(true);
    try {
      const result = await backfillAuthorityLevels();
      setBackfillCount(result.updated);
      addToast(`Authority levels backfilled for ${result.updated} employee(s)`, "success");
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Failed to backfill authority levels", "error");
    } finally {
      setBackfillSaving(false);
    }
  }, [addToast]);

  useEffect(() => {
    if (!isLoggedIn) return;
    if (tab === "org-chart") loadOrgChart();
    if (tab === "authority") loadAuthority();
    if (tab === "team") loadTeamMembers();
  }, [isLoggedIn, tab, loadOrgChart, loadAuthority, loadTeamMembers]);

  const chainColumns = useMemo<Array<EnterpriseColumn<HierarchyChainNode>>>(() => [
    { key: "user_id", label: "User ID", width: "110px", render: (n) => <span className="font-mono text-xs">{n.user_id}</span> },
    { key: "username", label: "Name", width: "220px", render: (n) => <span className="text-xs font-semibold text-text">{n.username}</span> },
    { key: "role", label: "Role", width: "180px", render: (n) => <span className="inline-flex rounded-md border px-1.5 py-0.5 text-[10px] font-semibold capitalize">{n.role.replace("_", " ")}</span> },
    { key: "authority_level", label: "Level", width: "100px", align: "right", render: (n) => <span className="font-mono text-xs">{n.authority_level ?? "—"}</span> },
    { key: "org_unit_name", label: "Org Unit", width: "180px", render: (n) => <span className="text-xs text-text-muted">{n.org_unit_name || "—"}</span> },
  ], []);

  const subordinateColumns = useMemo<Array<EnterpriseColumn<HierarchyChainNode>>>(() => [
    { key: "user_id", label: "User ID", width: "110px", render: (n) => <span className="font-mono text-xs">{n.user_id}</span> },
    { key: "username", label: "Subordinate", width: "240px", render: (n) => <span className="text-xs font-semibold text-text">{n.username}</span> },
    { key: "role", label: "Role", width: "180px", render: (n) => <span className="inline-flex rounded-md border px-1.5 py-0.5 text-[10px] font-semibold capitalize">{n.role.replace("_", " ")}</span> },
    { key: "authority_level", label: "Level", width: "100px", render: (n) => <span className="font-mono text-xs">{n.authority_level ?? "—"}</span> },
  ], []);

  const teamColumns = useMemo<Array<EnterpriseColumn<HierarchyChainNode>>>(() => [
    { key: "user_id", label: "User ID", width: "110px", render: (n) => <span className="font-mono text-xs">{n.user_id}</span> },
    { key: "username", label: "Team Member", width: "240px", render: (n) => <span className="text-xs font-semibold text-text">{n.username}</span> },
    { key: "role", label: "Role", width: "180px", render: (n) => <span className="inline-flex rounded-md border px-1.5 py-0.5 text-[10px] font-semibold capitalize">{n.role.replace("_", " ")}</span> },
    { key: "org_unit_name", label: "Org Unit", width: "200px", render: (n) => <span className="text-xs text-text-muted">{n.org_unit_name || "—"}</span> },
  ], []);

  if (!isLoggedIn) return null;

  return (
    <AdminLayout title="Hierarchy" headerMode="compact">
      <PanelContent className="space-y-3">
        <div className="theme-card rounded-xl border p-2">
          <PanelTabs
            items={SECTION_OPTIONS}
            value={tab}
            onChange={(next) => router.replace(`/admin/staff?section=${next}`, { scroll: false })}
            className="border-0 bg-transparent p-0"
          />
        </div>

        {tab === "org-chart" && (
          <div className="theme-card rounded-2xl border p-5">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-sm font-bold text-text">Organization Chart</h2>
                <p className="mt-1 text-xs text-text-muted">Org units and hierarchy structure.</p>
              </div>
              <button onClick={loadOrgChart} disabled={loading} className="theme-btn-secondary rounded-lg border px-3 py-2 text-xs font-semibold text-text-muted disabled:opacity-50">
                {loading ? "Refreshing..." : "Refresh"}
              </button>
            </div>
            {loading && orgChart.length === 0 ? (
              <div className="space-y-2">{Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-12 animate-pulse rounded-xl bg-surface-2" />)}</div>
            ) : orgChart.length === 0 ? (
              <p className="text-xs text-text-muted">No org units found.</p>
            ) : (
              <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
                {orgChart.map((unit) => (
                  <div key={unit.id} className="rounded-xl border border-border bg-surface-2/60 p-3">
                    <div className="flex items-center justify-between">
                      <p className="text-xs font-bold text-text">{unit.name}</p>
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${unit.is_active ? "bg-success/10 text-success" : "bg-danger/10 text-danger"}`}>
                        {unit.is_active ? "Active" : "Inactive"}
                      </span>
                    </div>
                    <p className="mt-1 text-[11px] text-text-muted">ID: {unit.id} • Parent: {unit.parent_id ?? "—"}</p>
                    {unit.path && <p className="mt-1 font-mono text-[10px] text-text-faint">{unit.path}</p>}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {tab === "authority" && (
          <div className="theme-card rounded-2xl border p-5">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-sm font-bold text-text">Authority Level Lookup</h2>
                <p className="mt-1 text-xs text-text-muted">Resolve a user's authority level in the org hierarchy.</p>
              </div>
              <div className="flex items-center gap-2">
                <input value={authorityUserId} onChange={(e) => setAuthorityUserId(e.target.value)} className="theme-input rounded-xl border px-3 py-2 text-xs w-24" />
                <button onClick={loadAuthority} disabled={loading} className="theme-btn-primary rounded-xl px-4 py-2 text-xs font-bold disabled:opacity-50">Lookup</button>
              </div>
            </div>

            {authorityLevel != null && (
              <div className="rounded-xl border border-border bg-surface-2/60 p-4">
                <p className="text-xs text-text-muted">User #{authorityUserId}</p>
                <p className="mt-1 text-lg font-bold text-text">Level {authorityLevel}</p>
              </div>
            )}

            <div className="mt-4">
              <h3 className="mb-2 text-xs font-bold text-text">Management Chain</h3>
              <div className="mb-2 flex items-center gap-2">
                <input value={chainUserId} onChange={(e) => setChainUserId(e.target.value)} className="theme-input rounded-xl border px-3 py-2 text-xs w-24" />
                <button onClick={loadChain} disabled={loading} className="theme-btn-secondary rounded-lg border px-3 py-2 text-xs font-semibold text-text-muted disabled:opacity-50">Load Chain</button>
              </div>
              {chain.length === 0 ? (
                <p className="text-xs text-text-muted">No chain entries.</p>
              ) : (
                <div className="space-y-2">
                  {chain.map((node) => (
                    <div key={node.user_id} className="flex items-center gap-3 rounded-xl border border-border bg-surface-2/60 p-3">
                      <ChevronRight className="h-4 w-4 text-text-faint" />
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-semibold text-text">{node.username}</p>
                        <p className="text-[11px] text-text-muted capitalize">{node.role.replace("_", " ")} • Level {node.authority_level ?? "—"}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {tab === "team" && (
          <div className="space-y-4">
            <div className="theme-card rounded-2xl border p-5">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-sm font-bold text-text">Subordinates</h2>
                  <p className="mt-1 text-xs text-text-muted">Direct reports under a manager.</p>
                </div>
                <div className="flex items-center gap-2">
                  <input value={subordinatesUserId} onChange={(e) => setSubordinatesUserId(e.target.value)} className="theme-input rounded-xl border px-3 py-2 text-xs w-24" />
                  <button onClick={loadSubordinates} disabled={loading} className="theme-btn-secondary rounded-lg border px-3 py-2 text-xs font-semibold text-text-muted disabled:opacity-50">Load</button>
                </div>
              </div>
              <EnterpriseDataTable
                columns={subordinateColumns}
                rows={subordinates}
                rowKey={(n) => n.user_id}
                densityMode={density}
                initialRowsPerPage={25}
                emptyState={loading ? "Loading subordinates..." : "No subordinates found."}
              />
            </div>

            <div className="theme-card rounded-2xl border p-5">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-sm font-bold text-text">Team Members</h2>
                  <p className="mt-1 text-xs text-text-muted">Peers and cross-team members accessible to a user.</p>
                </div>
                <div className="flex items-center gap-2">
                  <input value={teamUserId} onChange={(e) => setTeamUserId(e.target.value)} className="theme-input rounded-xl border px-3 py-2 text-xs w-24" />
                  <button onClick={loadTeamMembers} disabled={loading} className="theme-btn-secondary rounded-lg border px-3 py-2 text-xs font-semibold text-text-muted disabled:opacity-50">Load</button>
                </div>
              </div>
              <EnterpriseDataTable
                columns={teamColumns}
                rows={teamMembers}
                rowKey={(n) => n.user_id}
                densityMode={density}
                initialRowsPerPage={25}
                emptyState={loading ? "Loading team members..." : "No team members found."}
              />
            </div>
          </div>
        )}

        {tab === "reassign" && (
          <div className="theme-card rounded-2xl border p-5">
            <h2 className="text-sm font-bold text-text">Reassign Manager</h2>
            <p className="mt-1 mb-4 text-xs text-text-muted">Move an employee to a new reporting manager. Circular reporting is blocked.</p>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold text-text-muted">Employee User ID</span>
                <input value={reassignUserId} onChange={(e) => setReassignUserId(e.target.value)} className="theme-input w-full rounded-xl border px-3 py-2.5 text-xs" />
              </label>
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold text-text-muted">New Manager User ID (optional, blank to clear)</span>
                <input value={reassignNewManagerId} onChange={(e) => setReassignNewManagerId(e.target.value)} placeholder="e.g. 5" className="theme-input w-full rounded-xl border px-3 py-2.5 text-xs" />
              </label>
              <div className="flex items-end">
                <button onClick={doReassign} disabled={reassignSaving} className="theme-btn-primary w-full rounded-xl px-4 py-2.5 text-xs font-bold disabled:opacity-50">
                  {reassignSaving ? "Saving..." : "Reassign"}
                </button>
              </div>
            </div>
          </div>
        )}

        {tab === "backfill" && (
          <div className="theme-card rounded-2xl border p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-sm font-bold text-text">Backfill Authority Levels</h2>
                <p className="mt-1 text-xs text-text-muted">Rebuild authority levels from org chart depth. CEO receives the highest level.</p>
              </div>
              <div className="flex items-center gap-3">
                {backfillCount != null && (
                  <span className="text-xs text-text-muted">Last run updated <span className="font-mono font-semibold text-text">{backfillCount}</span> records</span>
                )}
                <button onClick={doBackfill} disabled={backfillSaving} className="theme-btn-primary rounded-xl px-4 py-2.5 text-xs font-bold disabled:opacity-50">
                  {backfillSaving ? "Running..." : "Run Backfill"}
                </button>
              </div>
            </div>
          </div>
        )}
      </PanelContent>
    </AdminLayout>
  );
}

export default function HierarchyPage() {
  return (
    <Suspense>
      <HierarchyInner />
    </Suspense>
  );
}

function DENSITY_TEXT(mode: Density) {
  return dc(mode, "text-[11px]", "text-xs", "text-sm");
}
