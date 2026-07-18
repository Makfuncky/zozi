"use client";

import { Button } from "@/components/ui/Button";

import { useState } from "react";
import { UserPlus, X, Save, ShieldCheck } from "@/lib/icons";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";

interface StaffAssignment {
  user_id: number;
  user_name: string;
  email: string;
  role: "country_head" | "country_manager" | "country_finance";
}

interface CountryStaffAssignmentModalProps {
  countryCode: string;
  isOpen: boolean;
  onClose: () => void;
  onAssigned: () => void;
}

export default function CountryStaffAssignmentModal({
  countryCode,
  isOpen,
  onClose,
  onAssigned,
}: CountryStaffAssignmentModalProps) {
  const addToast = useToastStore((state) => state.addToast);
  const [userId, setUserId] = useState("");
  const [userName, setUserName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"country_head" | "country_manager" | "country_finance">("country_manager");
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    if (!userId || !userName || !email) {
      addToast("User ID, name, and email are required", "warning");
      return;
    }

    setSaving(true);
    try {
      const response = await apiFetch(`/admin/countries/${countryCode}/staff`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: parseInt(userId, 10),
          user_name: userName,
          email,
          role,
        }),
      });

      const data = await parseJsonResponse(response);
      if (!response.ok) {
        throw new Error(data?.detail || "Failed to assign staff");
      }

      addToast(`${userName} assigned as ${role.replace("_", " ")}`, "success");
      setUserId("");
      setUserName("");
      setEmail("");
      setRole("country_manager");
      onAssigned();
    } catch (err: any) {
      addToast(err.message, "error");
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4" onClick={onClose}>
      <div className="theme-modal-card w-full max-w-md m-0" onClick={(e) => e.stopPropagation()}>
        <div className="p-4 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <UserPlus className="h-5 w-5 text-primary" />
            <h3 className="text-sm font-bold text-text">Assign Country Staff</h3>
          </div>
          <button onClick={onClose} className="text-text-muted hover:text-text transition">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="p-4 space-y-3">
          <label className="space-y-1 text-xs text-text-muted">
            User ID *
            <input
              type="number"
              className="w-full rounded border border-border bg-surface px-3 py-2 text-sm text-text"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="12345"
            />
          </label>

          <label className="space-y-1 text-xs text-text-muted">
            User Name *
            <input
              type="text"
              className="w-full rounded border border-border bg-surface px-3 py-2 text-sm text-text"
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
              placeholder="John Doe"
            />
          </label>

          <label className="space-y-1 text-xs text-text-muted">
            Email *
            <input
              type="email"
              className="w-full rounded border border-border bg-surface px-3 py-2 text-sm text-text"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="john@example.com"
            />
          </label>

          <label className="space-y-1 text-xs text-text-muted">
            Role
            <select
              className="w-full rounded border border-border bg-surface px-3 py-2 text-sm text-text"
              value={role}
              onChange={(e) => setRole(e.target.value as any)}
            >
              <option value="country_manager">Country Manager</option>
              <option value="country_head">Country Head</option>
              <option value="country_finance">Country Finance</option>
            </select>
          </label>
        </div>

        <div className="p-4 border-t border-border flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-lg border border-border px-3 py-2 text-xs font-semibold text-text-muted hover:bg-surface-2 transition"
          >
            Cancel
          </button>
          <Button variant="primary" onClick={handleSubmit}
            disabled={saving}>
            {saving ? (
              <>
                <div className="animate-spin rounded-full h-3 w-3 border-2 border-white border-t-transparent" />
                Assigning...
              </>
            ) : (
              <>
                <ShieldCheck className="h-3.5 w-3.5" />
                Assign Staff
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}


