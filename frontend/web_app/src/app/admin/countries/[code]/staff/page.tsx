"use client";

import { Button } from "@/components/ui/Button";

import { useEffect, useState, useMemo, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  UserPlus,
  Trash2,
  Shield,
  MapPin,
  X,
  Check,
} from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { useToastStore } from "@/lib/toastStore";
import { isAdminStaffRole } from "@shared/adminPermissions";
import { EnterpriseDataTable, type EnterpriseColumn } from "@shared/components/EnterpriseDataTable";
import { dc, useDensity } from "@/lib/densityContext";

interface CountryStaff {
  id: number;
  user_id: number;
  full_name: string;
  email: string;
  role: "country_manager" | "country_head" | "admin";
  is_active: boolean;
}

interface AvailableStaff {
  id: number;
  user_id: number;
  full_name: string;
  email: string;
  current_role: string | null;
}

export default function CountryStaffPage() {
  const params = useParams<{ code: string }>();
  const router = useRouter();
  const { user, isLoggedIn, isLoading } = useAuth();
  const { addToast } = useToastStore();

  const { density } = useDensity();
  const countryCode = params?.code?.toUpperCase() ?? "";

  const [loading, setLoading] = useState(true);
  const [countryStaff, setCountryStaff] = useState<CountryStaff[]>([]);
  const [availableStaff, setAvailableStaff] = useState<AvailableStaff[]>([]);
  const [selectedStaff, setSelectedStaff] = useState<AvailableStaff | null>(null);
  const [assigning, setAssigning] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const modalRef = useRef<HTMLDivElement>(null);
  const triggerButtonRef = useRef<HTMLButtonElement>(null);

  // Focus management for modal
  useEffect(() => {
    if (showAssignModal && modalRef.current) {
      // Focus the first focusable element in the modal
      const focusable = modalRef.current.querySelector(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      ) as HTMLElement;
      focusable?.focus();
    }
  }, [showAssignModal]);

  const handleCloseModal = () => {
    setShowAssignModal(false);
    triggerButtonRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      handleCloseModal();
    }
  };

  useEffect(() => {
    if (isLoading) return;
    if (!isLoggedIn || !isAdminStaffRole(user?.role ?? null)) {
      router.push("/admin/login");
      return;
    }
    if (!countryCode) return;

    const loadData = async () => {
      setLoading(true);
      try {
        const [staffRes, availableRes] = await Promise.all([
          apiFetch(`/admin/countries/${countryCode}/staff`),
          apiFetch(`/admin/staff?assignable=true`),
        ]);

        if (staffRes.ok) {
          const data = await staffRes.json().catch(() => null);
          setCountryStaff(Array.isArray(data) ? data : []);
        }

        if (availableRes.ok) {
          const data = await availableRes.json().catch(() => null);
          setAvailableStaff(Array.isArray(data) ? data : []);
        }
      } catch {
        addToast("Failed to load staff data", "error");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [isLoading, isLoggedIn, user, router, countryCode, addToast]);

  const handleAssign = async () => {
    if (!selectedStaff || !countryCode) return;
    setAssigning(true);
    try {
      const res = await apiFetch(`/admin/countries/${countryCode}/staff`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: selectedStaff.user_id, role: selectedStaff.current_role }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to assign staff");
      }

      addToast(`${selectedStaff.full_name} assigned to ${countryCode}`, "success");
      setShowAssignModal(false);
      setSelectedStaff(null);

      // Refresh list
      const staffRes = await apiFetch(`/admin/countries/${countryCode}/staff`);
      if (staffRes.ok) {
        setCountryStaff(await staffRes.json());
      }
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Assignment failed", "error");
    } finally {
      setAssigning(false);
    }
  };

  const handleUnassign = async (staffId: number) => {
    if (!countryCode) return;
    try {
      const res = await apiFetch(`/admin/countries/${countryCode}/staff/${staffId}`, {
        method: "DELETE",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to unassign staff");
      }

      addToast("Staff unassigned", "success");
      setCountryStaff((prev) => prev.filter((s) => s.id !== staffId));
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Unassignment failed", "error");
    }
  };

  const bodyText = dc(density, "text-[10px]", "text-xs", "text-sm");

  const columns = useMemo<Array<EnterpriseColumn<CountryStaff>>>(() => [
    {
      key: "full_name",
      label: "Staff",
      sortable: true,
      searchValue: (s) => `${s.full_name} ${s.email}`,
      render: (s) => (
        <div>
          <p className={`font-semibold text-text ${bodyText}`}>{s.full_name}</p>
          <p className={`${bodyText} text-text-muted`}>{s.email}</p>
        </div>
      ),
    },
    {
      key: "role",
      label: "Role",
      sortable: true,
      render: (s) => (
        <span
          className={`inline-flex rounded-full px-2 py-0.5 font-semibold ${bodyText} ${
            s.role === "admin"
              ? "bg-warning/10 text-warning"
              : s.role === "country_manager"
              ? "bg-primary/10 text-primary"
              : "bg-info/10 text-info"
          }`}
        >
          {s.role.replace("_", " ")}
        </span>
      ),
    },
    {
      key: "is_active",
      label: "Status",
      sortable: true,
      render: (s) => (
        <span
          className={`inline-flex rounded-full px-2 py-0.5 font-semibold ${bodyText} ${
            s.is_active ? "bg-success/10 text-success" : "bg-danger/10 text-danger"
          }`}
        >
          {s.is_active ? "Active" : "Inactive"}
        </span>
      ),
    },
  ], [bodyText]);

  if (isLoading || loading) {
    return (
      <AdminLayout title={`Country ${countryCode} - Staff`}>
        <PanelLoadingState count={3} />
      </AdminLayout>
    );
  }

  return (
    <AdminLayout title={`Country ${countryCode} - Staff`} headerMode="compact">
      <PanelContent className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-text">Staff Assignment</h2>
            <p className="text-xs text-text-muted">Manage staff assigned to {countryCode}</p>
          </div>
<button
              ref={triggerButtonRef}
              onClick={() => setShowAssignModal(true)}
              className="theme-btn-primary rounded-xl px-3 py-2 text-xs font-semibold flex items-center gap-2"
            >
              <UserPlus className="h-3.5 w-3.5" />
              Assign Staff
            </button>
        </div>

        <EnterpriseDataTable
          columns={columns}
          rows={countryStaff}
          rowKey={(r) => r.id}
          searchPlaceholder="Search by name or email..."
          emptyState="No staff assigned to this country yet."
          rowActions={(row) => (
            <Button variant="danger" className="rounded-md border border-danger/40 px-2 py-1 text-[11px] font-semibold text-danger" onClick={() => handleUnassign(row.id)}
            >
              Unassign
            </Button>
          )}
        />

        {/* Assign Modal */}
        {showAssignModal && (
          <div
            className="theme-overlay fixed inset-0 z-50 flex items-center justify-center p-4"
            onClick={handleCloseModal}
            onKeyDown={handleKeyDown}
            role="dialog"
            aria-modal="true"
            aria-labelledby="modal-title"
            tabIndex={-1}
          >
            <div
              ref={modalRef}
              className="theme-card w-full max-w-md rounded-2xl border p-6"
              onClick={(e) => e.stopPropagation()}
              role="document"
            >
              <h3 id="modal-title" className="text-lg font-bold text-text mb-4">
                Assign Staff to {countryCode}
              </h3>
              
              <div className="space-y-4">
                <p className="text-sm text-text-muted">
                  Select a staff member to assign to {countryCode}. They will gain access to country-specific tasks.
                </p>

                <select
                  value={selectedStaff?.user_id ?? ""}
                  onChange={(e) => {
                    const staff = availableStaff.find((s) => s.user_id === Number(e.target.value));
                    setSelectedStaff(staff ?? null);
                  }}
                  className="theme-input w-full rounded-xl border px-3 py-2 text-sm"
                  aria-label="Select staff member"
                >
                  <option value="">Select staff member</option>
                  {availableStaff.map((staff) => (
                    <option key={staff.user_id} value={staff.user_id}>
                      {staff.full_name} ({staff.email})
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex justify-end gap-2 mt-6">
                <button
                  onClick={handleCloseModal}
                  className="theme-btn-secondary rounded-lg px-4 py-2 text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAssign}
                  disabled={assigning || !selectedStaff}
                  className="theme-btn-primary rounded-lg px-4 py-2 text-xs font-semibold disabled:opacity-50"
                >
                  {assigning ? "Assigning..." : "Assign"}
                </button>
              </div>
            </div>
          </div>
        )}
      </PanelContent>
    </AdminLayout>
  );
}