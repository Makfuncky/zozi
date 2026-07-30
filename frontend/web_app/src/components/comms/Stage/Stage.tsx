"use client";

import { useMemo, lazy, Suspense, useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  MessageCircle, Mail, Video, Phone, MoreHorizontal, ArrowLeft,
  CheckCheck, Clock, Smile, Reply, Trash2, Edit3, FileText,
  UserPlus,
} from "@/lib/icons";
import { useComm, type ThreadSummary, type Message } from "../CommShell";
import { useDrag, DropZone } from "../DragProvider";
import { useAuth } from "@/lib/useAuth";
import { useCommState } from "@/hooks/useCommState";
import { useWebSocket } from "@/hooks/useWebSocket";
import ComposerDock from "../Composer";
import ChatStream from "./renderers/ChatStream";
import EmailView from "./renderers/EmailView";
import VideoRoom from "./renderers/VideoRoom";
import ContactTimeline from "./renderers/ContactTimeline";
import B2BMasked from "./renderers/B2BMasked";
import IncidentRoom from "./renderers/IncidentRoom";

// ── Thread Header ─────────────────────────────────────────────────────────

function ThreadHeader({ thread }: { thread: ThreadSummary }) {
  const { setActiveThread, setCtxOpen, setModality } = useComm();

  return (
    <div className="flex items-center gap-2 px-4 py-2.5 border-b border-border bg-surface/80 backdrop-blur-sm shrink-0">
      <button
        onClick={() => setActiveThread(null)}
        className="p-1.5 rounded-lg hover:bg-surface-2 text-text-muted hover:text-text transition-colors lg:hidden"
      >
        <ArrowLeft className="w-4 h-4" />
      </button>

      <div className="flex items-center gap-2.5 min-w-0 flex-1">
        <div className="relative w-8 h-8 rounded-full bg-surface-2 flex items-center justify-center shrink-0">
          <span className="text-[10px] font-bold text-text-muted">
            {thread.title.charAt(0).toUpperCase()}
          </span>
          <span className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full border-2 border-surface bg-emerald-500" />
        </div>

        <div className="min-w-0">
          <h2 className="text-sm font-semibold text-text truncate">{thread.title}</h2>
          <p className="text-[10px] text-text-muted">
            {thread.transport === "chat" && "Direct message"}
            {thread.transport === "group" && `${thread.participants || 0} members`}
            {thread.transport === "email" && "Email thread"}
            {thread.transport === "video" && "Video room"}
            {thread.transport === "contact" && "Contact timeline"}
            {thread.transport === "b2b_masked" && "Masked B2B conversation"}
            {thread.transport === "incident" && "Incident response room"}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-1">
        {(thread.transport === "chat" || thread.transport === "group") && (
          <>
            <button className="p-2 rounded-lg hover:bg-surface-2 text-text-muted hover:text-text transition-colors" title="Voice call">
              <Phone className="w-4 h-4" />
            </button>
            <button
              onClick={() => setModality("meet")}
              className="p-2 rounded-lg hover:bg-surface-2 text-text-muted hover:text-text transition-colors"
              title="Video call"
            >
              <Video className="w-4 h-4" />
            </button>
          </>
        )}
        <button
          onClick={() => setCtxOpen((v) => !v)}
          className="p-2 rounded-lg hover:bg-surface-2 text-text-muted hover:text-text transition-colors hidden lg:block"
          title="Toggle context panel"
        >
          <MoreHorizontal className="w-4 h-4" />
        </button>
        <button className="p-2 rounded-lg hover:bg-surface-2 text-text-muted hover:text-text transition-colors" title="More">
          <MoreHorizontal className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

// ── Skeleton shimmer ──────────────────────────────────────────────────────

function SkeletonShimmer() {
  return (
    <div className="flex-1 p-4 space-y-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex gap-3 animate-pulse">
          <div className="w-7 h-7 rounded-full bg-surface-2 shrink-0" />
          <div className="flex-1 space-y-2">
            <div className="h-3 w-24 rounded bg-surface-2" />
            <div className="h-8 w-3/4 rounded-xl bg-surface-2" />
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Transport router ──────────────────────────────────────────────────────

function renderTransport(transport: string, messages: Message[], threadId?: number, typingUserNames?: string[]) {
  switch (transport) {
    case "email":
      return <EmailView messages={messages} />;
    case "video":
      return <VideoRoom />;
    case "contact":
      return <ContactTimeline />;
    case "b2b_masked":
      return <B2BMasked />;
    case "incident":
      return <IncidentRoom />;
    default:
      return <ChatStream messages={messages} threadId={threadId} typingUserNames={typingUserNames} />;
  }
}

// ── Main Stage Component ──────────────────────────────────────────────────

export default function CommStage() {
  const { activeThread, messages, sendAs, setSendAs, density, setActiveThread } = useComm();
  const {
    loading: messagesLoading,
    error: messagesError,
  } = useCommState("comm-messages");

  // ── Real-time WebSocket ────────────────────────────────────────
  // When a chat/group thread is active, subscribe to real-time messages.
  // The WebSocket delivers messages from other participants without polling.
  // Also provides typingUserNames and sendTyping for the typing indicator.
  const { user } = useAuth();
  const wsThreadId =
    activeThread &&
    (activeThread.transport === "chat" || activeThread.transport === "group")
      ? activeThread.id
      : null;
  const { typingUserNames, sendTyping, sendReadReceipt } = useWebSocket(wsThreadId, user?.id);

  // ── Read Receipts ─────────────────────────────────────────────
  // When the user opens a chat/group thread, send a read receipt
  // to mark all unread messages as read, and immediately decrement
  // the local unread badge so the rail updates in real-time.
  // Uses a functional updater for setThreads to avoid stale closures.
  const { setThreads } = useComm();

  useEffect(() => {
    if (!activeThread || (activeThread.transport !== "chat" && activeThread.transport !== "group")) return;

    // Send read receipt to server (notifies other participants)
    sendReadReceipt();

    // Decrement local unread badge instantly using functional updater
    if (activeThread.unread > 0) {
      setThreads((prev) =>
        prev.map((t) =>
          t.id === activeThread.id ? { ...t, unread: 0 } : t
        )
      );
    }
  }, [activeThread?.id, activeThread?.transport, setThreads, sendReadReceipt]);

  const threadMessages = useMemo(() => {
    if (!activeThread) return [];
    return messages.filter((m) => m.threadId === activeThread.id);
  }, [activeThread, messages]);

  // Show skeleton on density change
  const densityKey = density;

  const { dragPayload } = useDrag();

  const [contactDrops, setContactDrops] = useState<
    Array<{ id: string; name: string; timestamp: number }>
  >([]);

  // Handle a contact dropped on the stage — create a new direct chat thread
  const handleContactDrop = useCallback(
    (contactName: string, contactId: string) => {
      const newThread: ThreadSummary = {
        id: `contact-${contactId}-${Date.now()}`,
        transport: "chat",
        title: contactName,
        preview: "Started from contact drag",
        peer: contactName,
        unread: 0,
        updatedAt: new Date().toISOString(),
        isPinned: false,
        isMuted: false,
      };
      setActiveThread(newThread);
      setContactDrops((prev) => [
        { id: contactId, name: contactName, timestamp: Date.now() },
        ...prev.slice(0, 9), // keep last 10
      ]);
      // Ping the rail to show the new contact thread
      window.dispatchEvent(new CustomEvent("comm-contact-drop", { detail: { name: contactName } }));
    },
    [setActiveThread]
  );

  if (!activeThread) {
    const canDropContact = dragPayload?.type === "contact";

    return (
      <DropZone
        zone="stage"
        onDrop={(payload) => {
          if (payload.type === "contact") {
            handleContactDrop(payload.contactName, payload.contactId);
          }
        }}
      >
        <div
          className={`flex flex-col items-center justify-center h-full text-center p-8 transition-all duration-200 ${
            canDropContact
              ? "bg-primary/5 ring-2 ring-dashed ring-primary/40 rounded-2xl m-4"
              : ""
          }`}
        >
          <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
            <MessageCircle className="w-8 h-8 text-primary" />
          </div>
          <h2 className="text-lg font-bold text-text mb-1">Communication Hub</h2>
          <p className="text-sm text-text-muted max-w-sm">
            {canDropContact
              ? `Drop ${dragPayload!.contactName} here to start a conversation`
              : "Select a conversation from the left or start a new one to begin working"}
          </p>

          {/* Recently dropped contacts */}
          {contactDrops.length > 0 && !canDropContact && (
            <div className="mt-6 space-y-1.5">
              <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wider">
                Recent drops
              </p>
              {contactDrops.slice(0, 3).map((d) => (
                <div
                  key={`${d.id}-${d.timestamp}`}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-2/50 text-xs text-text-muted"
                >
                  <UserPlus className="w-3 h-3 text-primary" />
                  Started conversation with {d.name}
                </div>
              ))}
            </div>
          )}
        </div>
      </DropZone>
    );
  }

  const senderId = user?.id;
  let threadId: number | undefined;
  if (activeThread?.id) {
    // activeThread.id could be a string like "contact-xxx-xxx" or a numeric string
    const parsed = parseInt(activeThread.id, 10);
    if (!Number.isNaN(parsed)) threadId = parsed;
  }

  const transport = activeThread.transport;

  return (
    <div className="flex flex-col h-full" key={densityKey}>
      <ThreadHeader thread={activeThread} />

      {/* Transport renderer with loading/error states */}
      <AnimatePresence mode="wait">
        <motion.div
          key={`${transport}-${activeThread.id}`}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 4 }}
          transition={{ duration: 0.15, ease: "easeOut" }}
          className="flex-1 flex flex-col min-h-0"
        >
          {/* Loading skeleton — shown while messages are being fetched */}
          {messagesLoading && threadMessages.length === 0 && (
            <SkeletonShimmer />
          )}

          {/* Error state — shown when message fetch fails */}
          {messagesError && !messagesLoading && threadMessages.length === 0 && (
            <div className="flex flex-col items-center justify-center flex-1 text-center p-8">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-danger/10 mb-3">
                <svg className="w-5 h-5 text-danger" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-sm font-semibold text-text mb-1">Failed to load messages</p>
              <p className="text-xs text-text-faint mb-3 max-w-[200px]">Could not fetch messages for this conversation.</p>
              <button
                onClick={() => {
                  window.dispatchEvent(new CustomEvent("comm-refetch"));
                  document.querySelector(".comm-shell")?.classList.remove("comm-messages-error");
                }}
                className="theme-btn-primary rounded-lg px-3 py-1.5 text-[11px] font-semibold"
              >
                Retry
              </button>
            </div>
          )}

          {/* Actual transport renderer */}
          {!((messagesLoading && threadMessages.length === 0) || (messagesError && threadMessages.length === 0)) && (
            <Suspense fallback={<SkeletonShimmer />}>
              {renderTransport(transport, threadMessages, threadId, typingUserNames)}
            </Suspense>
          )}
        </motion.div>
      </AnimatePresence>

      {/* Universal composer dock — hide for non-input transports */}
      {transport !== "contact" && transport !== "b2b_masked" && transport !== "incident" && transport !== "video" && (
        <ComposerDock
          sendAs={sendAs}
          setSendAs={setSendAs}
          threadId={threadId}
          senderId={senderId}
          onTypingChange={sendTyping}
        />
      )}
    </div>
  );
}
