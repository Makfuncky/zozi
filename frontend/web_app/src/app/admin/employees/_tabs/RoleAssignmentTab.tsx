"use client";

import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import {
  UserCog,
  Plus,
  X,
  Check,
  Shield,
  AlertCircle,
  Search,
  Briefcase,
} from "lucide-react";
import { apiFetch } from "@/lib/api";
import { useToastStore } from "@/stores/toastStore";
import { Employee } from "../employee-types";

interface RoleDefinition {
  id: number;
  role_id: string;
  role_name: string;
  department: string | null;
  description: string | null;
  icon: string | null;
  color: string | null;
}

interface RoleAssignment {
  id: number;
  role: string;
  department: string | null;
  is_primary: boolean;
  assigned_at: string;
}

const AVAILABLE_ROLES: RoleDefinition[] = [
  { id: 1, role_id: "moderator", role_name: "Content Moderator", department: "Content", description: "Moderate reviews, product descriptions, user content", icon: "shield", color: "blue" },
  { id: 2, role_id: "supplier_coordinator", role_name: "Supplier Coordinator", department: "Procurement", description: "Manage supplier relationships, orders, issues", icon: "truck", color: "green" },
  { id: 3, role_id: "customer_coordinator", role_name: "Customer Coordinator", department: "Support", description: "Handle customer tickets, returns, escalations", icon: "headphones", color: "purple" },
  { id: 4, role_id: "promotion_manager", role_name: "Promotion Manager", department: "Marketing", description: "Create/manage campaigns, deals, banners", icon: "megaphone", color: "orange" },
  { id: 5, role_id: "order_fulfillment", role_name: "Order Fulfillment", department: "Warehouse", description: "Process orders, manage inventory, shipping", icon: "package", color: "brown" },
  { id: 6, role_id: "delivery_coordinator", role_name: "Delivery Coordinator", department: "Logistics", description: "Manage drivers, routes, tracking", icon: "map-pin", color: "red" },
  { id: 7, role_id: "finance_clerk", role_name: "Finance Clerk", department: "Finance", description: "Process invoices, payments, reconciliation", icon: "dollar-sign", color: "green" },
  { id: 8, role_id: "hr_coordinator", role_name: "HR Coordinator", department: "HR", description: "Assist with employee records, onboarding", icon: "users", color: "blue" },
  { id: 9, role_id: "data_entry", role_name: "Data Entry", department: "Operations", description: "Enter/update product data, catalog management", icon: "database", color: "gray" },
  { id: 10, role_id: "quality_analyst", role_name: "Quality Analyst", department: "Quality", description: "Check product quality, handle complaints", icon: "check-circle", color: "green" },
  { id: 11, role_id: "social_media", role_name: "Social Media Manager", department: "Marketing", description: "Manage social posts, engagement", icon: "share-2", color: "pink" },
  { id: 12, role_id: "inventory_manager", role_name: "Inventory Manager", department: "Warehouse", description: "Track stock, manage warehouses, reorder", icon: "archive", color: "orange" },
  { id: 13, role_id: "returns_processor", role_name: "Returns Processor", department: "Support", description: "Process returns, refunds, exchanges", icon: "rotate-ccw", color: "red" },
  { id: 14, role_id: "content_writer", role_name: "Content Writer", department: "Content", description: "Write product descriptions, blog posts", icon: "edit-3", color: "blue" },
  { id: 15, role_id: "photography_editor", role_name: "Photography Editor", department: "Media", description: "Edit product images, manage media library", icon: "camera", color: "purple" },
  { id: 16, role_id: "accounts_payable", role_name: "Accounts Payable", department: "Finance", description: "Process supplier invoices, payments", icon: "credit-card", color: "green" },
  { id: 17, role_id: "accounts_receivable", role_name: "Accounts Receivable", department: "Finance", description: "Track customer payments, follow-ups", icon: "trending-up", color: "blue" },
];

export default function RoleAssignmentTab() {
  const { addToast } = useToastStore();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null);
  const [employeeRoles, setEmployeeRoles] = useState<RoleAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [showAssignModal, setShowAssignModal] = useState(false);

  const fetchEmployees = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch("/api/v1/admin/hr/employees");
      if (res.ok) {
        const data = await res.json();
        setEmployees(data.employees || data || []);
      }
    } catch {
      setEmployees([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchEmployeeRoles = useCallback(async (employeeId: number) => {
    try {
      const res = await apiFetch(`/api/v1/admin/hr/employees/${employeeId}/roles`);
      if (res.ok) {
        setEmployeeRoles(await res.json());
      }
    } catch {
      setEmployeeRoles([]);
    }
  }, []);

  useEffect(() => {
    fetchEmployees();
  }, [fetchEmployees]);

  useEffect(() => {
    if (selectedEmployee) {
      fetchEmployeeRoles(selectedEmployee.id);
    }
  }, [selectedEmployee, fetchEmployeeRoles]);

  const handleAssignRole = async (roleId: string, isPrimary: boolean) => {
    if (!selectedEmployee) return;
    setSaving(true);
    try {
      const res = await apiFetch(`/api/v1/admin/hr/employees/${selectedEmployee.id}/roles`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role: roleId, is_primary: isPrimary }),
      });
      if (res.ok) {
        addToast("Role assigned successfully", "success");
        fetchEmployeeRoles(selectedEmployee.id);
        setShowAssignModal(false);
      } else {
        addToast("Failed to assign role", "error");
      }
    } catch {
      addToast("Failed to assign role", "error");
    } finally {
      setSaving(false);
    }
  };

  const handleRevokeRole = async (role: string) => {
    if (!selectedEmployee) return;
    setSaving(true);
    try {
      const res = await apiFetch(`/api/v1/admin/hr/employees/${selectedEmployee.id}/roles/${role}`, {
        method: "DELETE",
      });
      if (res.ok) {
        addToast("Role revoked successfully", "success");
        fetchEmployeeRoles(selectedEmployee.id);
      } else {
        addToast("Failed to revoke role", "error");
      }
    } catch {
      addToast("Failed to revoke role", "error");
    } finally {
      setSaving(false);
    }
  };

  const filteredEmployees = employees.filter((emp) =>
    emp.full_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    emp.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    emp.employee_code?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const assignedRoleIds = employeeRoles.map((r) => r.role);
  const availableRoles = AVAILABLE_ROLES.filter((r) => !assignedRoleIds.includes(r.role_id));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-text">Role Assignment</h2>
          <p className="text-sm text-text-muted mt-1">
            Assign work roles to employees. Each role determines what tools and features the employee sees.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 rounded-xl bg-surface-2 animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Employee List */}
          <div className="rounded-xl border border-border bg-surface">
            <div className="border-b border-border p-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
                <input
                  type="text"
                  placeholder="Search employees..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full rounded-lg border border-border bg-surface-2 pl-10 pr-4 py-2 text-sm"
                />
              </div>
            </div>
            <div className="max-h-96 overflow-y-auto">
              {filteredEmployees.length === 0 ? (
                <div className="p-8 text-center">
                  <AlertCircle className="h-8 w-8 mx-auto mb-2 text-text-muted" />
                  <p className="text-sm text-text-muted">No employees found</p>
                </div>
              ) : (
                filteredEmployees.map((emp) => (
                  <button
                    key={emp.id}
                    onClick={() => setSelectedEmployee(emp)}
                    className={`w-full flex items-center gap-3 p-4 text-left transition-colors hover:bg-surface-2 ${
                      selectedEmployee?.id === emp.id ? "bg-primary/5 border-l-2 border-primary" : ""
                    }`}
                  >
                    <div className="rounded-full bg-primary/10 p-2">
                      <Briefcase className="h-4 w-4 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-text truncate">
                        {emp.full_name || emp.name || "Unknown"}
                      </p>
                      <p className="text-xs text-text-muted truncate">
                        {emp.email} • {emp.department || "No department"}
                      </p>
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Role Assignment Panel */}
          <div className="rounded-xl border border-border bg-surface">
            <div className="border-b border-border p-4 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-text">
                {selectedEmployee
                  ? `Roles for ${selectedEmployee.full_name || selectedEmployee.name}`
                  : "Select an employee"}
              </h3>
              {selectedEmployee && (
                <button
                  onClick={() => setShowAssignModal(true)}
                  className="flex items-center gap-1 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-white hover:bg-primary/90"
                >
                  <Plus className="h-3 w-3" />
                  Assign Role
                </button>
              )}
            </div>
            <div className="p-4">
              {!selectedEmployee ? (
                <div className="text-center py-8">
                  <UserCog className="h-12 w-12 mx-auto mb-3 text-text-muted" />
                  <p className="text-sm text-text-muted">Select an employee to manage their roles</p>
                </div>
              ) : employeeRoles.length === 0 ? (
                <div className="text-center py-8">
                  <Shield className="h-12 w-12 mx-auto mb-3 text-text-muted" />
                  <p className="text-sm text-text-muted">No roles assigned</p>
                  <p className="text-xs text-text-muted mt-1">Click &quot;Assign Role&quot; to get started</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {employeeRoles.map((assignment) => {
                    const roleDef = AVAILABLE_ROLES.find((r) => r.role_id === assignment.role);
                    return (
                      <div
                        key={assignment.id}
                        className="flex items-center justify-between rounded-lg border border-border bg-surface-2 p-3"
                      >
                        <div className="flex items-center gap-3">
                          <div className="rounded-lg bg-primary/10 p-2">
                            <Shield className="h-4 w-4 text-primary" />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-text">
                              {roleDef?.role_name || assignment.role}
                              {assignment.is_primary && (
                                <span className="ml-2 rounded-full bg-success/10 px-2 py-0.5 text-xs text-success">
                                  Primary
                                </span>
                              )}
                            </p>
                            <p className="text-xs text-text-muted">
                              {roleDef?.department || assignment.department}
                            </p>
                          </div>
                        </div>
                        <button
                          onClick={() => handleRevokeRole(assignment.role)}
                          disabled={saving}
                          className="rounded-lg p-1.5 text-text-muted hover:bg-danger/10 hover:text-danger"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Assign Role Modal */}
      {showAssignModal && selectedEmployee && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-full max-w-md rounded-xl bg-surface p-6 shadow-xl"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text">Assign Role</h3>
              <button
                onClick={() => setShowAssignModal(false)}
                className="rounded-lg p-1.5 text-text-muted hover:bg-surface-2"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <p className="text-sm text-text-muted mb-4">
              Select a role to assign to <strong>{selectedEmployee.full_name || selectedEmployee.name}</strong>
            </p>
            <div className="max-h-64 overflow-y-auto space-y-2">
              {availableRoles.length === 0 ? (
                <p className="text-sm text-text-muted text-center py-4">All roles already assigned</p>
              ) : (
                availableRoles.map((role) => (
                  <button
                    key={role.role_id}
                    onClick={() => handleAssignRole(role.role_id, employeeRoles.length === 0)}
                    disabled={saving}
                    className="w-full flex items-center gap-3 rounded-lg border border-border p-3 text-left hover:bg-surface-2 transition-colors"
                  >
                    <div className="rounded-lg bg-primary/10 p-2">
                      <Shield className="h-4 w-4 text-primary" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-text">{role.role_name}</p>
                      <p className="text-xs text-text-muted">{role.description}</p>
                    </div>
                  </button>
                ))
              )}
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
