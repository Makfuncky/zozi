"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelHero } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { isAdminStaffRole } from "@shared/adminPermissions";

type TicketStatus = "open" | "pending" | "in_progress" | "resolved" | "closed";

interface TicketAttachment {
  id: number;
  original_name: string;
  file_path: string;
  created_at: string;
}

interface TicketReply {
  id: number;
  username?: string;
  message: string;
  is_admin: boolean;
  created_at: string;
  attachments: TicketAttachment[];
}

interface AdminTicketDetail {
  id: number;
  user_id: number;
  username: string;
  subject: string;
  message: string;
  status: TicketStatus;
  priority: string;
  ticket_category?: string;
  raised_by_role?: string | null;
  related_entity_type?: string | null;
  related_entity_id?: number | null;
  created_at: string;
  updated_at: string;
  attachments: TicketAttachment[];
  replies: TicketReply[];
}

const STATUS_OPTIONS: TicketStatus[] = ["open", "pending", "in_progress", "resolved", "closed"];

export default function AdminTicketDetailPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const { user, isLoggedIn, isLoading } = useAuth();
  const role = user?.role ?? null;

  const [ticket, setTicket] = useState<AdminTicketDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reply, setReply] = useState("");
  const [sendingReply, setSendingReply] = useState(false);
  const [updatingStatus, setUpdatingStatus] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch(`/admin/tickets/${params?.id}`);
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(typeof data.detail === "string" ? data.detail : "Failed to load ticket.");
        return;
      }
      setTicket(await res.json());
      setError(null);
    } catch {
      setError("Network error.");
    } finally {
      setLoading(false);
    }
  }, [params?.id]);

  useEffect(() => {
    if (isLoading) {
      return;
    }
    if (!isLoggedIn || !isAdminStaffRole(role)) {
      router.push("/admin/login");
      return;
    }
    void load();
  }, [isLoading, isLoggedIn, load, role, router]);

  const handleReply = async () => {
    if (!reply.trim()) {
      return;
    }
    setSendingReply(true);
    try {
      const res = await apiFetch(`/admin/tickets/${params?.id}/reply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: reply.trim() }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(typeof data.detail === "string" ? data.detail : "Failed to send reply.");
        return;
      }
      setReply("");
      setTicket(await res.json());
      setError(null);
    } catch {
      setError("Network error.");
    } finally {
      setSendingReply(false);
    }
  };

  const handleStatusChange = async (status: TicketStatus) => {
    setUpdatingStatus(true);
    try {
      const res = await apiFetch(`/admin/tickets/${params?.id}/status`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(typeof data.detail === "string" ? data.detail : "Failed to update status.");
        return;
      }
      setTicket(await res.json());
      setError(null);
    } catch {
      setError("Network error.");
    } finally {
      setUpdatingStatus(false);
    }
  };

  const renderContent = () => {
    if (isLoading || loading) {
      return (
        <PanelContent width="roomy" className="space-y-4">
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className="h-24 rounded-xl bg-surface-2 animate-pulse" />
          ))}
        </PanelContent>
      );
    }

    if (!ticket) {
      return (
        <PanelContent width="roomy">
          <div className="theme-card p-6 text-sm text-danger">{error ?? "Ticket not found."}</div>
        </PanelContent>
      );
    }

    return (
      <PanelContent width="roomy" className="space-y-4">
        <PanelHero
          eyebrow={`Support ticket #${ticket.id}`}
          title={ticket.subject}
          description={(
            <span>
              Opened by {ticket.username} on {new Date(ticket.created_at).toLocaleString()}
              {ticket.related_entity_type && ticket.related_entity_id ? ` · Linked ${ticket.related_entity_type} #${ticket.related_entity_id}` : ""}
            </span>
          )}
          actions={(
            <>
              <button onClick={() => router.push("/admin/tickets")} className="rounded-xl border border-border px-3 py-2 text-xs font-semibold text-primary hover:bg-surface-2">
                Back to queue
              </button>
              <span className="rounded-full theme-chip-info px-2.5 py-1 text-xs font-semibold capitalize">{ticket.priority}</span>
              {ticket.ticket_category ? (
                <span className="rounded-full theme-chip-muted px-2.5 py-1 text-xs font-semibold capitalize">{ticket.ticket_category.replace("_", " ")}</span>
              ) : null}
              <span className="rounded-full theme-chip-muted px-2.5 py-1 text-xs font-semibold capitalize">{ticket.status.replace("_", " ")}</span>
              <select
                value={ticket.status}
                onChange={(event) => void handleStatusChange(event.target.value as TicketStatus)}
                disabled={updatingStatus}
                className="theme-input min-w-45"
              >
                {STATUS_OPTIONS.map((status) => (
                  <option key={status} value={status}>{status.replace("_", " ")}</option>
                ))}
              </select>
            </>
          )}
          className="rounded-xl p-4 sm:p-5"
        />

        <div className="theme-card p-5 space-y-3">
          <div className="rounded-xl border border-border bg-surface-2 p-4">
            <p className="whitespace-pre-wrap text-sm text-text">{ticket.message}</p>
          </div>

          {ticket.attachments.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {ticket.attachments.map((attachment) => (
                <a key={attachment.id} href={`/${attachment.file_path.replace(/^\//, "")}`} target="_blank" rel="noreferrer" className="rounded-full border border-border px-3 py-1 text-xs font-semibold text-primary hover:border-primary/40">
                  {attachment.original_name}
                </a>
              ))}
            </div>
          ) : null}
        </div>

        <div className="space-y-3">
          {ticket.replies.map((replyItem) => (
            <div key={replyItem.id} className={`theme-card p-4 ${replyItem.is_admin ? "border-primary/30" : ""}`}>
              <div className="mb-2 flex items-center justify-between gap-3">
                <span className="text-sm font-semibold text-text">
                  {replyItem.is_admin ? (replyItem.username || "Staff") : (replyItem.username || ticket.username)}
                </span>
                <span className="text-xs text-text-muted">{new Date(replyItem.created_at).toLocaleString()}</span>
              </div>
              <p className="whitespace-pre-wrap text-sm text-text">{replyItem.message}</p>
              {replyItem.attachments.length > 0 ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {replyItem.attachments.map((attachment) => (
                    <a key={attachment.id} href={`/${attachment.file_path.replace(/^\//, "")}`} target="_blank" rel="noreferrer" className="rounded-full border border-border px-3 py-1 text-xs font-semibold text-primary hover:border-primary/40">
                      {attachment.original_name}
                    </a>
                  ))}
                </div>
              ) : null}
            </div>
          ))}
        </div>

        <div className="theme-card p-4 space-y-3">
          <h2 className="text-sm font-semibold text-text">Reply</h2>
          <textarea
            value={reply}
            onChange={(event) => setReply(event.target.value)}
            rows={5}
            placeholder="Send an update to the ticket owner..."
            className="theme-input w-full resize-none"
          />
          <div className="flex items-center justify-between gap-3">
            {error ? <p className="text-sm text-danger">{error}</p> : <span />}
            <button onClick={() => void handleReply()} disabled={sendingReply || !reply.trim()} className="theme-btn-primary rounded-xl px-4 py-2 text-sm font-semibold disabled:opacity-50">
              {sendingReply ? "Sending..." : "Send Reply"}
            </button>
          </div>
        </div>
      </PanelContent>
    );
  };

  return <AdminLayout title="Tickets" headerMode="compact">{renderContent()}</AdminLayout>;
}