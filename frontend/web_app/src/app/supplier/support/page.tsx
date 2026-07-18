"use client";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import SupplierLayout from "@/components/SupplierLayout";
import { PanelContent } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";
import { AlertCircle, CheckCircle, Clock, MessageSquare, RefreshCw, Send, ShieldAlert } from "@/lib/icons";

type SupportView = "tickets" | "disputes";

interface Ticket {
  id: number;
  subject: string;
  status: string;
  priority: string;
  created_at: string;
  reply_count?: number;
}

interface SupplierDispute {
  id: number;
  dispute_type: string;
  priority: string;
  status: string;
  title: string;
  description: string;
  related_order_id?: number | null;
  created_at?: string | null;
  admin_notes?: string | null;
  resolution_notes?: string | null;
}

interface SupplierDisputeListResponse {
  data?: SupplierDispute[];
}

interface CreateDisputeFormState {
  dispute_type: string;
  priority: string;
  title: string;
  description: string;
  related_order_id: string;
}

const STATUS_CHIP: Record<string, string> = {
  open: "theme-chip-info",
  in_progress: "theme-chip-warning",
  resolved: "theme-chip-success",
  closed: "theme-chip-muted",
  pending: "theme-chip-warning",
  under_review: "theme-chip-info",
  rejected: "theme-chip-danger",
};

function formatDate(value?: string | null) {
  if (!value) return "-";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString();
}

function createDefaultDisputeForm(): CreateDisputeFormState {
  return {
    dispute_type: "other",
    priority: "medium",
    title: "",
    description: "",
    related_order_id: "",
  };
}

function SupplierSupportPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const addToast = useToastStore((state) => state.addToast);
  const [view, setView] = useState<SupportView>("tickets");
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [disputes, setDisputes] = useState<SupplierDispute[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [ticketSubject, setTicketSubject] = useState("");
  const [ticketMessage, setTicketMessage] = useState("");
  const [ticketPriority, setTicketPriority] = useState("normal");
  const [ticketSubmitting, setTicketSubmitting] = useState(false);
  const [disputeForm, setDisputeForm] = useState<CreateDisputeFormState>(createDefaultDisputeForm());
  const [disputeSubmitting, setDisputeSubmitting] = useState(false);

  useEffect(() => {
    const requestedSection = searchParams?.get("section");
    if (requestedSection === "disputes") {
      setView("disputes");
      return;
    }
    setView("tickets");
  }, [searchParams]);

  const loadWorkspace = useCallback(async ({ silent = false }: { silent?: boolean } = {}) => {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const [ticketRes, disputeRes] = await Promise.all([
        apiFetch("/tickets").catch(() => null),
        apiFetch("/supplier/disputes").catch(() => null),
      ]);

      if (ticketRes?.ok) {
        const ticketPayload = await ticketRes.json().catch(() => []);
        setTickets(Array.isArray(ticketPayload) ? ticketPayload : ticketPayload.tickets ?? []);
      } else {
        setTickets([]);
      }

      if (disputeRes?.ok) {
        const disputePayload = (await disputeRes.json().catch(() => ({}))) as SupplierDisputeListResponse;
        setDisputes(Array.isArray(disputePayload.data) ? disputePayload.data : []);
      } else {
        setDisputes([]);
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void loadWorkspace();
  }, [loadWorkspace]);

  const ticketSummary = useMemo(() => ({
    open: tickets.filter((ticket) => ticket.status === "open").length,
    active: tickets.filter((ticket) => ticket.status === "in_progress").length,
    resolved: tickets.filter((ticket) => ticket.status === "resolved" || ticket.status === "closed").length,
  }), [tickets]);

  const disputeSummary = useMemo(() => ({
    pending: disputes.filter((dispute) => dispute.status === "pending").length,
    review: disputes.filter((dispute) => dispute.status === "under_review").length,
    resolved: disputes.filter((dispute) => dispute.status === "resolved").length,
  }), [disputes]);

  const switchView = (nextView: SupportView) => {
    setView(nextView);
    router.replace(nextView === "disputes" ? "/supplier/support?section=disputes" : "/supplier/support");
  };

  const submitTicket = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!ticketSubject.trim() || !ticketMessage.trim()) {
      addToast("Subject and message are required", "error");
      return;
    }

    setTicketSubmitting(true);
    try {
      const response = await apiFetch("/tickets", {
        method: "POST",
        body: JSON.stringify({ subject: ticketSubject.trim(), message: ticketMessage.trim(), priority: ticketPriority }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.detail || payload.message || "Failed to submit support ticket");
      }
      setTicketSubject("");
      setTicketMessage("");
      setTicketPriority("normal");
      addToast("Support request submitted", "success");
      await loadWorkspace({ silent: true });
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Failed to submit support ticket", "error");
    } finally {
      setTicketSubmitting(false);
    }
  };

  const submitDispute = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!disputeForm.description.trim()) {
      addToast("Describe the issue before submitting a dispute", "error");
      return;
    }

    setDisputeSubmitting(true);
    try {
      const response = await apiFetch("/supplier/disputes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dispute_type: disputeForm.dispute_type,
          priority: disputeForm.priority,
          title: disputeForm.title.trim() || undefined,
          description: disputeForm.description.trim(),
          related_order_id: disputeForm.related_order_id.trim() ? Number(disputeForm.related_order_id) : undefined,
        }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.detail || "Failed to submit dispute");
      }
      setDisputeForm(createDefaultDisputeForm());
      addToast("Dispute submitted for admin review", "success");
      await loadWorkspace({ silent: true });
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Failed to submit dispute", "error");
    } finally {
      setDisputeSubmitting(false);
    }
  };

  return (
    <SupplierLayout title="Support">
      <PanelContent width="roomy" className="space-y-5">
        <div className="rounded-2xl border border-border bg-surface-1 p-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-faint">Admin communication</p>
              <h1 className="mt-2 text-2xl font-bold text-text">Support and dispute handling now live in one workspace</h1>
              <p className="mt-2 max-w-3xl text-sm text-text-muted">Use tickets for operational help and use disputes for return, payout, or order-specific escalation. Both channels are now kept together so supplier follow-up stays in one place.</p>
            </div>
            <button
              type="button"
              onClick={() => void loadWorkspace({ silent: true })}
              className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface-2 px-3 py-2 text-xs font-semibold text-text-muted transition-colors hover:text-text"
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} /> Refresh
            </button>
          </div>

          <div className="mt-5 grid gap-3 md:grid-cols-3 xl:grid-cols-6">
            <div className="rounded-xl border border-border bg-surface-2 px-4 py-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-faint">Open tickets</p>
              <p className="mt-2 text-xl font-bold text-text">{ticketSummary.open}</p>
            </div>
            <div className="rounded-xl border border-border bg-surface-2 px-4 py-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-faint">Active tickets</p>
              <p className="mt-2 text-xl font-bold text-text">{ticketSummary.active}</p>
            </div>
            <div className="rounded-xl border border-border bg-surface-2 px-4 py-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-faint">Resolved tickets</p>
              <p className="mt-2 text-xl font-bold text-text">{ticketSummary.resolved}</p>
            </div>
            <div className="rounded-xl border border-border bg-surface-2 px-4 py-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-faint">Pending disputes</p>
              <p className="mt-2 text-xl font-bold text-text">{disputeSummary.pending}</p>
            </div>
            <div className="rounded-xl border border-border bg-surface-2 px-4 py-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-faint">In review</p>
              <p className="mt-2 text-xl font-bold text-text">{disputeSummary.review}</p>
            </div>
            <div className="rounded-xl border border-border bg-surface-2 px-4 py-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-faint">Resolved disputes</p>
              <p className="mt-2 text-xl font-bold text-text">{disputeSummary.resolved}</p>
            </div>
          </div>
        </div>

        <div className="flex gap-2 rounded-2xl border border-border bg-surface-2 p-1">
          {[
            { key: "tickets", label: "Support Requests", icon: MessageSquare },
            { key: "disputes", label: "Dispute Cases", icon: ShieldAlert },
          ].map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              type="button"
              onClick={() => switchView(key as SupportView)}
              className={`flex flex-1 items-center justify-center gap-2 rounded-xl px-3 py-2 text-xs font-semibold transition-colors ${view === key ? "bg-primary text-on-brand" : "text-text-muted hover:text-text"}`}
            >
              <Icon className="h-4 w-4" /> {label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="rounded-2xl border border-border bg-surface-1 p-6 text-sm text-text-muted">Loading support workspace...</div>
        ) : view === "tickets" ? (
          <div className="grid gap-4 xl:grid-cols-[360px,1fr]">
            <form onSubmit={submitTicket} className="rounded-2xl border border-border bg-surface-1 p-5 space-y-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-faint">New support request</p>
                <p className="mt-2 text-sm text-text-muted">Use this for account access, workflow confusion, payout clarification, or operational help.</p>
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-text-muted">Subject</label>
                <input value={ticketSubject} onChange={(event) => setTicketSubject(event.target.value)} className="theme-input w-full rounded-xl border px-3 py-2 text-sm" placeholder="Brief description of the issue" />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-text-muted">Priority</label>
                <select value={ticketPriority} onChange={(event) => setTicketPriority(event.target.value)} className="theme-input w-full rounded-xl border px-3 py-2 text-sm">
                  <option value="low">Low</option>
                  <option value="normal">Normal</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-text-muted">Message</label>
                <textarea value={ticketMessage} onChange={(event) => setTicketMessage(event.target.value)} rows={5} className="theme-input w-full rounded-xl border px-3 py-2 text-sm resize-none" placeholder="Describe what happened and what you need from admin." />
              </div>
              <button type="submit" disabled={ticketSubmitting} className="inline-flex w-full items-center justify-center gap-2 rounded-xl theme-btn-primary px-4 py-2.5 text-sm font-semibold disabled:opacity-50">
                <Send className="h-4 w-4" /> {ticketSubmitting ? "Submitting..." : "Submit support request"}
              </button>
            </form>

            <div className="rounded-2xl border border-border bg-surface-1 overflow-hidden">
              <div className="border-b border-border px-5 py-4">
                <h2 className="text-sm font-semibold text-text">Ticket history</h2>
                <p className="mt-1 text-xs text-text-muted">Track open, active, and resolved conversations with admin.</p>
              </div>
              <div className="divide-y divide-border">
                {tickets.length > 0 ? tickets.map((ticket) => (
                  <article key={ticket.id} className="px-5 py-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-text">#{ticket.id} {ticket.subject}</p>
                        <p className="mt-1 text-xs text-text-muted">Created {formatDate(ticket.created_at)} · Priority {ticket.priority}</p>
                      </div>
                      <span className={`rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase ${STATUS_CHIP[ticket.status] || "theme-chip-muted"}`}>{ticket.status.replaceAll("_", " ")}</span>
                    </div>
                    {ticket.reply_count ? <p className="mt-2 text-xs text-text-faint">Replies: {ticket.reply_count}</p> : null}
                  </article>
                )) : (
                  <div className="px-5 py-10 text-sm text-text-muted">No support requests submitted yet.</div>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="grid gap-4 xl:grid-cols-[360px,1fr]">
            <form onSubmit={submitDispute} className="rounded-2xl border border-border bg-surface-1 p-5 space-y-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-faint">Escalate a dispute</p>
                <p className="mt-2 text-sm text-text-muted">Use disputes for return, payout, verification, or order-linked cases that need formal review.</p>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <select value={disputeForm.dispute_type} onChange={(event) => setDisputeForm((current) => ({ ...current, dispute_type: event.target.value }))} className="theme-input rounded-xl border px-3 py-2 text-sm">
                  <option value="return">Return</option>
                  <option value="verification">Verification</option>
                  <option value="invoice">Invoice</option>
                  <option value="payout">Payout</option>
                  <option value="other">Other</option>
                </select>
                <select value={disputeForm.priority} onChange={(event) => setDisputeForm((current) => ({ ...current, priority: event.target.value }))} className="theme-input rounded-xl border px-3 py-2 text-sm">
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-text-muted">Title</label>
                <input value={disputeForm.title} onChange={(event) => setDisputeForm((current) => ({ ...current, title: event.target.value }))} className="theme-input w-full rounded-xl border px-3 py-2 text-sm" placeholder="Short title for the case" />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-text-muted">Related Order ID</label>
                <input value={disputeForm.related_order_id} onChange={(event) => setDisputeForm((current) => ({ ...current, related_order_id: event.target.value }))} className="theme-input w-full rounded-xl border px-3 py-2 text-sm" placeholder="Optional order number" />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-text-muted">Description</label>
                <textarea value={disputeForm.description} onChange={(event) => setDisputeForm((current) => ({ ...current, description: event.target.value }))} rows={5} className="theme-input w-full rounded-xl border px-3 py-2 text-sm resize-none" placeholder="Describe the issue and what resolution you need." />
              </div>
              <button type="submit" disabled={disputeSubmitting} className="inline-flex w-full items-center justify-center gap-2 rounded-xl theme-btn-primary px-4 py-2.5 text-sm font-semibold disabled:opacity-50">
                <ShieldAlert className="h-4 w-4" /> {disputeSubmitting ? "Submitting..." : "Submit dispute"}
              </button>
            </form>

            <div className="rounded-2xl border border-border bg-surface-1 overflow-hidden">
              <div className="border-b border-border px-5 py-4">
                <h2 className="text-sm font-semibold text-text">Dispute cases</h2>
                <p className="mt-1 text-xs text-text-muted">Formal review cases tied to returns, payouts, and order evidence.</p>
              </div>
              <div className="divide-y divide-border">
                {disputes.length > 0 ? disputes.map((dispute) => (
                  <article key={dispute.id} className="px-5 py-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-text">#{dispute.id} {dispute.title || "Untitled dispute"}</p>
                        <p className="mt-1 text-xs text-text-muted">{dispute.dispute_type} · Priority {dispute.priority} · Created {formatDate(dispute.created_at)}</p>
                      </div>
                      <span className={`rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase ${STATUS_CHIP[dispute.status] || "theme-chip-muted"}`}>{dispute.status.replaceAll("_", " ")}</span>
                    </div>
                    <p className="mt-2 text-sm text-text-muted">{dispute.description}</p>
                    {dispute.related_order_id ? <p className="mt-2 text-xs text-text-faint">Related order #{dispute.related_order_id}</p> : null}
                    {dispute.admin_notes ? <p className="mt-2 text-xs text-text-muted">Admin notes: {dispute.admin_notes}</p> : null}
                    {dispute.resolution_notes ? <p className="mt-1 text-xs text-text-muted">Resolution: {dispute.resolution_notes}</p> : null}
                  </article>
                )) : (
                  <div className="px-5 py-10 text-sm text-text-muted">No dispute cases created yet.</div>
                )}
              </div>
            </div>
          </div>
        )}

        <div className="rounded-2xl border border-info/25 bg-info/5 p-4 text-sm text-info">
          <div className="flex items-start gap-3">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <p>Need order-level action first? Open the original order from Orders to review shipment, settlement, and return context before escalating it here.</p>
          </div>
        </div>
      </PanelContent>
    </SupplierLayout>
  );
}

export default function SupplierSupportPage() {
  return (
    <Suspense fallback={<div className="min-h-screen" />}>
      <SupplierSupportPageContent />
    </Suspense>
  );
}


