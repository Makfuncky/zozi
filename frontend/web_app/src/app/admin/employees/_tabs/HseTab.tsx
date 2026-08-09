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
  Shield,
  Activity,
  Heart,
  Users,
} from "@/lib/icons";
import type { Employee } from "../employee-types";

interface HseIncident {
  id: number;
  employee_id: number;
  employee_name?: string;
  incident_type: string;
  description: string;
  date_occurred: string;
  severity: string;
  status: string;
}

import type { ToastType } from "@/lib/toastStore";
import { apiFetch } from "@/lib/api";

interface HseTabProps {
  employees: Employee[];
  addToast: (message: string, type?: ToastType, duration?: number) => void;
}

export default function HseTab({ employees, addToast }: HseTabProps) {
  const [incidents, setIncidents] = useState<HseIncident[]>([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    employee_id: "",
    incident_type: "near_miss",
    description: "",
    date_occurred: new Date().toISOString().split("T")[0],
    severity: "low",
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch("/hr/hse/incidents");
      if (res.ok) {
        const data = await res.json().catch(() => []);
        setIncidents(Array.isArray(data) ? data : []);
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

  const handleSubmit = async () => {
    if (!form.employee_id || !form.description || !form.date_occurred) {
      addToast("Employee, date, and description are required", "error");
      return;
    }
    try {
      const res = await apiFetch("/hr/hse/incidents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, employee_id: parseInt(form.employee_id) }),
      });
      if (res.ok) {
        addToast("HSE incident recorded", "success");
        setShowForm(false);
        setForm({ employee_id: "", incident_type: "near_miss", description: "", date_occurred: new Date().toISOString().split("T")[0], severity: "low" });
        void loadData();
      } else {
        addToast("Failed to record incident", "error");
      }
    } catch {
      addToast("Network error", "error");
    }
  };

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text">Health, Safety & Environment (HSE)</h3>
        <Button variant="primary" className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold shadow-sm transition-colors" onClick={() => setShowForm(true)}
        >
          <Plus className="h-3.5 w-3.5" />
          Report Incident
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { label: "Near Miss", count: incidents.filter((i) => i.incident_type === "near_miss").length, color: "text-amber-400" },
          { label: "Injury", count: incidents.filter((i) => i.incident_type === "injury").length, color: "text-danger" },
          { label: "Property Damage", count: incidents.filter((i) => i.incident_type === "property_damage").length, color: "text-warning" },
        ].map((item) => (
          <div key={item.label} className="rounded-xl border border-border bg-surface-1 p-4">
            <div className="flex items-center gap-2">
              <Activity className={`h-4 w-4 ${item.color}`} />
              <p className="text-xs text-text-muted">{item.label}</p>
            </div>
            <p className="text-2xl font-bold text-text mt-2">{item.count}</p>
          </div>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-5 w-5 animate-spin text-text-faint" />
        </div>
      ) : incidents.length === 0 ? (
        <div className="rounded-xl border border-border bg-surface-1 p-8 text-center">
          <Shield className="h-8 w-8 mx-auto mb-2 text-text-faint/40" />
          <p className="text-sm text-text-muted">No HSE incidents on record</p>
        </div>
      ) : (
        <div className="rounded-xl border border-border bg-surface-1 overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border bg-surface-2 text-text-muted">
                <th className="px-4 py-2.5 font-semibold">Employee</th>
                <th className="px-4 py-2.5 font-semibold">Type</th>
                <th className="px-4 py-2.5 font-semibold">Severity</th>
                <th className="px-4 py-2.5 font-semibold">Date</th>
                <th className="px-4 py-2.5 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {incidents.map((incident) => (
                <tr key={incident.id} className="hover:bg-surface-2/50 transition-colors">
                  <td className="px-4 py-3 text-text">{incident.employee_name ?? `#${incident.employee_id}`}</td>
                  <td className="px-4 py-3 text-text-muted capitalize">{incident.incident_type.replace(/_/g, " ")}</td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full text-[10px] font-semibold px-2 py-0.5 border ${incident.severity === "critical" ? "bg-danger/10 text-danger border-danger/20" : incident.severity === "high" ? "bg-warning/10 text-warning border-warning/20" : "bg-surface-3 text-text-muted border-border"}`}>
                      {incident.severity}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-text-muted">
                    {incident.date_occurred ? new Date(incident.date_occurred).toLocaleDateString() : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full text-[10px] font-semibold px-2 py-0.5 border ${incident.status === "resolved" ? "bg-success/10 text-success border-success/20" : "bg-warning/10 text-warning border-warning/20"}`}>
                      {incident.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showForm && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4" onClick={(e: any) => e.target === e.currentTarget && setShowForm(false)}>
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }} className="w-full max-w-lg rounded-2xl border border-border bg-surface-1 shadow-2xl">
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <h2 className="font-bold text-text flex items-center gap-2"><Shield className="h-4 w-4 text-warning" /> Report HSE Incident</h2>
              <button onClick={() => setShowForm(false)} className="text-text-muted hover:text-text"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-5 space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">Employee *</label>
                <select value={form.employee_id} onChange={(e) => setForm((f) => ({ ...f, employee_id: e.target.value }))} className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none">
                  <option value="">Select employee</option>
                  {employees.map((emp) => (
                    <option key={emp.id} value={emp.id}>
                      {emp.full_name ?? emp.name ?? emp.employee_code}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">Incident Type *</label>
                <select value={form.incident_type} onChange={(e) => setForm((f) => ({ ...f, incident_type: e.target.value }))} className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none">
                  <option value="near_miss">Near Miss</option>
                  <option value="injury">Injury</option>
                  <option value="property_damage">Property Damage</option>
                  <option value="environmental">Environmental</option>
                </select>
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">Date Occurred *</label>
                <input type="date" value={form.date_occurred} onChange={(e) => setForm((f) => ({ ...f, date_occurred: e.target.value }))} className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none" />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">Severity *</label>
                <select value={form.severity} onChange={(e) => setForm((f) => ({ ...f, severity: e.target.value }))} className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none">
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">Description *</label>
                <textarea value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} placeholder="Describe the incident..." rows={3} className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text placeholder:text-text-faint outline-none focus:border-primary/50" />
              </div>
            </div>
            <div className="flex items-center justify-end gap-2 border-t border-border px-5 py-4">
              <button onClick={() => setShowForm(false)} className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text-muted hover:text-text transition-colors">Cancel</button>
              <Button variant="warning" onClick={handleSubmit}><Check className="h-3.5 w-3.5" /> Submit</Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </section>
  );
}


