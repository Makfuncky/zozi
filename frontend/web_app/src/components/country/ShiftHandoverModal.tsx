"use client";

import { Button } from "@/components/ui/Button";

import { useState } from "react";
import { FileText, UserCheck, Calendar, Shield, X, Save } from "@/lib/icons";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";

interface ShiftHandoverModalProps {
  countryCode: string;
  isOpen: boolean;
  onClose: () => void;
}

interface HandoverData {
  outgoingStaff: string;
  incomingStaff: string;
  notes: string;
  acknowledgment: string;
}

export default function ShiftHandoverModal({ countryCode, isOpen, onClose }: ShiftHandoverModalProps) {
  const addToast = useToastStore((state) => state.addToast);
  const [outgoingStaff, setOutgoingStaff] = useState("");
  const [incomingStaff, setIncomingStaff] = useState("");
  const [notes, setNotes] = useState("");
  const [acknowledgment, setAcknowledgment] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    if (!outgoingStaff || !incomingStaff || !acknowledgment) {
      addToast("Outgoing staff, incoming staff, and acknowledgment are required", "warning");
      return;
    }

    setSaving(true);
    try {
      const response = await apiFetch(`/admin/countries/${countryCode}/shift-handover`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          outgoing_staff: outgoingStaff,
          incoming_staff: incomingStaff,
          notes,
          acknowledgment,
        }),
      });

      const data = await parseJsonResponse(response);
      if (!response.ok) {
        throw new Error(data?.detail || "Failed to create handover");
      }

      addToast("Shift handover completed", "success");
      onClose();
    } catch (err: any) {
      addToast(err.message, "error");
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4" onClick={onClose}>
      <div className="theme-modal-card w-full max-w-lg m-0 max-h-[90vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        <div className="p-4 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            <h3 className="text-sm font-bold text-text">Shift Handover Log</h3>
          </div>
          <button onClick={onClose} className="text-text-muted hover:text-text transition">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="p-4 space-y-3 flex-1 overflow-y-auto">
          <div className="grid grid-cols-2 gap-3">
            <label className="space-y-1 text-xs text-text-muted">
              Outgoing Staff *
              <input
                type="text"
                className="w-full rounded border border-border bg-surface px-3 py-2 text-sm text-text"
                value={outgoingStaff}
                onChange={(e) => setOutgoingStaff(e.target.value)}
                placeholder="Name or ID"
              />
            </label>
            <label className="space-y-1 text-xs text-text-muted">
              Incoming Staff *
              <input
                type="text"
                className="w-full rounded border border-border bg-surface px-3 py-2 text-sm text-text"
                value={incomingStaff}
                onChange={(e) => setIncomingStaff(e.target.value)}
                placeholder="Name or ID"
              />
            </label>
          </div>

          <label className="space-y-1 text-xs text-text-muted">
            Notes (Optional)
            <textarea
              className="w-full rounded border border-border bg-surface px-3 py-2 text-sm text-text resize-none"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Key information for incoming staff..."
              rows={4}
            />
          </label>

          <label className="space-y-1 text-xs text-text-muted">
            Digital Acknowledgment *
            <textarea
              className="w-full rounded border border-border bg-surface px-3 py-2 text-sm text-text resize-none font-mono"
              value={acknowledgment}
              onChange={(e) => setAcknowledgment(e.target.value)}
              placeholder="Type 'I ACKNOWLEDGE' to confirm"
              rows={2}
            />
          </label>

          <div className="border border-border rounded-lg p-3 bg-warning/5">
            <div className="flex items-start gap-2">
              <Shield className="h-4 w-4 text-warning mt-0.5" />
              <div className="text-xs text-text-muted">
                <p className="font-semibold text-warning mb-1">Legal Notice</p>
                <p>This handover log is legally binding. The acknowledgment serves as a digital signature confirming receipt of all operational responsibilities.</p>
              </div>
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-border flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-lg border border-border px-3 py-2 text-xs font-semibold text-text-muted hover:bg-surface-2 transition"
          >
            Cancel
          </button>
          <Button variant="primary" onClick={handleSubmit}
            disabled={saving || acknowledgment !== "I ACKNOWLEDGE"}>
            {saving ? (
              <>
                <div className="animate-spin rounded-full h-3 w-3 border-2 border-white border-t-transparent" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-3.5 w-3.5" />
                Complete Handover
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}


