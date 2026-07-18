"use client";

import { Button } from "@/components/ui/Button";

import { useEffect, useMemo, useState, Suspense, type MouseEvent } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";

import { Shield, UserPlus, AlertCircle, Network } from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import BulkActionBar from "@/components/BulkActionBar";
import { PanelContent, PanelLoadingState, PanelTabs } from "@/components/PanelPage";
import HierarchyTab from "../dashboard/tabs/HierarchyTab";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { dc, useDensity } from "@/lib/densityContext";
import { EnterpriseDataTable, type EnterpriseColumn } from "@shared/components/EnterpriseDataTable";
import {
  ADMIN_PERMISSION_MAP,
  STAFF_PERMISSION_GROUPS,
  hasAdminPermission,
  isAdminStaffRole,
  type StaffPermissionGroup,
} from "@shared/adminPermissions";

const MotionDiv = motion.div as any;

type StaffRole = "admin" | "sub_admin" | "moderator" | "support";

interface StaffUser {
  id: number;
  username: string;
  full_name: string;
  email: string;
  phone?: string | null;
  role: StaffRole;
  is_active: boolean;
  staff_role_label?: string | null;
  staff_title?: string | null;
  staff_department?: string | null;
  staff_area_of_operation?: string | null;
  staff_hire_date?: string | null;
  staff_experience_level?: string | null;
  staff_performance_summary?: string | null;
  staff_assigned_tasks: string[];
  staff_assigned_projects: string[];
  permissions: string[];
  staff_notes?: string | null;
  created_at: string;
}

interface PermissionCatalogResponse {
  groups: StaffPermissionGroup[];
  defaults: Record<string, string[]>;
}

interface StaffFormState {
  full_name: string;
  username: string;
  email: string;
  phone: string;
  password: string;
  role: StaffRole;
  staff_role_label: string;
  staff_title: string;
  staff_department: string;
  staff_area_of_operation: string;
  staff_hire_date: string;
  staff_experience_level: string;
  staff_performance_summary: string;
  staff_assigned_tasks: string;
  staff_assigned_projects: string;
  permissions: string[];
  staff_notes: string;
  is_active: boolean;
}

interface FeedbackState {
  tone: "success" | "error";
  text: string;
}

const ROLE_BADGE: Record<StaffRole, string> = {
  admin: "theme-chip-warning",
  sub_admin: "theme-chip-warning",
  moderator: "theme-chip-brand",
  support: "theme-chip-info",
};

const ROLE_LABELS: Record<StaffRole, string> = {
  admin: "Admin",
  sub_admin: "Sub Admin",
  moderator: "Moderator",
  support: "Support",
};

const EXPERIENCE_OPTIONS = ["Junior", "Mid-level", "Senior", "Lead", "Specialist"];

function buildEmptyStaffForm(): StaffFormState {
  return {
    full_name: "",
    username: "",
    email: "",
    phone: "",
    password: "",
    role: "moderator",
    staff_role_label: "",
    staff_title: "",
    staff_department: "",
    staff_area_of_operation: "",
    staff_hire_date: "",
    staff_experience_level: "Mid-level",
    staff_performance_summary: "",
    staff_assigned_tasks: "",
    staff_assigned_projects: "",
    permissions: [...ADMIN_PERMISSION_MAP.moderator],
    staff_notes: "",
    is_active: true,
  };
}

function parseCommaSeparated(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function formatList(value: string[] | null | undefined): string {
  return Array.isArray(value) ? value.join(", ") : "";
}

function formatDate(value: string | null | undefined): string {
  if (!value) return "Not set";
  const dateValue = new Date(value);
  if (Number.isNaN(dateValue.getTime())) return value;
  return dateValue.toLocaleDateString();
}

export function StaffContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const section = searchParams?.get("section") ?? "staff";
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();
  const role = user?.role ?? null;
  const isAdmin = role === "admin";
  const { density } = useDensity();

  const [loading, setLoading] = useState(true);
  const [staffUsers, setStaffUsers] = useState<StaffUser[]>([]);
  const [roleFilter, setRoleFilter] = useState<"all" | StaffRole>("all");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "inactive">("all");
  const [showStaffModal, setShowStaffModal] = useState(false);
  const [editingStaff, setEditingStaff] = useState<StaffUser | null>(null);
  const [viewingStaff, setViewingStaff] = useState<StaffUser | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<StaffUser | null>(null);
  const [staffForm, setStaffForm] = useState<StaffFormState>(buildEmptyStaffForm());
  const [staffSaving, setStaffSaving] = useState(false);
  const [staffError, setStaffError] = useState("");
  const [feedback, setFeedback] = useState<FeedbackState | null>(null);
  const [permissionCatalog, setPermissionCatalog] = useState<PermissionCatalogResponse>({
    groups: [...STAFF_PERMISSION_GROUPS],
    defaults: Object.fromEntries(Object.entries(ADMIN_PERMISSION_MAP).map(([key, value]) => [key, [...value]])),
  });
  const [resetTarget, setResetTarget] = useState<StaffUser | null>(null);
  const [resetPassword, setResetPassword] = useState("StaffPass123!");
  const [resettingPassword, setResettingPassword] = useState(false);
  const [selectedStaffIds, setSelectedStaffIds] = useState<Set<number>>(new Set());
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [bulkForm, setBulkForm] = useState<Partial<StaffFormState>>({});
  const [bulkSaving, setBulkSaving] = useState(false);
  const [bulkError, setBulkError] = useState("");
  const [rowActionId, setRowActionId] = useState<number | null>(null);
  const [deleteSaving, setDeleteSaving] = useState(false);

  const roles = useMemo(() => Object.keys(ROLE_LABELS) as StaffRole[], []);
  const departments = useMemo(
    () => Array.from(new Set(staffUsers.map((item) => item.staff_department?.trim()).filter(Boolean) as string[])).sort(),
    [staffUsers]
  );
  const areas = useMemo(
    () => Array.from(new Set(staffUsers.map((item) => item.staff_area_of_operation?.trim()).filter(Boolean) as string[])).sort(),
    [staffUsers]
  );

  const permissionGroups = useMemo(
    () => Object.fromEntries(permissionCatalog.groups.map((group) => [group.label, [...group.permissions]])),
    [permissionCatalog.groups]
  );

  useEffect(() => {
    if (!feedback) return;
    const timeoutId = window.setTimeout(() => setFeedback(null), 3500);
    return () => window.clearTimeout(timeoutId);
  }, [feedback]);

  useEffect(() => {
    if (authLoading) return;

    if (!isLoggedIn || !isAdminStaffRole(role)) {
      router.push("/admin/login");
      return;
    }

    if (!isAdmin && section === "staff") {
      if (hasAdminPermission(role, "hierarchy.view")) {
        router.replace(`${pathname}?section=permissions`);
      } else {
        router.replace("/admin/dashboard");
      }
      return;
    }

    const fetchStaffContext = async () => {
      if (section !== "staff" || !isAdmin) {
        setLoading(false);
        return;
      }

      try {
        const [staffRes, catalogRes] = await Promise.all([
          apiFetch("/admin/staff"),
          apiFetch("/admin/staff/permission-catalog"),
        ]);

        if (staffRes.ok) {
          const staffData = await staffRes.json();
          setStaffUsers(Array.isArray(staffData) ? staffData : []);
        } else {
          setStaffUsers([]);
          setFeedback({ tone: "error", text: "Failed to load staff directory." });
        }

        if (catalogRes.ok) {
          const catalogData = (await catalogRes.json()) as PermissionCatalogResponse;
          if (Array.isArray(catalogData.groups) && catalogData.defaults) {
            setPermissionCatalog(catalogData);
          }
        }
      } catch {
        setStaffUsers([]);
        setFeedback({ tone: "error", text: "Network error while loading staff management." });
      }

      setLoading(false);
    };

    void fetchStaffContext();
  }, [authLoading, isLoggedIn, isAdmin, role, router, section]);

  const totalStaff = staffUsers.length;
  const activeStaff = staffUsers.filter((staffMember) => staffMember.is_active).length;
  const distinctAreas = new Set(
    staffUsers.map((staffMember) => staffMember.staff_area_of_operation?.trim()).filter(Boolean)
  ).size;
  const assignedProjects = staffUsers.reduce(
    (count, staffMember) => count + staffMember.staff_assigned_projects.length,
    0
  );

  const filteredStaff = useMemo(() => {
    return staffUsers.filter((staffMember) => {
      const matchesRole = roleFilter === "all" || staffMember.role === roleFilter;
      const matchesStatus =
        statusFilter === "all" ||
        (statusFilter === "active" ? staffMember.is_active : !staffMember.is_active);
      return matchesRole && matchesStatus;
    });
  }, [roleFilter, staffUsers, statusFilter]);

  const hasBulkChanges = useMemo(() => {
    return (
      Boolean(bulkForm.role) ||
      Boolean(bulkForm.staff_role_label) ||
      Boolean(bulkForm.staff_department) ||
      Boolean(bulkForm.staff_area_of_operation) ||
      bulkForm.is_active !== undefined ||
      Boolean(bulkForm.permissions && bulkForm.permissions.length > 0)
    );
  }, [bulkForm]);

  const openCreateModal = () => {
    setEditingStaff(null);
    setStaffForm(buildEmptyStaffForm());
    setStaffError("");
    setShowStaffModal(true);
  };

  const openEditModal = (staffMember: StaffUser) => {
    setEditingStaff(staffMember);
    setStaffForm({
      full_name: staffMember.full_name,
      username: staffMember.username,
      email: staffMember.email,
      phone: staffMember.phone ?? "",
      password: "",
      role: staffMember.role,
      staff_role_label: staffMember.staff_role_label ?? "",
      staff_title: staffMember.staff_title ?? "",
      staff_department: staffMember.staff_department ?? "",
      staff_area_of_operation: staffMember.staff_area_of_operation ?? "",
      staff_hire_date: staffMember.staff_hire_date ? String(staffMember.staff_hire_date).slice(0, 10) : "",
      staff_experience_level: staffMember.staff_experience_level ?? "Mid-level",
      staff_performance_summary: staffMember.staff_performance_summary ?? "",
      staff_assigned_tasks: formatList(staffMember.staff_assigned_tasks),
      staff_assigned_projects: formatList(staffMember.staff_assigned_projects),
      permissions: [...staffMember.permissions],
      staff_notes: staffMember.staff_notes ?? "",
      is_active: staffMember.is_active,
    });
    setStaffError("");
    setShowStaffModal(true);
  };

  const closeStaffModal = () => {
    setShowStaffModal(false);
    setEditingStaff(null);
    setStaffError("");
  };

  const applyRoleDefaults = (nextRole: StaffRole) => {
    const nextPermissions = permissionCatalog.defaults[nextRole] ?? ADMIN_PERMISSION_MAP[nextRole] ?? [];
    setStaffForm((current) => ({
      ...current,
      role: nextRole,
      permissions: [...nextPermissions],
    }));
  };

  const togglePermission = (permission: string) => {
    setStaffForm((current) => {
      const next = new Set(current.permissions);
      if (next.has(permission)) next.delete(permission);
      else next.add(permission);
      return { ...current, permissions: Array.from(next) };
    });
  };

  const toggleBulkPermission = (permission: string) => {
    setBulkForm((current) => {
      const next = new Set(current.permissions ?? []);
      if (next.has(permission)) next.delete(permission);
      else next.add(permission);
      return { ...current, permissions: Array.from(next) };
    });
  };

  const saveStaff = async () => {
    setStaffSaving(true);
    setStaffError("");

    const payload = {
      full_name: staffForm.full_name.trim(),
      ...(editingStaff ? {} : { username: staffForm.username.trim(), password: staffForm.password }),
      email: staffForm.email.trim(),
      phone: staffForm.phone.trim(),
      role: staffForm.role,
      staff_role_label: staffForm.staff_role_label.trim() || null,
      staff_title: staffForm.staff_title.trim(),
      staff_department: staffForm.staff_department.trim(),
      staff_area_of_operation: staffForm.staff_area_of_operation.trim(),
      staff_hire_date: staffForm.staff_hire_date,
      staff_experience_level: staffForm.staff_experience_level.trim() || null,
      staff_performance_summary: staffForm.staff_performance_summary.trim() || null,
      staff_assigned_tasks: parseCommaSeparated(staffForm.staff_assigned_tasks),
      staff_assigned_projects: parseCommaSeparated(staffForm.staff_assigned_projects),
      permissions: staffForm.permissions,
      staff_notes: staffForm.staff_notes.trim() || null,
      is_active: staffForm.is_active,
    };

    if (
      !payload.full_name ||
      !payload.email ||
      !payload.phone ||
      !payload.role ||
      !payload.staff_title ||
      !payload.staff_department ||
      !payload.staff_area_of_operation ||
      !payload.staff_hire_date ||
      payload.permissions.length === 0 ||
      (!editingStaff && (!staffForm.username.trim() || !staffForm.password.trim()))
    ) {
      setStaffSaving(false);
      setStaffError("Fill all required fields including contact, hire date, area, and at least one permission.");
      return;
    }

    try {
      const res = await apiFetch(editingStaff ? `/admin/staff/${editingStaff.id}` : "/admin/staff", {
        method: editingStaff ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setStaffError(err.detail || "Failed to save staff account");
        setStaffSaving(false);
        return;
      }

      const savedStaff = (await res.json()) as StaffUser;
      setStaffUsers((current) => {
        if (editingStaff) {
          return current.map((staffMember) => (staffMember.id === savedStaff.id ? savedStaff : staffMember));
        }
        return [savedStaff, ...current];
      });
      setFeedback({
        tone: "success",
        text: editingStaff ? "Staff profile updated successfully." : "Staff member created successfully.",
      });
      closeStaffModal();
    } catch {
      setStaffError("Network error while saving staff account");
    }

    setStaffSaving(false);
  };

  const toggleStaffStatus = async (staffMember: StaffUser) => {
    setRowActionId(staffMember.id);
    try {
      const res = await apiFetch(`/admin/staff/${staffMember.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: !staffMember.is_active }),
      });
      if (res.ok) {
        const updated = (await res.json()) as StaffUser;
        setStaffUsers((current) => current.map((item) => (item.id === updated.id ? updated : item)));
        setFeedback({
          tone: "success",
          text: `${updated.full_name} is now ${updated.is_active ? "active" : "inactive"}.`,
        });
      } else {
        setFeedback({ tone: "error", text: "Unable to update staff status." });
      }
    } finally {
      setRowActionId(null);
    }
  };

  const submitResetPassword = async () => {
    if (!resetTarget || resetPassword.trim().length < 8) return;
    setResettingPassword(true);
    try {
      const res = await apiFetch(`/admin/users/${resetTarget.id}/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_password: resetPassword.trim() }),
      });
      if (res.ok) {
        setFeedback({ tone: "success", text: `Temporary password set for ${resetTarget.full_name}.` });
        setResetTarget(null);
        setResetPassword("StaffPass123!");
      } else {
        setFeedback({ tone: "error", text: "Unable to reset staff password." });
      }
    } finally {
      setResettingPassword(false);
    }
  };

  const deleteStaff = async () => {
    if (!deleteTarget) return;
    setDeleteSaving(true);
    try {
      const res = await apiFetch(`/admin/staff/${deleteTarget.id}`, { method: "DELETE" });
      if (res.ok) {
        setStaffUsers((current) => current.filter((item) => item.id !== deleteTarget.id));
        setSelectedStaffIds((current) => {
          const next = new Set(current);
          next.delete(deleteTarget.id);
          return next;
        });
        setFeedback({ tone: "success", text: `${deleteTarget.full_name} was deleted.` });
        setDeleteTarget(null);
      } else {
        const err = await res.json().catch(() => ({}));
        setFeedback({ tone: "error", text: err.detail || "Unable to delete staff member." });
      }
    } finally {
      setDeleteSaving(false);
    }
  };

  const openBulkModal = () => {
    setBulkForm({});
    setBulkError("");
    setShowBulkModal(true);
  };

  const closeBulkModal = () => {
    setShowBulkModal(false);
    setBulkError("");
  };

  const saveBulkUpdate = async () => {
    if (selectedStaffIds.size === 0) return;
    setBulkSaving(true);
    setBulkError("");

    const updates: Record<string, unknown> = {};
    if (bulkForm.role) updates.role = bulkForm.role;
    if (bulkForm.staff_role_label) updates.staff_role_label = bulkForm.staff_role_label.trim();
    if (bulkForm.staff_department) updates.staff_department = bulkForm.staff_department.trim();
    if (bulkForm.staff_area_of_operation) updates.staff_area_of_operation = bulkForm.staff_area_of_operation.trim();
    if (bulkForm.is_active !== undefined) updates.is_active = bulkForm.is_active;
    if (bulkForm.permissions && bulkForm.permissions.length > 0) updates.permissions = bulkForm.permissions;

    if (Object.keys(updates).length === 0) {
      setBulkSaving(false);
      setBulkError("Select at least one field to update.");
      return;
    }

    try {
      const res = await apiFetch("/admin/staff/bulk", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_ids: Array.from(selectedStaffIds),
          updates,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setBulkError(err.detail || "Failed to bulk update staff.");
        setBulkSaving(false);
        return;
      }

      const result = await res.json();
      setStaffUsers((current) =>
        current.map((staffMember) =>
          result.updated_users.find((candidate: StaffUser) => candidate.id === staffMember.id) || staffMember
        )
      );
      setSelectedStaffIds(new Set());
      setFeedback({ tone: "success", text: `Updated ${result.updated_users.length} staff accounts.` });
      closeBulkModal();
    } catch {
      setBulkError("Network error while bulk updating staff.");
    }

    setBulkSaving(false);
  };

  const bodyText = dc(density, "text-[11px]", "text-xs", "text-sm");

  const staffColumns = useMemo<Array<EnterpriseColumn<StaffUser>>>(() => [
    {
      key: "full_name",
      label: "Staff",
      width: "280px",
      sortable: true,
      sortValue: (staffMember) => staffMember.full_name.toLowerCase(),
      searchValue: (staffMember) => `${staffMember.full_name} ${staffMember.username} ${staffMember.email} ${staffMember.phone ?? ""}`,
      render: (staffMember) => (
        <div className="space-y-0.5">
          <div className={`font-semibold text-text ${bodyText}`}>{staffMember.full_name}</div>
          <div className={`text-text-muted ${bodyText}`}>{staffMember.email}</div>
          <div className={`text-text-faint ${bodyText}`}>{staffMember.phone || "No phone"}</div>
          <div className={`text-text-faint ${bodyText}`}>Hired: {formatDate(staffMember.staff_hire_date)}</div>
        </div>
      ),
    },
    {
      key: "role",
      label: "Role",
      width: "220px",
      sortable: true,
      sortValue: (staffMember) => ROLE_LABELS[staffMember.role],
      searchValue: (staffMember) => `${ROLE_LABELS[staffMember.role]} ${staffMember.staff_role_label ?? ""} ${staffMember.staff_title ?? ""} ${staffMember.staff_department ?? ""}`,
      render: (staffMember) => (
        <div className="space-y-1">
          <span className={`inline-flex rounded-md border px-1.5 py-0.5 text-[11px] font-semibold ${ROLE_BADGE[staffMember.role]}`}>
            {ROLE_LABELS[staffMember.role]}
          </span>
          <div className={`font-semibold text-text ${bodyText}`}>
            {staffMember.staff_role_label || staffMember.staff_title || "Operational role pending"}
          </div>
          <div className={`text-text-muted ${bodyText}`}>{staffMember.staff_department || "No department"}</div>
        </div>
      ),
    },
    {
      key: "staff_area_of_operation",
      label: "Area",
      width: "220px",
      sortable: true,
      sortValue: (staffMember) => staffMember.staff_area_of_operation ?? "",
      searchValue: (staffMember) => `${staffMember.staff_area_of_operation ?? ""} ${staffMember.staff_assigned_projects.join(" ")}`,
      render: (staffMember) => (
        <div className="space-y-0.5">
          <div className={`font-medium text-text ${bodyText}`}>{staffMember.staff_area_of_operation || "Unassigned"}</div>
          <div className={`text-text-muted ${bodyText}`}>
            Projects: {staffMember.staff_assigned_projects.length > 0 ? staffMember.staff_assigned_projects.join(", ") : "None"}
          </div>
        </div>
      ),
    },
    {
      key: "is_active",
      label: "Status",
      width: "180px",
      sortable: true,
      sortValue: (staffMember) => Number(staffMember.is_active),
      searchValue: (staffMember) => `${staffMember.is_active ? "Active" : "Inactive"} ${staffMember.staff_experience_level ?? ""}`,
      render: (staffMember) => (
        <div className="space-y-1">
          <span
            className={`inline-flex rounded-full px-1.5 py-0.5 text-[10px] font-semibold ${
              staffMember.is_active ? "bg-success/10 text-success" : "bg-danger/10 text-danger"
            }`}
          >
            {staffMember.is_active ? "Active" : "Inactive"}
          </span>
          <div className={`text-text-muted ${bodyText}`}>
            {staffMember.staff_experience_level || "Experience not set"}
          </div>
        </div>
      ),
    },
    {
      key: "permissions",
      label: "Permissions",
      searchable: false,
      searchValue: (staffMember) => staffMember.permissions.join(" "),
      render: (staffMember) => (
        <div className="flex flex-wrap gap-1">
          {staffMember.permissions.slice(0, 4).map((permission) => (
            <span
              key={`${staffMember.id}-${permission}`}
              className="rounded-md border border-border bg-surface-2 px-1.5 py-0.5 text-[10px] font-semibold text-text-muted"
            >
              {permission}
            </span>
          ))}
          {staffMember.permissions.length > 4 && (
            <span className="rounded-md border border-border bg-surface-2 px-1.5 py-0.5 text-[10px] font-semibold text-text-muted">
              +{staffMember.permissions.length - 4} more
            </span>
          )}
        </div>
      ),
    },
  ], [bodyText]);

  if (authLoading || loading) {
    return (
      <PanelLoadingState count={4} blockClassName="h-14 animate-pulse rounded-xl bg-surface-2" />
    );
  }

  return (
    <PanelContent className="space-y-4">
      <div className="theme-card rounded-xl border p-2">
        <PanelTabs
          items={[
            { key: "staff", label: "Staff", icon: Shield },
            { key: "permissions", label: "Permissions", icon: Network },
          ]}
          value={section}
          onChange={(nextSection) => router.push(`${pathname}?section=${nextSection}`)}
          className="border-0 bg-transparent p-0"
        />
      </div>

      {section === "staff" && isAdmin && (
        <div className="space-y-4">
          {feedback && (
            <div
              className={`flex items-center gap-2 rounded-xl border px-3 py-2 text-xs ${
                feedback.tone === "success"
                  ? "border-success/30 bg-success/10 text-success"
                  : "border-danger/30 bg-danger/10 text-danger"
              }`}
            >
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{feedback.text}</span>
            </div>
          )}

          <div className="space-y-4">
            <div className="flex justify-end">
              <button
                onClick={openCreateModal}
                className="theme-btn-primary inline-flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-semibold shadow-none"
              >
                <UserPlus className="h-3.5 w-3.5" />
                Add Staff Member
              </button>
            </div>

            <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
              {[
                { label: "Total Staff", value: totalStaff, helper: "Managed accounts" },
                { label: "Active", value: activeStaff, helper: "Currently enabled" },
                { label: "Areas", value: distinctAreas, helper: "Operational coverage" },
                { label: "Projects", value: assignedProjects, helper: "Assigned projects" },
              ].map((card) => (
                <div key={card.label} className="rounded-xl border border-border bg-surface-1/80 px-3 py-2.5">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-text-faint">{card.label}</p>
                  <p className="mt-1 text-lg font-bold text-text">{card.value}</p>
                  <p className="mt-0.5 text-[10px] text-text-muted">{card.helper}</p>
                </div>
              ))}
            </div>
          </div>

          <h2 className="text-sm font-bold text-text">Staff Directory</h2>
          <EnterpriseDataTable
            columns={staffColumns}
            rows={filteredStaff}
            rowKey={(staffMember) => staffMember.id}
            densityMode={density}
            initialRowsPerPage={25}
            enableBulkActions
            enableExport
            searchPlaceholder="Search by name, email, role, department, area, or permission..."
            selectedRowKeys={Array.from(selectedStaffIds)}
            onSelectedRowKeysChange={(keys) => setSelectedStaffIds(new Set(keys.map((key) => Number(key))))}
            toolbarSlot={(
              <>
                <select
                  value={roleFilter}
                  onChange={(event) => setRoleFilter(event.target.value as "all" | StaffRole)}
                  className="theme-input rounded-xl border px-3 py-2 text-xs"
                >
                  <option value="all">All roles</option>
                  {roles.map((value) => (
                    <option key={value} value={value}>
                      {ROLE_LABELS[value]}
                    </option>
                  ))}
                </select>
                <select
                  value={statusFilter}
                  onChange={(event) => setStatusFilter(event.target.value as "all" | "active" | "inactive")}
                  className="theme-input rounded-xl border px-3 py-2 text-xs"
                >
                  <option value="all">All statuses</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </>
            )}
            emptyState="No staff matched the current filters."
            rowActions={(staffMember) => (
              <div className="flex flex-wrap justify-end gap-1">
                <button
                  onClick={() => setViewingStaff(staffMember)}
                  className="rounded-md border border-border bg-surface-2 px-2 py-1 text-[11px] font-semibold text-text hover:bg-surface-1"
                >
                  View
                </button>
                <button
                  onClick={() => openEditModal(staffMember)}
                  className="rounded-md border border-border bg-surface-2 px-2 py-1 text-[11px] font-semibold text-text hover:bg-surface-1"
                >
                  Edit
                </button>
                <button
                  onClick={() => toggleStaffStatus(staffMember)}
                  disabled={rowActionId === staffMember.id || staffMember.id === user?.id}
                  className={`rounded-md px-2 py-1 text-[11px] font-semibold disabled:opacity-50 ${
                    staffMember.is_active
                      ? "bg-warning text-on-warning hover:opacity-80"
                      : "bg-success text-white hover:bg-success/80"
                  }`}
                >
                  {rowActionId === staffMember.id ? "..." : staffMember.is_active ? "Deactivate" : "Activate"}
                </button>
                <button
                  onClick={() => {
                    setResetTarget(staffMember);
                    setResetPassword("StaffPass123!");
                  }}
                  className="rounded-md border border-border bg-surface-2 px-2 py-1 text-[11px] font-semibold text-text hover:bg-surface-1"
                >
                  Reset Pwd
                </button>
                <Button variant="danger" className="rounded-md border border-danger/40 px-2 py-1 text-[11px] font-semibold text-danger disabled:opacity-50" onClick={() => setDeleteTarget(staffMember)}
                  disabled={staffMember.id === user?.id}
                >
                  Delete
                </Button>
              </div>
            )}
          />

          <BulkActionBar
            selectedCount={selectedStaffIds.size}
            onClearSelection={() => setSelectedStaffIds(new Set())}
            actions={[
              {
                label: "Bulk Update",
                onClick: openBulkModal,
                variant: "primary",
              },
            ]}
          />

          <AnimatePresence>
            {showStaffModal && (
              <MotionDiv
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="theme-overlay fixed inset-0 z-50 flex items-center justify-center p-4"
                onClick={(event: MouseEvent<HTMLDivElement>) => event.target === event.currentTarget && closeStaffModal()}
              >
                <MotionDiv
                  initial={{ scale: 0.96, opacity: 0, y: 24 }}
                  animate={{ scale: 1, opacity: 1, y: 0 }}
                  exit={{ scale: 0.96, opacity: 0, y: 24 }}
                  className="theme-card w-full max-w-6xl max-h-[92vh] overflow-y-auto rounded-[1.75rem] border p-6 shadow-card-xl"
                >
                  <div className="flex flex-col gap-2 border-b border-border pb-5 sm:flex-row sm:items-end sm:justify-between">
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-text-faint">
                        {editingStaff ? "Update Staff" : "Create Staff"}
                      </p>
                      <h2 className="mt-1 text-xl font-bold text-text">
                        {editingStaff ? `Manage ${editingStaff.full_name}` : "New Staff Assignment"}
                      </h2>
                      <p className="mt-1 text-xs text-text-muted">
                        Capture identity, operational role, area ownership, and the exact permission set this staff member should have.
                      </p>
                    </div>
                    <button
                      onClick={closeStaffModal}
                      className="rounded-xl border border-border px-3 py-2 text-xs font-semibold text-text-muted hover:bg-surface-2"
                    >
                      Close
                    </button>
                  </div>

                  <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
                    <div className="grid gap-4 md:grid-cols-2">
                      {[
                        { key: "full_name", label: "Full Name", required: true },
                        { key: "username", label: "Username", required: !editingStaff, disabled: Boolean(editingStaff) },
                        { key: "email", label: "Email", required: true, type: "email" },
                        { key: "phone", label: "Contact Number", required: true, placeholder: "+96812345678" },
                        { key: "staff_role_label", label: "Custom Role Label", placeholder: "Returns Command Lead" },
                        { key: "staff_title", label: "Job Title", required: true },
                        { key: "staff_department", label: "Department", required: true },
                        { key: "staff_area_of_operation", label: "Area of Operation", required: true },
                      ].map((field) => (
                        <label key={field.key} className="block">
                          <span className="mb-1.5 block text-xs font-semibold text-text-muted">
                            {field.label}{field.required ? " *" : ""}
                          </span>
                          <input
                            type={field.type ?? "text"}
                            value={String(staffForm[field.key as keyof StaffFormState] ?? "")}
                            onChange={(event) => setStaffForm((current) => ({ ...current, [field.key]: event.target.value }))}
                            disabled={field.disabled}
                            placeholder={field.placeholder ?? field.label}
                            className="theme-input w-full rounded-xl border px-3 py-2.5 text-xs placeholder:text-text-faint disabled:opacity-60"
                          />
                        </label>
                      ))}

                      {!editingStaff && (
                        <label className="block md:col-span-2">
                          <span className="mb-1.5 block text-xs font-semibold text-text-muted">Password *</span>
                          <input
                            type="password"
                            value={staffForm.password}
                            onChange={(event) => setStaffForm((current) => ({ ...current, password: event.target.value }))}
                            placeholder="At least 8 chars, uppercase, lowercase, number"
                            className="theme-input w-full rounded-xl border px-3 py-2.5 text-xs placeholder:text-text-faint"
                          />
                        </label>
                      )}

                      <label className="block">
                        <span className="mb-1.5 block text-xs font-semibold text-text-muted">Base Access Role *</span>
                        <select
                          value={staffForm.role}
                          onChange={(event) => applyRoleDefaults(event.target.value as StaffRole)}
                          className="theme-input w-full rounded-xl border px-3 py-2.5 text-xs"
                        >
                          {roles.map((value) => (
                            <option key={value} value={value}>
                              {ROLE_LABELS[value]}
                            </option>
                          ))}
                        </select>
                      </label>

                      <label className="block">
                        <span className="mb-1.5 block text-xs font-semibold text-text-muted">Hire Date *</span>
                        <input
                          type="date"
                          value={staffForm.staff_hire_date}
                          onChange={(event) => setStaffForm((current) => ({ ...current, staff_hire_date: event.target.value }))}
                          className="theme-input w-full rounded-xl border px-3 py-2.5 text-xs"
                        />
                      </label>

                      <label className="block">
                        <span className="mb-1.5 block text-xs font-semibold text-text-muted">Experience Level</span>
                        <select
                          value={staffForm.staff_experience_level}
                          onChange={(event) => setStaffForm((current) => ({ ...current, staff_experience_level: event.target.value }))}
                          className="theme-input w-full rounded-xl border px-3 py-2.5 text-xs"
                        >
                          {EXPERIENCE_OPTIONS.map((option) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </select>
                      </label>

                      <label className="block md:col-span-2">
                        <span className="mb-1.5 block text-xs font-semibold text-text-muted">Performance Summary</span>
                        <textarea
                          value={staffForm.staff_performance_summary}
                          onChange={(event) => setStaffForm((current) => ({ ...current, staff_performance_summary: event.target.value }))}
                          rows={3}
                          placeholder="Trusted for escalations, high QA score"
                          className="theme-input w-full rounded-xl border px-3 py-2.5 text-xs placeholder:text-text-faint"
                        />
                      </label>

                      <label className="block md:col-span-2">
                        <span className="mb-1.5 block text-xs font-semibold text-text-muted">Assigned Tasks</span>
                        <input
                          value={staffForm.staff_assigned_tasks}
                          onChange={(event) => setStaffForm((current) => ({ ...current, staff_assigned_tasks: event.target.value }))}
                          placeholder="Fraud review, supplier QA, refund escalation"
                          className="theme-input w-full rounded-xl border px-3 py-2.5 text-xs placeholder:text-text-faint"
                        />
                      </label>

                      <label className="block md:col-span-2">
                        <span className="mb-1.5 block text-xs font-semibold text-text-muted">Assigned Projects</span>
                        <input
                          value={staffForm.staff_assigned_projects}
                          onChange={(event) => setStaffForm((current) => ({ ...current, staff_assigned_projects: event.target.value }))}
                          placeholder="Returns migration, VIP supplier onboarding"
                          className="theme-input w-full rounded-xl border px-3 py-2.5 text-xs placeholder:text-text-faint"
                        />
                      </label>

                      <label className="block md:col-span-2">
                        <span className="mb-1.5 block text-xs font-semibold text-text-muted">Internal Notes</span>
                        <textarea
                          value={staffForm.staff_notes}
                          onChange={(event) => setStaffForm((current) => ({ ...current, staff_notes: event.target.value }))}
                          rows={4}
                          placeholder="Escalation notes, onboarding context, coaching goals"
                          className="theme-input w-full rounded-xl border px-3 py-2.5 text-xs placeholder:text-text-faint"
                        />
                      </label>
                    </div>

                    <div className="rounded-xl border border-border bg-surface-2/55 p-4">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="text-xs font-bold text-text">Permission Assignment</p>
                          <p className="mt-1 text-xs text-text-muted">Permissions apply immediately after the next staff auth refresh.</p>
                        </div>
                        <button
                          type="button"
                          onClick={() => applyRoleDefaults(staffForm.role)}
                          className="rounded-lg border border-border px-2.5 py-1.5 text-[11px] font-semibold text-text-muted hover:bg-surface-1"
                        >
                          Reset to Role Default
                        </button>
                      </div>

                      <div className="mt-4 max-h-112 space-y-4 overflow-y-auto pr-1">
                        {permissionCatalog.groups.map((group) => (
                          <div key={group.key} className="rounded-xl border border-border bg-surface-1 p-3">
                            <div className="mb-2">
                              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-text-faint">{group.label}</p>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {group.permissions.map((permission) => {
                                const checked = staffForm.permissions.includes(permission);
                                return (
                                  <label
                                    key={`${group.key}-${permission}`}
                                    className={`flex cursor-pointer items-center gap-2 rounded-full border px-3 py-1.5 text-[11px] font-semibold transition-colors ${
                                      checked
                                        ? "border-primary bg-primary/10 text-text"
                                        : "border-border bg-surface-2 text-text-muted hover:border-primary/40"
                                    }`}
                                  >
                                    <input
                                      type="checkbox"
                                      checked={checked}
                                      onChange={() => togglePermission(permission)}
                                      className="h-3.5 w-3.5 accent-primary"
                                    />
                                    {permission}
                                  </label>
                                );
                              })}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {staffError && (
                    <div className="theme-alert-danger mt-4 flex items-center gap-2 rounded-xl p-3">
                      <AlertCircle className="h-4 w-4 shrink-0" />
                      <p className="text-xs">{staffError}</p>
                    </div>
                  )}

                  <div className="mt-6 flex flex-col gap-3 border-t border-border pt-5 sm:flex-row sm:justify-between">
                    <label className="inline-flex items-center gap-2 text-xs text-text-muted">
                      <input
                        type="checkbox"
                        checked={staffForm.is_active}
                        onChange={(event) => setStaffForm((current) => ({ ...current, is_active: event.target.checked }))}
                        className="h-4 w-4 accent-primary"
                      />
                      Staff account is active
                    </label>
                    <div className="flex gap-3">
                      <button
                        onClick={closeStaffModal}
                        className="theme-btn-secondary rounded-xl border px-4 py-2.5 text-xs font-semibold text-text-muted"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={saveStaff}
                        disabled={staffSaving}
                        className="theme-btn-primary rounded-xl px-4 py-2.5 text-xs font-bold disabled:opacity-50"
                      >
                        {staffSaving ? "Saving..." : editingStaff ? "Update Staff" : "Create Staff"}
                      </button>
                    </div>
                  </div>
                </MotionDiv>
              </MotionDiv>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {viewingStaff && (
              <MotionDiv
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="theme-overlay fixed inset-0 z-50 flex items-center justify-center p-4"
                onClick={(event: MouseEvent<HTMLDivElement>) => event.target === event.currentTarget && setViewingStaff(null)}
              >
                <MotionDiv
                  initial={{ scale: 0.96, opacity: 0, y: 24 }}
                  animate={{ scale: 1, opacity: 1, y: 0 }}
                  exit={{ scale: 0.96, opacity: 0, y: 24 }}
                  className="theme-card w-full max-w-3xl rounded-3xl border p-6"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-text-faint">Staff Profile</p>
                      <h3 className="mt-1 text-xl font-bold text-text">{viewingStaff.full_name}</h3>
                      <p className="mt-1 text-xs text-text-muted">{viewingStaff.email}</p>
                    </div>
                    <button
                      onClick={() => setViewingStaff(null)}
                      className="rounded-xl border border-border px-3 py-2 text-xs font-semibold text-text-muted hover:bg-surface-2"
                    >
                      Close
                    </button>
                  </div>

                  <div className="mt-6 grid gap-4 md:grid-cols-2">
                    {[
                      ["Base Role", ROLE_LABELS[viewingStaff.role]],
                      ["Custom Role", viewingStaff.staff_role_label || "Not set"],
                      ["Job Title", viewingStaff.staff_title || "Not set"],
                      ["Department", viewingStaff.staff_department || "Not set"],
                      ["Area", viewingStaff.staff_area_of_operation || "Not set"],
                      ["Hire Date", formatDate(viewingStaff.staff_hire_date)],
                      ["Status", viewingStaff.is_active ? "Active" : "Inactive"],
                      ["Experience", viewingStaff.staff_experience_level || "Not set"],
                    ].map(([label, value]) => (
                      <div key={label} className="rounded-xl border border-border bg-surface-2/60 p-4">
                        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-text-faint">{label}</p>
                        <p className="mt-2 text-xs font-semibold text-text">{value}</p>
                      </div>
                    ))}
                  </div>

                  <div className="mt-4 grid gap-4 lg:grid-cols-3">
                    <div className="rounded-xl border border-border bg-surface-2/60 p-4">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-text-faint">Tasks</p>
                      <p className="mt-2 text-xs text-text-muted">
                        {viewingStaff.staff_assigned_tasks.length > 0 ? viewingStaff.staff_assigned_tasks.join(", ") : "No task assignment"}
                      </p>
                    </div>
                    <div className="rounded-xl border border-border bg-surface-2/60 p-4">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-text-faint">Projects</p>
                      <p className="mt-2 text-xs text-text-muted">
                        {viewingStaff.staff_assigned_projects.length > 0 ? viewingStaff.staff_assigned_projects.join(", ") : "No project assignment"}
                      </p>
                    </div>
                    <div className="rounded-xl border border-border bg-surface-2/60 p-4">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-text-faint">Notes</p>
                      <p className="mt-2 text-xs text-text-muted">{viewingStaff.staff_notes || "No internal notes"}</p>
                    </div>
                  </div>

                  <div className="mt-4 rounded-xl border border-border bg-surface-2/60 p-4">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-text-faint">Permissions</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {viewingStaff.permissions.map((permission) => (
                        <span
                          key={`view-${viewingStaff.id}-${permission}`}
                          className="rounded-full border border-border bg-surface-1 px-2.5 py-1 text-[11px] font-semibold text-text-muted"
                        >
                          {permission}
                        </span>
                      ))}
                    </div>
                  </div>
                </MotionDiv>
              </MotionDiv>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {resetTarget && (
              <MotionDiv
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="theme-overlay fixed inset-0 z-50 flex items-center justify-center p-4"
                onClick={(event: MouseEvent<HTMLDivElement>) => event.target === event.currentTarget && setResetTarget(null)}
              >
                <MotionDiv
                  initial={{ scale: 0.96, opacity: 0, y: 24 }}
                  animate={{ scale: 1, opacity: 1, y: 0 }}
                  exit={{ scale: 0.96, opacity: 0, y: 24 }}
                  className="theme-card w-full max-w-lg rounded-3xl border p-6"
                >
                  <h3 className="text-lg font-bold text-text">Reset Staff Password</h3>
                  <p className="mt-2 text-xs text-text-muted">
                    Set a temporary password for <span className="font-semibold text-text">{resetTarget.full_name}</span>.
                  </p>
                  <label className="mt-4 block">
                    <span className="mb-1.5 block text-xs font-semibold text-text-muted">Temporary Password</span>
                    <input
                      type="text"
                      value={resetPassword}
                      onChange={(event) => setResetPassword(event.target.value)}
                      className="theme-input w-full rounded-xl border px-3 py-2.5 text-xs"
                    />
                  </label>
                  <div className="mt-5 flex justify-end gap-3">
                    <button
                      onClick={() => setResetTarget(null)}
                      className="theme-btn-secondary rounded-xl border px-4 py-2.5 text-xs font-semibold text-text-muted"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={submitResetPassword}
                      disabled={resettingPassword || resetPassword.trim().length < 8}
                      className="theme-btn-primary rounded-xl px-4 py-2.5 text-xs font-bold disabled:opacity-50"
                    >
                      {resettingPassword ? "Resetting..." : "Apply Reset"}
                    </button>
                  </div>
                </MotionDiv>
              </MotionDiv>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {showBulkModal && (
              <MotionDiv
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="theme-overlay fixed inset-0 z-50 flex items-center justify-center p-4"
                onClick={(event: MouseEvent<HTMLDivElement>) => event.target === event.currentTarget && closeBulkModal()}
              >
                <MotionDiv
                  initial={{ scale: 0.96, opacity: 0, y: 24 }}
                  animate={{ scale: 1, opacity: 1, y: 0 }}
                  exit={{ scale: 0.96, opacity: 0, y: 24 }}
                  className="theme-card w-full max-w-3xl rounded-3xl border p-6"
                >
                  <h3 className="text-lg font-bold text-text">Bulk Update Staff</h3>
                  <p className="mt-2 text-xs text-text-muted">
                    Update {selectedStaffIds.size} selected staff member{selectedStaffIds.size === 1 ? "" : "s"}.
                  </p>

                  <div className="mt-6 space-y-6">
                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                      <label className="block">
                        <span className="mb-1.5 block text-xs font-semibold text-text-muted">Role</span>
                        <select
                          value={bulkForm.role || ""}
                          onChange={(event) => setBulkForm((current) => ({ ...current, role: (event.target.value as StaffRole) || undefined }))}
                          className="theme-input w-full rounded-xl border px-3 py-2.5 text-xs"
                        >
                          <option value="">No change</option>
                          {roles.map((staffRole) => (
                            <option key={staffRole} value={staffRole}>
                              {ROLE_LABELS[staffRole]}
                            </option>
                          ))}
                        </select>
                      </label>

                      <label className="block">
                        <span className="mb-1.5 block text-xs font-semibold text-text-muted">Custom Role Label</span>
                        <input
                          value={bulkForm.staff_role_label || ""}
                          onChange={(event) => setBulkForm((current) => ({ ...current, staff_role_label: event.target.value || undefined }))}
                          placeholder="No change"
                          className="theme-input w-full rounded-xl border px-3 py-2.5 text-xs"
                        />
                      </label>

                      <label className="block">
                        <span className="mb-1.5 block text-xs font-semibold text-text-muted">Department</span>
                        <select
                          value={bulkForm.staff_department || ""}
                          onChange={(event) => setBulkForm((current) => ({ ...current, staff_department: event.target.value || undefined }))}
                          className="theme-input w-full rounded-xl border px-3 py-2.5 text-xs"
                        >
                          <option value="">No change</option>
                          {departments.map((department) => (
                            <option key={department} value={department}>
                              {department}
                            </option>
                          ))}
                        </select>
                      </label>

                      <label className="block">
                        <span className="mb-1.5 block text-xs font-semibold text-text-muted">Area</span>
                        <select
                          value={bulkForm.staff_area_of_operation || ""}
                          onChange={(event) => setBulkForm((current) => ({ ...current, staff_area_of_operation: event.target.value || undefined }))}
                          className="theme-input w-full rounded-xl border px-3 py-2.5 text-xs"
                        >
                          <option value="">No change</option>
                          {areas.map((area) => (
                            <option key={area} value={area}>
                              {area}
                            </option>
                          ))}
                        </select>
                      </label>
                    </div>

                    <label className="block">
                      <span className="mb-1.5 block text-xs font-semibold text-text-muted">Status</span>
                      <select
                        value={bulkForm.is_active === undefined ? "" : bulkForm.is_active ? "active" : "inactive"}
                        onChange={(event) =>
                          setBulkForm((current) => ({
                            ...current,
                            is_active: event.target.value === "" ? undefined : event.target.value === "active",
                          }))
                        }
                        className="theme-input w-full rounded-xl border px-3 py-2.5 text-xs"
                      >
                        <option value="">No change</option>
                        <option value="active">Active</option>
                        <option value="inactive">Inactive</option>
                      </select>
                    </label>

                    <div className="space-y-3">
                      <span className="block text-xs font-semibold text-text-muted">Permissions</span>
                      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                        {Object.entries(permissionGroups).map(([groupLabel, permissions]) => (
                          <div key={groupLabel} className="rounded-xl border border-border bg-surface-2/50 p-3">
                            <h4 className="text-xs font-semibold uppercase tracking-[0.14em] text-text-faint">{groupLabel}</h4>
                            <div className="mt-3 space-y-2">
                              {permissions.map((permission) => (
                                <label key={permission} className="flex items-center gap-2 text-xs text-text-muted">
                                  <input
                                    type="checkbox"
                                    checked={bulkForm.permissions?.includes(permission) || false}
                                    onChange={() => toggleBulkPermission(permission)}
                                    className="h-3.5 w-3.5 accent-primary"
                                  />
                                  {permission}
                                </label>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                      <p className="text-xs text-text-muted">If you check permissions here, the selected staff will receive exactly this updated permission set.</p>
                    </div>
                  </div>

                  {bulkError && (
                    <div className="theme-alert-danger mt-4 flex items-center gap-2 rounded-xl p-3">
                      <AlertCircle className="h-4 w-4 shrink-0" />
                      <p className="text-xs">{bulkError}</p>
                    </div>
                  )}

                  <div className="mt-6 flex justify-end gap-3">
                    <button
                      onClick={closeBulkModal}
                      className="theme-btn-secondary rounded-xl border px-4 py-2.5 text-xs font-semibold text-text-muted"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={saveBulkUpdate}
                      disabled={bulkSaving || !hasBulkChanges}
                      className="theme-btn-primary rounded-xl px-4 py-2.5 text-xs font-bold disabled:opacity-50"
                    >
                      {bulkSaving ? "Updating..." : `Update ${selectedStaffIds.size} Staff`}
                    </button>
                  </div>
                </MotionDiv>
              </MotionDiv>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {deleteTarget && (
              <MotionDiv
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="theme-overlay fixed inset-0 z-50 flex items-center justify-center p-4"
                onClick={(event: MouseEvent<HTMLDivElement>) => event.target === event.currentTarget && setDeleteTarget(null)}
              >
                <MotionDiv
                  initial={{ scale: 0.96, opacity: 0, y: 24 }}
                  animate={{ scale: 1, opacity: 1, y: 0 }}
                  exit={{ scale: 0.96, opacity: 0, y: 24 }}
                  className="theme-card w-full max-w-lg rounded-3xl border p-6"
                >
                  <h3 className="text-lg font-bold text-text">Delete Staff Member</h3>
                  <p className="mt-2 text-xs text-text-muted">
                    Delete <span className="font-semibold text-text">{deleteTarget.full_name}</span>. This will permanently remove the staff account if there are no retention blockers.
                  </p>
                  <div className="mt-5 flex justify-end gap-3">
                    <button
                      onClick={() => setDeleteTarget(null)}
                      className="theme-btn-secondary rounded-xl border px-4 py-2.5 text-xs font-semibold text-text-muted"
                    >
                      Cancel
                    </button>
                    <Button variant="danger" onClick={deleteStaff}
                      disabled={deleteSaving}>
                      {deleteSaving ? "Deleting..." : "Delete Staff"}
                    </Button>
                  </div>
                </MotionDiv>
              </MotionDiv>
            )}
          </AnimatePresence>
        </div>
      )}

      {section === "permissions" && <HierarchyTab />}
      </PanelContent>
  );
}

