"use client";

import { Button } from "@/components/ui/Button";
import { useState, useEffect, useCallback } from "react";
import { Plus, RefreshCw, Search, Send, X, Loader2 } from "@/lib/icons";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";
import { useAdminCountry } from "@/lib/useAdminCountry";

interface Campaign {
  id: number;
  name: string;
  subject: string;
  status: string;
  recipient_count?: number;
  sent_count?: number;
  opened_count?: number;
  clicked_count?: number;
  send_at?: string | null;
  sent_at?: string | null;
  created_at: string;
}

const STATUS_STYLE: Record<string, string> = {
  draft: "bg-surface-3 text-text-muted",
  sending: "bg-info/20 text-info",
  sent: "bg-success/20 text-success",
  scheduled: "bg-warning/20 text-warning",
  failed: "bg-danger/20 text-danger",
};

export default function EmailCampaignManager() {
  const addToast = useToastStore((s) => s.addToast);
  const { selectedCountry, assignedCountries, isGlobalView } = useAdminCountry();
  const countryCode = isGlobalView ? (assignedCountries[0]?.code || selectedCountry?.code || "AE") : (selectedCountry?.code || "AE");

  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ name: "", subject: "" });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const path = isGlobalView ? "/admin/" : `/admin/campaigns/${countryCode}`;
      const res = await apiFetch(path);
      if (res.ok) {
        const data = await parseJsonResponse(res);
        setCampaigns(Array.isArray(data) ? data : []);
      }
    } catch {
      addToast("Failed to load campaigns", "error");
    } finally {
      setLoading(false);
    }
  }, [isGlobalView, countryCode, addToast]);

  useEffect(() => { load(); }, [load]);

  const handleCreate = async () => {
    if (!form.name.trim() || !form.subject.trim()) { addToast("Name and subject required", "error"); return; }
    setCreating(true);
    try {
      const res = await apiFetch(`/admin/campaigns/${countryCode}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: form.name.trim(), subject: form.subject.trim() }),
      });
      if (res.ok) {
        addToast("Campaign created", "success");
        setShowCreate(false);
        setForm({ name: "", subject: "" });
        load();
      } else {
        const err = await parseJsonResponse(res);
        addToast(err?.detail ?? "Failed to create campaign", "error");
      }
    } catch {
      addToast("Network error", "error");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this campaign?")) return;
    try {
      const res = await apiFetch(`/admin/campaigns/${countryCode}/${id}`, { method: "DELETE" });
      if (res.ok) {
        addToast("Campaign deleted", "success");
        load();
      } else {
        addToast("Failed to delete campaign", "error");
      }
    } catch {
      addToast("Network error", "error");
    }
  };

  const filtered = search.trim()
    ? campaigns.filter((c) => c.name.toLowerCase().includes(search.toLowerCase()) || c.subject.toLowerCase().includes(search.toLowerCase()))
    : campaigns;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3 w-3 text-text-faint" />
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search campaigns..." className="rounded-lg border border-border bg-surface-2 py-1.5 pl-8 pr-3 text-xs text-text w-56" />
          </div>
          <button onClick={load} className="rounded-lg border border-border bg-surface-2 px-2.5 py-1.5 text-xs text-text-faint hover:bg-surface-3">
            <RefreshCw className={`h-3 w-3 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
        <Button variant="primary" className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold" onClick={() => setShowCreate(true)}>
          <Plus className="h-3.5 w-3.5" />
          New Campaign
        </Button>
      </div>

      {loading ? (
        <div className="space-y-2">{Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-14 animate-pulse rounded-xl bg-surface-2" />)}</div>
      ) : filtered.length === 0 ? (
        <div className="theme-card rounded-xl border p-8 text-center text-text-muted">
          <Send className="h-8 w-8 mx-auto mb-2 opacity-40" />
          <p className="text-sm">{search ? "No matching campaigns" : "No email campaigns yet"}</p>
          <p className="text-xs text-text-faint mt-1">Create your first campaign to start sending emails</p>
        </div>
      ) : (
        <div className="theme-card rounded-xl border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-surface-2 border-b border-border">
              <tr>
                <th className="text-left p-3 font-semibold text-[11px]">Name</th>
                <th className="text-left p-3 font-semibold text-[11px]">Subject</th>
                <th className="text-center p-3 font-semibold text-[11px]">Status</th>
                <th className="text-right p-3 font-semibold text-[11px]">Sent</th>
                <th className="text-right p-3 font-semibold text-[11px]">Opened</th>
                <th className="text-left p-3 font-semibold text-[11px]">Date</th>
                <th className="text-center p-3 font-semibold text-[11px]"></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => (
                <tr key={c.id} className="border-b border-border last:border-0 hover:bg-surface-1/50">
                  <td className="p-3 font-medium text-xs">{c.name}</td>
                  <td className="p-3 text-xs text-text-muted max-w-[200px] truncate">{c.subject}</td>
                  <td className="p-3 text-center">
                    <span className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold ${STATUS_STYLE[c.status] || "theme-chip-muted"}`}>{c.status}</span>
                  </td>
                  <td className="p-3 text-right text-xs">{c.sent_count ?? 0}</td>
                  <td className="p-3 text-right text-xs">{c.opened_count ?? 0}</td>
                  <td className="p-3 text-xs text-text-faint">{c.created_at?.slice(0, 10)}</td>
                  <td className="p-3 text-center">
                    <button onClick={() => handleDelete(c.id)} className="text-text-faint hover:text-danger transition" title="Delete">
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay">
          <div className="rounded-xl border border-border bg-surface-1 p-5 w-full max-w-md shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-text flex items-center gap-2">
                <Send className="h-4 w-4 text-primary" />
                New Email Campaign
              </h3>
              <button onClick={() => setShowCreate(false)} className="text-text-muted hover:text-text"><X className="h-4 w-4" /></button>
            </div>
            <div className="space-y-3">
              <label className="block space-y-1 text-[10px] text-text-muted">
                Campaign Name
                <input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text" placeholder="e.g. Summer Sale 2026" />
              </label>
              <label className="block space-y-1 text-[10px] text-text-muted">
                Email Subject
                <input value={form.subject} onChange={(e) => setForm((f) => ({ ...f, subject: e.target.value }))} className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text" placeholder="e.g. Don't miss our summer deals!" />
              </label>
            </div>
            <div className="flex items-center justify-end gap-2 mt-5">
              <button onClick={() => setShowCreate(false)} className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-text-muted hover:text-text">Cancel</button>
              <Button variant="primary" onClick={handleCreate} disabled={creating || !form.name.trim() || !form.subject.trim()}>
                {creating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-3.5 w-3.5" />}
                Create Campaign
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
