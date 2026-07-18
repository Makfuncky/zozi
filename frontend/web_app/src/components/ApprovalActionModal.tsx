"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  ArrowUpCircle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  ShieldX,
  Users,
  XCircle,
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";
import { PanelContent, PanelTabs } from "@/components/PanelPage";
import { EnterpriseDataTable, type EnterpriseColumn } from "@shared/components/EnterpriseDataTable";
import type { ApprovalChainItem, ApprovalEligibility } from "@/lib/approvalMatrixApi";
import { getApprovalMatrixRules, getUserApprovalChain } from "@/lib/approvalMatrixApi";

export type ResourceAction = "approve" | "reject" | "verify" | "suspend" | "activate";

const RESOURCE_TYPES = ["product", "supplier", "payout"] as const;

export interface ApprovalActionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (options?: { note?: string; status?: string }) => Promise<void>;
  resourceType: "product" | "supplier" | "payout";
  resourceLabel?: string;
  action: ResourceAction;
  disabled?: boolean;
  /** Optional extra payload overrides */
  statusOptions?: readonly string[];
}

interface ApprovalChainRow {
  user_id: number;
  username: string;
  role: string;
  authority_level: number;
  distance: number;
}

const ACTION_META: Record<ResourceAction, { label: string; tone: string; icon: typeof ShieldCheck }> = {
  approve: { label: "Approve", tone: "success", icon: CheckCircle2 },
  reject: { label: "Reject", tone: "danger", icon: XCircle },
  verify: { label: "Verify Payout", tone: "success", icon: ShieldCheck },
  suspend: { label: "Suspend", tone: "warning", icon: XCircle },
  activate: { label: "Activate", tone: "success", icon: CheckCircle2 },
};

export default function ApprovalActionModal({ isOpen, onClose, onConfirm, resourceType, resourceLabel, action, disabled = false, statusOptions = ["processing", "completed", "rejected"] }: ApprovalActionModalProps) {
  const [tab, setTab] = useState<"preview" | "chain" | "rules">("preview");
  const [loadingEligibility, setLoadingEligibility] = useState(false);
  const [eligibility, setEligibility] = useState<ApprovalEligibility | null>(null);
  const [chain, setChain] = useState<ApprovalChainItem[]>([]);
  const [rules, setRules] = useState<Record<string, any> | null>(null);
  const [note, setNote] = useState("");
  const [status, setStatus] = useState<string>("processing");
  const [submitting, setSubmitting] = useState(false);
  const [authLevel, setAuthLevel] = useState<number | null>(null);
  const addToast = useToastStore((state) => state.addToast);

  const meta = ACTION_META[action];

  useEffect(() => {
    if (!isOpen) return;
    setTab("preview");
    setNote("");
    setStatus("processing");
    setEligibility(null);
    setChain([]);
    setRules(null);
    setAuthLevel(null);
  }, [isOpen, resourceType, action]);

  const toneClass = useMemo(() => {
    if (meta.tone === "success") return "text-success";
    if (meta.tone === "danger") return "text-danger";
    return "text-text";
  }, [meta.tone]);

  const loadPreview = useCallback(async () => {
    setLoadingEligibility(true);
    try {
      const [meRes, rulesRes, chainRes] = await Promise.all([
        apiFetch("/auth/me"),
        getApprovalMatrixRules(),
        apiFetch(`/admin/hierarchy/authority-level?user_id=me`).then((r) => (r.ok ? r.json() : {})).catch(() => ({})),
      ]);

      const me = await meRes.json().catch(() => null);
      const userId = me?.id;
      if (userId) {
        setAuthLevel(me.authority_level ?? null);
        const chainData = await getUserApprovalChain(userId, resourceType);
        setChain(chainData.chain ?? []);
      }

      setRules(rulesRes.rules);
      const rule = rulesRes.rules[resourceType];
      if (rule && userId) {
        const qs = new URLSearchParams({ user_id: String(userId), resource_type: resourceType });
        const checkRes = await apiFetch(`/admin/hierarchy/approval-matrix/check?${qs.toString()}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ resource_type: resourceType }),
        });
        if (checkRes.ok) {
          const data = await checkRes.json();
          setEligibility(data);
        }
      }
    } catch {
      // best-effort preview; allow action to proceed if data unavailable
    } finally {
      setLoadingEligibility(false);
    }
  }, [resourceType]);

  useEffect(() => {
    if (!isOpen) return;
    if (tab === "preview") loadPreview();
  }, [isOpen, tab, loadPreview]);

  const handleConfirm = async () => {
    setSubmitting(true);
    try {
      const payload: Record<string, unknown> = { note: note.trim() || undefined };
      if (resourceType === "payout") payload.status = status;
      await onConfirm(payload);
      onClose();
    } catch (err) {
      addToast(err instanceof Error ? err.message : `Failed to ${action}`, "error");
    } finally {
      setSubmitting(false);
    }
  };

  const canProceed = eligibility?.can_approve ?? true;
  const rule = rules?.[resourceType];

  const chainColumns = useMemo<Array<EnterpriseColumn<ApprovalChainRow>>>(
    () => [
      { key: "distance", label: "Step", width: "80px", render: (r) => <span className="font-mono text-xs">{r.distance}</span> },
      { key: "username", label: "Approver", width: "220px", render: (r) => <span className="text-xs font-semibold text-text">{r.username}</span> },
      { key: "role", label: "Role", width: "160px", render: (r) => <span className="inline-flex rounded-md border px-1.5 py-0.5 text-[10px] font-semibold capitalize">{r.role.replace("_", " ")}</span> },
      { key: "authority_level", label: "Level", width: "100px", align: "right", render: (r) => <span className="font-mono text-xs">{r.authority_level}</span> },
    ],
    [],
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4" onClick={onClose}>
      <div className="theme-card max-h-[90vh] w-full max-w-2xl overflow-auto rounded-2xl border" onClick={(e) => e.stopPropagation()}>
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-surface-1 px-5 py-3">
          <div className="flex items-center gap-2">
            <meta.icon className={`h-4 w-4 ${toneClass}`} />
            <h2 className="text-sm font-bold text-text">
              {meta.label} {resourceLabel ? resourceLabel : resourceType}
            </h2>
            {eligibility?.can_approve === false && (
              <span className="ml-2 inline-flex items-center gap-1 rounded-full border border-danger/30 bg-danger/10 px-2 py-0.5 text-[10px] font-semibold text-danger">
                <ShieldX className="h-3 w-3" />
                Requires higher authority
              </span>
            )}
          </div>
          <button type="button" onClick={onClose} className="theme-btn-secondary rounded-lg border px-2 py-1 text-[11px] text-text-muted">
            Close
          </button>
        </div>

        <PanelContent className="space-y-3">
          <div className="theme-card rounded-xl border p-2">
            <PanelTabs
              items={[
                { key: "preview", label: "Preview", icon: ShieldCheck },
                { key: "chain", label: "Approval Chain", icon: Users },
                { key: "rules", label: "Rule", icon: ArrowUpCircle },
              ]}
              value={tab}
              onChange={(next) => setTab(next as any)}
              className="border-0 bg-transparent p-0"
            />
          </div>

          {tab === "preview" && (
            <div className="space-y-3">
              {eligibility?.can_approve === false && (
                <div className="rounded-xl border border-danger/30 bg-danger/5 p-4">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="mt-0.5 h-4 w-4 text-danger" />
                    <div>
                      <p className="text-xs font-bold text-danger">Action blocked by approval matrix</p>
                      <p className="mt-1 text-[11px] text-text-muted">
                        {eligibility.reason || "Your authority level is below the required threshold for this action."}
                      </p>
                      {eligibility.authority_level != null && eligibility.requiredLevel != null && (
                        <p className="mt-1 font-mono text-[11px] text-text">
                          Your level: {eligibility.authority_level} · Required: {eligibility.requiredLevel}
                        </p>
                      )}
                      {eligibility.approvers && eligibility.approvers.length > 0 && (
                        <div className="mt-2">
                          <p className="text-[11px] font-semibold text-text">Eligible approvers:</p>
                          <div className="mt-1 flex flex-wrap gap-1">
                            {eligibility.approvers.slice(0, 6).map((a) => (
                              <span key={a.user_id} className="rounded-full border border-border bg-surface-2 px-2 py-0.5 text-[10px] font-semibold text-text-muted">
                                {a.username} (L{a.authority_level})
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              <div className="grid gap-2 sm:grid-cols-2">
                <label className="block">
                  <span className="mb-1.5 block text-xs font-semibold text-text-muted">Note (optional)</span>
                  <textarea
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    className="theme-input w-full rounded-xl border px-3 py-2.5 text-xs"
                    rows={2}
                  />
                </label>
                {resourceType === "payout" && (
                  <label className="block">
                    <span className="mb-1.5 block text-xs font-semibold text-text-muted">Status</span>
                    <select value={status} onChange={(e) => setStatus(e.target.value)} className="theme-input w-full rounded-xl border px-3 py-2.5 text-xs">
                      {statusOptions.map((s) => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </label>
                )}
              </div>

              <div className="flex items-center justify-end gap-2">
                <button type="button" onClick={onClose} className="theme-btn-secondary rounded-xl border px-4 py-2.5 text-xs font-semibold text-text-muted">
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleConfirm}
                  disabled={submitting || disabled || eligibility?.can_approve === false}
                  className={`theme-btn-primary rounded-xl px-4 py-2.5 text-xs font-bold disabled:opacity-50 ${!canProceed ? "opacity-70" : ""}`}
                >
                  {submitting ? "Processing..." : canProceed ? `${meta.label}` : `Cannot ${meta.label.toLowerCase()}`}
                </button>
              </div>
            </div>
          )}

          {tab === "chain" && (
            <div className="space-y-2">
              {chain.length === 0 ? (
                <p className="text-xs text-text-muted">No approval chain data available. Verify with a user with Employee records.</p>
              ) : (
                <>
                  <p className="text-xs text-text-muted">{chain.length} step(s) in chain</p>
                  <div className="space-y-2">
                    {chain.map((item, idx) => (
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

          {tab === "rules" && (
            <div className="space-y-2">
              {!rule ? (
                <p className="text-xs text-text-muted">No rule loaded for resource type "{resourceType}".</p>
              ) : (
                <div className="rounded-xl border border-border bg-surface-2/60 p-4 space-y-1.5 text-xs text-text-muted">
                  <p>Minimum authority level: <span className="font-mono font-semibold text-text">{rule.min_authority_level}</span></p>
                  {rule.department && <p>Department: <span className="font-semibold text-text">{rule.department}</span></p>}
                  <p>Org unit required: <span className="font-semibold text-text">{rule.org_unit_required ? "Yes" : "No"}</span></p>
                  <p className="pt-1 text-text-faint">{rule.description}</p>
                </div>
              )}
              {authLevel != null && (
                <p className="text-[11px] text-text-muted">Your authority level: <span className="font-mono font-semibold text-text">{authLevel}</span></p>
              )}
            </div>
          )}
        </PanelContent>
      </div>
    </div>
  );
}
