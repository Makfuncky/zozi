"use client";

import { useEffect, useState, useMemo, useCallback, Suspense } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Users,
  MapPin,
  Clock,
  Calendar,
  FileText,
  Shield,
  Building2,
  Plus,
  X,
  Check,
  AlertCircle,
  Search,
  Download,
  QrCode,
  Fingerprint,
  Globe,
  Briefcase,
  DollarSign,
  BarChart3,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Eye,
  Activity,
  TrendingUp,
  Star,
  Award,
  Phone,
  Mail,
  Key,
  Lock,
  Unlock,
  Video,
  MessageCircle,
  Settings,
  ChevronRight,
  Loader2,
  Upload,
  UserX,
} from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelLoadingState, PanelTabs } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { useAdminCountry } from "@/lib/useAdminCountry";
import { useToastStore, type ToastType } from "@/lib/toastStore";
import { isAdminStaffRole } from "@shared/adminPermissions";
import { EnterpriseDataTable, type EnterpriseColumn } from "@shared/components/EnterpriseDataTable";

import { Button } from "@/components/ui/Button";
import { Modal, ModalFooter } from "@/components/ui/shared/Modal";
import { Badge, StatusBadge } from "@/components/ui/shared/Badge";
import { Table, TableHeader, TableHeaderCell, TableBody, TableRow, TableCell } from "@/components/ui/shared/Table";
import { EmptyState } from "@/components/ui/shared/EmptyState";
import CommunicationsTab from "./tabs/CommunicationsTab";
import AddressMatrixTab from "./tabs/AddressMatrixTab";
import PerformanceTab from "./tabs/PerformanceTab";
import DisciplinaryOffboardingTab from "./tabs/DisciplinaryOffboardingTab";
import HseTab from "./tabs/HseTab";
import AlumniContractorTab from "./tabs/AlumniContractorTab";
import InsuranceBenefitsTab from "./tabs/InsuranceBenefitsTab";
import DEITab from "./tabs/DEITab";

import { EmployeeTab, Employee, Office, AttendanceRecord, LeaveRequest, ShiftRoster, CreateEmployeeForm, EMPTY_FORM } from "./employee-types";

export function EmployeesContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const tab = (searchParams?.get("tab") ?? "directory") as EmployeeTab;
  const { user, isLoggedIn, isLoading } = useAuth();
  const { selectedCountry } = useAdminCountry();
  const countryCode = selectedCountry?.code || "*";
  const currency = selectedCountry?.currency || "OMR";
  const { addToast } = useToastStore();

  const [loading, setLoading] = useState(true);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [offices, setOffices] = useState<Office[]>([]);
  const [leaveRequests, setLeaveRequests] = useState<LeaveRequest[]>([]);
  const [shifts, setShifts] = useState<ShiftRoster[]>([]);
  const [attendance, setAttendance] = useState<AttendanceRecord[]>([]);
  const [payroll, setPayroll] = useState<{ employee_count: number; total_gross: number; total_tax: number; total_net: number } | null>(null);

  // Search & filter
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [deptFilter, setDeptFilter] = useState("all");

  // Add Employee modal
  const [showAddEmployee, setShowAddEmployee] = useState(false);
  const [addForm, setAddForm] = useState<CreateEmployeeForm>(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);

  // Add Office modal
  const [showAddOffice, setShowAddOffice] = useState(false);
  const [officeName, setOfficeName] = useState("");
  const [officeCity, setOfficeCity] = useState("");
  const [officeCountry, setOfficeCountry] = useState("");
  const [submittingOffice, setSubmittingOffice] = useState(false);

  // Selected employee for detail view
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null);

  // QR token state
  const [qrTokens, setQrTokens] = useState<Record<number, string>>({});
  const [generatingQR, setGeneratingQR] = useState<number | null>(null);

  // Leave request form state
  const [showLeaveForm, setShowLeaveForm] = useState(false);
  const [leaveForm, setLeaveForm] = useState({
    employee_id: "",
    leave_type: "annual",
    start_date: "",
    end_date: "",
    notes: "",
  });
  const [submittingLeave, setSubmittingLeave] = useState(false);

  // Shift roster form state
  const [showShiftForm, setShowShiftForm] = useState(false);
  const [shiftForm, setShiftForm] = useState({
    employee_id: "",
    shift_date: "",
    start_time: "09:00",
    end_time: "17:00",
    shift_type: "scheduled",
    status: "scheduled",
  });
  const [submittingShift, setSubmittingShift] = useState(false);

  // Document upload state
  const [showDocForm, setShowDocForm] = useState(false);
  const [docForm, setDocForm] = useState({
    employee_id: "",
    document_type: "",
    document_name: "",
    file_url: "",
    expires_at: "",
    notes: "",
  });
  const [selectedDocEmployeeId, setSelectedDocEmployeeId] = useState<number | null>(null);
  const [submittingDoc, setSubmittingDoc] = useState(false);
  const [employeeDocs, setEmployeeDocs] = useState<Record<number, any[]>>({});

  // Audit trail state
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditPage, setAuditPage] = useState(1);
  const [auditTotal, setAuditTotal] = useState(0);

  // COI state
  const [coiEmployeeId, setCoiEmployeeId] = useState<number | null>(null);
  const [coiConflicts, setCoiConflicts] = useState<any[]>([]);
  const [coiLoading, setCoiLoading] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [empRes, offRes, leaveRes, shiftRes] = await Promise.allSettled([
        apiFetch(`/admin/${countryCode}/employees`),
        apiFetch(`/admin/${countryCode}/offices`).catch(() => apiFetch("/employees/")),
        apiFetch(`/admin/${countryCode}/employees/leave-requests`).catch(() => null),
        apiFetch(`/admin/${countryCode}/employees/shifts`).catch(() => null),
      ]);

      if (empRes.status === "fulfilled" && empRes.value.ok) {
        const data = await empRes.value.json().catch(() => ({}));
        if (Array.isArray(data)) {
          setEmployees(data);
        } else {
          setEmployees(Array.isArray(data?.employees) ? data.employees : []);
          setOffices(Array.isArray(data?.offices) ? data.offices : []);
        }
      }

      if (offRes.status === "fulfilled" && offRes.value?.ok) {
        const offData = await offRes.value.json().catch(() => []);
        if (Array.isArray(offData)) setOffices(offData);
      }

      if (leaveRes.status === "fulfilled" && leaveRes.value?.ok) {
        const leaveData = await leaveRes.value.json().catch(() => []);
        if (Array.isArray(leaveData)) setLeaveRequests(leaveData);
      }

      if (shiftRes.status === "fulfilled" && shiftRes.value?.ok) {
        const shiftData = await shiftRes.value.json().catch(() => []);
        if (Array.isArray(shiftData)) setShifts(shiftData);
      }
    } catch {
      addToast("Failed to load employee data", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast, countryCode]);

  const loadAuditLogs = useCallback(async () => {
    if (tab !== "audit") return;
    setAuditLoading(true);
    try {
      const res = await apiFetch(`/audit?limit=50&offset=${(auditPage - 1) * 50}`);
      if (res.ok) {
        const data = await res.json().catch(() => []);
        setAuditLogs(Array.isArray(data) ? data : []);
        setAuditTotal(Array.isArray(data) ? data.length : 0);
      }
    } catch {
      addToast("Failed to load audit logs", "error");
    } finally {
      setAuditLoading(false);
    }
  }, [addToast, auditPage, countryCode, tab]);

  useEffect(() => {
    if (isLoading) return;
    if (!isLoggedIn || !isAdminStaffRole(user?.role ?? null)) {
      router.push("/admin/login");
      return;
    }
    loadData();
    if (tab === "audit") loadAuditLogs();
  }, [isLoading, isLoggedIn, user, router, loadData, tab, loadAuditLogs]);

  useEffect(() => {
    if (isLoading) return;
    if (!isLoggedIn || !isAdminStaffRole(user?.role ?? null)) return;
    if (tab === "payroll") loadPayrollData();
  }, [isLoading, isLoggedIn, user, tab]);

  const handleTabChange = (newTab: string) => {
    router.push(`${pathname}?tab=${newTab}`);
  };

  const handleAddEmployee = async () => {
    if (!addForm.employee_code || !addForm.hire_date) {
      addToast("Employee code and hire date are required", "error");
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        employee_code: addForm.employee_code,
        user_id: addForm.user_id ? parseInt(addForm.user_id) : undefined,
        office_id: addForm.office_id ? parseInt(addForm.office_id) : undefined,
        department: addForm.department || undefined,
        position: addForm.position || undefined,
        employment_type: addForm.employment_type,
        salary: addForm.salary ? parseFloat(addForm.salary) : undefined,
        currency: addForm.currency,
        hire_date: addForm.hire_date,
        country_code: addForm.country_code || undefined,
      };
      const res = await apiFetch(`/admin/${countryCode}/employees`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        addToast("Employee added successfully", "success");
        setShowAddEmployee(false);
        setAddForm(EMPTY_FORM);
        loadData();
      } else {
        const err = await res.json().catch(() => ({}));
        addToast(err.detail ?? "Failed to add employee", "error");
      }
    } catch {
      addToast("Network error", "error");
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddOffice = async () => {
    if (!officeName) {
      addToast("Office name is required", "error");
      return;
    }
    setSubmittingOffice(true);
    try {
      const res = await apiFetch(`/admin/${countryCode}/offices`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: officeName,
          city: officeCity || undefined,
          country_code: officeCountry || countryCode,
        }),
      });
      if (res.ok) {
        addToast("Office added", "success");
        setShowAddOffice(false);
        setOfficeName("");
        setOfficeCity("");
        loadData();
      } else {
        addToast("Failed to add office", "error");
      }
    } finally {
      setSubmittingOffice(false);
    }
  };

  const handleGenerateQR = async (employeeId: number) => {
    setGeneratingQR(employeeId);
    try {
      const res = await apiFetch(`/employees/${employeeId}/qr-token`, { method: "POST" });
      if (res.ok) {
        const data = await res.json().catch(() => ({}));
        setQrTokens((prev) => ({ ...prev, [employeeId]: data.qr_token ?? data.token ?? "GENERATED" }));
        addToast("QR token generated (expires in 60s)", "success");
      } else {
        addToast("Failed to generate QR token", "error");
      }
    } finally {
      setGeneratingQR(null);
    }
  };

  const handleApproveLeave = async (leaveId: number, action: "approved" | "rejected") => {
    try {
      const res = await apiFetch(`/admin/${countryCode}/employees/leave-requests/${leaveId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: action }),
      });
      if (res.ok) {
        addToast(`Leave request ${action}`, "success");
        setLeaveRequests((prev) =>
          prev.map((lr) => (lr.id === leaveId ? { ...lr, status: action } : lr))
        );
      } else {
        addToast("Failed to update leave request", "error");
      }
    } catch {
      addToast("Network error", "error");
    }
  };

  const handleCreateLeave = async () => {
    if (!leaveForm.employee_id || !leaveForm.start_date || !leaveForm.end_date) {
      addToast("Employee, start date, and end date are required", "error");
      return;
    }
    setSubmittingLeave(true);
    try {
      const res = await apiFetch(`/admin/${countryCode}/employees/leave-requests`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          employee_id: parseInt(leaveForm.employee_id),
          leave_type: leaveForm.leave_type,
          start_date: leaveForm.start_date,
          end_date: leaveForm.end_date,
          notes: leaveForm.notes || undefined,
        }),
      });
      if (res.ok) {
        const data = await res.json().catch(() => ({}));
        addToast("Leave request submitted", "success");
        setShowLeaveForm(false);
        setLeaveForm({ employee_id: "", leave_type: "annual", start_date: "", end_date: "", notes: "" });
        loadData();
        if (data?.id) {
          setLeaveRequests((prev) => [data, ...prev]);
        }
      } else {
        const err = await res.json().catch(() => ({}));
        addToast(err.detail ?? "Failed to create leave request", "error");
      }
    } catch {
      addToast("Network error", "error");
    } finally {
      setSubmittingLeave(false);
    }
  };

  const handleCreateShift = async () => {
    if (!shiftForm.employee_id || !shiftForm.shift_date || !shiftForm.start_time || !shiftForm.end_time) {
      addToast("Employee, date, start time, and end time are required", "error");
      return;
    }
    setSubmittingShift(true);
    try {
      const res = await apiFetch(`/admin/${countryCode}/employees/shifts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          employee_id: parseInt(shiftForm.employee_id),
          shift_date: shiftForm.shift_date,
          start_time: shiftForm.start_time,
          end_time: shiftForm.end_time,
          shift_type: shiftForm.shift_type,
          status: shiftForm.status,
        }),
      });
      if (res.ok) {
        const data = await res.json().catch(() => ({}));
        addToast("Shift assigned", "success");
        setShowShiftForm(false);
        setShiftForm({ employee_id: "", shift_date: "", start_time: "09:00", end_time: "17:00", shift_type: "scheduled", status: "scheduled" });
        loadData();
        if (data?.id) {
          setShifts((prev) => [data, ...prev]);
        }
      } else {
        const err = await res.json().catch(() => ({}));
        addToast(err.detail ?? "Failed to create shift", "error");
      }
    } catch {
      addToast("Network error", "error");
    } finally {
      setSubmittingShift(false);
    }
  };

  const handleCreateDoc = async () => {
    if (!docForm.employee_id || !docForm.document_type || !docForm.document_name || !docForm.file_url) {
      addToast("All document fields are required", "error");
      return;
    }
    setSubmittingDoc(true);
    try {
      const res = await apiFetch(`/admin/${countryCode}/employees/${docForm.employee_id}/documents`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          document_type: docForm.document_type,
          document_name: docForm.document_name,
          file_url: docForm.file_url,
          expires_at: docForm.expires_at || undefined,
          notes: docForm.notes || undefined,
        }),
      });
      if (res.ok) {
        addToast("Document uploaded", "success");
        setShowDocForm(false);
        setDocForm({ employee_id: "", document_type: "", document_name: "", file_url: "", expires_at: "", notes: "" });
        setSelectedDocEmployeeId(null);
        if (selectedDocEmployeeId) {
          loadEmployeeDocs(selectedDocEmployeeId);
        }
      } else {
        const err = await res.json().catch(() => ({}));
        addToast(err.detail ?? "Failed to upload document", "error");
      }
    } catch {
      addToast("Network error", "error");
    } finally {
      setSubmittingDoc(false);
    }
  };

  const loadEmployeeDocs = async (employeeId: number) => {
    try {
      const res = await apiFetch(`/admin/${countryCode}/employees/${employeeId}/documents`);
      if (res.ok) {
        const data = await res.json().catch(() => []);
        if (Array.isArray(data)) {
          setEmployeeDocs((prev) => ({ ...prev, [employeeId]: data }));
        }
      }
    } catch {
      // silent
    }
  };

  const exportAuditLogs = useCallback(async () => {
    try {
      const res = await apiFetch(`/audit/export?date_from=${(() => { const d = new Date(); d.setDate(d.getDate() - 30); return d.toISOString().split("T")[0]; })()}`);
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `audit-logs-${new Date().toISOString().split("T")[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
        addToast("Audit logs exported", "success");
      } else {
        addToast("Failed to export audit logs", "error");
      }
    } catch {
      addToast("Network error", "error");
    }
  }, [addToast, countryCode]);

  const checkCoi = useCallback(async (employeeId: number) => {
    setCoiEmployeeId(employeeId);
    setCoiLoading(true);
    try {
      const res = await apiFetch(`/hr/${employeeId}/coi-check`);
      if (res.ok) {
        const data = await res.json().catch(() => ({}));
        setCoiConflicts(Array.isArray(data?.conflicts) ? data.conflicts : []);
      }
    } catch {
      addToast("Failed to check COI", "error");
    } finally {
      setCoiLoading(false);
    }
  }, [addToast, countryCode]);

  async function loadPayrollData() {
    if (tab !== "payroll") return;
    if (!countryCode || countryCode === "*") {
      setPayroll(null);
      return;
    }
    try {
      const res = await apiFetch(`/admin/treasury/payroll/equity`);
      if (res.ok) {
        const data = await res.json().catch(() => null);
        if (data && typeof data === "object") {
          setPayroll({
            employee_count: Number(data.employee_count) || 0,
            total_gross: Number(data.total_gross) || 0,
            total_tax: Number(data.total_tax) || 0,
            total_net: Number(data.total_net) || 0,
          });
        }
      } else {
        setPayroll(null);
      }
    } catch {
      setPayroll(null);
    }
  }

  const loadAttendanceForEmployee = useCallback(async (employeeId: number) => {
    try {
      const res = await apiFetch(`/admin/${countryCode}/employees/${employeeId}/attendance?limit=30`);
      if (res.ok) {
        const data = await res.json().catch(() => []);
        if (Array.isArray(data)) {
          setAttendance(data);
        }
      }
    } catch {
      addToast("Failed to load attendance", "error");
    }
  }, [addToast]);

  // Filtered employees
  const filteredEmployees = useMemo(() => {
    let list = employees;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      list = list.filter(
        (e) =>
          e.employee_code?.toLowerCase().includes(q) ||
          (e.full_name ?? e.name ?? "").toLowerCase().includes(q) ||
          e.email?.toLowerCase().includes(q) ||
          e.department?.toLowerCase().includes(q) ||
          e.position?.toLowerCase().includes(q)
      );
    }
    if (statusFilter !== "all") {
      list = list.filter((e) => e.employment_status === statusFilter);
    }
    if (deptFilter !== "all") {
      list = list.filter((e) => e.department === deptFilter);
    }
    return list;
  }, [employees, searchQuery, statusFilter, deptFilter]);

  const departments = useMemo(() => {
    const depts = new Set(employees.map((e) => e.department).filter(Boolean) as string[]);
    return Array.from(depts).sort();
  }, [employees]);

  // Stats
  const stats = useMemo(() => ({
    total: employees.length,
    active: employees.filter((e) => e.employment_status === "active").length,
    onLeave: leaveRequests.filter((lr) => lr.status === "approved").length,
    pendingLeave: leaveRequests.filter((lr) => lr.status === "pending").length,
    offices: offices.length,
  }), [employees, leaveRequests, offices]);

  const employeeColumns = useMemo<Array<EnterpriseColumn<Employee>>>(() => [
    {
      key: "employee_code",
      label: "Code",
      width: "100px",
      render: (e) => (
        <span className="font-mono text-[11px] text-text-muted bg-glass-mid border border-glass-border rounded px-1.5 py-0.5">
          {e.employee_code}
        </span>
      ),
    },
    {
      key: "full_name",
      label: "Employee",
      render: (e) => {
        const name = e.full_name ?? e.name ?? "—";
        return (
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary/30 to-primary/10 text-primary font-bold text-xs">
              {name.charAt(0).toUpperCase()}
            </div>
            <div>
              <p className="font-semibold text-text text-sm">{name}</p>
              <p className="text-[10px] text-text-muted">{e.email ?? "—"}</p>
            </div>
          </div>
        );
      },
    },
    {
      key: "position",
      label: "Role",
      render: (e) => (
        <div>
          <p className="text-[12px] text-text">{e.position ?? "—"}</p>
          {e.department && (
            <p className="text-[10px] text-text-faint">{e.department}</p>
          )}
        </div>
      ),
    },
    {
      key: "office",
      label: "Office",
      render: (e) => (
        <span className="text-[11px] text-text-muted">{e.office ?? "—"}</span>
      ),
    },
    {
      key: "employment_status",
      label: "Status",
      render: (e) => <StatusBadge status={e.employment_status} />,
    },
    {
      key: "salary",
      label: "Salary",
      render: (e) =>
        e.salary ? (
          <span className="text-[12px] font-mono text-text">
            {e.currency} {e.salary.toLocaleString()}
          </span>
        ) : (
          <span className="text-text-faint text-[11px]">—</span>
        ),
    },
  ], []);

  if (isLoading || loading) {
    return (
      <PanelLoadingState count={4} />
    );
  }

  return (
    <PanelContent className="space-y-5">

        {/* Metric cards */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          <div className="theme-card rounded-xl border p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-glass-mid text-primary">
                <Users className="h-4 w-4" />
              </div>
              <span className="text-xs text-text-muted font-medium">Total Employees</span>
            </div>
            <p className="text-2xl font-bold text-text">{stats.total}</p>
            <p className="mt-1 text-[11px] text-text-faint">All employment types</p>
          </div>
          <div className="theme-card rounded-xl border p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-glass-mid text-success">
                <CheckCircle2 className="h-4 w-4" />
              </div>
              <span className="text-xs text-text-muted font-medium">Active</span>
            </div>
            <p className="text-2xl font-bold text-text">{stats.active}</p>
            <p className="mt-1 text-[11px] text-text-faint">Currently working</p>
          </div>
          <div className="theme-card rounded-xl border p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-glass-mid text-warning">
                <Calendar className="h-4 w-4" />
              </div>
              <span className="text-xs text-text-muted font-medium">On Leave</span>
            </div>
            <p className="text-2xl font-bold text-text">{stats.onLeave}</p>
            <p className="mt-1 text-[11px] text-text-faint">Approved leaves</p>
          </div>
          <div className="theme-card rounded-xl border p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-glass-mid text-warning">
                <AlertCircle className="h-4 w-4" />
              </div>
              <span className="text-xs text-text-muted font-medium">Pending Leaves</span>
            </div>
            <p className="text-2xl font-bold text-text">{stats.pendingLeave}</p>
            <p className="mt-1 text-[11px] text-text-faint">Awaiting approval</p>
          </div>
          <div className="theme-card rounded-xl border p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-glass-mid text-info">
                <Building2 className="h-4 w-4" />
              </div>
              <span className="text-xs text-text-muted font-medium">Offices</span>
            </div>
            <p className="text-2xl font-bold text-text">{stats.offices}</p>
            <p className="mt-1 text-[11px] text-text-faint">Active locations</p>
          </div>
        </div>

        {/* Tab navigation */}
        <PanelTabs
          items={[
            { key: "directory", label: "Directory", icon: Users },
            { key: "offices", label: "Offices", icon: Building2 },
            { key: "attendance", label: "Attendance", icon: Clock },
            { key: "leaves", label: "Leave Requests", icon: Calendar },
            { key: "shifts", label: "Shift Rosters", icon: Shield },
            { key: "iam", label: "IAM & QR", icon: QrCode },
            { key: "payroll", label: "Payroll", icon: DollarSign },
            { key: "documents", label: "Documents", icon: FileText },
            { key: "coi", label: "COI Engine", icon: AlertTriangle },
            { key: "communications", label: "Comms Suite", icon: MessageCircle },
            { key: "addresses", label: "Addresses", icon: MapPin },
            { key: "performance", label: "Performance", icon: TrendingUp },
            { key: "disciplinary", label: "Disciplinary", icon: AlertTriangle },
            { key: "hse", label: "HSE", icon: Shield },
            { key: "alumni", label: "Alumni", icon: Users },
            { key: "insurance", label: "Insurance", icon: Shield },
            { key: "dei", label: "DEI", icon: BarChart3 },
            { key: "audit", label: "Audit Trail", icon: Activity },
          ]}
          value={tab}
          onChange={handleTabChange}
        />

        {/* ─── DIRECTORY TAB ─── */}
        {tab === "directory" && (
          <section className="space-y-4">
            {/* Toolbar */}
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-2 flex-1">
                <div className="relative flex-1 max-w-xs">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-text-faint" />
                  <input
                    type="text"
                    placeholder="Search employees..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full rounded-lg border border-glass-border bg-glass-mid pl-8 pr-3 py-2 text-xs text-text placeholder:text-text-faint outline-none focus:border-primary/50"
                  />
                </div>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="rounded-lg border border-glass-border bg-glass-mid px-2 py-2 text-xs text-text outline-none"
                >
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="terminated">Terminated</option>
                </select>
                {departments.length > 0 && (
                  <select
                    value={deptFilter}
                    onChange={(e) => setDeptFilter(e.target.value)}
                    className="rounded-lg border border-glass-border bg-glass-mid px-2 py-2 text-xs text-text outline-none"
                  >
                    <option value="all">All Departments</option>
                    {departments.map((d) => (
                      <option key={d} value={d}>{d}</option>
                    ))}
                  </select>
                )}
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={loadData}
                  className="rounded-lg border border-glass-border p-2 text-text-muted hover:text-text transition-colors"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                </button>
                <Button size="sm" onClick={() => setShowAddEmployee(true)}>
                  <Plus className="h-3.5 w-3.5" />
                  Add Employee
                </Button>
              </div>
            </div>

            {/* Table */}
            {filteredEmployees.length === 0 ? (
              <EmptyState 
                icon={Users} 
                title="No employees found" 
                description="Try adjusting your search or filters"
              />
            ) : (
              <>
                <Table>
                  <TableHeader>
                    <TableHeaderCell>Code</TableHeaderCell>
                    <TableHeaderCell>Employee</TableHeaderCell>
                    <TableHeaderCell>Role</TableHeaderCell>
                    <TableHeaderCell>Office</TableHeaderCell>
                    <TableHeaderCell>Status</TableHeaderCell>
                    <TableHeaderCell>Salary</TableHeaderCell>
                    <TableHeaderCell>Actions</TableHeaderCell>
                  </TableHeader>
                  <TableBody>
                    {filteredEmployees.map((employee) => (
                      <TableRow key={employee.id}>
                        <TableCell>
                          <span className="font-mono text-[11px] text-text-muted bg-glass-mid border border-glass-border rounded px-1.5 py-0.5">
                            {employee.employee_code}
                          </span>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2.5">
                            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary/30 to-primary/10 text-primary font-bold text-xs">
                              {(employee.full_name ?? employee.name ?? "").charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <p className="font-semibold text-text text-sm">{employee.full_name ?? employee.name ?? "—"}</p>
                              <p className="text-[10px] text-text-muted">{employee.email ?? "—"}</p>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="text-[12px] text-text">{employee.position ?? "—"}</p>
                            {employee.department && (
                              <p className="text-[10px] text-text-faint">{employee.department}</p>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <span className="text-[11px] text-text-muted">{employee.office ?? "—"}</span>
                        </TableCell>
                        <TableCell>
                          <StatusBadge status={employee.employment_status} />
                        </TableCell>
                        <TableCell>
                          {employee.salary ? (
                            <span className="text-[12px] font-mono text-text">
                              {employee.currency} {employee.salary.toLocaleString()}
                            </span>
                          ) : (
                            <span className="text-text-faint text-[11px]">—</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1.5">
                            <Button variant="secondary" className="rounded-md border border-glass-border px-2 py-1 text-[10px] font-medium text-text-muted hover:text-primary transition-colors" onClick={() => setSelectedEmployee(employee)}
                            >
                              View
                            </Button>
                            <Button variant="secondary" className="rounded-md border border-glass-border px-2 py-1 text-[10px] font-medium text-text-muted hover:text-primary transition-colors" onClick={() => handleGenerateQR(employee.id)}
                              disabled={generatingQR === employee.id}
                              title="Generate QR Token"
                            >
                              {generatingQR === employee.id ? (
                                <Loader2 className="h-3 w-3 animate-spin" />
                              ) : (
                                <QrCode className="h-3 w-3" />
                              )}
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>

                {/* Employee count */}
                <p className="text-[11px] text-text-faint text-right">
                  Showing {filteredEmployees.length} of {employees.length} employees
                </p>
              </>
            )}
          </section>
        )}

        {/* ─── OFFICES TAB ─── */}
        {tab === "offices" && (
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-text">Office Locations</h3>
              <Button size="sm" onClick={() => setShowAddOffice(true)}>
                <Plus className="h-3.5 w-3.5" />
                Add Office
              </Button>
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {offices.map((office) => (
                <div key={office.id} className="rounded-lg border border-glass-border bg-glass-panel p-4 space-y-2">
                  <div className="flex items-center gap-2">
                    <Building2 className="h-4 w-4 text-primary" />
                    <span className="font-semibold text-text text-sm">{office.name}</span>
                  </div>
                  <p className="text-[11px] text-text-muted">
                    {office.city ?? "—"}, {office.country_code}
                  </p>
                  {office.address && <p className="text-[10px] text-text-faint">{office.address}</p>}
                  <StatusBadge status={office.is_active ? "active" : "inactive"} />
                </div>
              ))}
            </div>
          </section>
        )}

        {/* ─── ATTENDANCE TAB ─── */}
        {tab === "attendance" && (
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-text">Attendance Records</h3>
              <div className="flex items-center gap-2">
                <select className="rounded-lg border border-glass-border bg-glass-mid px-2 py-1.5 text-xs text-text outline-none">
                  <option>All Employees</option>
                  {employees.map(e => (
                    <option key={e.id} value={e.id}>{e.full_name ?? e.name}</option>
                  ))}
                </select>
                <Button size="sm" onClick={() => {}}>
                  <RefreshCw className="h-3.5 w-3.5" />
                  Refresh
                </Button>
              </div>
            </div>
            <div className="rounded-lg border border-glass-border bg-glass-panel overflow-hidden">
              <Table>
                <TableHeader>
                  <TableHeaderCell>Employee</TableHeaderCell>
                  <TableHeaderCell>Date</TableHeaderCell>
                  <TableHeaderCell>Scan In</TableHeaderCell>
                  <TableHeaderCell>Scan Out</TableHeaderCell>
                  <TableHeaderCell>Hours</TableHeaderCell>
                  <TableHeaderCell>Status</TableHeaderCell>
                </TableHeader>
                <TableBody>
                  {attendance.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6}>
                        <EmptyState icon={Clock} title="No attendance records" description="Select an employee to view attendance" />
                      </TableCell>
                    </TableRow>
                  ) : attendance.map((rec) => (
                    <TableRow key={rec.id}>
                      <TableCell className="text-xs text-text">
                        {employees.find(e => e.id === rec.employee_id)?.full_name ?? `#${rec.employee_id}`}
                      </TableCell>
                      <TableCell className="text-xs text-text-muted">{rec.date}</TableCell>
                      <TableCell className="text-xs text-text-muted">{rec.scan_in_time ?? "—"}</TableCell>
                      <TableCell className="text-xs text-text-muted">{rec.scan_out_time ?? "—"}</TableCell>
                      <TableCell className="text-xs font-mono text-text">{rec.hours_worked ? `${rec.hours_worked.toFixed(1)}h` : "—"}</TableCell>
                      <TableCell><StatusBadge status={rec.is_anomaly ? "anomaly" : rec.status} /></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {/* ─── LEAVES TAB ─── */}
        {tab === "leaves" && (
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-text">Leave Requests</h3>
              <Button size="sm" onClick={() => setShowLeaveForm(true)}>
                <Plus className="h-3.5 w-3.5" />
                New Request
              </Button>
            </div>
            <div className="rounded-lg border border-glass-border bg-glass-panel overflow-hidden">
              <Table>
                <TableHeader>
                  <TableHeaderCell>Employee</TableHeaderCell>
                  <TableHeaderCell>Type</TableHeaderCell>
                  <TableHeaderCell>Start</TableHeaderCell>
                  <TableHeaderCell>End</TableHeaderCell>
                  <TableHeaderCell>Days</TableHeaderCell>
                  <TableHeaderCell>Status</TableHeaderCell>
                  <TableHeaderCell>Actions</TableHeaderCell>
                </TableHeader>
                <TableBody>
                  {leaveRequests.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7}>
                        <EmptyState icon={Calendar} title="No leave requests" description="Leave requests will appear here" />
                      </TableCell>
                    </TableRow>
                  ) : leaveRequests.map((lr) => (
                    <TableRow key={lr.id}>
                      <TableCell className="text-xs text-text">{lr.employee_name ?? `#${lr.employee_id}`}</TableCell>
                      <TableCell className="text-xs text-text-muted capitalize">{lr.leave_type}</TableCell>
                      <TableCell className="text-xs text-text-muted">{lr.start_date}</TableCell>
                      <TableCell className="text-xs text-text-muted">{lr.end_date}</TableCell>
                      <TableCell className="text-xs font-mono text-text">{lr.days_requested}</TableCell>
                      <TableCell><StatusBadge status={lr.status} /></TableCell>
                      <TableCell>
                        {lr.status === "pending" && (
                          <div className="flex items-center gap-1">
                            <Button variant="primary" className="rounded-md border border-success px-2 py-1 text-[10px] text-success transition-colors" onClick={() => handleApproveLeave(lr.id, "approved")}>Approve</Button>
                            <Button variant="danger" className="rounded-md border border-danger/30 px-2 py-1 text-[10px] text-danger transition-colors" onClick={() => handleApproveLeave(lr.id, "rejected")}>Reject</Button>
                          </div>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {/* ─── SHIFTS TAB ─── */}
        {tab === "shifts" && (
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-text">Shift Rosters</h3>
              <Button size="sm" onClick={() => setShowShiftForm(true)}>
                <Plus className="h-3.5 w-3.5" />
                Assign Shift
              </Button>
            </div>
            <div className="rounded-lg border border-glass-border bg-glass-panel overflow-hidden">
              <Table>
                <TableHeader>
                  <TableHeaderCell>Employee</TableHeaderCell>
                  <TableHeaderCell>Date</TableHeaderCell>
                  <TableHeaderCell>Start</TableHeaderCell>
                  <TableHeaderCell>End</TableHeaderCell>
                  <TableHeaderCell>Type</TableHeaderCell>
                  <TableHeaderCell>Status</TableHeaderCell>
                </TableHeader>
                <TableBody>
                  {shifts.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6}>
                        <EmptyState icon={Shield} title="No shifts assigned" description="Assign shifts to employees" />
                      </TableCell>
                    </TableRow>
                  ) : shifts.map((s) => (
                    <TableRow key={s.id}>
                      <TableCell className="text-xs text-text">{s.employee_name ?? `#${s.employee_id}`}</TableCell>
                      <TableCell className="text-xs text-text-muted">{s.shift_date}</TableCell>
                      <TableCell className="text-xs font-mono text-text">{s.start_time}</TableCell>
                      <TableCell className="text-xs font-mono text-text">{s.end_time}</TableCell>
                      <TableCell className="text-xs text-text-muted capitalize">{s.shift_type}</TableCell>
                      <TableCell><StatusBadge status={s.status} /></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {/* ─── IAM & QR TAB ─── */}
        {tab === "iam" && (
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-text">IAM & QR Access Control</h3>
              <Button size="sm" onClick={() => {}}>
                <RefreshCw className="h-3.5 w-3.5" />
                Sync Directory
              </Button>
            </div>
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <div className="rounded-lg border border-glass-border bg-glass-panel p-4 space-y-3">
                <div className="flex items-center gap-2">
                  <QrCode className="h-5 w-5 text-primary" />
                  <h4 className="text-sm font-semibold text-text">QR Authentication</h4>
                </div>
                <p className="text-[11px] text-text-muted">Generate and manage QR tokens for secure doorless access and attendance scanning.</p>
                <div className="space-y-2">
                  {employees.slice(0, 10).map((emp) => (
                    <div key={emp.id} className="flex items-center justify-between rounded-md border border-glass-border bg-glass-mid p-2">
                      <span className="text-xs text-text">{emp.full_name ?? emp.name}</span>
                      <button
                        onClick={() => handleGenerateQR(emp.id)}
                        disabled={generatingQR === emp.id}
                        className="rounded-md border border-glass-border px-2 py-1 text-[10px] text-text-muted hover:text-primary transition-colors"
                      >
                        {generatingQR === emp.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <QrCode className="h-3 w-3" />}
                      </button>
                    </div>
                  ))}
                </div>
                {employees.length > 10 && (
                  <p className="text-[10px] text-text-faint text-center">+{employees.length - 10} more employees</p>
                )}
              </div>
              <div className="rounded-lg border border-glass-border bg-glass-panel p-4 space-y-3">
                <div className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-primary" />
                  <h4 className="text-sm font-semibold text-text">Access Policies</h4>
                </div>
                <p className="text-[11px] text-text-muted">Role-based access rules, MFA enforcement, and identity provider configuration.</p>
                <div className="space-y-2">
                  <div className="flex items-center justify-between rounded-md border border-glass-border bg-glass-mid p-2">
                    <span className="text-xs text-text">MFA Enforcement</span>
                    <StatusBadge status="active" />
                  </div>
                  <div className="flex items-center justify-between rounded-md border border-glass-border bg-glass-mid p-2">
                    <span className="text-xs text-text">SSO (SAML/OIDC)</span>
                    <StatusBadge status="active" />
                  </div>
                  <div className="flex items-center justify-between rounded-md border border-glass-border bg-glass-mid p-2">
                    <span className="text-xs text-text">Password Policy</span>
                    <StatusBadge status="active" />
                  </div>
                  <div className="flex items-center justify-between rounded-md border border-glass-border bg-glass-mid p-2">
                    <span className="text-xs text-text">QR Token Lifetime</span>
                    <span className="text-[10px] text-text-muted">60 seconds</span>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* ─── PAYROLL TAB ─── */}
        {tab === "payroll" && (
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-text">Payroll Management</h3>
              <div className="flex items-center gap-2">
                <Button size="sm" onClick={() => {}}>
                  <Download className="h-3.5 w-3.5" />
                  Export
                </Button>
                <Button size="sm">Run Payroll</Button>
              </div>
            </div>
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
              <div className="rounded-lg border border-glass-border bg-glass-panel p-4 space-y-2">
                <span className="text-[10px] text-text-faint font-medium uppercase tracking-wider">Total Gross Payroll</span>
                <p className="text-2xl font-bold text-text">{currency} {payroll ? payroll.total_gross.toLocaleString(undefined, { maximumFractionDigits: 2 }) : "—"}</p>
                <p className="text-[10px] text-text-faint">Current month</p>
              </div>
              <div className="rounded-lg border border-glass-border bg-glass-panel p-4 space-y-2">
                <span className="text-[10px] text-text-faint font-medium uppercase tracking-wider">Active Employees</span>
                <p className="text-2xl font-bold text-text">{payroll ? payroll.employee_count : stats.active}</p>
                <p className="text-[10px] text-text-faint">Receiving salary</p>
              </div>
              <div className="rounded-lg border border-glass-border bg-glass-panel p-4 space-y-2">
                <span className="text-[10px] text-text-faint font-medium uppercase tracking-wider">Net Payroll</span>
                <p className="text-2xl font-bold text-text">{currency} {payroll ? payroll.total_net.toLocaleString(undefined, { maximumFractionDigits: 2 }) : "—"}</p>
                <p className="text-[10px] text-text-faint">After tax</p>
              </div>
            </div>
            <div className="rounded-lg border border-glass-border bg-glass-panel overflow-hidden">
              <Table>
                <TableHeader>
                  <TableHeaderCell>Employee</TableHeaderCell>
                  <TableHeaderCell>Salary</TableHeaderCell>
                  <TableHeaderCell>Currency</TableHeaderCell>
                  <TableHeaderCell>Department</TableHeaderCell>
                  <TableHeaderCell>Status</TableHeaderCell>
                </TableHeader>
                <TableBody>
                  {employees.filter(e => e.salary).length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5}>
                        <EmptyState icon={DollarSign} title="No payroll data" description="Connect payroll to view salary information" />
                      </TableCell>
                    </TableRow>
                  ) : employees.filter(e => e.salary).map((emp) => (
                    <TableRow key={emp.id}>
                      <TableCell className="text-xs text-text">{emp.full_name ?? emp.name}</TableCell>
                      <TableCell className="text-xs font-mono text-text">{emp.salary?.toLocaleString()}</TableCell>
                      <TableCell className="text-xs text-text-muted">{emp.currency}</TableCell>
                      <TableCell className="text-xs text-text-muted">{emp.department ?? "—"}</TableCell>
                      <TableCell><StatusBadge status={emp.employment_status} /></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {/* ─── DOCUMENTS TAB ─── */}
        {tab === "documents" && (
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-text">Employee Documents</h3>
              <div className="flex items-center gap-2">
                <select
                  value={selectedDocEmployeeId ?? ""}
                  onChange={(e) => {
                    const id = parseInt(e.target.value);
                    setSelectedDocEmployeeId(id);
                    if (id) loadEmployeeDocs(id);
                  }}
                  className="rounded-lg border border-glass-border bg-glass-mid px-2 py-1.5 text-xs text-text outline-none"
                >
                  <option value="">Select Employee</option>
                  {employees.map(e => (
                    <option key={e.id} value={e.id}>{e.full_name ?? e.name}</option>
                  ))}
                </select>
                <Button size="sm" onClick={() => setShowDocForm(true)} disabled={!selectedDocEmployeeId}>
                  <Plus className="h-3.5 w-3.5" />
                  Upload
                </Button>
              </div>
            </div>
            <div className="rounded-lg border border-glass-border bg-glass-panel overflow-hidden">
              <Table>
                <TableHeader>
                  <TableHeaderCell>Name</TableHeaderCell>
                  <TableHeaderCell>Type</TableHeaderCell>
                  <TableHeaderCell>Expires</TableHeaderCell>
                  <TableHeaderCell>Notes</TableHeaderCell>
                </TableHeader>
                <TableBody>
                  {!selectedDocEmployeeId || !employeeDocs[selectedDocEmployeeId]?.length ? (
                    <TableRow>
                      <TableCell colSpan={4}>
                        <EmptyState icon={FileText} title="No documents" description="Select an employee and upload documents" />
                      </TableCell>
                    </TableRow>
                  ) : employeeDocs[selectedDocEmployeeId].map((doc: any, i: number) => (
                    <TableRow key={doc.id ?? i}>
                      <TableCell className="text-xs text-text">{doc.document_name}</TableCell>
                      <TableCell className="text-xs text-text-muted capitalize">{doc.document_type}</TableCell>
                      <TableCell className="text-xs text-text-muted">{doc.expires_at ?? "—"}</TableCell>
                      <TableCell className="text-xs text-text-faint">{doc.notes ?? "—"}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>
        )}

        {/* ─── COI ENGINE TAB ─── */}
        {tab === "coi" && (
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-text">Conflict of Interest Engine</h3>
              <div className="flex items-center gap-2">
                <select
                  value={coiEmployeeId ?? ""}
                  onChange={(e) => {
                    const id = parseInt(e.target.value);
                    setCoiEmployeeId(id);
                    if (id) checkCoi(id);
                  }}
                  className="rounded-lg border border-glass-border bg-glass-mid px-2 py-1.5 text-xs text-text outline-none"
                >
                  <option value="">Select Employee</option>
                  {employees.map(e => (
                    <option key={e.id} value={e.id}>{e.full_name ?? e.name}</option>
                  ))}
                </select>
              </div>
            </div>
            {coiLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-text-muted" />
              </div>
            ) : coiConflicts.length > 0 ? (
              <div className="space-y-2">
                {coiConflicts.map((c: any, i: number) => (
                  <div key={i} className="rounded-lg border border-danger/30 bg-danger/5 p-3 flex items-start gap-3">
                    <AlertTriangle className="h-4 w-4 text-danger shrink-0 mt-0.5" />
                    <div>
                      <p className="text-xs font-medium text-danger">{c.type ?? "Conflict Detected"}</p>
                      <p className="text-[10px] text-text-muted mt-0.5">{c.description ?? JSON.stringify(c)}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : coiEmployeeId ? (
              <div className="rounded-lg border border-success bg-success/5 p-4 flex items-center gap-3">
                <Check className="h-4 w-4 text-success" />
                <span className="text-xs text-success">No conflicts of interest found for this employee</span>
              </div>
            ) : (
              <EmptyState icon={AlertTriangle} title="COI Check" description="Select an employee to run a conflict of interest check" />
            )}
          </section>
        )}

        {/* ─── COMMUNICATIONS TAB ─── */}
        {tab === "communications" && (
          <CommunicationsTab employees={employees} addToast={addToast} />
        )}

        {/* ─── ADDRESSES TAB ─── */}
        {tab === "addresses" && (
          <AddressMatrixTab employees={employees} addToast={addToast} />
        )}

        {/* ─── PERFORMANCE TAB ─── */}
        {tab === "performance" && (
          <PerformanceTab employees={employees} addToast={addToast} />
        )}

        {/* ─── DISCIPLINARY TAB ─── */}
        {tab === "disciplinary" && (
          <DisciplinaryOffboardingTab employees={employees} addToast={addToast} />
        )}

        {/* ─── HSE TAB ─── */}
        {tab === "hse" && (
          <HseTab employees={employees} addToast={addToast} />
        )}

        {/* ─── ALUMNI TAB ─── */}
        {tab === "alumni" && (
          <AlumniContractorTab employees={employees} addToast={addToast} />
        )}

        {/* ─── INSURANCE TAB ─── */}
        {tab === "insurance" && (
          <InsuranceBenefitsTab employees={employees} addToast={addToast} />
        )}

        {/* ─── DEI TAB ─── */}
        {tab === "dei" && (
          <DEITab addToast={addToast} />
        )}

        {/* ─── AUDIT TRAIL TAB ─── */}
        {tab === "audit" && (
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-text">Audit Trail</h3>
              <div className="flex items-center gap-2">
                <Button size="sm" onClick={loadAuditLogs}>
                  <RefreshCw className="h-3.5 w-3.5" />
                </Button>
                <Button size="sm" onClick={exportAuditLogs}>
                  <Download className="h-3.5 w-3.5" />
                  Export
                </Button>
              </div>
            </div>
            <div className="rounded-lg border border-glass-border bg-glass-panel overflow-hidden">
              <Table>
                <TableHeader>
                  <TableHeaderCell>Timestamp</TableHeaderCell>
                  <TableHeaderCell>Action</TableHeaderCell>
                  <TableHeaderCell>Entity</TableHeaderCell>
                  <TableHeaderCell>Details</TableHeaderCell>
                  <TableHeaderCell>User</TableHeaderCell>
                </TableHeader>
                <TableBody>
                  {auditLoading ? (
                    <TableRow>
                      <TableCell colSpan={5}>
                        <div className="flex items-center justify-center py-8">
                          <Loader2 className="h-5 w-5 animate-spin text-text-muted" />
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : auditLogs.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5}>
                        <EmptyState icon={Activity} title="No audit logs" description="Audit events will appear here as actions are performed" />
                      </TableCell>
                    </TableRow>
                  ) : auditLogs.map((log: any, i: number) => (
                    <TableRow key={log.id ?? i}>
                      <TableCell className="text-[10px] text-text-muted whitespace-nowrap">{log.created_at ?? log.timestamp}</TableCell>
                      <TableCell className="text-xs text-text capitalize">{log.action ?? log.event_type}</TableCell>
                      <TableCell className="text-xs text-text-muted">{log.entity_type ?? log.resource_type}</TableCell>
                      <TableCell className="text-[10px] text-text-faint max-w-[200px] truncate">{log.details ?? log.description ?? "—"}</TableCell>
                      <TableCell className="text-xs text-text-muted">{log.user_name ?? log.user_id ?? "—"}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            {auditTotal > 0 && (
              <div className="flex items-center justify-between">
                <p className="text-[10px] text-text-faint">{auditTotal} total entries</p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setAuditPage((p) => Math.max(1, p - 1))}
                    disabled={auditPage <= 1}
                    className="rounded-md border border-glass-border px-2 py-1 text-[10px] text-text-muted disabled:opacity-30"
                  >
                    Previous
                  </button>
                  <span className="text-[10px] text-text-faint">Page {auditPage}</span>
                  <button
                    onClick={() => setAuditPage((p) => p + 1)}
                    disabled={auditPage * 50 >= auditTotal}
                    className="rounded-md border border-glass-border px-2 py-1 text-[10px] text-text-muted disabled:opacity-30"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </section>
        )}

      </PanelContent>
  );
}

