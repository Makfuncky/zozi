"use client";

import { Button } from "@/components/ui/Button";

import { useCallback, useState } from "react";
import { motion } from "framer-motion";
import {
  Plus,
  X,
  Check,
  Loader2,
  AlertTriangle,
  Shield,
  Heart,
  Users,
  Car,
} from "@/lib/icons";
import type { Employee } from "../employee-types";

interface Dependent {
  id: number;
  employee_id: number;
  full_name: string;
  relationship: string;
  date_of_birth: string | null;
  gender: string | null;
}

interface LicenseRecord {
  id: number;
  employee_id: number;
  employee_name?: string;
  license_type: string;
  license_number: string;
  issued_at: string;
  expires_at: string;
  status: string;
  suspension_reason?: string | null;
}

import type { ToastType } from "@/lib/toastStore";
import { apiFetch } from "@/lib/api";

interface InsuranceBenefitsTabProps {
  employees: Employee[];
  addToast: (message: string, type?: ToastType, duration?: number) => void;
}

export default function InsuranceBenefitsTab({ employees, addToast }: InsuranceBenefitsTabProps) {
  const [dependents, setDependents] = useState<Dependent[]>([]);
  const [licenses, setLicenses] = useState<LicenseRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [showDependentModal, setShowDependentModal] = useState(false);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | null>(null);

  const [depForm, setDepForm] = useState({
    employee_id: "",
    full_name: "",
    relationship: "spouse",
    date_of_birth: "",
    gender: "female",
  });

  const loadDependents = useCallback(async (employeeId: number) => {
    setLoading(true);
    try {
      const res = await apiFetch(`/employees/${employeeId}/dependents`);
      if (res.ok) {
        const data = await res.json().catch(() => []);
        setDependents(Array.isArray(data) ? data : data?.dependents ?? []);
      }
    } catch {
      addToast("Failed to load dependents", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  const handleAddDependent = async () => {
    if (!depForm.employee_id || !depForm.full_name) {
      addToast("Employee and name are required", "error");
      return;
    }
    try {
      const res = await apiFetch(`/employees/${depForm.employee_id}/dependents`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(depForm),
      });
      if (res.ok) {
        addToast("Dependent added", "success");
        setShowDependentModal(false);
        setDepForm({ employee_id: "", full_name: "", relationship: "spouse", date_of_birth: "", gender: "female" });
        if (depForm.employee_id) loadDependents(parseInt(depForm.employee_id));
      } else {
        addToast("Failed to add dependent", "error");
      }
    } catch {
      addToast("Network error", "error");
    }
  };

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text">Insurance & Benefits</h3>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-border bg-surface-1 p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-text flex items-center gap-2">
              <Users className="h-4 w-4 text-primary" />
              Dependents
            </h4>
            <Button variant="primary" className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-[10px] font-semibold shadow-sm transition-colors" onClick={() => {
                if (!selectedEmployeeId) {
                  addToast("Select an employee first", "error");
                  return;
                }
                setDepForm((f) => ({ ...f, employee_id: String(selectedEmployeeId) }));
                setShowDependentModal(true);
              }}
            >
              <Plus className="h-3 w-3" />
              Add
            </Button>
          </div>
          <div className="flex items-center gap-2">
            <select
              onChange={(e) => {
                const id = parseInt(e.target.value);
                if (id) {
                  setSelectedEmployeeId(id);
                  loadDependents(id);
                }
              }}
              className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-xs text-text outline-none"
            >
              <option value="">Select employee</option>
              {employees.map((emp) => (
                <option key={emp.id} value={emp.id}>
                  {emp.full_name ?? emp.name ?? emp.employee_code}
                </option>
              ))}
            </select>
          </div>
          {loading ? (
            <div className="flex items-center justify-center py-6">
              <Loader2 className="h-5 w-5 animate-spin text-text-faint" />
            </div>
          ) : dependents.length === 0 ? (
            <p className="text-[11px] text-text-faint text-center py-4">No dependents</p>
          ) : (
            <div className="space-y-2 max-h-[260px] overflow-y-auto">
              {dependents.map((d) => (
                <div key={d.id} className="rounded-lg bg-surface-2 border border-border p-3 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-text">{d.full_name}</p>
                    <p className="text-[10px] text-text-faint mt-0.5 capitalize">{d.relationship}{d.date_of_birth ? ` · Born ${new Date(d.date_of_birth).toLocaleDateString()}` : ""}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="rounded-xl border border-border bg-surface-1 p-5 space-y-3">
          <h4 className="text-sm font-semibold text-text flex items-center gap-2">
            <Car className="h-4 w-4 text-amber-400" />
            License & Suspension Registry
          </h4>
          {licenses.length === 0 ? (
            <p className="text-[11px] text-text-faint text-center py-4">No license records</p>
          ) : (
            <div className="space-y-2 max-h-[320px] overflow-y-auto">
              {licenses.map((l) => (
                <div key={l.id} className="rounded-lg bg-surface-2 border border-border p-3">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-semibold text-text">{l.employee_name ?? `#${l.employee_id}`}</p>
                    <span className={`rounded-full text-[10px] font-semibold px-2 py-0.5 border ${l.status === "valid" ? "bg-success/10 text-success border-success/20" : "bg-danger/10 text-danger border-danger/20"}`}>
                      {l.status}
                    </span>
                  </div>
                  <p className="text-[10px] text-text-faint mt-0.5 capitalize">{l.license_type} · Expires {new Date(l.expires_at).toLocaleDateString()}</p>
                  {l.suspension_reason && <p className="text-[10px] text-danger mt-1">Reason: {l.suspension_reason}</p>}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {showDependentModal && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4" onClick={(e: any) => e.target === e.currentTarget && setShowDependentModal(false)}>
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }} className="w-full max-w-lg rounded-2xl border border-border bg-surface-1 shadow-2xl">
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <h2 className="font-bold text-text flex items-center gap-2"><Users className="h-4 w-4 text-primary" /> Add Dependent</h2>
              <button onClick={() => setShowDependentModal(false)} className="text-text-muted hover:text-text"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-5 space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">Full Name *</label>
                <input type="text" value={depForm.full_name} onChange={(e) => setDepForm((f) => ({ ...f, full_name: e.target.value }))} placeholder="Full legal name" className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text placeholder:text-text-faint outline-none focus:border-primary/50" />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">Relationship</label>
                <select value={depForm.relationship} onChange={(e) => setDepForm((f) => ({ ...f, relationship: e.target.value }))} className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none">
                  <option value="spouse">Spouse</option>
                  <option value="child">Child</option>
                  <option value="parent">Parent</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">Date of Birth</label>
                <input type="date" value={depForm.date_of_birth} onChange={(e) => setDepForm((f) => ({ ...f, date_of_birth: e.target.value }))} className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none" />
              </div>
            </div>
            <div className="flex items-center justify-end gap-2 border-t border-border px-5 py-4">
              <button onClick={() => setShowDependentModal(false)} className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text-muted hover:text-text transition-colors">Cancel</button>
              <Button variant="primary" onClick={handleAddDependent}><Check className="h-3.5 w-3.5" /> Save</Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </section>
  );
}


