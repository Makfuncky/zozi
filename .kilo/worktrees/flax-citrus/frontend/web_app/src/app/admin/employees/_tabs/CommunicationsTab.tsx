"use client";

import { Button } from "@/components/ui/Button";

import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Video,
  MessageCircle,
  Mail,
  Shield,
  Lock,
  Eye,
  Plus,
  X,
  Check,
  AlertTriangle,
  Loader2,
  ChevronDown,
  Phone,
  UserX,
  Send,
  Inbox,
  Globe,
  FileSearch,
  BookOpen,
} from "@/lib/icons";
import type { Employee } from "../employee-types";

interface VideoRoom {
  id: number;
  name: string;
  purpose: string;
  created_at: string;
  status: string;
}

interface ChatThread {
  id: number;
  title: string;
  last_message_at: string;
  is_private: boolean;
}

interface Message {
  id: number;
  content: string;
  sender_name: string;
  created_at: string;
  direction: string;
}

import type { ToastType } from "@/lib/toastStore";
import { apiFetch } from "@/lib/api";

interface CommunicationsTabProps {
  employees: Employee[];
  addToast: (message: string, type?: ToastType, duration?: number) => void;
}

export default function CommunicationsTab({ employees, addToast }: CommunicationsTabProps) {
  const [activeSection, setActiveSection] = useState<string | null>("video");
  const [rooms, setRooms] = useState<VideoRoom[]>([]);
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [showVideoModal, setShowVideoModal] = useState(false);
  const [showChatModal, setShowChatModal] = useState(false);
  const [showEmailModal, setShowEmailModal] = useState(false);

  const [videoForm, setVideoForm] = useState({ name: "", purpose: "meeting", participants: "" });
  const [chatForm, setChatForm] = useState({ title: "", is_private: false, participant_ids: "" as number[] | string });
  const [emailForm, setEmailForm] = useState({ to: "", subject: "", body: "", cc: "", is_external: false });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
const [videoRes, chatRes] = await Promise.allSettled([
         apiFetch("/admin/video/rooms"),
         apiFetch("/admin/chat/threads"),
       ]);
      if (videoRes.status === "fulfilled") {
        const data = await videoRes.value.json().catch(() => []);
        setRooms(Array.isArray(data) ? data : []);
      }
      if (chatRes.status === "fulfilled") {
        const data = await chatRes.value.json().catch(() => []);
        setThreads(Array.isArray(data) ? data : []);
      }
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const handleCreateVideoRoom = async () => {
    if (!videoForm.name) {
      addToast("Room name is required", "error");
      return;
    }
    try {
      // Parse participants as comma-separated list of integers
      const participants = videoForm.participants
        .split(",")
        .map((s) => parseInt(s.trim()))
        .filter((n) => !Number.isNaN(n));
const res = await apiFetch("/admin/video/rooms", {
         method: "POST",
         headers: { "Content-Type": "application/json" },
         body: JSON.stringify({ name: videoForm.name, participants, is_boardroom: videoForm.purpose === "meeting" }),
       });
      if (res.ok) {
        addToast("Video room created", "success");
        setShowVideoModal(false);
        setVideoForm({ name: "", purpose: "meeting", participants: "" });
        void loadData();
      } else {
        addToast("Failed to create video room", "error");
      }
    } catch {
      addToast("Network error", "error");
    }
  };

  const handleCreateChatThread = async () => {
    if (!chatForm.title) {
      addToast("Thread title is required", "error");
      return;
    }
    try {
      // Parse participant_ids as comma-separated list of integers
      const participantIds = typeof chatForm.participant_ids === "string"
        ? chatForm.participant_ids.split(",").map((s) => parseInt(s.trim())).filter((n) => !Number.isNaN(n))
        : chatForm.participant_ids;
      const endpoint = chatForm.is_private ? "/admin/chat/direct" : "/admin/chat/group";
      const res = await apiFetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: chatForm.title, participants: participantIds, name: chatForm.title }),
      });
      if (res.ok) {
        addToast("Chat thread created", "success");
        setShowChatModal(false);
        setChatForm({ title: "", is_private: false, participant_ids: "" });
        void loadData();
      } else {
        addToast("Failed to create chat thread", "error");
      }
    } catch {
      addToast("Network error", "error");
    }
  };

  const handleSendEmail = async () => {
    if (!emailForm.to || !emailForm.subject || !emailForm.body) {
      addToast("To, subject, and body are required", "error");
      return;
    }
    try {
      const endpoint = emailForm.is_external ? "/admin/messaging/external" : "/admin/messaging/internal";
      const res = await apiFetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          to: emailForm.to,
          subject: emailForm.subject,
          body: emailForm.body,
          sender_id: 0, // Will be set by backend from auth token
        }),
      });
      if (res.ok) {
        addToast("Email sent", "success");
        setShowEmailModal(false);
        setEmailForm({ to: "", subject: "", body: "", cc: "", is_external: false });
      } else {
        addToast("Failed to send email", "error");
      }
    } catch {
      addToast("Network error", "error");
    }
  };

  const sections = [
    { key: "video", label: "Video Rooms", icon: Video },
    { key: "chat", label: "Contextual Chat", icon: MessageCircle },
    { key: "b2b", label: "B2B Masked Channels", icon: Globe },
    { key: "email", label: "Email", icon: Mail },
    { key: "dlp", label: "DLP & Security", icon: Lock },
    { key: "archive", label: "E-Discovery", icon: FileSearch },
  ];

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text">Enterprise Communication Suite</h3>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        {[
          { icon: Video, title: "Video Rooms", desc: "Jitsi/WebRTC rooms with screen sharing, recording, and participant management" },
          { icon: MessageCircle, title: "Contextual Chat", desc: "Auto-generated threads per entity, approval chain, or incident" },
          { icon: Globe, title: "B2B Masked Channels", desc: "Clients see masked email/LinkedIn only; platform routes to true contact" },
          { icon: Mail, title: "Unified Email", desc: "Internal/external email with templates, tracking, and signature enforcement" },
          { icon: Shield, title: "DLP & Leak Prevention", desc: "Regex + OCR scanning on outbound email, chat, and file attachments" },
          { icon: FileSearch, title: "E-Discovery", desc: "Sovereign search across all channels with legal hold and export" },
        ].map(({ icon: Icon, title, desc }) => (
          <button
            key={title}
            onClick={() => setActiveSection(title === "Video Rooms" ? "video" : title === "Contextual Chat" ? "chat" : title === "B2B Masked Channels" ? "b2b" : title === "Unified Email" ? "email" : title === "DLP & Leak Prevention" ? "dlp" : "archive")}
            className={`rounded-xl border p-4 text-left transition-colors ${activeSection === (title === "Video Rooms" ? "video" : title === "Contextual Chat" ? "chat" : title === "B2B Masked Channels" ? "b2b" : title === "Unified Email" ? "email" : title === "DLP & Leak Prevention" ? "dlp" : "archive") ? "border-primary/40 bg-primary/5" : "border-border bg-surface-1 hover:border-primary/30"}`}
          >
            <Icon className={`h-5 w-5 mb-2 ${activeSection === (title === "Video Rooms" ? "video" : title === "Contextual Chat" ? "chat" : title === "B2B Masked Channels" ? "b2b" : title === "Unified Email" ? "email" : title === "DLP & Leak Prevention" ? "dlp" : "archive") ? "text-primary" : "text-text-muted"}`} />
            <h4 className="text-sm font-semibold text-text">{title}</h4>
            <p className="mt-1 text-[11px] text-text-muted leading-relaxed">{desc}</p>
          </button>
        ))}
      </div>

      {activeSection === "video" && (
        <div className="rounded-xl border border-border bg-surface-1 p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-text">Video Rooms</h4>
            <Button variant="primary" className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold shadow-sm transition-colors" onClick={() => setShowVideoModal(true)}
            >
              <Plus className="h-3.5 w-3.5" />
              Create Room
            </Button>
          </div>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-text-faint" />
            </div>
          ) : rooms.length === 0 ? (
            <div className="text-center py-8">
              <Video className="h-8 w-8 mx-auto mb-2 text-text-faint/40" />
              <p className="text-sm text-text-muted">No video rooms configured</p>
            </div>
          ) : (
            <div className="rounded-xl border border-border bg-surface-1 overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-border bg-surface-2 text-text-muted">
                    <th className="px-4 py-2.5 font-semibold">Room</th>
                    <th className="px-4 py-2.5 font-semibold">Purpose</th>
                    <th className="px-4 py-2.5 font-semibold">Status</th>
                    <th className="px-4 py-2.5 font-semibold">Created</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {rooms.map((room) => (
                    <tr key={room.id} className="hover:bg-surface-2/50 transition-colors">
                      <td className="px-4 py-3 text-text font-semibold">{room.name}</td>
                      <td className="px-4 py-3 text-text-muted capitalize">{room.purpose}</td>
                      <td className="px-4 py-3">
                        <span className="rounded-full bg-success/10 text-success text-[10px] font-semibold px-2 py-0.5 border border-success/20">
                          {room.status ?? "active"}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-text-muted">
                        {room.created_at ? new Date(room.created_at).toLocaleDateString() : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeSection === "chat" && (
        <div className="rounded-xl border border-border bg-surface-1 p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-text">Contextual Chat Threads</h4>
            <Button variant="primary" className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold shadow-sm transition-colors" onClick={() => setShowChatModal(true)}
            >
              <Plus className="h-3.5 w-3.5" />
              New Thread
            </Button>
          </div>
          {threads.length === 0 ? (
            <div className="text-center py-8">
              <MessageCircle className="h-8 w-8 mx-auto mb-2 text-text-faint/40" />
              <p className="text-sm text-text-muted">No chat threads</p>
            </div>
          ) : (
            <div className="space-y-2">
              {threads.map((thread) => (
                <div key={thread.id} className="flex items-center justify-between rounded-lg bg-surface-2 border border-border p-3 hover:border-primary/30 transition-colors">
                  <div>
                    <p className="text-xs font-semibold text-text">{thread.title}</p>
                    <p className="text-[10px] text-text-faint">Last activity: {thread.last_message_at ? new Date(thread.last_message_at).toLocaleString() : "—"}</p>
                  </div>
                  <span className="rounded-full bg-surface-3 text-text-muted text-[10px] font-semibold px-2 py-0.5 border border-border">
                    {thread.is_private ? "Private" : "Group"}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeSection === "b2b" && (
        <div className="rounded-xl border border-border bg-surface-1 p-4 space-y-4">
          <h4 className="text-sm font-semibold text-text">B2B Masked Communication Channels</h4>
          <div className="grid gap-3 sm:grid-cols-2">
            {[
              { label: "Masked Email Gateway", desc: "Clients see masked address; replies route through entity proxy" },
              { label: "LinkedIn Messaging Proxy", desc: "Platform sends on behalf of employee; client never sees true contact" },
              { label: "WhatsApp Business Bridge", desc: "Outbound messages routed through company WhatsApp Business API" },
              { label: "Auto-Contact Form", desc: "Website contact forms routed to correct employee via department rules" },
            ].map((item) => (
              <div key={item.label} className="rounded-lg bg-surface-2 border border-border p-3">
                <p className="text-xs font-semibold text-text">{item.label}</p>
                <p className="text-[10px] text-text-muted mt-1">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeSection === "email" && (
        <div className="rounded-xl border border-border bg-surface-1 p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-text">Unified Email</h4>
            <Button variant="primary" className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold shadow-sm transition-colors" onClick={() => setShowEmailModal(true)}
            >
              <Plus className="h-3.5 w-3.5" />
              Compose
            </Button>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            {["Internal Memo", "Client Correspondence", "Compliance Notice"].map((label) => (
              <div key={label} className="rounded-lg bg-surface-2 border border-border p-3 text-center">
                <Mail className="h-4 w-4 mx-auto mb-1 text-primary" />
                <p className="text-[11px] font-semibold text-text">{label}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeSection === "dlp" && (
        <div className="rounded-xl border border-border bg-surface-1 p-4 space-y-4">
          <h4 className="text-sm font-semibold text-text text-danger">Data Loss Prevention (DLP)</h4>
          <div className="grid gap-3 sm:grid-cols-3">
            {[
              { title: "Regex Pattern Matching", desc: "IBAN, credit card, Omani ID patterns scanned on outbound channels" },
              { title: "OCR on Attachments", desc: "Scanned PDFs and images still protected against PII leakage" },
              { title: "Quarantine Actions", desc: "Suspicious messages held for review, admin alerted via incident channel" },
            ].map((item) => (
              <div key={item.title} className="rounded-lg bg-surface-2 border border-border p-3">
                <p className="text-xs font-semibold text-text">{item.title}</p>
                <p className="text-[10px] text-text-muted mt-1">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeSection === "archive" && (
        <div className="rounded-xl border border-border bg-surface-1 p-4 space-y-4">
          <h4 className="text-sm font-semibold text-text">E-Discovery & Legal Hold</h4>
          <div className="space-y-2">
            {["Sovereign search across all communication channels", "Legal hold suspends deletion on targeted threads", "Export as WORM-compliant archive", "Chain of custody metadata preserved"].map((item) => (
              <div key={item} className="flex items-center gap-2">
                <Check className="h-3.5 w-3.5 text-success shrink-0" />
                <span className="text-[12px] text-text">{item}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Modals */}
      {showVideoModal && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4" onClick={(e: any) => e.target === e.currentTarget && setShowVideoModal(false)}>
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }} className="w-full max-w-lg rounded-2xl border border-border bg-surface-1 shadow-2xl">
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <h2 className="font-bold text-text flex items-center gap-2"><Video className="h-4 w-4 text-primary" /> Create Video Room</h2>
              <button onClick={() => setShowVideoModal(false)} className="text-text-muted hover:text-text"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-5 space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">Room Name *</label>
                <input type="text" value={videoForm.name} onChange={(e) => setVideoForm((f) => ({ ...f, name: e.target.value }))} placeholder="Q3 Board Review" className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text placeholder:text-text-faint outline-none focus:border-primary/50" />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">Purpose</label>
                <select value={videoForm.purpose} onChange={(e) => setVideoForm((f) => ({ ...f, purpose: e.target.value }))} className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none">
                  <option value="meeting">Meeting</option>
                  <option value="training">Training</option>
                  <option value="interview">Interview</option>
                  <option value="incident">Incident Review</option>
                </select>
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">Participants (comma-separated employee IDs)</label>
                <input type="text" value={videoForm.participants} onChange={(e) => setVideoForm((f) => ({ ...f, participants: e.target.value }))} placeholder="1, 2, 3" className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text placeholder:text-text-faint outline-none focus:border-primary/50" />
              </div>
            </div>
            <div className="flex items-center justify-end gap-2 border-t border-border px-5 py-4">
              <button onClick={() => setShowVideoModal(false)} className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text-muted hover:text-text transition-colors">Cancel</button>
              <Button variant="primary" onClick={handleCreateVideoRoom}><Check className="h-3.5 w-3.5" /> Create</Button>
            </div>
          </motion.div>
        </motion.div>
      )}

      {showChatModal && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4" onClick={(e: any) => e.target === e.currentTarget && setShowChatModal(false)}>
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }} className="w-full max-w-lg rounded-2xl border border-border bg-surface-1 shadow-2xl">
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <h2 className="font-bold text-text flex items-center gap-2"><MessageCircle className="h-4 w-4 text-primary" /> New Chat Thread</h2>
              <button onClick={() => setShowChatModal(false)} className="text-text-muted hover:text-text"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-5 space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">Thread Title *</label>
                <input type="text" value={chatForm.title} onChange={(e) => setChatForm((f) => ({ ...f, title: e.target.value }))} placeholder="Approval Chain - Invoice #1234" className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text placeholder:text-text-faint outline-none focus:border-primary/50" />
              </div>
              <div className="flex items-center gap-2">
                <input type="checkbox" checked={chatForm.is_private} onChange={(e) => setChatForm((f) => ({ ...f, is_private: e.target.checked }))} className="rounded border-border" />
                <label className="text-xs text-text-muted">Private thread (DM)</label>
              </div>
            </div>
            <div className="flex items-center justify-end gap-2 border-t border-border px-5 py-4">
              <button onClick={() => setShowChatModal(false)} className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text-muted hover:text-text transition-colors">Cancel</button>
              <Button variant="primary" onClick={handleCreateChatThread}><Check className="h-3.5 w-3.5" /> Create</Button>
            </div>
          </motion.div>
        </motion.div>
      )}

      {showEmailModal && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4" onClick={(e: any) => e.target === e.currentTarget && setShowEmailModal(false)}>
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }} className="w-full max-w-lg rounded-2xl border border-border bg-surface-1 shadow-2xl">
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <h2 className="font-bold text-text flex items-center gap-2"><Mail className="h-4 w-4 text-primary" /> Compose Email</h2>
              <button onClick={() => setShowEmailModal(false)} className="text-text-muted hover:text-text"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-5 space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">To *</label>
                <input type="email" value={emailForm.to} onChange={(e) => setEmailForm((f) => ({ ...f, to: e.target.value }))} placeholder="recipient@example.com" className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text placeholder:text-text-faint outline-none focus:border-primary/50" />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">CC</label>
                <input type="text" value={emailForm.cc} onChange={(e) => setEmailForm((f) => ({ ...f, cc: e.target.value }))} placeholder="cc@example.com, cc2@example.com" className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text placeholder:text-text-faint outline-none focus:border-primary/50" />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">Subject *</label>
                <input type="text" value={emailForm.subject} onChange={(e) => setEmailForm((f) => ({ ...f, subject: e.target.value }))} placeholder="Subject" className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text placeholder:text-text-faint outline-none focus:border-primary/50" />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">Body *</label>
                <textarea value={emailForm.body} onChange={(e) => setEmailForm((f) => ({ ...f, body: e.target.value }))} placeholder="Type your message..." rows={4} className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text placeholder:text-text-faint outline-none focus:border-primary/50" />
              </div>
              <div className="flex items-center gap-2">
                <input type="checkbox" checked={emailForm.is_external} onChange={(e) => setEmailForm((f) => ({ ...f, is_external: e.target.checked }))} className="rounded border-border" />
                <label className="text-xs text-text-muted">External recipient (DLP scanning applies)</label>
              </div>
            </div>
            <div className="flex items-center justify-end gap-2 border-t border-border px-5 py-4">
              <button onClick={() => setShowEmailModal(false)} className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text-muted hover:text-text transition-colors">Cancel</button>
              <Button variant="primary" onClick={handleSendEmail}><Send className="h-3.5 w-3.5" /> Send</Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </section>
  );
}


