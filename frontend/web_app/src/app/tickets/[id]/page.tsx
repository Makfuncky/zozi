"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowLeft, Send, User, ShieldCheck } from "@/lib/icons";
import { API_URL, apiFetch } from "@/lib/api";
import { connectUserRealtimeSocket, isTicketRealtimeMessage } from "@/lib/userRealtime";
import { useAuth } from "@/lib/useAuth";
import { createRealtimeRefreshScheduler } from "@shared/realtime";

type Priority = "low" | "normal" | "high" | "urgent";
type Status = "open" | "pending" | "in_progress" | "resolved" | "closed";

interface TicketAttachment {
  id: number;
  original_name: string;
  file_path: string;
  mime_type?: string | null;
  file_size_bytes?: number | null;
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

interface Ticket {
  id: number;
  subject: string;
  message: string;
  status: Status;
  priority: Priority;
  ticket_category: "customer" | "supplier" | "logistics_partner";
  raised_by_role?: string | null;
  related_entity_type?: string | null;
  related_entity_id?: number | null;
  created_at: string;
  attachments: TicketAttachment[];
  replies: TicketReply[];
}

const STATUS_CHIP: Record<Status, string> = {
  open: "bg-success/10 text-success border border-success/20",
  pending: "bg-warning/10 text-warning border border-warning/20",
  in_progress: "bg-warning/10 text-warning border border-warning/20",
  resolved: "bg-info/10 text-info border border-info/20",
  closed: "bg-surface-2 text-text-muted border border-border",
};

const PRIORITY_CHIP: Record<Priority, string> = {
  low: "bg-surface-2 text-text-muted border border-border",
  normal: "bg-success/10 text-success border border-success/20",
  high: "bg-warning/10 text-warning border border-warning/20",
  urgent: "bg-danger/10 text-danger border border-danger/20",
};

export default function TicketDetailPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const { isLoggedIn, isLoading: authLoading } = useAuth();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reply, setReply] = useState("");
  const [attachmentFiles, setAttachmentFiles] = useState<File[]>([]);
  const [uploadingAttachments, setUploadingAttachments] = useState(false);
  const [sending, setSending] = useState(false);
  const [replyError, setReplyError] = useState<string | null>(null);

  const load = useCallback(async ({ silent = false }: { silent?: boolean } = {}) => {
    if (!silent) {
      setLoading(true);
    }
    try {
      const res = await apiFetch(`/tickets/${params?.id}`);
      if (res.ok) {
        setTicket(await res.json());
      } else if (res.status === 404) {
        setError("Ticket not found.");
      } else {
        setError("Failed to load ticket.");
      }
    } catch {
      setError("Network error.");
    }
    if (!silent) {
      setLoading(false);
    }
  }, [params?.id]);

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn) { router.push("/login"); return; }
    void load();
  }, [authLoading, isLoggedIn, router, load]);

  useEffect(() => {
    if (authLoading || !isLoggedIn) {
      return;
    }

    const ticketId = Number(params?.id);
    if (!Number.isFinite(ticketId)) {
      return;
    }

    const scheduler = createRealtimeRefreshScheduler(() => load({ silent: true }));

    const socket = connectUserRealtimeSocket(
      () => undefined,
      (payload) => {
        if (isTicketRealtimeMessage(payload) && payload?.ticket_id === ticketId) {
          scheduler.trigger();
        }
      },
    );

    return () => {
      scheduler.cancel();
      socket?.close();
    };
  }, [authLoading, isLoggedIn, load, params?.id]);

  const uploadAttachments = useCallback(async () => {
    if (attachmentFiles.length === 0) {
      return;
    }
    setUploadingAttachments(true);
    try {
      for (const file of attachmentFiles) {
        const payload = new FormData();
        payload.append("file", file);
        const res = await apiFetch(`/tickets/${params?.id}/attachments`, {
          method: "POST",
          body: payload,
        });
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error(typeof data.detail === "string" ? data.detail : "Attachment upload failed.");
        }
      }
      setAttachmentFiles([]);
      await load({ silent: true });
    } catch (err) {
      setReplyError(err instanceof Error ? err.message : "Attachment upload failed.");
    } finally {
      setUploadingAttachments(false);
    }
  }, [attachmentFiles, load, params?.id]);

  const handleReply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (reply.trim().length < 1) return;
    setSending(true);
    setReplyError(null);
    try {
      const res = await apiFetch(`/tickets/${params?.id}/reply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: reply.trim() }),
      });
      if (res.ok) {
        setReply("");
        load();
      } else {
        const d = await res.json().catch(() => ({}));
        setReplyError(d.detail ?? "Failed to send reply.");
      }
    } catch { setReplyError("Network error."); }
    setSending(false);
  };

  if (authLoading || loading) {
    return (
      <main className="min-h-screen px-4 py-8">
        <div className="max-w-2xl mx-auto space-y-3">
          <div className="theme-card h-32 animate-pulse" />
          <div className="theme-card h-20 animate-pulse" />
        </div>
      </main>
    );
  }

  if (error || !ticket) {
    return (
      <main className="min-h-screen px-4 py-8">
        <div className="max-w-2xl mx-auto theme-card p-8 text-center">
          <p className="text-danger font-semibold">{error ?? "Ticket not found"}</p>
          <button onClick={() => router.push("/tickets")} className="mt-4 text-brand text-sm hover:underline">
            ← Back to Tickets
          </button>
        </div>
      </main>
    );
  }

  const isClosed = ticket.status === "closed" || ticket.status === "resolved";
  const buildAttachmentHref = (attachment: TicketAttachment) => `${API_URL.replace(/\/$/, "")}/${attachment.file_path.replace(/^\//, "")}`;

  return (
    <main className="min-h-screen px-4 py-8">
      <div className="max-w-2xl mx-auto">
        {/* Back */}
        <button
          onClick={() => router.push("/tickets")}
          className="flex items-center gap-2 text-sm theme-text-muted hover:text-brand transition-colors mb-5"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Tickets
        </button>

        {/* Header */}
        <div className="theme-card p-5 mb-4">
          <h1 className="font-extrabold text-lg theme-text mb-3">{ticket.subject}</h1>
          <div className="flex flex-wrap gap-2 mb-3">
            <span className={`text-xs px-2 py-0.5 rounded-full font-semibold capitalize ${STATUS_CHIP[ticket.status]}`}>
              {ticket.status.replace("_", " ")}
            </span>
            <span className={`text-xs px-2 py-0.5 rounded-full font-semibold capitalize ${PRIORITY_CHIP[ticket.priority]}`}>
              {ticket.priority} priority
            </span>
            <span className="text-xs px-2 py-0.5 rounded-full font-semibold capitalize theme-chip-muted">
              {ticket.ticket_category.replace("_", " ")}
            </span>
            {ticket.related_entity_type && ticket.related_entity_id ? (
              <span className="text-xs px-2 py-0.5 rounded-full font-semibold theme-chip-muted">
                {ticket.related_entity_type} #{ticket.related_entity_id}
              </span>
            ) : null}
            <span className="text-xs theme-text-muted">
              Opened {new Date(ticket.created_at).toLocaleDateString()}
            </span>
          </div>
          {/* Original message */}
          <div className="bg-surface-1 rounded-xl p-4 border border-border">
            <p className="text-sm theme-text whitespace-pre-wrap">{ticket.message}</p>
          </div>
          {ticket.attachments.length > 0 && (
            <div className="mt-4 space-y-2">
              <p className="text-xs font-semibold theme-text-muted uppercase tracking-wide">Attachments</p>
              <div className="flex flex-wrap gap-2">
                {ticket.attachments.map((attachment) => (
                  <a
                    key={attachment.id}
                    href={buildAttachmentHref(attachment)}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-full border border-border px-3 py-1 text-xs font-semibold text-primary hover:border-primary/40"
                  >
                    {attachment.original_name}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Replies */}
        {ticket.replies.length > 0 && (
          <div className="space-y-3 mb-4">
            {ticket.replies.map((r, i) => (
              <motion.div
                key={r.id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className={`theme-card p-4 ${r.is_admin ? "border-brand/30" : ""}`}
              >
                <div className="flex items-center gap-2 mb-2">
                  {r.is_admin ? (
                    <>
                      <ShieldCheck className="w-4 h-4 text-brand" />
                      <span className="text-xs font-bold text-brand">Support Team</span>
                    </>
                  ) : (
                    <>
                      <User className="w-4 h-4 theme-text-muted" />
                      <span className="text-xs font-semibold theme-text-muted">You</span>
                    </>
                  )}
                  <span className="text-xs theme-text-muted ml-auto">
                    {new Date(r.created_at).toLocaleString()}
                  </span>
                </div>
                <p className="text-sm theme-text whitespace-pre-wrap">{r.message}</p>
                {r.attachments.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {r.attachments.map((attachment) => (
                      <a
                        key={attachment.id}
                        href={buildAttachmentHref(attachment)}
                        target="_blank"
                        rel="noreferrer"
                        className="rounded-full border border-border px-3 py-1 text-xs font-semibold text-primary hover:border-primary/40"
                      >
                        {attachment.original_name}
                      </a>
                    ))}
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        )}

        {/* Reply form */}
        {!isClosed ? (
          <div className="theme-card p-4">
            <h3 className="font-semibold theme-text mb-3 text-sm">Add Reply</h3>
            <form onSubmit={handleReply} className="space-y-3">
              <textarea
                value={reply}
                onChange={(e) => setReply(e.target.value)}
                rows={4}
                placeholder="Write your reply…"
                className="theme-input w-full resize-none"
              />
              <div>
                <label className="text-xs font-semibold text-text-muted block mb-1">Supporting files</label>
                <input
                  type="file"
                  multiple
                  onChange={(event) => setAttachmentFiles(Array.from(event.target.files ?? []))}
                  className="block w-full text-sm text-text-muted file:mr-3 file:rounded-lg file:border-0 file:bg-surface-2 file:px-3 file:py-2 file:text-sm file:font-semibold file:text-text"
                />
                {attachmentFiles.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {attachmentFiles.map((file) => (
                      <span key={`${file.name}-${file.size}`} className="rounded-full border border-border px-2 py-1 text-xs text-text-muted">
                        {file.name}
                      </span>
                    ))}
                  </div>
                )}
                <button
                  type="button"
                  onClick={() => void uploadAttachments()}
                  disabled={uploadingAttachments || attachmentFiles.length === 0}
                  className="mt-3 rounded-xl border border-border px-4 py-2 text-sm font-semibold text-text disabled:opacity-50"
                >
                  {uploadingAttachments ? "Uploading…" : "Upload Attachments"}
                </button>
              </div>
              {replyError && <p className="text-danger text-sm">{replyError}</p>}
              <button
                type="submit"
                disabled={sending || !reply.trim()}
                className="flex items-center gap-2 px-4 py-2 rounded-xl theme-btn-primary font-semibold text-sm disabled:opacity-50"
              >
                <Send className="w-4 h-4" />
                {sending ? "Sending…" : "Send Reply"}
              </button>
            </form>
          </div>
        ) : (
          <div className="theme-card p-4 text-center">
            <p className="text-sm theme-text-muted">
              This ticket is {ticket.status}. Open a new ticket if you need further assistance.
            </p>
          </div>
        )}
      </div>
    </main>
  );
}
