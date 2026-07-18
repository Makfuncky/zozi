"use client";

import { Button } from "@/components/ui/Button";

import { useState, useEffect, useRef, useCallback } from "react";
import {
  MessageCircle, Send, Hash, Package, Shield, AlertCircle, Users, X,
  Loader2, RefreshCw, ChevronDown, ChevronRight, Bell, CheckCircle,
  Clock, Filter, Inbox,
} from "@/lib/icons";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";

interface CommsMessage {
  id: number;
  sender_id: number;
  sender_name: string;
  sender_role: string;
  subject: string;
  body: string;
  priority: string;
  category: string;
  is_read: boolean;
  created_at: string;
  related_entity_type?: string;
  related_entity_id?: number;
}

interface InternalCommunicationsSystemProps {
  countryCode: string;
}

const PRIORITY_STYLES: Record<string, string> = {
  urgent: "bg-danger/10 text-danger border-danger/20",
  high: "bg-orange-500/10 text-orange-400 border-orange-500/20",
  normal: "bg-info/10 text-info border-info/20",
  low: "bg-surface-3 text-text-muted border-border",
};

const CATEGORY_STYLES: Record<string, string> = {
  escalation: "bg-danger/10 text-danger",
  financial: "bg-success/10 text-success",
  operational: "bg-info/10 text-info",
  announcement: "bg-purple-500/10 text-purple-400",
  dispute: "bg-orange-500/10 text-orange-400",
};

export default function InternalCommunicationsSystem({ countryCode }: InternalCommunicationsSystemProps) {
  const addToast = useToastStore((s) => s.addToast);

  const [messages, setMessages] = useState<CommsMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [activeCategory, setActiveCategory] = useState<string>("all");

  // New message form
  const [showNewMessage, setShowNewMessage] = useState(false);
  const [newSubject, setNewSubject] = useState("");
  const [newBody, setNewBody] = useState("");
  const [newPriority, setNewPriority] = useState("normal");
  const [newCategory, setNewCategory] = useState("operational");
  const [newEntityType, setNewEntityType] = useState("");
  const [newEntityId, setNewEntityId] = useState("");

  const ENTITY_TYPES = [
    { value: "", label: "None (general)" },
    { value: "order", label: "Order" },
    { value: "supplier", label: "Supplier" },
    { value: "ticket", label: "Support Ticket" },
    { value: "payout", label: "Payout" },
    { value: "country", label: "Country" },
  ];

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const loadMessages = useCallback(async () => {
    if (!countryCode) return;
    setLoading(true);
    try {
      const params = activeCategory !== "all" ? `?category=${activeCategory}` : "";
      const res = await apiFetch(`/admin/countries/${countryCode}/communications${params}`);
      if (res.ok) {
        const data = await parseJsonResponse(res);
        setMessages(Array.isArray(data) ? data : []);
      }
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, [countryCode, activeCategory]);

  useEffect(() => {
    loadMessages();
  }, [loadMessages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!newSubject.trim() || !newBody.trim()) return;
    setSending(true);
    try {
      const body: Record<string, any> = {
        subject: newSubject.trim(),
        body: newBody.trim(),
        priority: newPriority,
        category: newCategory,
      };
      if (newEntityType && newEntityId) {
        body.related_entity_type = newEntityType;
        body.related_entity_id = parseInt(newEntityId, 10) || 0;
      }
      const res = await apiFetch(`/admin/countries/${countryCode}/communications`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        addToast("Message sent", "success");
        setNewSubject("");
        setNewBody("");
        setNewEntityType("");
        setNewEntityId("");
        setShowNewMessage(false);
        loadMessages();
      } else {
        const err = await parseJsonResponse(res);
        addToast(err?.detail ?? "Failed to send", "error");
      }
    } catch {
      addToast("Network error", "error");
    } finally {
      setSending(false);
    }
  };

  const handleMarkRead = async (id: number) => {
    try {
      await apiFetch(`/admin/countries/communications/${id}/read`, { method: "PATCH" });
      setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, is_read: true } : m)));
    } catch {
      // silent
    }
  };

  const categories = [
    { id: "all", label: "All", icon: Inbox },
    { id: "operational", label: "Operational", icon: Hash },
    { id: "financial", label: "Financial", icon: Shield },
    { id: "escalation", label: "Escalations", icon: AlertCircle },
    { id: "announcement", label: "Announcements", icon: Bell },
    { id: "dispute", label: "Disputes", icon: Package },
  ];

  const filtered = activeCategory === "all"
    ? messages
    : messages.filter((m) => m.category === activeCategory);

  return (
    <div className="space-y-4">
      {/* Category filters + new message */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex flex-wrap gap-1">
          {categories.map((cat) => {
            const Icon = cat.icon;
            const isActive = activeCategory === cat.id;
            return (
              <button
                key={cat.id}
                onClick={() => setActiveCategory(cat.id)}
                className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[10px] font-semibold transition-colors ${
                  isActive
                    ? "bg-primary text-white"
                    : "bg-surface-2 text-text-muted hover:text-text border border-border"
                }`}
              >
                <Icon className="h-3 w-3" />
                {cat.label}
                {!isActive && cat.id !== "all" && messages.filter((m) => m.category === cat.id).length > 0 && (
                  <span className="ml-1 bg-surface-3 px-1.5 py-0.5 rounded text-[9px]">
                    {messages.filter((m) => m.category === cat.id).length}
                  </span>
                )}
              </button>
            );
          })}
        </div>
        <Button variant="primary" className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[11px] font-semibold transition" onClick={() => setShowNewMessage(!showNewMessage)}
        >
          {showNewMessage ? <X className="h-3.5 w-3.5" /> : <Send className="h-3.5 w-3.5" />}
          {showNewMessage ? "Cancel" : "New Message"}
        </Button>
      </div>

      {/* New message form */}
      {showNewMessage && (
        <div className="rounded-xl border border-primary/30 bg-primary/5 p-4 space-y-3">
          <h4 className="text-xs font-bold text-text flex items-center gap-2">
            <Send className="h-3.5 w-3.5 text-primary" />
            New Internal Communication
          </h4>
          <div className="grid gap-3 sm:grid-cols-3">
            <label className="space-y-1 text-[10px] text-text-muted">
              Subject
              <input
                value={newSubject}
                onChange={(e) => setNewSubject(e.target.value)}
                className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text"
                placeholder="Brief subject line..."
              />
            </label>
            <label className="space-y-1 text-[10px] text-text-muted">
              Priority
              <select
                value={newPriority}
                onChange={(e) => setNewPriority(e.target.value)}
                className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text"
              >
                <option value="low">Low</option>
                <option value="normal">Normal</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </label>
            <label className="space-y-1 text-[10px] text-text-muted">
              Category
              <select
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
                className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text"
              >
                <option value="operational">Operational</option>
                <option value="financial">Financial</option>
                <option value="escalation">Escalation</option>
                <option value="announcement">Announcement</option>
                <option value="dispute">Dispute</option>
              </select>
            </label>
          </div>
          {/* Entity linking (war room chat) */}
          <div className="rounded-lg border border-border bg-surface-2 p-3">
            <div className="flex items-center gap-2 mb-2">
              <Hash className="h-3.5 w-3.5 text-text-faint" />
              <span className="text-[10px] font-semibold text-text-faint uppercase">Link to Entity (optional)</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <select
                value={newEntityType}
                onChange={(e) => setNewEntityType(e.target.value)}
                className="rounded-lg border border-border bg-surface px-2 py-1.5 text-[11px] text-text"
              >
                {ENTITY_TYPES.map((et) => (
                  <option key={et.value} value={et.value}>{et.label}</option>
                ))}
              </select>
              <input
                value={newEntityId}
                onChange={(e) => setNewEntityId(e.target.value)}
                placeholder="Entity ID (e.g. 1234)"
                disabled={!newEntityType}
                className="rounded-lg border border-border bg-surface px-2 py-1.5 text-[11px] text-text disabled:opacity-40"
              />
            </div>
            {newEntityType && newEntityId && (
              <p className="mt-1.5 text-[9px] text-text-faint flex items-center gap-1">
                <Hash className="h-2.5 w-2.5" />
                Message will be linked to {newEntityType}#{newEntityId}
              </p>
            )}
          </div>
          <label className="space-y-1 text-[10px] text-text-muted">
            Message Body
            <textarea
              value={newBody}
              onChange={(e) => setNewBody(e.target.value)}
              rows={3}
              className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text resize-none"
              placeholder="Describe the issue, decision, or announcement..."
            />
          </label>
          <div className="flex justify-end">
            <Button variant="primary" onClick={handleSend}
              disabled={sending || !newSubject.trim() || !newBody.trim()}>
              {sending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
              {sending ? "Sending..." : "Send"}
            </Button>
          </div>
        </div>
      )}

      {/* Messages list */}
      <div className="space-y-2 max-h-[500px] overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-8 text-text-muted">
            <MessageCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No communications yet</p>
            <p className="text-xs text-text-faint mt-1">Click &quot;New Message&quot; to send the first one</p>
          </div>
        ) : (
          filtered.map((msg) => (
            <div
              key={msg.id}
              className={`rounded-xl border p-3 transition-colors ${
                msg.is_read ? "border-border bg-surface" : "border-primary/30 bg-primary/5"
              }`}
              onClick={() => !msg.is_read && handleMarkRead(msg.id)}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  {!msg.is_read && <span className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1" />}
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-semibold text-text truncate">{msg.subject}</span>
                      <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-semibold border ${PRIORITY_STYLES[msg.priority] ?? PRIORITY_STYLES.normal}`}>
                        {msg.priority.charAt(0).toUpperCase() + msg.priority.slice(1)}
                      </span>
                      <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-semibold ${CATEGORY_STYLES[msg.category] ?? ""}`}>
                        {msg.category}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-[10px] text-text-muted">
                      <span>{msg.sender_name}</span>
                      <span className="text-text-faint">·</span>
                      <span className="text-text-faint">{new Date(msg.created_at).toLocaleString()}</span>
                      {msg.related_entity_type && (
                        <>
                          <span className="text-text-faint">·</span>
                          <span className="font-mono text-text-faint">{msg.related_entity_type}#{msg.related_entity_id}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
                {!msg.is_read && (
                  <button
                    onClick={(e) => { e.stopPropagation(); handleMarkRead(msg.id); }}
                    className="shrink-0 text-text-faint hover:text-primary transition"
                    title="Mark as read"
                  >
                    <CheckCircle className="h-4 w-4" />
                  </button>
                )}
              </div>
              <p className="mt-2 text-xs text-text leading-relaxed whitespace-pre-wrap">{msg.body}</p>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}


