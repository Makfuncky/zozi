"use client";

import { useEffect, useState, useCallback } from "react";
import { CheckCircle2, Mail, RefreshCw, Send, Server, Settings2, ShieldAlert } from "@/lib/icons";
import { apiFetch, getErrorMessage, parseJsonResponse } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";

type EmailPurpose =
  | "promotional"
  | "transactional"
  | "notification"
  | "alert"
  | "verification"
  | "login_verification"
  | "password_reset";

interface RuntimeEmailConfig {
  id?: number | null;
  provider: "environment" | "resend" | "smtp" | "disabled";
  active_provider: string;
  source: string;
  available: boolean;
  live: boolean;
  preview_only: boolean;
  supports_webhooks: boolean;
  smtp_host?: string | null;
  smtp_port: number;
  smtp_username?: string | null;
  smtp_use_tls: boolean;
  smtp_use_ssl: boolean;
  smtp_timeout_seconds: number;
  email_from_default?: string | null;
  email_from_promotional?: string | null;
  email_from_transactional?: string | null;
  email_from_notification?: string | null;
  email_from_alert?: string | null;
  email_from_verification?: string | null;
  email_from_login_verification?: string | null;
  email_from_password_reset?: string | null;
  resend_api_key_configured: boolean;
  resend_webhook_secret_configured: boolean;
  smtp_password_configured: boolean;
}

interface ProviderFormState {
  provider: RuntimeEmailConfig["provider"];
  resend_api_key: string;
  resend_webhook_secret: string;
  smtp_host: string;
  smtp_port: number;
  smtp_username: string;
  smtp_password: string;
  smtp_use_tls: boolean;
  smtp_use_ssl: boolean;
  smtp_timeout_seconds: number;
  email_from_default: string;
  email_from_promotional: string;
  email_from_transactional: string;
  email_from_notification: string;
  email_from_alert: string;
  email_from_verification: string;
  email_from_login_verification: string;
  email_from_password_reset: string;
}

const DEFAULT_FORM: ProviderFormState = {
  provider: "environment",
  resend_api_key: "",
  resend_webhook_secret: "",
  smtp_host: "",
  smtp_port: 587,
  smtp_username: "",
  smtp_password: "",
  smtp_use_tls: true,
  smtp_use_ssl: false,
  smtp_timeout_seconds: 15,
  email_from_default: "",
  email_from_promotional: "",
  email_from_transactional: "",
  email_from_notification: "",
  email_from_alert: "",
  email_from_verification: "",
  email_from_login_verification: "",
  email_from_password_reset: "",
};

function configToForm(config: RuntimeEmailConfig): ProviderFormState {
  return {
    provider: config.provider,
    resend_api_key: "",
    resend_webhook_secret: "",
    smtp_host: config.smtp_host || "",
    smtp_port: config.smtp_port || 587,
    smtp_username: config.smtp_username || "",
    smtp_password: "",
    smtp_use_tls: config.smtp_use_tls,
    smtp_use_ssl: config.smtp_use_ssl,
    smtp_timeout_seconds: config.smtp_timeout_seconds || 15,
    email_from_default: config.email_from_default || "",
    email_from_promotional: config.email_from_promotional || "",
    email_from_transactional: config.email_from_transactional || "",
    email_from_notification: config.email_from_notification || "",
    email_from_alert: config.email_from_alert || "",
    email_from_verification: config.email_from_verification || "",
    email_from_login_verification: config.email_from_login_verification || "",
    email_from_password_reset: config.email_from_password_reset || "",
  };
}

export default function EmailProviderConfigManager() {
  const [config, setConfig] = useState<RuntimeEmailConfig | null>(null);
  const [form, setForm] = useState<ProviderFormState>(DEFAULT_FORM);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [sendingTest, setSendingTest] = useState(false);
  const [testResult, setTestResult] = useState<Record<string, unknown> | null>(null);
  const [testPayload, setTestPayload] = useState({
    to_email: "",
    purpose: "transactional" as EmailPurpose,
    subject: "",
  });
const addToast = useToastStore((state) => state.addToast);

   const loadConfig = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiFetch("/email/config/runtime", { disableCache: true });
      const payload = (await parseJsonResponse(response)) ?? {};
      if (!response.ok) {
        throw new Error(getErrorMessage(payload));
      }
      setConfig(payload as RuntimeEmailConfig);
      setForm(configToForm(payload as RuntimeEmailConfig));
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load email delivery settings";
      addToast(message, "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    void loadConfig();
  }, [loadConfig]);

  const setField = <K extends keyof ProviderFormState>(field: K, value: ProviderFormState[K]) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const buildPayload = () => {
    const payload: Record<string, unknown> = {
      provider: form.provider,
      smtp_port: Number(form.smtp_port) || 587,
      smtp_use_tls: form.smtp_use_tls,
      smtp_use_ssl: form.smtp_use_ssl,
      smtp_timeout_seconds: Number(form.smtp_timeout_seconds) || 15,
      email_from_default: form.email_from_default.trim() || null,
      email_from_promotional: form.email_from_promotional.trim() || null,
      email_from_transactional: form.email_from_transactional.trim() || null,
      email_from_notification: form.email_from_notification.trim() || null,
      email_from_alert: form.email_from_alert.trim() || null,
      email_from_verification: form.email_from_verification.trim() || null,
      email_from_login_verification: form.email_from_login_verification.trim() || null,
      email_from_password_reset: form.email_from_password_reset.trim() || null,
    };

    if (form.provider === "resend") {
      if (form.resend_api_key.trim()) payload.resend_api_key = form.resend_api_key.trim();
      if (form.resend_webhook_secret.trim()) payload.resend_webhook_secret = form.resend_webhook_secret.trim();
    }

    if (form.provider === "smtp") {
      payload.smtp_host = form.smtp_host.trim() || null;
      payload.smtp_username = form.smtp_username.trim() || null;
      if (form.smtp_password.trim()) payload.smtp_password = form.smtp_password;
    }

    return payload;
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await apiFetch("/email/config/runtime", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildPayload()),
      });
      const payload = (await parseJsonResponse(response)) ?? {};
      if (!response.ok) {
        throw new Error(getErrorMessage(payload));
      }
      const updated = payload as RuntimeEmailConfig;
      setConfig(updated);
      setForm(configToForm(updated));
      addToast("Email delivery settings updated", "success");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to update email delivery settings";
      addToast(message, "error");
    } finally {
      setSaving(false);
    }
  };

  const handleTestSend = async () => {
    setSendingTest(true);
    setTestResult(null);
    try {
      const response = await apiFetch("/email/config/test-send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          to_email: testPayload.to_email.trim(),
          purpose: testPayload.purpose,
          subject: testPayload.subject.trim() || undefined,
        }),
      });
      const payload = (await parseJsonResponse(response)) ?? {};
      if (!response.ok) {
        throw new Error(getErrorMessage(payload));
      }
      setTestResult(payload);
      addToast("Test email dispatched", "success");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to send test email";
      addToast(message, "error");
    } finally {
      setSendingTest(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center p-10 text-text-muted">Loading email delivery settings...</div>;
  }

  const status = config;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-text">Delivery Settings</h2>
          <p className="text-text-muted">Manage live provider selection, sender identities, and test sends without restarting the backend.</p>
        </div>
        <button
          onClick={() => void loadConfig()}
          className="theme-panel inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm text-text-muted transition-colors hover:bg-surface-2 hover:text-text"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <StatusCard title="Configured" value={status?.provider || "environment"} icon={Settings2} />
        <StatusCard title="Active" value={status?.active_provider || "disabled"} icon={Server} />
        <StatusCard title="Mode" value={status?.live ? "Live" : status?.preview_only ? "Preview" : "Disabled"} icon={Mail} />
        <StatusCard title="Webhooks" value={status?.supports_webhooks ? "Supported" : "Not supported"} icon={ShieldAlert} />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="theme-card rounded-2xl p-6">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h3 className="text-lg font-medium text-text">Provider Configuration</h3>
              <p className="text-sm text-text-muted">Blank secret fields keep the currently stored secret in place.</p>
            </div>
            <span className="theme-chip-info rounded-full px-3 py-1 text-xs uppercase tracking-[0.2em]">{status?.source || "database"}</span>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <label className="space-y-1 text-sm text-text-muted">
              <span className="font-medium text-text">Provider</span>
              <select
                value={form.provider}
                onChange={(event) => setField("provider", event.target.value as ProviderFormState["provider"])}
                className="w-full rounded-xl border border-border bg-surface-1 px-3 py-2 text-text"
              >
                <option value="environment">Environment bootstrap</option>
                <option value="resend">Resend</option>
                <option value="smtp">SMTP</option>
                <option value="disabled">Disabled</option>
              </select>
            </label>

            <label className="space-y-1 text-sm text-text-muted">
              <span className="font-medium text-text">Default Sender</span>
              <input
                value={form.email_from_default}
                onChange={(event) => setField("email_from_default", event.target.value)}
                className="w-full rounded-xl border border-border bg-surface-1 px-3 py-2 text-text"
                placeholder="noreply@zozi.com"
              />
            </label>

            {form.provider === "resend" && (
              <>
                <SecretField
                  label={`Resend API key${status?.resend_api_key_configured ? " (stored)" : ""}`}
                  value={form.resend_api_key}
                  onChange={(value) => setField("resend_api_key", value)}
                  placeholder="re_..."
                />
                <SecretField
                  label={`Webhook secret${status?.resend_webhook_secret_configured ? " (stored)" : ""}`}
                  value={form.resend_webhook_secret}
                  onChange={(value) => setField("resend_webhook_secret", value)}
                  placeholder="whsec_..."
                />
              </>
            )}

            {form.provider === "smtp" && (
              <>
                <label className="space-y-1 text-sm text-text-muted">
                  <span className="font-medium text-text">SMTP Host</span>
                  <input value={form.smtp_host} onChange={(event) => setField("smtp_host", event.target.value)} className="w-full rounded-xl border border-border bg-surface-1 px-3 py-2 text-text" placeholder="smtp.example.com" />
                </label>
                <label className="space-y-1 text-sm text-text-muted">
                  <span className="font-medium text-text">SMTP Port</span>
                  <input type="number" value={form.smtp_port} onChange={(event) => setField("smtp_port", Number(event.target.value) || 587)} className="w-full rounded-xl border border-border bg-surface-1 px-3 py-2 text-text" />
                </label>
                <label className="space-y-1 text-sm text-text-muted">
                  <span className="font-medium text-text">SMTP Username</span>
                  <input value={form.smtp_username} onChange={(event) => setField("smtp_username", event.target.value)} className="w-full rounded-xl border border-border bg-surface-1 px-3 py-2 text-text" />
                </label>
                <SecretField
                  label={`SMTP Password${status?.smtp_password_configured ? " (stored)" : ""}`}
                  value={form.smtp_password}
                  onChange={(value) => setField("smtp_password", value)}
                  placeholder="Leave blank to keep existing password"
                />
                <label className="space-y-1 text-sm text-text-muted">
                  <span className="font-medium text-text">Timeout (seconds)</span>
                  <input type="number" value={form.smtp_timeout_seconds} onChange={(event) => setField("smtp_timeout_seconds", Number(event.target.value) || 15)} className="w-full rounded-xl border border-border bg-surface-1 px-3 py-2 text-text" />
                </label>
                <div className="flex items-center gap-6 pt-6 text-sm text-text-muted">
                  <label className="inline-flex items-center gap-2">
                    <input type="checkbox" checked={form.smtp_use_tls} onChange={(event) => setField("smtp_use_tls", event.target.checked)} />
                    TLS
                  </label>
                  <label className="inline-flex items-center gap-2">
                    <input type="checkbox" checked={form.smtp_use_ssl} onChange={(event) => setField("smtp_use_ssl", event.target.checked)} />
                    SSL
                  </label>
                </div>
              </>
            )}
          </div>

          <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
            <SenderField label="Promotional sender" value={form.email_from_promotional} onChange={(value) => setField("email_from_promotional", value)} />
            <SenderField label="Transactional sender" value={form.email_from_transactional} onChange={(value) => setField("email_from_transactional", value)} />
            <SenderField label="Notification sender" value={form.email_from_notification} onChange={(value) => setField("email_from_notification", value)} />
            <SenderField label="Alert sender" value={form.email_from_alert} onChange={(value) => setField("email_from_alert", value)} />
            <SenderField label="Verification sender" value={form.email_from_verification} onChange={(value) => setField("email_from_verification", value)} />
            <SenderField label="Login verification sender" value={form.email_from_login_verification} onChange={(value) => setField("email_from_login_verification", value)} />
            <SenderField label="Password reset sender" value={form.email_from_password_reset} onChange={(value) => setField("email_from_password_reset", value)} />
          </div>

          <div className="mt-6 flex justify-end">
            <button onClick={() => void handleSave()} disabled={saving} className="theme-btn-primary rounded-xl px-5 py-2.5 text-sm disabled:opacity-60">
              {saving ? "Saving..." : "Save Delivery Settings"}
            </button>
          </div>
        </div>

        <div className="space-y-6">
          <div className="theme-card rounded-2xl p-6">
            <div className="mb-4 flex items-center gap-2">
              <Send className="h-5 w-5 text-primary" />
              <h3 className="text-lg font-medium text-text">Test Send</h3>
            </div>
            <div className="space-y-4">
              <label className="block space-y-1 text-sm text-text-muted">
                <span className="font-medium text-text">Recipient email</span>
                <input value={testPayload.to_email} onChange={(event) => setTestPayload((current) => ({ ...current, to_email: event.target.value }))} className="w-full rounded-xl border border-border bg-surface-1 px-3 py-2 text-text" placeholder="qa@zozi.com" />
              </label>
              <label className="block space-y-1 text-sm text-text-muted">
                <span className="font-medium text-text">Purpose</span>
                <select value={testPayload.purpose} onChange={(event) => setTestPayload((current) => ({ ...current, purpose: event.target.value as EmailPurpose }))} className="w-full rounded-xl border border-border bg-surface-1 px-3 py-2 text-text">
                  <option value="transactional">Transactional</option>
                  <option value="notification">Notification</option>
                  <option value="verification">Verification</option>
                  <option value="password_reset">Password reset</option>
                  <option value="promotional">Promotional</option>
                  <option value="alert">Alert</option>
                  <option value="login_verification">Login verification</option>
                </select>
              </label>
              <label className="block space-y-1 text-sm text-text-muted">
                <span className="font-medium text-text">Subject override</span>
                <input value={testPayload.subject} onChange={(event) => setTestPayload((current) => ({ ...current, subject: event.target.value }))} className="w-full rounded-xl border border-border bg-surface-1 px-3 py-2 text-text" placeholder="Optional test subject" />
              </label>
              <button onClick={() => void handleTestSend()} disabled={sendingTest} className="theme-btn-primary w-full rounded-xl px-4 py-2.5 text-sm disabled:opacity-60">
                {sendingTest ? "Dispatching test email..." : "Send Test Email"}
              </button>
            </div>
            {testResult && (
              <div className="mt-4 rounded-2xl border border-border bg-surface-2 p-4 text-sm text-text-muted">
                <div className="mb-2 flex items-center gap-2 text-text">
                  <CheckCircle2 className="h-4 w-4 text-success" />
                  <span className="font-medium">Test request accepted</span>
                </div>
                <p>Provider: {String(testResult.provider || "unknown")}</p>
                <p>From: {String(testResult.from_address || "-")}</p>
                <p>Mode: {Boolean(testResult.preview_only) ? "Preview only" : "Live delivery"}</p>
              </div>
            )}
          </div>

          <div className="theme-card rounded-2xl p-6 text-sm text-text-muted">
            <h3 className="mb-3 text-lg font-medium text-text">Provider Notes</h3>
            <ul className="space-y-2">
              <li>Resend webhooks are now supported through the backend webhook endpoint and require the signing secret to be stored here.</li>
              <li>SMTP mode records outbound send attempts and still respects suppressions, but it does not expose provider-side bounce webhooks.</li>
              <li>Blank secret fields keep the stored credentials. Sender address fields can be cleared by saving them empty.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatusCard({ title, value, icon: Icon }: { title: string; value: string; icon: React.ComponentType<{ className?: string }> }) {
  return (
    <div className="theme-card rounded-2xl p-5">
      <div className="flex items-center gap-3">
        <div className="rounded-2xl bg-surface-2 p-3">
          <Icon className="h-5 w-5 text-primary" />
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-text-faint">{title}</p>
          <p className="text-lg font-semibold text-text">{value}</p>
        </div>
      </div>
    </div>
  );
}

function SenderField({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="space-y-1 text-sm text-text-muted">
      <span className="font-medium text-text">{label}</span>
      <input value={value} onChange={(event) => onChange(event.target.value)} className="w-full rounded-xl border border-border bg-surface-1 px-3 py-2 text-text" />
    </label>
  );
}

function SecretField({ label, value, onChange, placeholder }: { label: string; value: string; onChange: (value: string) => void; placeholder: string }) {
  return (
    <label className="space-y-1 text-sm text-text-muted">
      <span className="font-medium text-text">{label}</span>
      <input type="password" value={value} onChange={(event) => onChange(event.target.value)} className="w-full rounded-xl border border-border bg-surface-1 px-3 py-2 text-text" placeholder={placeholder} />
    </label>
  );
}


