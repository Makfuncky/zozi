"use client";

import { Button } from "@/components/ui/Button";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  MessageCircle, Send, Hash, Users, Shield,
  Plus, Loader2, Search, ChevronRight, ChevronDown,
  Video, Phone, Mail, X, CheckCircle, Clock,
  AlertCircle, UserPlus, Globe, Wifi, WifiOff,
  CheckCheck,
} from "@/lib/icons";
import { apiFetch, parseJsonResponse, getAccessToken } from "@/lib/api";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";
import { useAuth } from "@/lib/useAuth";
import { useAdminCountry } from "@/lib/useAdminCountry";
import { useToastStore } from "@/lib/toastStore";
import { isAdminStaffRole } from "@shared/adminPermissions";
import ShiftHandoverModal from "@/components/country/ShiftHandoverModal";
import { useChatWebSocket, type WsChatMessage } from "@/hooks/useChatWebSocket";
import { PresenceIndicator } from "@/components/chat/PresenceIndicator";
import { TypingIndicator } from "@/components/chat/TypingIndicator";

interface ChatThread {
  id: number;
  title: string;
  entity_type?: string;
  entity_id?: number;
  last_message_at?: string;
  last_message_preview?: string;
  is_direct: boolean;
  unread_count?: number;
}

interface ChatMessage {
  id: number;
  sender_id: number;
  sender_name: string;
  message: string;
  created_at: string;
}

export default function AdminChatPanel() {
  const router = useRouter();
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();
  const addToast = useToastStore((s) => s.addToast);

  const { selectedCountry, assignedCountries, isGlobalView } = useAdminCountry();
  const countryCode = isGlobalView ? (assignedCountries[0]?.code || selectedCountry?.code || "AE") : (selectedCountry?.code || "AE");
  const [loading, setLoading] = useState(true);
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [activeThread, setActiveThread] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [newMessage, setNewMessage] = useState("");
  const [sendingMessage, setSendingMessage] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // Create thread modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newThreadTitle, setNewThreadTitle] = useState("");
  const [newThreadEntityType, setNewThreadEntityType] = useState("");
  const [newThreadEntityId, setNewThreadEntityId] = useState("");
  const [creatingThread, setCreatingThread] = useState(false);

  // Shift handover
  const [showHandoverModal, setShowHandoverModal] = useState(false);
  const [handoverCountryCode, setHandoverCountryCode] = useState("GLOBAL");

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const typingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Real-time WebSocket connection
  const {
    isConnected,
    roomUsers,
    typingUserNames,
    sendMessage: wsSendMessage,
    sendTyping,
    sendReadReceipt,
    sendPresence,
  } = useChatWebSocket({
    roomId: activeThread ? String(activeThread) : null,
    token: typeof window !== "undefined" ? getAccessToken() ?? "" : "",
    userId: user?.id ?? null,
    onMessage: (msg: WsChatMessage) => {
      // Append incoming real-time message to the current thread
      setMessages((prev) => {
        if (prev.some((m) => m.id === msg.message_id)) return prev;
        return [
          ...prev,
          {
            id: msg.message_id,
            sender_id: msg.sender_id,
            sender_name: msg.sender_name,
            message: msg.content,
            created_at: msg.created_at,
          },
        ];
      });
      // Update thread list with latest preview
      setThreads((prev) =>
        prev.map((t) =>
          t.id === Number(msg.room_id)
            ? { ...t, last_message_preview: msg.content, last_message_at: msg.created_at }
            : t
        )
      );
    },
  });

  // Store WebSocket token when user logs in
  useEffect(() => {
    if (user?.id && typeof window !== "undefined") {
      const stored = localStorage.getItem("zozi_ws_token");
      if (!stored) {
        localStorage.setItem("zozi_ws_token", getAccessToken() ?? "");
      }
    }
  }, [user?.id]);

  const loadThreads = useCallback(async () => {
    try {
      const path = isGlobalView ? "/admin/chat/threads" : `/admin/chat/threads/${countryCode}`;
      const res = await apiFetch(path);
      if (res.ok) {
        const data = await parseJsonResponse(res);
        setThreads(Array.isArray(data) ? data : []);
      }
    } catch {
      // silent
    }
  }, [isGlobalView, countryCode]);

  const loadMessages = useCallback(async (threadId: number) => {
    setMessagesLoading(true);
    try {
      const res = await apiFetch(`/admin/chat/threads/${countryCode}/${threadId}/messages?limit=100`);
      if (res.ok) {
        const data = await parseJsonResponse(res);
        setMessages(data?.messages ?? []);
      }
    } catch {
      // silent
    } finally {
      setMessagesLoading(false);
    }
  }, [isGlobalView, countryCode]);

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn || !isAdminStaffRole(user?.role)) {
      router.replace("/admin/login");
      return;
    }
    (async () => {
      await loadThreads();
      setLoading(false);
    })();
  }, [authLoading, isLoggedIn, loadThreads, router, user?.role]);

  useEffect(() => {
    if (activeThread) {
      loadMessages(activeThread);
      // Send presence and read receipt when entering a room
      sendPresence("online");
      sendReadReceipt();
    }
  }, [activeThread, loadMessages, sendPresence, sendReadReceipt]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Send typing indicator
  const handleTyping = useCallback(
    (isTyping: boolean) => {
      sendTyping(isTyping);
      if (isTyping && typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
      if (!isTyping) return;
      typingTimeoutRef.current = setTimeout(() => {
        sendTyping(false);
      }, 3000);
    },
    [sendTyping]
  );

  const handleSendMessage = async () => {
    if (!activeThread || !newMessage.trim()) return;
    setSendingMessage(true);
    sendTyping(false);

    // Send via WebSocket for real-time delivery
    wsSendMessage(newMessage.trim());

    // Also persist via REST as fallback
    try {
      await apiFetch(`/admin/chat/threads/${countryCode}/${activeThread}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: newMessage.trim(), sender_id: user?.id }),
      });
    } catch {
      // WebSocket already handled it
    }

    setNewMessage("");
    setSendingMessage(false);

    // Immediately update thread preview
    setThreads((prev) =>
      prev.map((t) =>
        t.id === activeThread
          ? { ...t, last_message_preview: newMessage.trim(), last_message_at: new Date().toISOString() }
          : t
      )
    );
  };

  const handleCreateThread = async () => {
    if (!newThreadTitle.trim()) return;
    setCreatingThread(true);
    try {
      const params = new URLSearchParams({ title: newThreadTitle.trim() });
      if (newThreadEntityType && newThreadEntityId) {
        params.set("entity_type", newThreadEntityType);
        params.set("entity_id", newThreadEntityId);
      }
      const res = await apiFetch(`/admin/chat/threads/${countryCode}?${params.toString()}`, { method: "POST" });
      if (res.ok) {
        addToast("Thread created", "success");
        setShowCreateModal(false);
        setNewThreadTitle("");
        setNewThreadEntityType("");
        setNewThreadEntityId("");
        loadThreads();
      } else {
        const err = await parseJsonResponse(res);
        addToast(err?.detail ?? "Failed to create thread", "error");
      }
    } catch {
      addToast("Network error", "error");
    } finally {
      setCreatingThread(false);
    }
  };

  const filteredThreads = searchQuery
    ? threads.filter(
        (t) =>
          t.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          t.entity_type?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : threads;

  const currentThread = threads.find((t) => t.id === activeThread);

  if (authLoading || loading) {
    return <PanelLoadingState count={3} />;
  }

  if (!isLoggedIn || !isAdminStaffRole(user?.role)) return null;

  return (
    <PanelContent width="full" className="h-[calc(100vh-8rem)]">
      <span className="text-[10px] text-text-faint">{isGlobalView ? "Global View" : `Country: ${selectedCountry?.code || countryCode}`}</span>
      <div className="flex h-full gap-3">
        {/* Threads sidebar */}
        <div className="w-72 shrink-0 flex flex-col rounded-xl border border-border bg-surface-1 overflow-hidden">
          <div className="flex items-center justify-between px-3 py-2.5 border-b border-border bg-surface-2">
            <span className="text-xs font-bold text-text flex items-center gap-2">
              <MessageCircle className="h-3.5 w-3.5 text-primary" />
              Threads
            </span>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setShowHandoverModal(true)}
                className="flex items-center gap-1 rounded-lg border border-border/60 px-2 py-1 text-[10px] font-medium text-text-muted hover:text-text hover:bg-surface-3 transition"
                title="Shift Handover"
              >
                <Clock className="h-3 w-3" />
                Handover
              </button>
              <Button variant="primary" className="flex items-center gap-1 rounded-lg px-2 py-1 text-[10px] font-semibold transition" onClick={() => setShowCreateModal(true)}
              >
                <Plus className="h-3 w-3" />
                New
              </Button>
            </div>
          </div>

          {/* Search */}
          <div className="px-3 py-2 border-b border-border/60">
            <div className="relative">
              <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-text-faint" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search threads..."
                className="w-full rounded-lg border border-border bg-surface pl-7 pr-2 py-1.5 text-[10px] text-text outline-none focus:border-primary/50"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto">
            {filteredThreads.length === 0 ? (
              <div className="text-center py-8 text-text-muted px-3">
                <MessageCircle className="h-6 w-6 mx-auto mb-1 opacity-40" />
                <p className="text-xs">{searchQuery ? "No matching threads" : "No chat threads"}</p>
                <p className="text-[10px] text-text-faint mt-1">
                  {searchQuery ? "Try a different search term" : "Create a thread to start chatting"}
                </p>
              </div>
            ) : (
              filteredThreads.map((thread) => (
                <button
                  key={thread.id}
                  onClick={() => setActiveThread(thread.id)}
                  className={`w-full text-left px-3 py-2.5 border-b border-border/60 transition-colors hover:bg-surface-2 ${
                    activeThread === thread.id ? "bg-primary/5 border-l-2 border-l-primary" : ""
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-text truncate">{thread.title}</span>
                    {(thread.unread_count ?? 0) > 0 && (
                      <span className="bg-primary text-white text-[9px] px-1.5 py-0.5 rounded-full font-bold">
                        {thread.unread_count}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    {thread.entity_type && (
                      <span className="text-[9px] font-mono text-text-faint bg-surface-3 px-1 py-0.5 rounded">
                        {thread.entity_type}#{thread.entity_id}
                      </span>
                    )}
                    {thread.last_message_preview && (
                      <span className="text-[10px] text-text-muted truncate">{thread.last_message_preview}</span>
                    )}
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Chat area */}
        <div className="flex-1 flex flex-col rounded-xl border border-border bg-surface-1 overflow-hidden">
          {activeThread ? (
            <>
              {/* Chat header with presence */}
              <div className="px-4 py-2.5 border-b border-border bg-surface-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-text">
                      {currentThread?.title ?? "Chat"}
                    </span>
                    {currentThread?.entity_type && (
                      <span className="text-[9px] font-mono text-text-faint bg-surface-3 px-1 py-0.5 rounded">
                        {currentThread.entity_type}#{currentThread.entity_id}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <PresenceIndicator users={roomUsers} currentUserId={user?.id} showList />
                    <div className="flex items-center gap-1 text-[9px] text-text-faint">
                      {isConnected ? (
                        <Wifi className="h-3 w-3 text-success" />
                      ) : (
                        <WifiOff className="h-3 w-3 text-danger" />
                      )}
                      {isConnected ? "Live" : "Offline"}
                    </div>
                  </div>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto px-4 py-3">
                <div className="space-y-2">
                  {messagesLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-5 w-5 animate-spin text-primary" />
                    </div>
                  ) : messages.length === 0 ? (
                    <div className="text-center py-8 text-text-muted">
                      <MessageCircle className="h-6 w-6 mx-auto mb-1 opacity-40" />
                      <p className="text-xs">No messages yet</p>
                      <p className="text-[10px] text-text-faint mt-1">Send a message to start the conversation</p>
                    </div>
                  ) : (
                    messages.map((msg, idx) => {
                      const isOwn = msg.sender_id === user?.id;
                      const prevMsg = idx > 0 ? messages[idx - 1] : null;
                      const showAvatar = !prevMsg || prevMsg.sender_id !== msg.sender_id;
                      return (
                        <div
                          key={msg.id}
                          className={`flex items-start gap-2 ${isOwn ? "flex-row-reverse" : ""}`}
                        >
                          {showAvatar ? (
                            <div
                              className={`h-6 w-6 rounded-full flex items-center justify-center shrink-0 ${
                                isOwn ? "bg-primary" : "bg-primary/20"
                              }`}
                            >
                              <span className={`text-[10px] font-bold ${isOwn ? "text-white" : "text-primary"}`}>
                                {msg.sender_name?.charAt(0)?.toUpperCase() ?? "?"}
                              </span>
                            </div>
                          ) : (
                            <div className="w-6 shrink-0" />
                          )}
                          <div className={`flex-1 min-w-0 max-w-[80%] ${isOwn ? "text-right" : ""}`}>
                            {showAvatar && (
                              <div className={`flex items-center gap-2 mb-0.5 ${isOwn ? "justify-end" : ""}`}>
                                <span className="text-[10px] font-semibold text-text">
                                  {isOwn ? "You" : msg.sender_name}
                                </span>
                                <span className="text-[8px] text-text-faint">
                                  {new Date(msg.created_at).toLocaleTimeString([], {
                                    hour: "2-digit",
                                    minute: "2-digit",
                                  })}
                                </span>
                              </div>
                            )}
                            <div
                              className={`inline-block rounded-xl px-3 py-1.5 text-xs ${
                                isOwn
                                  ? "bg-primary text-white rounded-tr-md"
                                  : "bg-surface-2 text-text rounded-tl-md"
                              }`}
                            >
                              {msg.message}
                            </div>
                          </div>
                        </div>
                      );
                    })
                  )}
                  <div ref={messagesEndRef} />
                </div>
              </div>

              {/* Typing indicator */}
              <TypingIndicator typingUserNames={typingUserNames} />

              {/* Message input */}
              <div className="px-4 py-2.5 border-t border-border bg-surface-2">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newMessage}
                    onChange={(e) => {
                      setNewMessage(e.target.value);
                      handleTyping(e.target.value.length > 0);
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage();
                      }
                    }}
                    onBlur={() => sendTyping(false)}
                    placeholder="Type a message..."
                    className="flex-1 rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text outline-none focus:border-primary/50"
                  />
                  <Button variant="primary" onClick={handleSendMessage}
                    disabled={sendingMessage || !newMessage.trim()}>
                    {sendingMessage ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-text-muted">
              <div className="text-center">
                <MessageCircle className="h-10 w-10 mx-auto mb-2 opacity-40" />
                <p className="text-sm font-medium">Select a thread to start chatting</p>
                <p className="text-xs text-text-faint mt-1">Choose a conversation from the sidebar</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Create thread modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay">
          <div className="rounded-xl border border-border bg-surface-1 p-5 w-full max-w-md shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-text flex items-center gap-2">
                <MessageCircle className="h-4 w-4 text-primary" />
                New Chat Thread
              </h3>
              <button onClick={() => setShowCreateModal(false)} className="text-text-muted hover:text-text">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-3">
              <label className="block space-y-1 text-[10px] text-text-muted">
                Thread Title
                <input
                  value={newThreadTitle}
                  onChange={(e) => setNewThreadTitle(e.target.value)}
                  className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text"
                  placeholder="e.g. Order #1234 Discussion"
                />
              </label>
              <div className="grid grid-cols-2 gap-2">
                <label className="block space-y-1 text-[10px] text-text-muted">
                  Entity Type (optional)
                  <input
                    value={newThreadEntityType}
                    onChange={(e) => setNewThreadEntityType(e.target.value)}
                    className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text"
                    placeholder="order, supplier, ticket"
                  />
                </label>
                <label className="block space-y-1 text-[10px] text-text-muted">
                  Entity ID (optional)
                  <input
                    value={newThreadEntityId}
                    onChange={(e) => setNewThreadEntityId(e.target.value)}
                    className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text"
                    placeholder="1234"
                  />
                </label>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 mt-5">
              <button
                onClick={() => setShowCreateModal(false)}
                className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-text-muted hover:text-text transition"
              >
                Cancel
              </button>
              <Button variant="primary" onClick={handleCreateThread}
                disabled={creatingThread || !newThreadTitle.trim()}>
                {creatingThread ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-3.5 w-3.5" />}
                Create Thread
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Shift Handover Modal */}
      <ShiftHandoverModal
        countryCode={handoverCountryCode}
        isOpen={showHandoverModal}
        onClose={() => setShowHandoverModal(false)}
      />
    </PanelContent>
  );
}
