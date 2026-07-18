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
  Target,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  BarChart3,
  Star,
  Award,
} from "@/lib/icons";
import type { Employee } from "../employee-types";

interface Okr {
  id: number;
  employee_id: number;
  title: string;
  description: string;
  progress: number;
  due_date: string;
  status: string;
}

interface FlightRisk {
  id: number;
  employee_id: number;
  score: number;
  risk_level: string;
  factors: string[];
  last_evaluated_at: string;
}

import type { ToastType } from "@/lib/toastStore";
import { apiFetch } from "@/lib/api";

interface PerformanceTabProps {
  employees: Employee[];
  addToast: (message: string, type?: ToastType, duration?: number) => void;
}

export default function PerformanceTab({ employees, addToast }: PerformanceTabProps) {
  const [okrs, setOkrs] = useState<Okr[]>([]);
  const [flightRisks, setFlightRisks] = useState<FlightRisk[]>([]);
  const [loading, setLoading] = useState(false);
  const [showOkrModal, setShowOkrModal] = useState(false);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | null>(null);

  const [okrForm, setOkrForm] = useState({
    employee_id: "",
    title: "",
    description: "",
    progress: 0,
    due_date: "",
    status: "in_progress",
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [okrRes, riskRes] = await Promise.allSettled([
        apiFetch("/okr/employee/0"),  // Falls back if employee ID needed
        apiFetch("/risk/0/risk-score"),
      ]);
      if (okrRes.status === "fulfilled") {
        const data = await okrRes.value.json().catch(() => []);
        setOkrs(Array.isArray(data) ? data : []);
      }
      if (riskRes.status === "fulfilled") {
        const data = await riskRes.value.json().catch(() => []);
        setFlightRisks(Array.isArray(data) ? data : []);
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

  const handleCreateOkr = async () => {
    if (!okrForm.employee_id || !okrForm.title || !okrForm.due_date) {
      addToast("Employee, title, and due date are required", "error");
      return;
    }
    try {
      const res = await apiFetch("/okr/objectives", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          employee_id: parseInt(okrForm.employee_id),
          title: okrForm.title,
          description: okrForm.description,
          key_results: [],
          period_start: okrForm.due_date,
          period_end: okrForm.due_date,
        }),
      });
      if (res.ok) {
        addToast("OKR created", "success");
        setShowOkrModal(false);
        setOkrForm({ employee_id: "", title: "", description: "", progress: 0, due_date: "", status: "in_progress" });
        void loadData();
      } else {
        addToast("Failed to create OKR", "error");
      }
    } catch {
      addToast("Network error", "error");
    }
  };

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text">Performance & Flight Risk</h3>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-border bg-surface-1 p-5">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-semibold text-text flex items-center gap-2">
              <Target className="h-4 w-4 text-primary" />
              OKRs & KPIs
            </h4>
            <Button variant="primary" className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-[10px] font-semibold shadow-sm transition-colors" onClick={() => setShowOkrModal(true)}
            >
              <Plus className="h-3 w-3" />
              New OKR
            </Button>
          </div>
          {loading ? (
            <div className="flex items-center justify-center py-6">
              <Loader2 className="h-5 w-5 animate-spin text-text-faint" />
            </div>
          ) : okrs.length === 0 ? (
            <p className="text-[11px] text-text-faint text-center py-4">No OKRs recorded</p>
          ) : (
            <div className="space-y-2 max-h-[320px] overflow-y-auto">
              {okrs.map((okr) => (
                <div key={okr.id} className="rounded-lg bg-surface-2 border border-border p-3">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-semibold text-text truncate max-w-[220px]">{okr.title}</p>
                    <span className="text-[10px] text-text-faint">{okr.progress}%</span>
                  </div>
                  <div className="mt-2 h-1.5 rounded-full bg-surface-3 overflow-hidden">
                    <div className="h-full rounded-full bg-primary" style={{ width: `${okr.progress}%` }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="rounded-xl border border-border bg-surface-1 p-5">
          <h4 className="text-sm font-semibold text-text flex items-center gap-2 mb-3">
            <AlertCircle className="h-4 w-4 text-warning" />
            Flight Risk Monitor
          </h4>
          {flightRisks.length === 0 ? (
            <p className="text-[11px] text-text-faint text-center py-4">No flight risk assessments</p>
          ) : (
            <div className="space-y-2 max-h-[320px] overflow-y-auto">
              {flightRisks.map((risk) => {
                const emp = employees.find((e) => e.id === risk.employee_id);
                const levelColor = risk.risk_level === "critical" ? "text-danger" : risk.risk_level === "high" ? "text-warning" : "text-text-muted";
                return (
                  <div key={risk.id} className="rounded-lg bg-surface-2 border border-border p-3 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-semibold text-text">{emp?.full_name ?? emp?.name ?? `Employee #${risk.employee_id}`}</p>
                      <p className="text-[10px] text-text-faint mt-0.5">Score: {risk.score}/100</p>
                    </div>
                    <span className={`rounded-full text-[10px] font-semibold px-2 py-0.5 border ${risk.risk_level === "critical" ? "bg-danger/10 text-danger border-danger/20" : risk.risk_level === "high" ? "bg-warning/10 text-warning border-warning/20" : "bg-surface-3 text-text-muted border-border"}`}>
                      {risk.risk_level}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {showOkrModal && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4" onClick={(e: any) => e.target === e.currentTarget && setShowOkrModal(false)}>
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }} className="w-full max-w-lg rounded-2xl border border-border bg-surface-1 shadow-2xl">
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <h2 className="font-bold text-text flex items-center gap-2"><Target className="h-4 w-4 text-primary" /> New OKR</h2>
              <button onClick={() => setShowOkrModal(false)} className="text-text-muted hover:text-text"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-5 space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">Employee *</label>
                <select value={okrForm.employee_id} onChange={(e) => setOkrForm((f) => ({ ...f, employee_id: e.target.value }))} className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none">
                  <option value="">Select employee</option>
                  {employees.map((emp) => (
                    <option key={emp.id} value={emp.id}>
                      {emp.full_name ?? emp.name ?? emp.employee_code}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">Title *</label>
                <input type="text" value={okrForm.title} onChange={(e) => setOkrForm((f) => ({ ...f, title: e.target.value }))} placeholder="Increase ARR by 20%" className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text placeholder:text-text-faint outline-none focus:border-primary/50" />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">Due Date *</label>
                <input type="date" value={okrForm.due_date} onChange={(e) => setOkrForm((f) => ({ ...f, due_date: e.target.value }))} className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none" />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">Progress (%)</label>
                <input type="number" min="0" max="100" value={okrForm.progress} onChange={(e) => setOkrForm((f) => ({ ...f, progress: parseInt(e.target.value) || 0 }))} className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none" />
              </div>
            </div>
            <div className="flex items-center justify-end gap-2 border-t border-border px-5 py-4">
              <button onClick={() => setShowOkrModal(false)} className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text-muted hover:text-text transition-colors">Cancel</button>
              <Button variant="primary" onClick={handleCreateOkr}><Check className="h-3.5 w-3.5" /> Save OKR</Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </section>
  );
}


