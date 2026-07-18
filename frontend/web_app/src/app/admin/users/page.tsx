"use client";

import { Button } from "@/components/ui/Button";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { Users, ShieldAlert, RotateCcw, Trash2, ToggleRight, Search } from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import BulkActionBar from "@/components/BulkActionBar";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { hasAdminPermission, isAdminStaffRole } from "@shared/adminPermissions";

const PAGE_LIMIT = 500;

type UserRole =
  | "customer"
  | "supplier"
  | "admin"
  | "sub_admin"
  | "moderator"
  | "support"
  | "country_head"
  | "country_manager"
  | "employee";

interface PlatformUser {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  is_verified?: boolean;
  email_verified?: boolean;
  last_login?: string | null;
  created_at: string;
}

const ROLE_LABELS: Record<string, string> = {
  customer: "Customer",
  supplier: "Supplier",
  admin: "Admin",
  sub_admin: "Sub Admin",
  moderator: "Moderator",
  support: "Support",
  country_head: "Country Head",
  country_manager: "Country Manager",
  employee: "Employee",
};

const ROLE_OPTIONS: UserRole[] = [
  "customer",
  "supplier",
  "sub_admin",
  "moderator",
  "support",
  "country_head",
  "country_manager",
  "employee",
];

function normalizePage(raw: unknown): PlatformUser[] {
  if (Array.isArray(raw)) return raw as PlatformUser[];
  if (raw && typeof raw === "object" && Array.isArray((raw as any).data)) {
    return (raw as any).data as PlatformUser[];
  }
  return [];
}

export default function AdminUsersPage() {
  const router = useRouter();
  const { user, isLoggedIn, isLoading } = useAuth();
  const role = user?.role ?? null;

  const [users, setUsers] = useState<PlatformUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("all");
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

  const [resetTarget, setResetTarget] = useState<PlatformUser | null>(null);
  const [resetPassword, setResetPassword] = useState("");
  const [resetting, setResetting] = useState(false);

  const [bulkRole, setBulkRole] = useState<UserRole>("customer");
  const [bulkWorking, setBulkWorking] = useState(false);

  const canRead = hasAdminPermission(role, "users.read");
  const canToggle = hasAdminPermission(role, "users.toggle_active");
  const canReset = hasAdminPermission(role, "users.reset_password");
  const canRole = hasAdminPermission(role, "users.role.update");
  const canDelete = hasAdminPermission(role, "users.delete");

  // ── Auth gate: support cannot access user management ──
  useEffect(() => {
    if (isLoading) return;
    if (!isLoggedIn || !isAdminStaffRole(role) || role === "support") {
      router.push("/admin/login");
    }
  }, [isLoading, isLoggedIn, role, router]);

  const loadUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const all: PlatformUser[] = [];
      let offset = 0;
      let more = true;
      while (more) {
        const res = await apiFetch(`/admin/users?limit=${PAGE_LIMIT}&offset=${offset}`);
        if (!res.ok) throw new Error("Failed to load users");
        const page = normalizePage(await res.json());
        all.push(...page);
        if (page.length < PAGE_LIMIT) more = false;
        else offset += PAGE_LIMIT;
      }
      setUsers(all);
    } catch {
      setUsers([]);
      setError("Unable to load users. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isLoading) return;
    if (!isLoggedIn || !isAdminStaffRole(role) || role === "support") return;
    void loadUsers();
  }, [isLoading, isLoggedIn, role, loadUsers]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return users.filter((u) => {
      const matchesRole = roleFilter === "all" || u.role === roleFilter;
      const matchesSearch =
        !q ||
        String(u.id).includes(q) ||
        u.username.toLowerCase().includes(q) ||
        u.email.toLowerCase().includes(q) ||
        u.role.toLowerCase().includes(q) ||
        (u.last_login ?? "").toLowerCase().includes(q);
      return matchesRole && matchesSearch;
    });
  }, [users, search, roleFilter]);

  const allSelected = filtered.length > 0 && filtered.every((u) => selectedIds.has(u.id));
  const someSelected = filtered.some((u) => selectedIds.has(u.id));

  const toggleOne = (id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (allSelected) filtered.forEach((u) => next.delete(u.id));
      else filtered.forEach((u) => next.add(u.id));
      return next;
    });
  };

  const clearSelection = () => setSelectedIds(new Set());

  const toggleUserActive = async (target: PlatformUser) => {
    try {
      const res = await apiFetch(`/admin/users/${target.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: !target.is_active }),
      });
      if (res.ok) {
        const updated = (await res.json()) as PlatformUser;
        setUsers((cur) => cur.map((u) => (u.id === updated.id ? updated : u)));
      }
    } catch {
      /* no-op */
    }
  };

  const deleteUser = async (target: PlatformUser) => {
    if (!window.confirm(`Delete user "${target.username}"? This cannot be undone.`)) return;
    try {
      const res = await apiFetch(`/admin/users/${target.id}`, { method: "DELETE" });
      if (res.ok) {
        setUsers((cur) => cur.filter((u) => u.id !== target.id));
        setSelectedIds((prev) => {
          const next = new Set(prev);
          next.delete(target.id);
          return next;
        });
      }
    } catch {
      /* no-op */
    }
  };

  const submitResetPassword = async () => {
    if (!resetTarget || resetPassword.trim().length < 6) return;
    setResetting(true);
    try {
      const res = await apiFetch(`/admin/users/${resetTarget.id}/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_password: resetPassword.trim() }),
      });
      if (res.ok) {
        setResetTarget(null);
        setResetPassword("");
      }
    } finally {
      setResetting(false);
    }
  };

  const suspendSelected = async () => {
    if (selectedIds.size === 0) return;
    setBulkWorking(true);
    try {
      await apiFetch("/admin/users/bulk-toggle-active", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_ids: Array.from(selectedIds), is_active: false }),
      });
      clearSelection();
    } finally {
      setBulkWorking(false);
    }
  };

  const activateSelected = async () => {
    if (selectedIds.size === 0) return;
    setBulkWorking(true);
    try {
      await apiFetch("/admin/users/bulk-toggle-active", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_ids: Array.from(selectedIds), is_active: true }),
      });
      clearSelection();
    } finally {
      setBulkWorking(false);
    }
  };

  const assignRoleSelected = async () => {
    if (selectedIds.size === 0) return;
    setBulkWorking(true);
    try {
      await apiFetch("/admin/users/bulk-role", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_ids: Array.from(selectedIds), role: bulkRole }),
      });
      clearSelection();
    } finally {
      setBulkWorking(false);
    }
  };

  const roleBadge = (r: string) =>
    r === "admin" || r === "sub_admin"
      ? "theme-chip-warning"
      : r === "support"
      ? "theme-chip-info"
      : "theme-chip-brand";

  if (!isLoggedIn || !isAdminStaffRole(role) || role === "support") {
    return (
      <AdminLayout title="Users">
        <div className="p-6 text-sm text-text-muted">Redirecting…</div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout title="Users">
      <div className="space-y-4 p-4 md:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-text flex items-center gap-2">
              <Users className="h-5 w-5 text-warning" /> User Management
            </h1>
            <p className="text-xs text-text-muted">
              Manage customer, supplier, and staff accounts across the platform.
            </p>
          </div>
          <div className="text-xs text-text-muted">
            {filtered.length} of {users.length} users
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[240px]">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search user ID, name, email, role, or login activity..."
              className="w-full rounded-xl border border-border bg-surface-1 py-2 pl-9 pr-3 text-sm text-text placeholder:text-text-muted focus:border-warning focus:outline-none"
            />
          </div>
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="rounded-xl border border-border bg-surface-1 px-3 py-2 text-sm text-text focus:border-warning focus:outline-none"
          >
            <option value="all">All roles</option>
            {Object.entries(ROLE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>

        {error && (
          <div className="flex items-center gap-2 rounded-xl border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-danger">
            <ShieldAlert className="h-4 w-4" /> {error}
          </div>
        )}

        <div className="overflow-x-auto rounded-2xl border border-border bg-surface-1">
          <table className="w-full text-sm">
            <thead className="bg-surface-2 text-left text-text-muted">
              <tr>
                <th className="w-10 px-3 py-2">
                  <input
                    type="checkbox"
                    aria-label="Select all users"
                    checked={allSelected}
                    ref={(el) => {
                      if (el) el.indeterminate = !allSelected && someSelected;
                    }}
                    onChange={toggleAll}
                  />
                </th>
                <th className="px-3 py-2 font-semibold">ID</th>
                <th className="px-3 py-2 font-semibold">Username</th>
                <th className="px-3 py-2 font-semibold">Email</th>
                <th className="px-3 py-2 font-semibold">Role</th>
                <th className="px-3 py-2 font-semibold">Verified</th>
                <th className="px-3 py-2 font-semibold">Active</th>
                <th className="px-3 py-2 font-semibold">Created</th>
                <th className="px-3 py-2 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={9} className="px-3 py-10 text-center text-text-muted">
                    Loading users…
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-3 py-10 text-center text-text-muted">
                    No users found.
                  </td>
                </tr>
              ) : (
                filtered.map((u) => (
                  <tr key={u.id} className="border-t border-border/60 hover:bg-surface-2/50">
                    <td className="px-3 py-2">
                      <input
                        type="checkbox"
                        aria-label={`Select ${u.username}`}
                        checked={selectedIds.has(u.id)}
                        onChange={() => toggleOne(u.id)}
                      />
                    </td>
                    <td className="px-3 py-2 text-text-muted">{u.id}</td>
                    <td className="px-3 py-2 font-medium text-text">{u.username}</td>
                    <td className="px-3 py-2 text-text">{u.email}</td>
                    <td className="px-3 py-2">
                      <span className={`theme-chip ${roleBadge(u.role)}`}>
                        {ROLE_LABELS[u.role] ?? u.role}
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      {u.is_verified || u.email_verified ? (
                        <span className="text-success">Yes</span>
                      ) : (
                        <span className="text-text-muted">No</span>
                      )}
                    </td>
                    <td className="px-3 py-2">
                      {u.is_active ? (
                        <span className="text-success">Active</span>
                      ) : (
                        <span className="text-danger">Suspended</span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-text-muted">
                      {u.created_at ? new Date(u.created_at).toLocaleDateString() : "—"}
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex flex-wrap items-center justify-end gap-1">
                        {canReset && (
                          <button
                            type="button"
                            aria-label={`Reset password for ${u.username}`}
                            onClick={() => setResetTarget(u)}
                            className="rounded-lg p-1.5 text-text-muted hover:bg-surface-2 hover:text-text"
                            title="Reset password"
                          >
                            <RotateCcw className="h-4 w-4" />
                          </button>
                        )}
                        {canToggle && (
                          <button
                            type="button"
                            aria-label={`Toggle active for ${u.username}`}
                            onClick={() => toggleUserActive(u)}
                            className="rounded-lg p-1.5 text-text-muted hover:bg-surface-2 hover:text-text"
                            title={u.is_active ? "Suspend" : "Activate"}
                          >
                            <ToggleRight className="h-4 w-4" />
                          </button>
                        )}
                        {canDelete && (
                          <Button variant="danger" className="rounded-lg p-1.5 text-text-muted hover:text-danger" type="button"
                            aria-label={`Delete ${u.username}`}
                            onClick={() => deleteUser(u)}
                            title="Delete user"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <BulkActionBar
        selectedCount={selectedIds.size}
        onClearSelection={clearSelection}
        actions={
          canToggle
            ? [
                { label: "Suspend Selected", onClick: suspendSelected, loading: bulkWorking, variant: "danger", disabled: bulkWorking },
                { label: "Activate Selected", onClick: activateSelected, loading: bulkWorking, variant: "success", disabled: bulkWorking },
                { label: "Assign Role", onClick: assignRoleSelected, loading: bulkWorking, variant: "primary", disabled: bulkWorking || !canRole },
              ]
            : []
        }
      >
        {canRole && (
          <select
            aria-label="Bulk role target"
            value={bulkRole}
            onChange={(e) => setBulkRole(e.target.value as UserRole)}
            className="rounded-xl border border-border bg-surface-1 px-2 py-1.5 text-xs text-text focus:border-warning focus:outline-none"
          >
            {ROLE_OPTIONS.map((r) => (
              <option key={r} value={r}>
                {ROLE_LABELS[r] ?? r}
              </option>
            ))}
          </select>
        )}
      </BulkActionBar>

      {resetTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4" role="dialog" aria-modal="true" onClick={() => { setResetTarget(null); setResetPassword(""); }}>
          <div className="glass-panel border w-full max-w-sm rounded-2xl p-5" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-base font-semibold text-text">Reset password</h2>
            <p className="mt-1 text-xs text-text-muted">
              Set a temporary password for <span className="font-medium text-text">{resetTarget.username}</span>.
            </p>
            <input
              type="text"
              value={resetPassword}
              onChange={(e) => setResetPassword(e.target.value)}
              placeholder="New password (min 6 chars)"
              className="mt-3 w-full rounded-xl border border-border bg-surface-2 px-3 py-2 text-sm text-text placeholder:text-text-muted focus:border-warning focus:outline-none"
            />
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => {
                  setResetTarget(null);
                  setResetPassword("");
                }}
                className="rounded-xl px-3 py-1.5 text-sm text-text-muted hover:bg-surface-2"
              >
                Cancel
              </button>
              <Button variant="warning" type="button"
                onClick={submitResetPassword}
                disabled={resetting || resetPassword.trim().length < 6}>
                {resetting ? "Working…" : "Reset"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}
