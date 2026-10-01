"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Lock,
  Shield,
  Users,
  Plus,
  X,
  Check,
  Search,
  ChevronDown,
  ChevronRight,
  Loader2,
  Trash2,
  ToggleLeft,
  ToggleRight,
} from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelLoadingState, PanelTabs } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { useToastStore } from "@/lib/toastStore";
import { isAdminStaffRole } from "@shared/adminPermissions";

import { Button } from "@/components/ui/Button";
import { Modal, ModalFooter } from "@/components/ui/shared/Modal";
import { Badge } from "@/components/ui/shared/Badge";
import { EmptyState } from "@/components/ui/shared/EmptyState";

type PermissionTab = "categories" | "roles" | "users";

interface PermissionCategory {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  icon: string | null;
  sort_order: number;
  permissions_count: number;
  is_active: boolean;
  permissions: Permission[];
}

interface Permission {
  id: number;
  category_id: number;
  name: string;
  slug: string;
  description: string | null;
  scope: string;
  is_active: boolean;
}

interface RolePermission {
  granted: boolean;
  permission_id: number;
  name: string;
}

type RolePermissionMap = Record<string, RolePermission>;

const ADMIN_ROLES = ["admin", "sub_admin", "moderator", "support", "country_head", "country_manager"];

export function PermissionsContent() {
  const router = useRouter();
  const { user, isLoggedIn, isLoading } = useAuth();
  const { addToast } = useToastStore();

  const [activeTab, setActiveTab] = useState<PermissionTab>("categories");
  const [loading, setLoading] = useState(true);
  const [categories, setCategories] = useState<PermissionCategory[]>([]);

  const [showAddCategory, setShowAddCategory] = useState(false);
  const [catName, setCatName] = useState("");
  const [catDesc, setCatDesc] = useState("");
  const [catIcon, setCatIcon] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [expandedCategory, setExpandedCategory] = useState<number | null>(null);

  // Roles tab
  const [allPermissions, setAllPermissions] = useState<Permission[]>([]);
  const [roleData, setRoleData] = useState<Record<string, RolePermissionMap> | null>(null);
  const [selectedRole, setSelectedRole] = useState<string>("");
  const [togglingPermission, setTogglingPermission] = useState<string | null>(null);

  // Users tab
  const [userSearch, setUserSearch] = useState("");
  const [users, setUsers] = useState<any[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [selectedUserInfo, setSelectedUserInfo] = useState<{ role: string; name: string } | null>(null);
  const [userOverrides, setUserOverrides] = useState<RolePermissionMap | null>(null);
  const [userOverridesLoading, setUserOverridesLoading] = useState(false);
  const [togglingOverride, setTogglingOverride] = useState<string | null>(null);
  const [overrideBaseRole, setOverrideBaseRole] = useState("admin");

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch("/permissions/categories");
      if (res.ok) {
        const data = await res.json();
        setCategories(Array.isArray(data) ? data : []);
      }
    } catch {
      addToast("Failed to load permission categories", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  const loadAllPermissions = useCallback(async () => {
    try {
      const res = await apiFetch("/permissions/list");
      if (res.ok) setAllPermissions(await res.json());
    } catch {}
  }, []);

  const loadRolePermissions = useCallback(async () => {
    try {
      const result: Record<string, RolePermissionMap> = {};
      for (const role of ADMIN_ROLES) {
        const res = await apiFetch(`/permissions/roles/${role}`);
        if (res.ok) result[role] = await res.json();
      }
      setRoleData(result);
    } catch {
      addToast("Failed to load role permissions", "error");
    }
  }, [addToast]);

  const loadUsers = useCallback(async (search?: string) => {
    setUsersLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.set("search", search);
      params.set("limit", "50");
      const res = await apiFetch(`/admin/users?${params}`);
      if (res.ok) {
        const data = await res.json();
        setUsers(data?.items ?? data?.data ?? Array.isArray(data) ? data : []);
      }
    } catch {
      addToast("Failed to load users", "error");
    } finally {
      setUsersLoading(false);
    }
  }, [addToast]);

  const loadUserOverrides = useCallback(async (userId: number) => {
    setUserOverridesLoading(true);
    try {
      const role = overrideBaseRole;
      const res = await apiFetch(`/permissions/roles/${role}`);
      if (res.ok) {
        const allData: RolePermissionMap = await res.json();
        setUserOverrides(allData);
      }
    } catch {
      addToast("Failed to load user overrides", "error");
    } finally {
      setUserOverridesLoading(false);
    }
  }, [addToast, overrideBaseRole]);

  useEffect(() => {
    if (isLoading) return;
    if (!isLoggedIn || !isAdminStaffRole(user?.role ?? null)) {
      router.push("/admin/login");
      return;
    }
    loadData();
    loadAllPermissions();
    loadRolePermissions();
  }, [isLoading, isLoggedIn, user, router, loadData, loadAllPermissions, loadRolePermissions]);

  const handleAddCategory = async () => {
    if (!catName.trim()) {
      addToast("Category name is required", "error");
      return;
    }
    setSubmitting(true);
    try {
      const res = await apiFetch("/permissions/categories", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: catName, description: catDesc, icon: catIcon || undefined }),
      });
      if (res.ok) {
        addToast("Category created", "success");
        setShowAddCategory(false);
        setCatName("");
        setCatDesc("");
        setCatIcon("");
        loadData();
      } else {
        const err = await res.json().catch(() => ({}));
        addToast(err.detail ?? "Failed to create category", "error");
      }
    } catch {
      addToast("Network error", "error");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteCategory = async (id: number) => {
    try {
      const res = await apiFetch(`/permissions/categories/${id}`, { method: "DELETE" });
      if (res.ok) {
        addToast("Category deleted", "success");
        loadData();
      } else {
        addToast("Failed to delete category", "error");
      }
    } catch {
      addToast("Network error", "error");
    }
  };

  const handleTogglePermission = async (role: string, perm: Permission) => {
    if (togglingPermission) return;
    setTogglingPermission(`${role}:${perm.id}`);
    const current = roleData?.[role]?.[perm.slug]?.granted ?? false;
    const endpoint = current ? "revoke" : "assign";
    try {
      const res = await apiFetch(`/permissions/roles/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role_name: role, permission_id: perm.id }),
      });
      if (res.ok) {
        addToast(`${current ? "Revoked" : "Assigned"} ${perm.name} ${current ? "from" : "to"} ${role}`, "success");
        loadRolePermissions();
      } else {
        const err = await res.json().catch(() => ({}));
        addToast(err.detail ?? "Failed to update permission", "error");
      }
    } catch {
      addToast("Network error", "error");
    } finally {
      setTogglingPermission(null);
    }
  };

  const handleBatchToggle = async (role: string, perms: Permission[], grant: boolean) => {
    if (togglingPermission) return;
    setTogglingPermission("batch");
    const endpoint = grant ? "assign" : "revoke";
    const label = grant ? "Granted" : "Revoked";
    let successCount = 0;
    let failCount = 0;
    for (const perm of perms) {
      try {
        const res = await apiFetch(`/permissions/roles/${endpoint}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ role_name: role, permission_id: perm.id }),
        });
        if (res.ok) successCount++;
        else failCount++;
      } catch {
        failCount++;
      }
    }
    addToast(`${label} ${successCount} permission${successCount !== 1 ? "s" : ""}${failCount > 0 ? ` (${failCount} failed)` : ""}`, failCount > 0 ? "warning" : "success");
    loadRolePermissions();
    setTogglingPermission(null);
  };

  const handleToggleOverride = async (perm: Permission, granted: boolean) => {
    if (!selectedUserId || togglingOverride) return;
    setTogglingOverride(perm.slug);
    try {
      const res = await apiFetch("/permissions/users/override", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: selectedUserId,
          permission_id: perm.id,
          is_granted: !granted,
        }),
      });
      if (res.ok) {
        addToast(`Updated override for ${perm.name}`, "success");
        loadUserOverrides(selectedUserId);
      } else {
        const err = await res.json().catch(() => ({}));
        addToast(err.detail ?? "Failed to update override", "error");
      }
    } catch {
      addToast("Network error", "error");
    } finally {
      setTogglingOverride(null);
    }
  };

  const handleUserSearch = () => {
    loadUsers(userSearch.trim() || undefined);
  };

  const handleSelectUser = (userId: number, userInfo?: { role: string; name: string }) => {
    setSelectedUserId(userId);
    if (userInfo) {
      setSelectedUserInfo(userInfo);
      setOverrideBaseRole(userInfo.role);
    }
    loadUserOverrides(userId);
  };

  const tabs: { key: PermissionTab; label: string; icon: any }[] = [
    { key: "categories", label: "Categories", icon: Lock },
    { key: "roles", label: "Role Permissions", icon: Shield },
    { key: "users", label: "User Overrides", icon: Users },
  ];

  const groupedByCategory = (permissions: Permission[]) => {
    const groups: Record<number, { name: string; permissions: Permission[] }> = {};
    for (const cat of categories) {
      const perms = permissions.filter((p) => p.category_id === cat.id);
      if (perms.length > 0) groups[cat.id] = { name: cat.name, permissions: perms };
    }
    const uncategorized = permissions.filter(
      (p) => !categories.some((c) => c.id === p.category_id)
    );
    if (uncategorized.length > 0) groups[-1] = { name: "Other", permissions: uncategorized };
    return groups;
  };

  const roleGroups = roleData && allPermissions.length > 0
    ? groupedByCategory(allPermissions)
    : {};

  return (
    <PanelContent>
      <PanelTabs
        items={tabs.map((t) => ({ key: t.key, label: t.label, icon: t.icon }))}
          value={activeTab}
          onChange={(k) => setActiveTab(k as PermissionTab)}
        />

        {activeTab === "categories" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Search className="h-4 w-4 text-text-muted" />
                <input
                  className="rounded border border-border bg-surface px-3 py-1.5 text-sm text-text"
                  placeholder="Search categories..."
                />
              </div>
              <Button onClick={() => setShowAddCategory(true)}>
                <Plus className="h-4 w-4 mr-1" /> New Category
              </Button>
            </div>

            {loading ? (
              <PanelLoadingState />
            ) : categories.length === 0 ? (
              <EmptyState icon={Lock} title="No Permission Categories" description="Create your first permission category to define access controls." />
            ) : (
              <div className="grid gap-3">
                {categories.map((cat) => (
                  <div key={cat.id} className="theme-card rounded-xl border overflow-hidden">
                    <div className="flex items-center justify-between gap-3 p-4 border-b border-border" role="heading" aria-level={2}>
                      <div className="flex items-center gap-3">
                        <button
                          className="text-text-muted hover:text-text"
                          onClick={() => setExpandedCategory(expandedCategory === cat.id ? null : cat.id)}
                        >
                          {expandedCategory === cat.id ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                        </button>
                        <div>
                          <span className="font-medium text-text">{cat.name}</span>
                          {cat.description && (
                            <span className="ml-2 text-xs text-text-muted">{cat.description}</span>
                          )}
                        </div>
                        <Badge variant={cat.is_active ? "default" : "outline"}>
                          {cat.permissions_count} permissions
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          className="text-text-muted hover:text-danger p-1"
                          onClick={() => handleDeleteCategory(cat.id)}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                    {expandedCategory === cat.id && (
                      <div className="p-4">
                        {cat.permissions.length === 0 ? (
                          <p className="text-sm text-text-muted py-4 text-center">No permissions in this category yet.</p>
                        ) : (
                          <div className="space-y-2">
                            {cat.permissions.map((perm) => (
                              <div key={perm.id} className="flex items-center justify-between rounded border border-border bg-surface-2 px-3 py-2">
                                <div>
                                  <span className="text-sm font-medium text-text">{perm.name}</span>
                                  <code className="ml-2 text-[10px] bg-surface-3 px-1.5 py-0.5 rounded text-text-muted">{perm.slug}</code>
                                  {perm.description && (
                                    <span className="ml-2 text-xs text-text-muted">{perm.description}</span>
                                  )}
                                </div>
                                <Badge variant={perm.scope === "global" ? "info" : "warning"}>
                                  {perm.scope}
                                </Badge>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "roles" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 flex-wrap">
                {ADMIN_ROLES.map((role) => (
                  <button
                    key={role}
                    className={`rounded-full px-3 py-1 text-xs font-medium transition ${
                      selectedRole === role
                        ? "bg-primary text-white"
                        : "bg-surface-2 text-text-muted hover:bg-surface-3"
                    }`}
                    onClick={() => setSelectedRole(role)}
                  >
                    {role.replace("_", " ")}
                  </button>
                ))}
                {!selectedRole && (
                  <span className="text-xs text-text-muted ml-2">Select a role to manage permissions</span>
                )}
              </div>
            </div>

            {!roleData ? (
              <PanelLoadingState />
            ) : selectedRole ? (
              <div className="space-y-4">
                {(() => {
                  const grantedCount = Object.values(roleData[selectedRole] || {}).filter((p) => p.granted).length;
                  const totalCount = Object.keys(roleData[selectedRole] || {}).length;
                  return (
                    <div className="flex items-center gap-3 rounded border border-border bg-surface-2 px-4 py-2 text-sm">
                      <Shield className="h-4 w-4 text-primary" />
                      <span className="font-medium text-text">{selectedRole.replace("_", " ")}</span>
                      <span className="text-text-muted">—</span>
                      <span className="text-success font-medium">{grantedCount} granted</span>
                      <span className="text-text-muted">/</span>
                      <span className="text-text">{totalCount} total</span>
                      {totalCount > 0 && (
                        <>
                          <span className="text-text-muted">—</span>
                          <span className="text-text-muted">
                            {Math.round((grantedCount / totalCount) * 100)}% coverage
                          </span>
                        </>
                      )}
                    </div>
                  );
                })()}
                {Object.entries(roleGroups).map(([catId, group]) => {
                  const allGrantedInCat = group.permissions.every(
                    (p) => roleData[selectedRole]?.[p.slug]?.granted
                  );
                  const anyGrantedInCat = group.permissions.some(
                    (p) => roleData[selectedRole]?.[p.slug]?.granted
                  );
                  return (
                  <div key={catId} className="theme-card rounded-xl border overflow-hidden">
                    <div className="flex items-center justify-between w-full p-4 border-b border-border" role="heading" aria-level={2}>
                      <span className="font-medium text-text">{group.name}</span>
                      <div className="flex items-center gap-1">
                        <Button variant="primary" onClick={() => handleBatchToggle(selectedRole, group.permissions, true)}
                          disabled={togglingPermission !== null}
                        >
                          <ToggleRight className="h-3 w-3" />
                          Grant All
                        </Button>
                        <Button variant="danger" className="flex items-center gap-1 rounded px-2 py-0.5 text-[10px] font-medium disabled:opacity-40" onClick={() => handleBatchToggle(selectedRole, group.permissions, false)}
                          disabled={togglingPermission !== null}
                        >
                          <ToggleLeft className="h-3 w-3" />
                          Deny All
                        </Button>
                      </div>
                    </div>
                    <div className="p-4">
                      <div className="space-y-2">
                        {group.permissions.map((perm) => {
                          const granted = roleData[selectedRole]?.[perm.slug]?.granted ?? false;
                          const isToggling = togglingPermission === `${selectedRole}:${perm.id}`;
                          return (
                            <div key={perm.id} className="flex items-center justify-between rounded border border-border bg-surface-2 px-3 py-2">
                              <div className="flex items-center gap-2">
                                <span className="text-sm text-text">{perm.name}</span>
                                <code className="text-[10px] bg-surface-3 px-1.5 py-0.5 rounded text-text-muted">{perm.slug}</code>
                              </div>
                              <button
                                className={`flex items-center gap-1.5 rounded px-2 py-1 text-xs font-medium transition ${
                                  granted
                                    ? "bg-success/10 text-success hover:bg-success/20"
                                    : "bg-surface-3 text-text-muted hover:bg-surface-1"
                                }`}
                                onClick={() => handleTogglePermission(selectedRole, perm)}
                                disabled={isToggling}
                              >
                                {isToggling ? (
                                  <Loader2 className="h-3 w-3 animate-spin" />
                                ) : granted ? (
                                  <Check className="h-3 w-3" />
                                ) : (
                                  <X className="h-3 w-3" />
                                )}
                                {granted ? "Granted" : "Denied"}
                              </button>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                );
              })}
              </div>
            ) : (
              <div className="py-12 text-center">
                <Shield className="h-12 w-12 text-text-muted mx-auto mb-3" />
                <h3 className="text-lg font-medium text-text mb-1">Select a Role</h3>
                <p className="text-sm text-text-muted">
                  Choose an admin role above to view and manage its permission assignments.
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === "users" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-1 space-y-3">
              <div className="theme-card rounded-xl border overflow-hidden">
                <div className="p-4 border-b border-border" role="heading" aria-level={2}>
                  <span className="font-medium text-text">Search Users</span>
                </div>
                <div className="p-4 space-y-2">
                  <div className="flex gap-2">
                    <input
                      className="flex-1 rounded border border-border bg-surface px-3 py-1.5 text-sm text-text"
                      placeholder="Name, email, or ID..."
                      value={userSearch}
                      onChange={(e) => setUserSearch(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleUserSearch()}
                    />
                    <Button size="sm" onClick={handleUserSearch}>
                      <Search className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                  {usersLoading ? (
                    <PanelLoadingState />
                  ) : users.length > 0 ? (
                    <div className="space-y-1 max-h-96 overflow-y-auto">
                      {users.map((u: any) => (
                        <button
                          key={u.id}
                          className={`w-full text-left rounded px-3 py-2 text-sm transition ${
                            selectedUserId === u.id
                              ? "bg-primary/10 text-primary"
                              : "hover:bg-surface-2 text-text"
                          }`}
                          onClick={() => handleSelectUser(u.id, { role: u.role || "admin", name: u.full_name || u.username || u.email })}
                        >
                          <div className="font-medium">{u.full_name || u.username || u.email}</div>
                          <div className="text-xs text-text-muted">{u.email} — {u.role}</div>
                        </button>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-text-muted text-center py-4">Search for users to manage overrides.</p>
                  )}
                </div>
              </div>
            </div>

            <div className="lg:col-span-2">
              {selectedUserId ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-medium text-text">
                      Permission Overrides for {selectedUserInfo?.name || `User #${selectedUserId}`}
                    </h3>
                    <Badge variant="info">Role: {selectedUserInfo?.role || overrideBaseRole}</Badge>
                    <div className="flex items-center gap-1 ml-2">
                      <span className="text-[10px] text-text-muted">Base role:</span>
                      <select
                        className="rounded border border-border bg-surface px-1.5 py-0.5 text-[10px] text-text"
                        value={overrideBaseRole}
                        onChange={(e) => {
                          setOverrideBaseRole(e.target.value);
                          if (selectedUserId) setTimeout(() => loadUserOverrides(selectedUserId), 0);
                        }}
                      >
                        {ADMIN_ROLES.map((r) => (
                          <option key={r} value={r}>{r.replace("_", " ")}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  {userOverridesLoading ? (
                    <PanelLoadingState />
                  ) : allPermissions.length > 0 ? (
                    Object.entries(roleGroups).map(([catId, group]) => (
                      <div key={catId} className="theme-card rounded-xl border overflow-hidden">
                        <div className="p-4 border-b border-border" role="heading" aria-level={2}>
                          <span className="font-medium text-text">{group.name}</span>
                        </div>
                        <div className="p-4">
                          <div className="space-y-2">
                            {group.permissions.map((perm) => {
                              const granted = userOverrides?.[perm.slug]?.granted ?? false;
                              const isToggling = togglingOverride === perm.slug;
                              return (
                                <div key={perm.id} className="flex items-center justify-between rounded border border-border bg-surface-2 px-3 py-2">
                                  <div className="flex items-center gap-2">
                                    <span className="text-sm text-text">{perm.name}</span>
                                    <code className="text-[10px] bg-surface-3 px-1.5 py-0.5 rounded text-text-muted">{perm.slug}</code>
                                  </div>
                                  <button
                                    className={`flex items-center gap-1.5 rounded px-2 py-1 text-xs font-medium transition ${
                                      granted
                                        ? "bg-success/10 text-success hover:bg-success/20"
                                        : "bg-surface-3 text-text-muted hover:bg-surface-1"
                                    }`}
                                    onClick={() => handleToggleOverride(perm, granted)}
                                    disabled={isToggling}
                                  >
                                    {isToggling ? (
                                      <Loader2 className="h-3 w-3 animate-spin" />
                                    ) : granted ? (
                                      <Check className="h-3 w-3" />
                                    ) : (
                                      <X className="h-3 w-3" />
                                    )}
                                    {granted ? "Granted" : "Denied"}
                                  </button>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                    ))
                  ) : null}
                </div>
              ) : (
                <div className="py-12 text-center">
                  <Users className="h-12 w-12 text-text-muted mx-auto mb-3" />
                  <h3 className="text-lg font-medium text-text mb-1">User Permission Overrides</h3>
                  <p className="text-sm text-text-muted">
                    Search for a user on the left to view and manage their individual permission overrides.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

      <Modal isOpen={showAddCategory} onClose={() => setShowAddCategory(false)} title="New Permission Category">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text mb-1">Name *</label>
            <input
              className="w-full rounded border border-border bg-surface px-3 py-2 text-sm text-text"
              value={catName}
              onChange={(e) => setCatName(e.target.value)}
              placeholder="e.g., Inventory Management"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text mb-1">Description</label>
            <textarea
              className="w-full rounded border border-border bg-surface px-3 py-2 text-sm text-text"
              value={catDesc}
              onChange={(e) => setCatDesc(e.target.value)}
              placeholder="What permissions does this category group?"
              rows={2}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text mb-1">Icon</label>
            <input
              className="w-full rounded border border-border bg-surface px-3 py-2 text-sm text-text"
              value={catIcon}
              onChange={(e) => setCatIcon(e.target.value)}
              placeholder="icon name (e.g., Package)"
            />
          </div>
        </div>
        <ModalFooter>
          <Button variant="ghost" onClick={() => setShowAddCategory(false)}>Cancel</Button>
          <Button onClick={handleAddCategory} disabled={submitting}>
            {submitting ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Plus className="h-4 w-4 mr-1" />}
            Create Category
          </Button>
        </ModalFooter>
        </Modal>
      </PanelContent>
  );
}

