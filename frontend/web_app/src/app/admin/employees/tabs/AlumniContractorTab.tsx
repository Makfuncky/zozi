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
  Users,
  Briefcase,
  Clock,
  Star,
  Award,
  TrendingUp,
  Mail,
} from "@/lib/icons";
import type { Employee } from "../employee-types";

interface AlumniRecord {
  id: number;
  employee_id: number;
  full_name: string;
  reason: string;
  end_date: string;
}

interface ContractorMilestone {
  id: number;
  employee_id: number;
  employee_name?: string;
  milestone_type: string;
  due_date: string;
  status: string;
}

import type { ToastType } from "@/lib/toastStore";
import { apiFetch } from "@/lib/api";

interface AlumniContractorTabProps {
  employees: Employee[];
  addToast: (message: string, type?: ToastType, duration?: number) => void;
}

export default function AlumniContractorTab({ employees, addToast }: AlumniContractorTabProps) {
  const [alumni, setAlumni] = useState<AlumniRecord[]>([]);
  const [milestones, setMilestones] = useState<ContractorMilestone[]>([]);
  const [loading, setLoading] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [alumniRes, milestoneRes] = await Promise.allSettled([
        apiFetch("/hr/alumni"),
        apiFetch("/admin/expenses/contractor-milestones"),
      ]);
      if (alumniRes.status === "fulfilled") {
        const data = await alumniRes.value.json().catch(() => []);
        setAlumni(Array.isArray(data) ? data : []);
      }
      if (milestoneRes.status === "fulfilled") {
        const data = await milestoneRes.value.json().catch(() => []);
        setMilestones(Array.isArray(data) ? data : []);
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

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text">Alumni Network & Contractor Milestones</h3>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-border bg-surface-1 p-5">
          <h4 className="text-sm font-semibold text-text flex items-center gap-2 mb-3">
            <Award className="h-4 w-4 text-primary" />
            Alumni Network
          </h4>
          {loading ? (
            <div className="flex items-center justify-center py-6">
              <Loader2 className="h-5 w-5 animate-spin text-text-faint" />
            </div>
          ) : alumni.length === 0 ? (
            <div className="text-center py-6">
              <Users className="h-8 w-8 mx-auto mb-2 text-text-faint/40" />
              <p className="text-sm text-text-muted">No alumni records</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-[320px] overflow-y-auto">
              {alumni.map((record) => (
                <div key={record.id} className="rounded-lg bg-surface-2 border border-border p-3 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-text">{record.full_name}</p>
                    <p className="text-[10px] text-text-faint mt-0.5 capitalize">{record.reason} · Ended {new Date(record.end_date).toLocaleDateString()}</p>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Button variant="secondary" title="Rehire">
                      <Star className="h-3 w-3" />
                    </Button>
                    <Button variant="secondary" title="Reference Check">
                      <Users className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="rounded-xl border border-border bg-surface-1 p-5 space-y-3">
          <h4 className="text-sm font-semibold text-text flex items-center gap-2">
            <Briefcase className="h-4 w-4 text-amber-400" />
            Contractor Milestones
          </h4>
          {loading ? (
            <div className="flex items-center justify-center py-6">
              <Loader2 className="h-5 w-5 animate-spin text-text-faint" />
            </div>
          ) : milestones.length === 0 ? (
            <div className="text-center py-6">
              <Clock className="h-8 w-8 mx-auto mb-2 text-text-faint/40" />
              <p className="text-sm text-text-muted">No contractor milestones</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-[320px] overflow-y-auto">
              {milestones.map((milestone) => (
                <div key={milestone.id} className="rounded-lg bg-surface-2 border border-border p-3 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-text">{milestone.employee_name ?? `#${milestone.employee_id}`}</p>
                    <p className="text-[10px] text-text-faint mt-0.5 capitalize">{milestone.milestone_type.replace(/_/g, " ")} · Due {new Date(milestone.due_date).toLocaleDateString()}</p>
                  </div>
                  <span className={`rounded-full text-[10px] font-semibold px-2 py-0.5 border ${milestone.status === "completed" ? "bg-success/10 text-success border-success/20" : milestone.status === "overdue" ? "bg-danger/10 text-danger border-danger/20" : "bg-warning/10 text-warning border-warning/20"}`}>
                    {milestone.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}


