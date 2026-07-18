"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import SupplierLayout from "@/components/SupplierLayout";
import { PanelContent, PanelHero, PanelLoadingState } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";
import { Bell, RefreshCw } from "@/lib/icons";

type PreferenceField =
  | "notify_new_order"
  | "notify_low_stock"
  | "notify_payout_processed"
  | "notify_doc_expiry"
  | "notify_return_updates"
  | "notify_dispute_updates"
  | "in_app_enabled"
  | "email_enabled"
  | "push_enabled";

interface SupplierNotificationPreferences {
  supplier_id: number;
  notify_new_order: boolean;
  notify_low_stock: boolean;
  notify_payout_processed: boolean;
  notify_doc_expiry: boolean;
  notify_return_updates: boolean;
  notify_dispute_updates: boolean;
  in_app_enabled: boolean;
  email_enabled: boolean;
  push_enabled: boolean;
  updated_at?: string | null;
}

const DEFAULT_PREFERENCES: SupplierNotificationPreferences = {
  supplier_id: 0,
  notify_new_order: true,
  notify_low_stock: true,
  notify_payout_processed: true,
  notify_doc_expiry: true,
  notify_return_updates: true,
  notify_dispute_updates: true,
  in_app_enabled: true,
  email_enabled: true,
  push_enabled: false,
};

const EVENT_TOGGLES: Array<{ key: PreferenceField; label: string; description: string }> = [
  {
    key: "notify_new_order",
    label: "New orders",
    description: "Alert me when a new order is assigned to my storefront.",
  },
  {
    key: "notify_low_stock",
    label: "Low stock",
    description: "Alert me when inventory drops below low-stock threshold.",
  },
  {
    key: "notify_payout_processed",
    label: "Payout processed",
    description: "Alert me when payout requests move to processing or completion.",
  },
  {
    key: "notify_doc_expiry",
    label: "Document expiry",
    description: "Alert me before KYC and compliance documents expire.",
  },
  {
    key: "notify_return_updates",
    label: "Return updates",
    description: "Alert me about return request status updates.",
  },
  {
    key: "notify_dispute_updates",
    label: "Dispute updates",
    description: "Alert me when disputes are reviewed or resolved by admins.",
  },
];

const CHANNEL_TOGGLES: Array<{ key: PreferenceField; label: string; description: string }> = [
  {
    key: "in_app_enabled",
    label: "In-app notifications",
    description: "Show alerts inside supplier dashboard panels.",
  },
  {
    key: "email_enabled",
    label: "Email notifications",
    description: "Send alerts to your account email.",
  },
  {
    key: "push_enabled",
    label: "Push notifications",
    description: "Send device push notifications when supported.",
  },
];

function formatUpdatedAt(value?: string | null): string {
  if (!value) {
    return "Not updated yet";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "Not updated yet";
  }
  return parsed.toLocaleString();
}

interface ToggleRowProps {
  label: string;
  description: string;
  checked: boolean;
  disabled: boolean;
  onToggle: () => void;
}

function ToggleRow({ label, description, checked, disabled, onToggle }: ToggleRowProps) {
  return (
    <div className="flex items-start justify-between gap-4 rounded-xl border border-border bg-surface-1 p-4">
      <div>
        <p className="text-sm font-semibold text-text">{label}</p>
        <p className="mt-1 text-xs text-text-muted">{description}</p>
      </div>
      <button
        type="button"
        onClick={onToggle}
        disabled={disabled}
        className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors ${
          checked ? "bg-primary" : "bg-surface-2"
        } disabled:cursor-not-allowed disabled:opacity-60`}
        aria-pressed={checked}
        aria-label={`Toggle ${label}`}
      >
        <span
          className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${
            checked ? "translate-x-5" : "translate-x-1"
          }`}
        />
      </button>
    </div>
  );
}

export default function SupplierNotificationPreferencesPage() {
  const addToast = useToastStore((state) => state.addToast);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [prefs, setPrefs] = useState<SupplierNotificationPreferences>(DEFAULT_PREFERENCES);

  const loadPreferences = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiFetch("/supplier/notification-preferences");
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.detail || "Failed to load notification preferences");
      }
      setPrefs({ ...DEFAULT_PREFERENCES, ...payload });
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Failed to load notification preferences", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    void loadPreferences();
  }, [loadPreferences]);

  const savePreferences = useCallback(
    async (nextState: SupplierNotificationPreferences) => {
      setSaving(true);
      try {
        const response = await apiFetch("/supplier/notification-preferences", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(nextState),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(payload.detail || "Failed to save notification preferences");
        }
        setPrefs({ ...DEFAULT_PREFERENCES, ...payload });
        addToast("Notification preferences saved", "success");
      } catch (error) {
        addToast(error instanceof Error ? error.message : "Failed to save notification preferences", "error");
      } finally {
        setSaving(false);
      }
    },
    [addToast],
  );

  const updatePreference = useCallback(
    (field: PreferenceField) => {
      const nextState = { ...prefs, [field]: !prefs[field] };
      setPrefs(nextState);
      void savePreferences(nextState);
    },
    [prefs, savePreferences],
  );

  const enabledCount = useMemo(() => {
    return EVENT_TOGGLES.reduce((count, row) => (prefs[row.key] ? count + 1 : count), 0);
  }, [prefs]);

  return (
    <SupplierLayout title="Notification Preferences">
      <PanelContent width="roomy" className="space-y-6">
        <PanelHero
          eyebrow="Alerts"
          title="Supplier Notification Preferences"
          description="Control which supplier events trigger alerts and which channels deliver them."
          actions={
            <button
              onClick={() => void loadPreferences()}
              disabled={loading || saving}
              className="flex items-center gap-2 rounded-xl border border-border bg-surface-2 px-4 py-2 text-xs font-semibold text-text-muted hover:text-text disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </button>
          }
        />

        <div className="grid gap-3 sm:grid-cols-3">
          <div className="theme-card rounded-xl border p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-text-faint">Enabled event alerts</p>
            <p className="mt-2 text-2xl font-bold text-text">{enabledCount}</p>
            <p className="text-xs text-text-muted">of {EVENT_TOGGLES.length} event types</p>
          </div>
          <div className="theme-card rounded-xl border p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-text-faint">Enabled channels</p>
            <p className="mt-2 text-2xl font-bold text-text">
              {CHANNEL_TOGGLES.reduce((count, row) => (prefs[row.key] ? count + 1 : count), 0)}
            </p>
            <p className="text-xs text-text-muted">of {CHANNEL_TOGGLES.length} delivery channels</p>
          </div>
          <div className="theme-card rounded-xl border p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-text-faint">Last updated</p>
            <p className="mt-2 text-sm font-semibold text-text">{formatUpdatedAt(prefs.updated_at)}</p>
            <div className="mt-2 inline-flex items-center gap-1 rounded-full bg-surface-2 px-2 py-1 text-[11px] text-text-muted">
              <Bell className="h-3.5 w-3.5" />
              {saving ? "Saving changes..." : "Auto-save enabled"}
            </div>
          </div>
        </div>

        {loading ? (
          <PanelLoadingState count={6} blockClassName="h-20 rounded-xl border border-border bg-surface-1 animate-pulse" />
        ) : (
          <div className="grid gap-6 lg:grid-cols-2">
            <section className="space-y-3">
              <h2 className="text-sm font-semibold text-text">Event Preferences</h2>
              {EVENT_TOGGLES.map((row) => (
                <ToggleRow
                  key={row.key}
                  label={row.label}
                  description={row.description}
                  checked={prefs[row.key]}
                  disabled={saving}
                  onToggle={() => updatePreference(row.key)}
                />
              ))}
            </section>

            <section className="space-y-3">
              <h2 className="text-sm font-semibold text-text">Delivery Channels</h2>
              {CHANNEL_TOGGLES.map((row) => (
                <ToggleRow
                  key={row.key}
                  label={row.label}
                  description={row.description}
                  checked={prefs[row.key]}
                  disabled={saving}
                  onToggle={() => updatePreference(row.key)}
                />
              ))}
            </section>
          </div>
        )}
      </PanelContent>
    </SupplierLayout>
  );
}


