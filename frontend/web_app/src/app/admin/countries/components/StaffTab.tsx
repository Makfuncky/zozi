"use client";

import { Fragment } from "react";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Save, Trash2, Plus, Eye, UploadCloud, RefreshCw, Edit3, X, Check } from "@/lib/icons";
import type { CountriesTabProps } from "./CountriesTabProps";

export default function StaffTab({
  ...p
}: CountriesTabProps) {
  const { addToast, countries, country, newStaffEmail, newStaffRole, newStaffUserId, newStaffUserName, selectedCountryCode, staffAssignments, setNewStaffEmail, setNewStaffRole, setNewStaffUserId, setNewStaffUserName, setStaffAssignments } = p;

  return (
    <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
      <h3 className="text-sm font-bold text-text">Staff Assignments & Role Management</h3>
      <p className="text-xs text-text-muted">Assign country-specific roles to users (Country Head, Country Manager, Country Finance).</p>

      <div className="space-y-4">
        <div className="border-t border-border pt-4">
          <h4 className="text-xs font-bold text-text mb-2">Assign New Staff</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            <label className="space-y-1 text-[10px] text-text-muted">
              User ID
              <input
                type="text"
                className="w-full rounded border border-border bg-surface px-2 py-1 text-xs text-text"
                value={newStaffUserId}
                onChange={(e) => setNewStaffUserId(e.target.value)}
                placeholder="12345"
              />
            </label>
            <label className="space-y-1 text-[10px] text-text-muted">
              User Name
              <input
                type="text"
                className="w-full rounded border border-border bg-surface px-2 py-1 text-xs text-text"
                value={newStaffUserName}
                onChange={(e) => setNewStaffUserName(e.target.value)}
                placeholder="John Doe"
              />
            </label>
            <label className="space-y-1 text-[10px] text-text-muted">
              Email
              <input
                type="email"
                className="w-full rounded border border-border bg-surface px-2 py-1 text-xs text-text"
                value={newStaffEmail}
                onChange={(e) => setNewStaffEmail(e.target.value)}
                placeholder="john@example.com"
              />
            </label>
            <label className="space-y-1 text-[10px] text-text-muted">
              Role
              <select
                className="w-full rounded border border-border bg-surface px-2 py-1 text-xs text-text"
                value={newStaffRole}
                onChange={(e) => setNewStaffRole(e.target.value as any)}
              >
                <option value="country_manager">Country Manager</option>
                <option value="country_head">Country Head</option>
                <option value="country_finance">Country Finance</option>
              </select>
            </label>
          </div>
          <Button variant="primary" className="mt-2 inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold hover:opacity-90 transition disabled:opacity-60" type="button"
            disabled={!newStaffUserId || !newStaffUserName}
            onClick={async () => {
              try {
                const res = await apiFetch(`/admin/countries/${selectedCountryCode}/staff`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    user_id: Number(newStaffUserId),
                    user_name: newStaffUserName,
                    email: newStaffEmail,
                    role: newStaffRole,
                  }),
                });
                if (!res.ok) throw new Error("Failed to assign");
                addToast("Staff assigned", "success");
                setNewStaffUserId("");
                setNewStaffUserName("");
                setNewStaffEmail("");
                if (res.ok) {
                  const data = await parseJsonResponse(res);
                  setStaffAssignments(Array.isArray(data) ? data : []);
                }
              } catch (err: any) {
                addToast(err.message, "error");
              }
            }}
          >
            <Plus className="h-3.5 w-3.5" />
            Assign Staff
          </Button>
        </div>

        <div className="border-t border-border pt-4">
          <h4 className="text-xs font-bold text-text mb-2">Assigned Staff</h4>
          {staffAssignments.length === 0 ? (
            <p className="text-sm text-text-muted italic">No staff assigned to this country.</p>
          ) : (
            <div className="space-y-2">
              {staffAssignments.map((staff) => (
                <div key={staff.user_id} className="flex items-center justify-between rounded-lg border border-border bg-surface p-3 text-xs">
                  <div>
                    <span className="font-medium text-text">{staff.user_name}</span>
                    <span className="text-text-muted ml-2">({staff.email})</span>
                    <div className="text-text-faint mt-1">Role: <span className="font-medium">{staff.role.replace("_", " ")}</span></div>
                  </div>
                  <Button variant="danger" className="p-1 rounded transition" type="button"
                    onClick={async () => {
                      try {
                        await apiFetch(`/admin/countries/${selectedCountryCode}/staff/${staff.user_id}`, { method: "DELETE" });
                        addToast("Staff removed", "success");
                        setStaffAssignments(staffAssignments.filter((s) => s.user_id !== staff.user_id));
                      } catch {
                        addToast("Failed to remove staff", "error");
                      }
                    }}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
