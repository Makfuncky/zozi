"use client";

import { Button } from "@/components/ui/Button";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Plus,
  X,
  Check,
  AlertTriangle,
  Loader2,
  UserX,
  ShieldOff,
  BookOpen,
  TrendingDown,
  UserCheck,
  Lock,
  Unlock,
} from "@/lib/icons";
import type { Employee } from "../employee-types";

interface DisciplinaryCase {
  id: number;
  employee_id: number;
  employee_name?: string;
  stage: string;
  description: string;
  issued_at: string;
  status: string;
}

interface OffboardingCase {
  id: number;
  employee_id: number;
  employee_name?: string;
  reason: string;
  status: string;
  initiated_at: string;
  completed_at?: string | null;
}

import type { ToastType } from "@/lib/toastStore";
import { apiFetch } from "@/lib/api";

interface DisciplinaryOffboardingTabProps {
  employees: Employee[];
  addToast: (message: string, type?: ToastType, duration?: number) => void;
}

export default function DisciplinaryOffboardingTab({ employees, addToast }: DisciplinaryOffboardingTabProps) {
  const [disciplinary, setDisciplinary] = useState<DisciplinaryCase[]>([]);
  const [offboarding, setOffboarding] = useState<OffboardingCase[]>([]);
  const [loading, setLoading] = useState(false);
  const [showDisciplinaryModal, setShowDisciplinaryModal] = useState(false);
  const [showOffboardingModal, setShowOffboardingModal] = useState(false);

  const [discForm, setDiscForm] = useState({
    employee_id: "",
    stage: "verbal_warning",
    description: "",
  });
  const [offboardForm, setOffboardForm] = useState({
    employee_id: "",
    reason: "resignation",
    notes: "",
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [discRes, offRes] = await Promise.allSettled([
        apiFetch("/hr/disciplinary"),
        apiFetch("/hr/offboarding"),
      ]);
      if (discRes.status === "fulfilled") {
        const data = await discRes.value.json().catch(() => []);
        setDisciplinary(Array.isArray(data) ? data : []);
      }
      if (offRes.status === "fulfilled") {
        const data = await offRes.value.json().catch(() => []);
        setOffboarding(Array.isArray(data) ? data : []);
      }
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const handleIssueDisciplinary = async () => {
    if (!discForm.employee_id || !discForm.description) {
      addToast("Employee and description are required", "error");
      return;
    }
    try {
      const res = await apiFetch("/hr/disciplinary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...discForm, employee_id: parseInt(discForm.employee_id) }),
      });
      if (res.ok) {
        addToast("Disciplinary case issued", "success");
        setShowDisciplinaryModal(false);
        setDiscForm({ employee_id: "", stage: "verbal_warning", description: "" });
        void loadData();
      } else {
        addToast("Failed to issue disciplinary case", "error");
      }
    } catch {
      addToast("Network error", "error");
    }
  };

  const handleKillSwitch = async (employeeId: number) => {
    try {
      const res = await apiFetch(`/employees/${employeeId}/kill-switch`, { method: "POST" });
      if (res.ok) {
        addToast("Kill switch activated — all access revoked", "success");
      } else {
        addToast("Failed to activate kill switch", "error");
      }
    } catch {
      addToast("Network error", "error");
    }
  };

  const handleInitiateOffboarding = async () => {
    if (!offboardForm.employee_id) {
      addToast("Employee is required", "error");
      return;
    }
    try {
      const res = await apiFetch("/hr/offboarding", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ employee_id: parseInt(offboardForm.employee_id), reason: offboardForm.reason, notes: offboardForm.notes }),
      });
      if (res.ok) {
        addToast("Offboarding initiated", "success");
        setShowOffboardingModal(false);
        setOffboardForm({ employee_id: "", reason: "resignation", notes: "" });
        void loadData();
      } else {
        addToast("Failed to initiate offboarding", "error");
      }
    } catch {
      addToast("Network error", "error");
    }
  };

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text">Disciplinary & Offboarding</h3>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-border bg-surface-1 p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-text flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-warning" />
              Disciplinary Ladder
            </h4>
            <Button variant="warning" className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-[10px] font-semibold shadow-sm transition-colors" onClick={() => setShowDisciplinaryModal(true)}
            >
              <Plus className="h-3 w-3" />
              Issue Case
            </Button>
          </div>
          {loading ? (
            <div className="flex items-center justify-center py-6">
              <Loader2 className="h-5 w-5 animate-spin text-text-faint" />
            </div>
          ) : disciplinary.length === 0 ? (
            <p className="text-[11px] text-text-faint text-center py-4">No disciplinary cases</p>
          ) : (
            <div className="space-y-2 max-h-[280px] overflow-y-auto">
              {disciplinary.map((c) => (
                <div key={c.id} className="rounded-lg bg-surface-2 border border-border p-3">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-semibold text-text">{c.employee_name ?? `#${c.employee_id}`}</p>
                    <span className="text-[10px] text-text-faint capitalize">{c.stage.replace(/_/g, " ")}</span>
                  </div>
                  <p className="text-[10px] text-text-muted mt-1 line-clamp-2">{c.description}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="rounded-xl border border-border bg-surface-1 p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-text flex items-center gap-2">
              <UserX className="h-4 w-4 text-danger" />
              Offboarding Queue
            </h4>
            <Button variant="danger" className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-[10px] font-semibold shadow-sm transition-colors" onClick={() => setShowOffboardingModal(true)}
            >
              <Plus className="h-3 w-3" />
              Initiate
            </Button>
          </div>
          {offboarding.length === 0 ? (
            <p className="text-[11px] text-text-faint text-center py-4">No offboarding cases</p>
          ) : (
            <div className="space-y-2 max-h-[280px] overflow-y-auto">
              {offboarding.map((case_) => (
                <div key={case_.id} className="rounded-lg bg-surface-2 border border-border p-3 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-text">{case_.employee_name ?? `#${case_.employee_id}`}</p>
                    <p className="text-[10px] text-text-muted mt-0.5 capitalize">{case_.reason}</p>
                  </div>
                  <span className={`rounded-full text-[10px] font-semibold px-2 py-0.5 border ${case_.status === "completed" ? "bg-success/10 text-success border-success/20" : "bg-warning/10 text-warning border-warning/20"}`}>
                    {case_.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="rounded-xl border border-border bg-surface-1 p-4 space-y-2">
        <h4 className="text-sm font-semibold text-text flex items-center gap-2">
          <ShieldOff className="h-4 w-4 text-danger" />
          Kill Switch
        </h4>
        <p className="text-[11px] text-text-muted">Instant revocation of all JWT tokens and physical QR access across all buildings. Use only for terminations or suspected compromise.</p>
        <div className="mt-2">
          <select
            onChange={(e) => {
              if (e.target.value) handleKillSwitch(parseInt(e.target.value));
            }}
            className="rounded-lg border border-border bg-surface-2 px-3 py-2 text-xs text-text outline-none"
          >
            <option value="">Select employee to revoke access</option>
            {employees.map((emp) => (
              <option key={emp.id} value={emp.id}>
                {emp.full_name ?? emp.name ?? emp.employee_code}
              </option>
            ))}
          </select>
        </div>
      </div>

      {showDisciplinaryModal && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4" onClick={(e: any) => e.target === e.currentTarget && setShowDisciplinaryModal(false)}>
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }} className="w-full max-w-lg rounded-2xl border border-border bg-surface-1 shadow-2xl">
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <h2 className="font-bold text-text flex items-center gap-2"><BookOpen className="h-4 w-4 text-warning" /> Issue Disciplinary Case</h2>
              <button onClick={() => setShowDisciplinaryModal(false)} className="text-text-muted hover:text-text"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-5 space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">Employee *</label>
                <select value={discForm.employee_id} onChange={(e) => setDiscForm((f) => ({ ...f, employee_id: e.target.value }))} className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none">
                  <option value="">Select employee</option>
                  {employees.map((emp) => (
                    <option key={emp.id} value={emp.id}>
                      {emp.full_name ?? emp.name ?? emp.employee_code}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">Stage</label>
                <select value={discForm.stage} onChange={(e) => setDiscForm((f) => ({ ...f, stage: e.target.value }))} className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none">
                  <option value="verbal_warning">Verbal Warning</option>
                  <option value="written_warning">Written Warning</option>
                  <option value="final_warning">Final Warning</option>
                  <option value="suspension">Suspension</option>
                  <option value="termination">Termination</option>
                </select>
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">Description *</label>
                <textarea value={discForm.description} onChange={(e) => setDiscForm((f) => ({ ...f, description: e.target.value }))} placeholder="Describe the incident..." rows={3} className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text placeholder:text-text-faint outline-none focus:border-primary/50" />
              </div>
            </div>
            <div className="flex items-center justify-end gap-2 border-t border-border px-5 py-4">
              <button onClick={() => setShowDisciplinaryModal(false)} className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text-muted hover:text-text transition-colors">Cancel</button>
              <Button variant="warning" onClick={handleIssueDisciplinary}><AlertTriangle className="h-3.5 w-3.5" /> Issue</Button>
            </div>
          </motion.div>
        </motion.div>
      )}

      {showOffboardingModal && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4" onClick={(e: any) => e.target === e.currentTarget && setShowOffboardingModal(false)}>
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }} className="w-full max-w-lg rounded-2xl border border-border bg-surface-1 shadow-2xl">
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <h2 className="font-bold text-text flex items-center gap-2"><UserX className="h-4 w-4 text-danger" /> Initiate Offboarding</h2>
              <button onClick={() => setShowOffboardingModal(false)} className="text-text-muted hover:text-text"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-5 space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">Employee *</label>
                <select value={offboardForm.employee_id} onChange={(e) => setOffboardForm((f) => ({ ...f, employee_id: e.target.value }))} className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none">
                  <option value="">Select employee</option>
                  {employees.map((emp) => (
                    <option key={emp.id} value={emp.id}>
                      {emp.full_name ?? emp.name ?? emp.employee_code}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">Reason</label>
                <select value={offboardForm.reason} onChange={(e) => setOffboardForm((f) => ({ ...f, reason: e.target.value }))} className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none">
                  <option value="resignation">Resignation</option>
                  <option value="termination">Termination</option>
                  <option value="retirement">Retirement</option>
                  <option value="contract_end">Contract End</option>
                </select>
              </div>
            </div>
            <div className="flex items-center justify-end gap-2 border-t border-border px-5 py-4">
              <button onClick={() => setShowOffboardingModal(false)} className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text-muted hover:text-text transition-colors">Cancel</button>
              <Button variant="danger" onClick={handleInitiateOffboarding}><UserX className="h-3.5 w-3.5" /> Initiate</Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </section>
  );
}


