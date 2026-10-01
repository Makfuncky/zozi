"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  DollarSign, CheckCircle2, AlertCircle, Clock, Loader2,
  Shield, Users, FileText, Banknote, TrendingUp,
  ArrowRight, Check, X, RefreshCw, Wallet,
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { StatusBadge, Badge } from "@/components/ui/shared/Badge";
import { PanelCard, PanelGrid, PanelSection, PanelStatCard, PanelActionBar, PanelFilterBar, PanelMetric, PanelDivider } from "@/components/PanelPage";
import { useToastStore } from "@/lib/toastStore";
import { cn } from "@/lib/utils";

interface PayrollWorkflowProps {
  countryCode?: string;
  className?: string;
}

interface PayrollBatch {
  id: number;
  batch_uuid: string;
  total_amount: string;
  currency: string;
  employee_count: number;
  status: string;
  notes: string | null;
  created_at: string;
}

const PIPELINE_STEPS = [
  { key: "draft", label: "Draft", icon: FileText, color: "text-text-muted" },
  { key: "pending_approval", label: "Pending Approval", icon: Clock, color: "text-warning" },
  { key: "approved", label: "Approved", icon: CheckCircle2, color: "text-primary" },
  { key: "processing", label: "Processing", icon: Loader2, color: "text-info" },
  { key: "completed", label: "Completed", icon: DollarSign, color: "text-success" },
];

export default function PayrollWorkflow({ countryCode, className }: PayrollWorkflowProps) {
  const addToast = useToastStore((s) => s.addToast);
  const [batches, setBatches] = useState<PayrollBatch[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const loadBatches = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiFetch(`/payroll/batches?country_code=${countryCode || "*"}&limit=10`);
      const json = await response.json();
      const list = Array.isArray(json) ? json : json?.batches || json?.items || [];
      setBatches(list);
    } catch (e: any) {
      setError(e?.message || "Failed to load");
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (batchId: number, action: "approve" | "reject" | "disburse") => {
    setActionLoading(`${action}-${batchId}`);
    try {
      const params = new URLSearchParams({ batch_id: String(batchId) });
      await apiFetch(`/payroll/${action}?${params.toString()}`, { method: "POST" });
      addToast(`Batch ${action}d successfully`, "success");
      await loadBatches();
    } catch (e: any) {
      addToast(e?.message || `Failed to ${action}`, "error");
    } finally {
      setActionLoading(null);
    }
  };

  const getStepIndex = (status: string) => {
    const idx = PIPELINE_STEPS.findIndex((s) => s.key === status);
    return idx >= 0 ? idx : 0;
  };

  const getAmount = (amount: string) => {
    const num = parseFloat(amount);
    return new Intl.NumberFormat("en-US", { style: "currency", currency: "OMR", minimumFractionDigits: 2 }).format(num);
  };

  const stats = {
    total: batches.length,
    pending: batches.filter((b) => b.status === "pending_approval").length,
    completed: batches.filter((b) => b.status === "completed").length,
    totalAmount: batches.reduce((s, b) => s + parseFloat(b.total_amount || "0"), 0),
  };

  return (
    <PanelSection className={className} title="Payroll Pipeline" description="Maker-checker approval workflow"
      action={
        <PanelActionBar>
          <Button variant="ghost" size="sm" leftIcon={<RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />}
            onClick={loadBatches} disabled={loading}>Refresh</Button>
          <Button variant="primary" size="sm" leftIcon={<DollarSign className="w-4 h-4" />}>New Batch</Button>
        </PanelActionBar>
      }>

      {batches.length > 0 && (
        <PanelGrid cols={4}>
          <PanelMetric label="Total Batches" value={stats.total} icon={Wallet} />
          <PanelMetric label="Pending Approval" value={stats.pending} icon={Clock} trend={stats.pending > 0 ? `${stats.pending} need review` : undefined} />
          <PanelMetric label="Completed" value={stats.completed} icon={CheckCircle2} />
          <PanelMetric label="Total Amount" value={getAmount(String(stats.totalAmount))} icon={Banknote} />
        </PanelGrid>
      )}

      <PanelDivider />

      {error && (
        <div className="flex items-center gap-2 text-sm text-danger bg-danger/5 rounded-xl px-4 py-3 border border-danger/20">
          <AlertCircle className="w-4 h-4 flex-shrink-0" /> {error}
        </div>
      )}

      {batches.length === 0 && !loading ? (
        <PanelCard className="text-center py-12">
          <Banknote className="w-12 h-12 text-text-muted/30 mx-auto mb-3" />
          <p className="text-text-muted font-medium">No payroll batches found</p>
          <p className="text-xs text-text-muted/60 mt-1">Create a new batch to get started</p>
        </PanelCard>
      ) : (
        <div className="space-y-4">
          {batches.map((batch, idx) => {
            const stepIdx = getStepIndex(batch.status);
            return (
              <motion.div key={batch.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}>
                <PanelCard>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-500/20 flex items-center justify-center">
                        <Banknote className="w-5 h-5 text-emerald-500" />
                      </div>
                      <div>
                        <p className="font-semibold text-text text-sm">Batch #{batch.batch_uuid.slice(0, 8)}</p>
                        <p className="text-xs text-text-muted">{new Date(batch.created_at).toLocaleDateString()} · {batch.employee_count} employees</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-text">{getAmount(batch.total_amount)}</p>
                      <StatusBadge status={
                        batch.status === "completed" ? "success"
                        : batch.status === "pending_approval" ? "warning"
                        : batch.status === "approved" ? "info"
                        : "default"
                      }>{batch.status}</StatusBadge>
                    </div>
                  </div>

                  {/* Pipeline visualization */}
                  <div className="flex items-center gap-1 mb-4">
                    {PIPELINE_STEPS.map((step, i) => {
                      const StepIcon = step.icon;
                      const active = i <= stepIdx;
                      const current = i === stepIdx;
                      return (
                        <div key={step.key} className="flex items-center flex-1">
                          <div className={cn(
                            "flex items-center gap-1.5 px-2 py-1 rounded-lg text-xs font-medium transition-all",
                            current ? "bg-primary/15 text-primary shadow-sm" : active ? "text-text" : "text-text-muted/50",
                          )}>
                            <StepIcon className={cn("w-3 h-3", current && "animate-pulse")} />
                            <span className="hidden sm:inline">{step.label}</span>
                          </div>
                          {i < PIPELINE_STEPS.length - 1 && (
                            <div className={cn("flex-1 h-px mx-1", i < stepIdx ? "bg-primary/40" : "bg-border")} />
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {/* Action buttons */}
                  {batch.status === "pending_approval" && (
                    <PanelActionBar className="pt-3 border-t border-border">
                      <Button size="sm" variant="primary" leftIcon={<Check className="w-4 h-4" />}
                        onClick={() => handleAction(batch.id, "approve")}
                        isLoading={actionLoading === `approve-${batch.id}`}>Approve</Button>
                      <Button size="sm" variant="danger-outline" leftIcon={<X className="w-4 h-4" />}
                        onClick={() => handleAction(batch.id, "reject")}
                        isLoading={actionLoading === `reject-${batch.id}`}>Reject</Button>
                      <Button size="sm" variant="accent" leftIcon={<DollarSign className="w-4 h-4" />}
                        onClick={() => handleAction(batch.id, "disburse")}
                        isLoading={actionLoading === `disburse-${batch.id}`}>Disburse Now</Button>
                    </PanelActionBar>
                  )}
                  {batch.status === "approved" && (
                    <PanelActionBar className="pt-3 border-t border-border">
                      <Button size="sm" variant="accent" leftIcon={<DollarSign className="w-4 h-4" />}
                        onClick={() => handleAction(batch.id, "disburse")}
                        isLoading={actionLoading === `disburse-${batch.id}`}>Execute Disbursement</Button>
                    </PanelActionBar>
                  )}
                </PanelCard>
              </motion.div>
            );
          })}
        </div>
      )}
    </PanelSection>
  );
}
