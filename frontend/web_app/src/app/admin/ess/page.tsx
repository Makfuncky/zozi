"use client";

import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelLoadingState, PanelTabs, PanelCard, PanelGrid, PanelSection, PanelStatCard, PanelMetric, PanelFilterBar, PanelActionBar, PanelDivider } from "@/components/PanelPage";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { useToastStore } from "@/lib/toastStore";
import { Button } from "@/components/ui/Button";
import { Badge, StatusBadge } from "@/components/ui/shared/Badge";
import { EmptyState } from "@/components/ui/shared/EmptyState";
import ActivityTimeline from "@/components/ems/ActivityTimeline";
import {
  User, Briefcase, Calendar, DollarSign, Clock, Target,
  Building2, ChevronRight, Mail, Phone, MapPin,
  Award, TrendingUp, CheckCircle2, AlertCircle, Loader2,
  FileText, Shield, BarChart3, Users, Star, Edit3,
  RefreshCw, Sparkles, Heart, Gift, Eye, GitBranch, Layers, Activity,
} from "@/lib/icons";

interface Profile {
  id: number; user_id: number; employee_code: string; job_title: string;
  department: string; org_unit_id: number; employment_status: string;
  phone: string; address: string; emergency_contact_name: string;
  emergency_contact_phone: string; country_code: string; hire_date: string;
  email: string; full_name: string; role: string;
  unit_name: string; unit_path: string;
}

interface LeaveBalance {
  leave_type: string; year: number; allocated_days: number;
  used_days: number; carried_forward_days: number;
  pending_days: number; remaining_days: number;
}

interface Payslip {
  id: number; payroll_date: string; gross_amount: string;
  net_amount: string; deductions: string; status: string; created_at: string;
}

interface Attendance {
  id: number; clock_in: string; clock_out: string; status: string; created_at: string;
}

interface OKR {
  id: number; title: string; description: string; objective_type: string;
  quarter: string; year: number; status: string; progress_pct: number;
  confidence_level: number; created_at: string; kpis: KPI[];
}
interface KPI {
  id: number; metric_name: string; metric_type: string;
  target_value: string; current_value: string; weight_pct: number;
}

type EssTab = "dashboard" | "profile" | "leave" | "payslips" | "attendance" | "okrs" | "org-chart";

export default function EssPage() {
  const { user } = useAuth();
  const addToast = useToastStore((s) => s.addToast);
  const [tab, setTab] = useState<EssTab>("dashboard");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [profile, setProfile] = useState<Profile | null>(null);
  const [leaveBalance, setLeaveBalance] = useState<LeaveBalance[]>([]);
  const [payslips, setPayslips] = useState<Payslip[]>([]);
  const [attendance, setAttendance] = useState<Attendance[]>([]);
  const [okrs, setOkrs] = useState<OKR[]>([]);
  const [orgChart, setOrgChart] = useState<any>(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadAll = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      const [prof, leave, pay, att, okrData, org] = await Promise.all([
          apiFetch("/ess/profile").then(parseJsonResponse).catch(() => null),
          apiFetch("/ess/leave/balance").then(parseJsonResponse).catch(() => []),
          apiFetch("/ess/payslips").then(parseJsonResponse).catch(() => []),
          apiFetch("/ess/attendance").then(parseJsonResponse).catch(() => []),
          apiFetch("/ess/okrs").then(parseJsonResponse).catch(() => []),
          apiFetch("/ess/org-chart").then(parseJsonResponse).catch(() => null),
        ]);
        if (prof && typeof prof === "object") setProfile(prof);
        if (Array.isArray(leave)) setLeaveBalance(leave);
        if (Array.isArray(pay)) setPayslips(pay);
        if (Array.isArray(att)) setAttendance(att);
        if (Array.isArray(okrData)) setOkrs(okrData);
        if (org && typeof org === "object") setOrgChart(org);
    } catch (e: any) {
      setError(e?.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => { loadAll(); }, [loadAll]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadAll();
    setRefreshing(false);
    addToast("Data refreshed", "success");
  };

  const tabs = [
    { key: "dashboard" as EssTab, label: "Dashboard", icon: Sparkles },
    { key: "profile" as EssTab, label: "Profile", icon: User },
    { key: "leave" as EssTab, label: "Leave", icon: Calendar },
    { key: "payslips" as EssTab, label: "Payslips", icon: DollarSign },
    { key: "attendance" as EssTab, label: "Attendance", icon: Clock },
    { key: "okrs" as EssTab, label: "OKRs", icon: Target },
    { key: "org-chart" as EssTab, label: "Org Chart", icon: Building2 },
  ];

  return (
    <AdminLayout title="Employee Self-Service">
      <PanelContent>
        <div className="flex items-center justify-between mb-2">
          <div>
            <h1 className="text-2xl font-display font-bold text-text">
              {profile ? `Welcome, ${profile.full_name}` : "Employee Self-Service"}
            </h1>
            <p className="text-text-muted text-sm mt-1">Manage your profile, leave, payslips, attendance, and OKRs</p>
          </div>
          <PanelActionBar>
            <Button variant="ghost" size="sm" leftIcon={<RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
            } onClick={handleRefresh} disabled={refreshing}>Refresh</Button>
            {profile && <Badge className="bg-primary/10 text-primary border-primary/20 px-3 py-1">{profile.employee_code}</Badge>}
          </PanelActionBar>
        </div>

        <PanelTabs items={tabs} value={tab} onChange={setTab} />

        {loading ? (
          <PanelLoadingState count={4} />
        ) : error ? (
          <EmptyState icon={AlertCircle} title="Connection Error" description={error} />
        ) : (
          <AnimatePresence mode="wait">
            <motion.div key={tab} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }} transition={{ duration: 0.2 }}>
              {tab === "dashboard" && <DashboardView profile={profile} leaveBalance={leaveBalance}
                payslips={payslips} attendance={attendance} okrs={okrs} employeeId={profile?.id} onNavigate={setTab} />}
              {tab === "profile" && <ProfileView profile={profile} onRefresh={loadAll} />}
              {tab === "leave" && <LeaveView balances={leaveBalance} onRefresh={loadAll} />}
              {tab === "payslips" && <PayslipsView payslips={payslips} />}
              {tab === "attendance" && <AttendanceView attendance={attendance} />}
              {tab === "okrs" && <OkrsView okrs={okrs} />}
              {tab === "org-chart" && <OrgChartView data={orgChart} />}
            </motion.div>
          </AnimatePresence>
        )}
      </PanelContent>
    </AdminLayout>
  );
}

function DashboardView({ profile, leaveBalance, payslips, attendance, okrs, employeeId, onNavigate }: {
  profile: Profile | null; leaveBalance: LeaveBalance[]; payslips: Payslip[];
  attendance: Attendance[]; okrs: OKR[]; employeeId?: number; onNavigate: (t: EssTab) => void;
}) {
  const totalRemaining = leaveBalance.reduce((s, l) => s + l.remaining_days, 0);
  const activeOkrs = okrs.filter((o) => o.status === "active").length;
  const avgProgress = okrs.length ? Math.round(okrs.reduce((s, o) => s + o.progress_pct, 0) / okrs.length) : 0;
  const latestPayslip = payslips[0];

  return (
    <PanelSection className="mt-4">
      <PanelGrid cols={4}>
        <PanelStatCard label="Leave Balance" value={`${totalRemaining}d`} icon={Calendar}
          color="from-emerald-500 to-teal-500" subtitle="Days remaining"
          onClick={() => onNavigate("leave")} />
        <PanelStatCard label="Active OKRs" value={activeOkrs} icon={Target}
          color="from-violet-500 to-purple-500" subtitle="In progress"
          onClick={() => onNavigate("okrs")} />
        <PanelStatCard label="Avg Progress" value={`${avgProgress}%`} icon={TrendingUp}
          color="from-blue-500 to-indigo-500" subtitle="Across all OKRs"
          onClick={() => onNavigate("okrs")} />
        <PanelStatCard label="Latest Payslip" value={latestPayslip ? `OMR ${latestPayslip.net_amount}` : "—"}
          icon={DollarSign} color="from-amber-500 to-orange-500"
          subtitle={latestPayslip ? new Date(latestPayslip.payroll_date).toLocaleDateString() : "No data"}
          onClick={() => onNavigate("payslips")} />
      </PanelGrid>

      <PanelGrid cols={2}>
        {profile && (
          <PanelCard>
            <PanelCard.Header>
              <span className="flex items-center gap-2"><User className="w-4 h-4 text-primary" /> Profile Summary</span>
            </PanelCard.Header>
            <div className="space-y-2.5">
              {[Briefcase, Building2, Building2, Mail, Phone].map((Icon, i) => {
                const labels = ["Job Title", "Department", "Unit", "Email", "Phone"];
                const values = [profile.job_title, profile.department, profile.unit_name, profile.email, profile.phone || "—"];
                return (
                  <div key={labels[i]} className="flex items-center gap-3 text-sm">
                    <Icon className="w-4 h-4 text-text-muted flex-shrink-0" />
                    <span className="text-text-muted w-24">{labels[i]}</span>
                    <span className="text-text font-medium truncate">{values[i] || "—"}</span>
                  </div>
                );
              })}
            </div>
          </PanelCard>
        )}

        <PanelCard>
          <PanelCard.Header>
            <span className="flex items-center gap-2"><Activity className="w-4 h-4 text-primary" /> Recent Activity</span>
          </PanelCard.Header>
          <ActivityTimeline compact employeeId={employeeId} />
        </PanelCard>
      </PanelGrid>
    </PanelSection>
  );
}

function ProfileView({ profile, onRefresh }: { profile: Profile | null; onRefresh: () => void }) {
  const addToast = useToastStore((s) => s.addToast);
  const [editing, setEditing] = useState(false);
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [ecName, setEcName] = useState("");
  const [ecPhone, setEcPhone] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (profile) {
      setPhone(profile.phone || "");
      setAddress(profile.address || "");
      setEcName(profile.emergency_contact_name || "");
      setEcPhone(profile.emergency_contact_phone || "");
    }
  }, [profile]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const params = new URLSearchParams();
      if (phone) params.set("phone", phone);
      if (address) params.set("address", address);
      if (ecName) params.set("emergency_contact_name", ecName);
      if (ecPhone) params.set("emergency_contact_phone", ecPhone);
      await apiFetch(`/ess/profile?${params.toString()}`, { method: "PUT" });
      addToast("Profile updated", "success");
      setEditing(false);
      onRefresh();
    } catch (e: any) {
      addToast(e?.message || "Failed to update", "error");
    } finally {
      setSaving(false);
    }
  };

  if (!profile) return <EmptyState icon={User} title="No Profile" description="Could not load profile data" />;

  return (
    <PanelSection className="mt-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-display font-semibold text-text">Personal Information</h2>
        <Button variant={editing ? "primary" : "ghost"} size="sm"
          leftIcon={editing ? undefined : <Edit3 className="w-4 h-4" />}
          onClick={() => editing ? handleSave() : setEditing(true)} isLoading={saving}>
          {editing ? "Save Changes" : "Edit"}
        </Button>
      </div>

      <PanelGrid cols={2}>
        <PanelCard>
          <PanelCard.Header>Employment Details</PanelCard.Header>
          {[
            ["Employee Code", profile.employee_code], ["Full Name", profile.full_name],
            ["Email", profile.email], ["Role", profile.role],
            ["Job Title", profile.job_title], ["Department", profile.department],
            ["Unit", profile.unit_name], ["Status", profile.employment_status],
            ["Hire Date", profile.hire_date], ["Country", profile.country_code],
          ].map(([label, value]) => (
            <div key={label as string} className="flex justify-between text-sm py-1.5">
              <span className="text-text-muted">{label as string}</span>
              <span className="text-text font-medium">{(value as string) || "—"}</span>
            </div>
          ))}
        </PanelCard>

        <PanelCard>
          <PanelCard.Header>Contact & Emergency</PanelCard.Header>
          {editing ? (
            <div className="space-y-3">
              <div><label className="text-xs text-text-muted">Phone</label>
                <input value={phone} onChange={(e) => setPhone(e.target.value)}
                  className="w-full mt-1 px-3 py-2 rounded-lg bg-surface border border-border text-text text-sm" /></div>
              <div><label className="text-xs text-text-muted">Address</label>
                <textarea value={address} onChange={(e) => setAddress(e.target.value)} rows={2}
                  className="w-full mt-1 px-3 py-2 rounded-lg bg-surface border border-border text-text text-sm" /></div>
              <div><label className="text-xs text-text-muted">Emergency Contact</label>
                <input value={ecName} onChange={(e) => setEcName(e.target.value)} placeholder="Name"
                  className="w-full mt-1 px-3 py-2 rounded-lg bg-surface border border-border text-text text-sm mb-2" />
                <input value={ecPhone} onChange={(e) => setEcPhone(e.target.value)} placeholder="Phone"
                  className="w-full px-3 py-2 rounded-lg bg-surface border border-border text-text text-sm" /></div>
              <PanelActionBar>
                <Button size="sm" variant="primary" onClick={handleSave} isLoading={saving}>Save</Button>
                <Button size="sm" variant="ghost" onClick={() => setEditing(false)}>Cancel</Button>
              </PanelActionBar>
            </div>
          ) : (
            <div className="space-y-2.5">
              {[
                ["Phone", profile.phone], ["Address", profile.address],
                ["Emergency Contact", profile.emergency_contact_name],
                ["Emergency Phone", profile.emergency_contact_phone],
              ].map(([label, value]) => (
                <div key={label as string} className="flex justify-between text-sm">
                  <span className="text-text-muted">{label as string}</span>
                  <span className="text-text font-medium">{(value as string) || "—"}</span>
                </div>
              ))}
            </div>
          )}
        </PanelCard>
      </PanelGrid>
    </PanelSection>
  );
}

function LeaveView({ balances, onRefresh }: { balances: LeaveBalance[]; onRefresh: () => void }) {
  const addToast = useToastStore((s) => s.addToast);
  const [showRequest, setShowRequest] = useState(false);
  const [leaveType, setLeaveType] = useState("annual");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleRequest = async () => {
    if (!startDate || !endDate) return;
    setSubmitting(true);
    try {
      const params = new URLSearchParams({ leave_type: leaveType, start_date: startDate, end_date: endDate, reason });
      await apiFetch(`/ess/leave/request?${params.toString()}`, { method: "POST" });
      addToast("Leave request submitted", "success");
      setShowRequest(false);
      setStartDate(""); setEndDate(""); setReason("");
      onRefresh();
    } catch (e: any) {
      addToast(e?.message || "Failed to submit", "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <PanelSection className="mt-4" title="Leave Balance" action={
      <Button size="sm" leftIcon={<Calendar className="w-4 h-4" />}
        onClick={() => setShowRequest(!showRequest)}>
        {showRequest ? "Cancel" : "Request Leave"}
      </Button>
    }>
      <AnimatePresence>
        {showRequest && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
            <PanelCard className="mb-4">
              <PanelCard.Header>New Leave Request</PanelCard.Header>
              <div className="grid sm:grid-cols-2 gap-4">
                <div><label className="text-xs text-text-muted">Type</label>
                  <select value={leaveType} onChange={(e) => setLeaveType(e.target.value)}
                    className="w-full mt-1 px-3 py-2 rounded-lg bg-surface border border-border text-text text-sm">
                    <option value="annual">Annual</option><option value="sick">Sick</option>
                    <option value="personal">Personal</option><option value="maternity">Maternity</option>
                    <option value="paternity">Paternity</option><option value="unpaid">Unpaid</option>
                  </select></div>
                <div><label className="text-xs text-text-muted">Start Date</label>
                  <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)}
                    className="w-full mt-1 px-3 py-2 rounded-lg bg-surface border border-border text-text text-sm" /></div>
                <div><label className="text-xs text-text-muted">End Date</label>
                  <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)}
                    className="w-full mt-1 px-3 py-2 rounded-lg bg-surface border border-border text-text text-sm" /></div>
                <div className="sm:col-span-2"><label className="text-xs text-text-muted">Reason</label>
                  <textarea value={reason} onChange={(e) => setReason(e.target.value)} rows={2}
                    className="w-full mt-1 px-3 py-2 rounded-lg bg-surface border border-border text-text text-sm" /></div>
              </div>
              <PanelActionBar className="mt-3">
                <Button size="sm" onClick={handleRequest} isLoading={submitting} disabled={!startDate || !endDate}>Submit</Button>
                <Button size="sm" variant="ghost" onClick={() => setShowRequest(false)}>Cancel</Button>
              </PanelActionBar>
            </PanelCard>
          </motion.div>
        )}
      </AnimatePresence>

      {balances.length === 0 ? (
        <EmptyState icon={Calendar} title="No Leave Data" description="No leave balance records found" />
      ) : (
        <PanelGrid cols={3}>
          {balances.map((b) => (
            <PanelCard key={`${b.leave_type}-${b.year}`}>
              <div className="flex items-center justify-between mb-3">
                <Badge className="bg-primary/10 text-primary border-primary/20 capitalize">{b.leave_type}</Badge>
                <span className="text-xs text-text-muted">{b.year}</span>
              </div>
              <PanelMetric label="days remaining" value={b.remaining_days} size="lg" />
              <div className="w-full h-2 bg-surface-2 rounded-full overflow-hidden mt-2">
                <div className="h-full bg-gradient-to-r from-primary to-accent rounded-full transition-all"
                  style={{ width: `${Math.min(100, (b.used_days / Math.max(1, b.allocated_days)) * 100)}%` }} />
              </div>
              <div className="flex justify-between text-xs text-text-muted mt-1.5">
                <span>{b.used_days} used</span>
                <span>{b.allocated_days} allocated</span>
              </div>
            </PanelCard>
          ))}
        </PanelGrid>
      )}
    </PanelSection>
  );
}

function PayslipsView({ payslips }: { payslips: Payslip[] }) {
  if (payslips.length === 0) return <EmptyState icon={DollarSign} title="No Payslips" description="No payroll records found" />;

  return (
    <PanelSection className="mt-4" title="Payroll History">
      <div className="space-y-3">
        {payslips.map((p) => (
          <PanelCard key={p.id} hover>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-500/20 flex items-center justify-center">
                  <DollarSign className="w-6 h-6 text-emerald-500" />
                </div>
                <div>
                  <p className="font-semibold text-text">{new Date(p.payroll_date).toLocaleDateString("en-US", { month: "long", year: "numeric" })}</p>
                  <p className="text-sm text-text-muted">Gross: {p.gross_amount} | Deductions: {p.deductions}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-lg font-bold text-text">{p.net_amount}</p>
                <StatusBadge status={p.status === "paid" ? "success" : p.status === "pending" ? "warning" : "info"} />
              </div>
            </div>
          </PanelCard>
        ))}
      </div>
    </PanelSection>
  );
}

function AttendanceView({ attendance }: { attendance: Attendance[] }) {
  if (!attendance || attendance.length === 0) return <EmptyState icon={Clock} title="No Records" description="No attendance records found" />;

  return (
    <PanelSection className="mt-4" title="Attendance Records">
      <div className="overflow-x-auto rounded-2xl border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-surface-2 border-b border-border">
              <th className="text-left py-3 px-4 text-text-muted font-medium text-xs uppercase tracking-wider">Date</th>
              <th className="text-left py-3 px-4 text-text-muted font-medium text-xs uppercase tracking-wider">Clock In</th>
              <th className="text-left py-3 px-4 text-text-muted font-medium text-xs uppercase tracking-wider">Clock Out</th>
              <th className="text-left py-3 px-4 text-text-muted font-medium text-xs uppercase tracking-wider">Duration</th>
              <th className="text-left py-3 px-4 text-text-muted font-medium text-xs uppercase tracking-wider">Status</th>
            </tr>
          </thead>
          <tbody>
            {attendance.map((r) => {
              const clockIn = r.clock_in ? new Date(r.clock_in) : null;
              const clockOut = r.clock_out ? new Date(r.clock_out) : null;
              const duration = clockIn && clockOut
                ? `${Math.round((clockOut.getTime() - clockIn.getTime()) / 3600000)}h`
                : "—";
              return (
                <tr key={r.id} className="border-b border-border/50 hover:bg-surface-1/50 transition-colors">
                  <td className="py-3 px-4 text-text">{clockIn?.toLocaleDateString() || "—"}</td>
                  <td className="py-3 px-4 text-text">{clockIn?.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) || "—"}</td>
                  <td className="py-3 px-4 text-text">{clockOut?.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) || "—"}</td>
                  <td className="py-3 px-4 text-text font-mono">{duration}</td>
                  <td className="py-3 px-4"><StatusBadge status={r.status === "present" ? "success" : r.status === "late" ? "warning" : "info"}>{r.status}</StatusBadge></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </PanelSection>
  );
}

function OkrsView({ okrs }: { okrs: OKR[] }) {
  if (okrs.length === 0) return <EmptyState icon={Target} title="No OKRs" description="No OKR objectives found" />;

  return (
    <PanelSection className="mt-4" title="My OKRs">
      <div className="space-y-4">
        {okrs.map((o) => (
          <PanelCard key={o.id} hover>
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-semibold text-text">{o.title}</h3>
                <p className="text-sm text-text-muted">{o.quarter} {o.year} · {o.objective_type}</p>
              </div>
              <StatusBadge status={o.status === "active" ? "success" : o.status === "completed" ? "info" : "warning"}>{o.status}</StatusBadge>
            </div>
            {o.description && <p className="text-sm text-text-muted mb-3">{o.description}</p>}
            <div className="flex items-center gap-3 mb-4">
              <div className="flex-1 h-2.5 bg-surface-2 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-violet-500 to-purple-500 rounded-full transition-all"
                  style={{ width: `${o.progress_pct}%` }} />
              </div>
              <span className="text-sm font-semibold text-text">{o.progress_pct}%</span>
            </div>
            {o.kpis?.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs text-text-muted uppercase tracking-wider font-semibold">Key Results</p>
                {o.kpis.map((k) => (
                  <div key={k.id} className="flex items-center gap-3 text-sm bg-surface-1/50 rounded-xl px-4 py-2.5">
                    <Target className="w-3.5 h-3.5 text-primary flex-shrink-0" />
                    <span className="text-text flex-1">{k.metric_name}</span>
                    <span className="text-text-muted">{k.current_value} / {k.target_value}</span>
                    <div className="w-20 h-1.5 bg-surface-2 rounded-full overflow-hidden">
                      <div className="h-full bg-accent rounded-full"
                        style={{ width: `${Math.min(100, (Number(k.current_value) / Math.max(1, Number(k.target_value))) * 100)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </PanelCard>
        ))}
      </div>
    </PanelSection>
  );
}

function OrgChartView({ data }: { data: any }) {
  if (!data?.org_unit) return <EmptyState icon={Building2} title="No Org Data" description="Could not load organization chart" />;

  return (
    <PanelSection className="mt-4" title="My Organization">
      <PanelCard className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-accent/20 mb-3">
          <Building2 className="w-8 h-8 text-primary" />
        </div>
        <h3 className="text-xl font-bold text-text">{data.org_unit.name}</h3>
        <p className="text-sm text-text-muted">Manager: {data.org_unit.manager_name || "N/A"} · Depth: {data.org_unit.depth}</p>
      </PanelCard>

      <PanelGrid cols={2}>
        <PanelCard>
          <PanelCard.Header>
            <span className="flex items-center gap-2"><Users className="w-4 h-4 text-primary" /> Colleagues ({data.colleagues?.length || 0})</span>
          </PanelCard.Header>
          <div className="space-y-1">
            {data.colleagues?.map((c: any) => (
              <div key={c.id} className="flex items-center gap-3 p-2.5 rounded-xl hover:bg-surface-1/50 transition-colors">
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center">
                  <User className="w-4 h-4 text-primary" />
                </div>
                <div>
                  <p className="text-sm font-medium text-text">{c.full_name}</p>
                  <p className="text-xs text-text-muted">{c.job_title || c.employee_code}</p>
                </div>
              </div>
            ))}
          </div>
        </PanelCard>

        <PanelCard>
          <PanelCard.Header>
            <span className="flex items-center gap-2"><Layers className="w-4 h-4 text-primary" /> Sub-Units ({data.sub_units?.length || 0})</span>
          </PanelCard.Header>
          <div className="space-y-1">
            {data.sub_units?.map((s: any) => (
              <div key={s.id} className="flex items-center gap-3 p-2.5 rounded-xl hover:bg-surface-1/50 transition-colors">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-amber-500/20 to-orange-500/20 flex items-center justify-center">
                  <GitBranch className="w-4 h-4 text-amber-500" />
                </div>
                <div>
                  <p className="text-sm font-medium text-text">{s.name}</p>
                  <p className="text-xs text-text-muted">{s.manager_name ? `Manager: ${s.manager_name}` : ""} · Depth {s.depth}</p>
                </div>
              </div>
            ))}
          </div>
        </PanelCard>
      </PanelGrid>
    </PanelSection>
  );
}
