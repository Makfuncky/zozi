"use client";

import { useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";

interface ProviderStatus {
  sms: { mode: string; provider: string };
  whatsapp: { mode: string; provider: string };
}

interface Template {
  id: string;
  channel: string;
  description: string;
  body: string;
}

interface SendResult {
  success: boolean;
  channel: string;
  to: string;
  template_id: string | null;
  preview: boolean;
  error: string | null;
  timestamp: string;
}

export default function CommsTestPage() {
  const [status, setStatus] = useState<ProviderStatus | null>(null);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [phone, setPhone] = useState("+971501234567");
  const [channel, setChannel] = useState<"sms" | "whatsapp">("sms");
  const [templateId, setTemplateId] = useState("otp_sms");
  const [customBody, setCustomBody] = useState("");
  const [useCustom, setUseCustom] = useState(false);
  const [result, setResult] = useState<SendResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchStatus();
    fetchTemplates();
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await apiFetch("/api/v1/comms/status");
      if (res.ok) {
        setStatus(await res.json());
      }
    } catch {
      // ignore
    }
  };

  const fetchTemplates = async () => {
    try {
      const res = await apiFetch("/api/v1/comms/templates");
      if (res.ok) {
        setTemplates(await res.json());
      }
    } catch {
      // ignore
    }
  };

  const handleSend = async () => {
    setLoading(true);
    setResult(null);
    try {
      const payload: Record<string, string> = { to: phone, channel };
      if (useCustom) {
        payload.body = customBody;
      } else {
        payload.template_id = templateId;
      }
      const res = await apiFetch("/api/v1/comms/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        setResult(await res.json());
      } else {
        setResult({
          success: false,
          channel,
          to: phone,
          template_id: useCustom ? null : templateId,
          preview: false,
          error: `HTTP ${res.status}`,
          timestamp: new Date().toISOString(),
        });
      }
    } catch (exc) {
      setResult({
        success: false,
        channel,
        to: phone,
        template_id: useCustom ? null : templateId,
        preview: false,
        error: String(exc),
        timestamp: new Date().toISOString(),
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-text">SMS / WhatsApp Tester</h1>

      {/* Provider Status */}
      <div className="theme-card rounded-xl border p-4">
        <h2 className="text-sm font-semibold text-text mb-3">Provider Status</h2>
        {status ? (
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="rounded-lg bg-surface-2/60 p-3">
              <div className="font-semibold text-text">SMS</div>
              <div className="text-text-faint">Mode: <span className="text-text">{status.sms.mode}</span></div>
              <div className="text-text-faint">Provider: <span className="text-text">{status.sms.provider}</span></div>
            </div>
            <div className="rounded-lg bg-surface-2/60 p-3">
              <div className="font-semibold text-text">WhatsApp</div>
              <div className="text-text-faint">Mode: <span className="text-text">{status.whatsapp.mode}</span></div>
              <div className="text-text-faint">Provider: <span className="text-text">{status.whatsapp.provider}</span></div>
            </div>
          </div>
        ) : (
          <div className="text-sm text-text-faint">Loading...</div>
        )}
      </div>

      {/* Send Form */}
      <div className="theme-card rounded-xl border p-4">
        <h2 className="text-sm font-semibold text-text mb-3">Send Test Message</h2>
        <div className="space-y-3">
          <div>
            <label className="mb-1 block text-xs font-semibold text-text-faint">Phone Number</label>
            <input
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+971501234567"
              className="theme-input w-full rounded-lg border px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-text-faint">Channel</label>
            <div className="flex gap-2">
              <button
                onClick={() => { setChannel("sms"); setTemplateId("otp_sms"); }}
                className={`rounded-lg px-4 py-2 text-sm font-semibold ${channel === "sms" ? "theme-btn-primary" : "theme-btn-secondary"}`}
              >
                SMS
              </button>
              <button
                onClick={() => { setChannel("whatsapp"); setTemplateId("otp_whatsapp"); }}
                className={`rounded-lg px-4 py-2 text-sm font-semibold ${channel === "whatsapp" ? "theme-btn-primary" : "theme-btn-secondary"}`}
              >
                WhatsApp
              </button>
            </div>
          </div>

          <div>
            <label className="mb-1 flex items-center gap-2 text-xs font-semibold text-text-faint">
              <input
                type="checkbox"
                checked={useCustom}
                onChange={(e) => setUseCustom(e.target.checked)}
                className="rounded"
              />
              Use custom message
            </label>
            {useCustom ? (
              <textarea
                value={customBody}
                onChange={(e) => setCustomBody(e.target.value)}
                placeholder="Enter custom message..."
                rows={3}
                className="theme-input w-full rounded-lg border px-3 py-2 text-sm"
              />
            ) : (
              <select
                value={templateId}
                onChange={(e) => setTemplateId(e.target.value)}
                className="theme-input w-full rounded-lg border px-3 py-2 text-sm"
              >
                {templates
                  .filter((t) => t.channel === channel)
                  .map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.id} — {t.description}
                    </option>
                  ))}
              </select>
            )}
          </div>

          <button
            onClick={handleSend}
            disabled={loading || !phone}
            className="theme-btn-primary rounded-lg px-6 py-2 text-sm font-semibold disabled:opacity-50"
          >
            {loading ? "Sending..." : "Send Message"}
          </button>
        </div>
      </div>

      {/* Result */}
      {result && (
        <div className={`theme-card rounded-xl border p-4 ${result.success ? "border-success/30" : result.preview ? "border-warning/30" : "border-danger/30"}`}>
          <h2 className="text-sm font-semibold text-text mb-2">
            {result.success ? "✅ Sent" : result.preview ? "⚠️ Preview Mode" : "❌ Failed"}
          </h2>
          <div className="space-y-1 text-sm text-text-faint">
            <div>Channel: <span className="text-text">{result.channel}</span></div>
            <div>To: <span className="text-text">{result.to}</span></div>
            <div>Template: <span className="text-text">{result.template_id || "custom"}</span></div>
            {result.error && <div>Error: <span className="text-danger">{result.error}</span></div>}
            <div>Time: <span className="text-text">{result.timestamp}</span></div>
          </div>
        </div>
      )}

      {/* Template Preview */}
      <div className="theme-card rounded-xl border p-4">
        <h2 className="text-sm font-semibold text-text mb-3">Available Templates</h2>
        <div className="space-y-2">
          {templates
            .filter((t) => t.channel === channel)
            .map((t) => (
              <div key={t.id} className="rounded-lg bg-surface-2/40 p-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-text">{t.id}</span>
                  <span className="text-xs text-text-faint">{t.description}</span>
                </div>
                <pre className="mt-1 whitespace-pre-wrap text-xs text-text-faint">{t.body}</pre>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}
