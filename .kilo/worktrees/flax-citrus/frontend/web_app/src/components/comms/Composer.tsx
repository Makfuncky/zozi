"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import {
  Paperclip,
  Mic,
  Smile,
  AtSign,
  Hash,
  Send,
  X,
  ImageIcon,
  ChevronDown,
  Clock,
  CheckCheck,
  AlertCircle,
} from "@/lib/icons";
import { useSendMessage } from "@/hooks/useSendMessage";
import { useComm } from "./CommShell";

interface ComposerDockProps {
  sendAs: "chat" | "email";
  setSendAs: (v: "chat" | "email") => void;
  threadId?: number;
  senderId?: number;
  onTypingChange?: (isTyping: boolean) => void;
}

export default function ComposerDock({ sendAs, setSendAs, threadId, senderId, onTypingChange }: ComposerDockProps) {
  const [message, setMessage] = useState("");
  const [attachments, setAttachments] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [sendState, setSendState] = useState<"idle" | "sending" | "sent" | "failed">("idle");
  const [toast, setToast] = useState<string | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { setMessages, messages, replyToEmail, setReplyToEmail } = useComm();
  const messagesRef = useRef(messages);
  messagesRef.current = messages;
  const { sendMessage, sendInternalEmail } = useSendMessage();
  const { activeThread } = useComm();

  // Auto-dismiss toast after 3s
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 3000);
    return () => clearTimeout(t);
  }, [toast]);

  // ── Typing indicator debounce ─────────────────────────────────
  const typingDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isTypingRef = useRef(false);

  const handleTypingChange = useCallback(
    (text: string) => {
      if (!threadId || !onTypingChange) return;

      if (text.trim().length > 0) {
        // First keystroke after idle — send typing=true immediately
        if (!isTypingRef.current) {
          isTypingRef.current = true;
          onTypingChange(true);
        }

        // Reset the debounce timer
        if (typingDebounceRef.current) {
          clearTimeout(typingDebounceRef.current);
        }
        typingDebounceRef.current = setTimeout(() => {
          isTypingRef.current = false;
          onTypingChange(false);
        }, 2000);
      } else {
        // Empty input — stop typing immediately
        if (isTypingRef.current) {
          isTypingRef.current = false;
          onTypingChange(false);
        }
        if (typingDebounceRef.current) {
          clearTimeout(typingDebounceRef.current);
          typingDebounceRef.current = null;
        }
      }
    },
    [threadId, onTypingChange],
  );

  // Cleanup typing state on unmount or thread change
  useEffect(() => {
    return () => {
      if (typingDebounceRef.current) {
        clearTimeout(typingDebounceRef.current);
      }
      if (isTypingRef.current && onTypingChange) {
        onTypingChange(false);
      }
      isTypingRef.current = false;
    };
  }, [threadId, onTypingChange]);

  // Email fields (collapsible)
  const [showEmailFields, setShowEmailFields] = useState(false);
  const [to, setTo] = useState("");
  const [cc, setCc] = useState("");
  const [subject, setSubject] = useState("");

  // ── Reply-to-email: pre-populate fields when replying ─────────────
  const toInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (replyToEmail) {
      setSendAs("email");
      setShowEmailFields(true);
      setCc(replyToEmail.cc.join(", "));
      setSubject(
        replyToEmail.subject.startsWith("Re:")
          ? replyToEmail.subject
          : `Re: ${replyToEmail.subject}`
      );
      setMessage("");
      // Focus the To: input so the user can type the recipient
      setTimeout(() => toInputRef.current?.focus(), 100);
    }
  }, [replyToEmail, setSendAs]);

  const handleSend = useCallback(async () => {
    if ((!message.trim() && attachments.length === 0) || !senderId) return;

    setSendState("sending");
    const text = message.trim();

    if (sendAs === "email") {
      // ── Email mode: send via internal-email endpoint ──
      const toEmails = to.split(/[,;\s]+/).filter(Boolean);
      const ccEmails = cc.split(/[,;\s]+/).filter(Boolean);

      if (!toEmails.length) {
        setSendState("failed");
        setToast("At least one recipient is required");
        setTimeout(() => setSendState("idle"), 3000);
        return;
      }

      const inReplyToId = replyToEmail?.messageId || undefined;
      const result = await sendInternalEmail(toEmails, subject, text, ccEmails.length > 0 ? ccEmails : undefined, inReplyToId);

      if (result) {
        setSendState("sent");
        // Add a local email to the message list so it shows in the stream
        const emailMsg = {
          id: `email_${result.email_id}`,
          threadId: result.thread_id,
          senderId: String(senderId),
          senderName: "You",
          body: `📧 ${result.subject}\nTo: ${result.to.join(", ")}\n\n${text}`,
          createdAt: result.sent_at,
          transport: "email" as const,
        };
        const currentMessages = messagesRef.current;
        setMessages([...currentMessages, emailMsg as any]);
        setMessage("");
        setSubject("");
        setTo("");
        setCc("");
        setReplyToEmail(null);
        setTimeout(() => setSendState("idle"), 1500);
      } else {
        setSendState("failed");
        setToast("Failed to send email — check your connection");
        setTimeout(() => setSendState("idle"), 3000);
      }

      setAttachments([]);
      return;
    }

    // ── Chat mode: send via chat endpoint ──
    if (!threadId) return;
    const currentMessages = messagesRef.current;

    // Optimistically add a local message so the UI feels instant
    const optimisticId = `temp_${Date.now()}`;
    const optimisticMessage = {
      id: optimisticId,
      threadId: String(threadId),
      senderId: String(senderId),
      senderName: "You",
      body: text,
      createdAt: new Date().toISOString(),
      transport: activeThread?.transport || "chat" as const,
    };
    setMessages([...currentMessages, optimisticMessage as any]);
    setMessage("");

    // Send to backend (with files if any)
    const result = await sendMessage(threadId, senderId, text, attachments.length > 0 ? attachments : undefined);

    if (result) {
      setSendState("sent");
      // Replace optimistic message id with server id via fresh ref
      const latest = messagesRef.current;
      setMessages(
        latest.map((m: any) =>
          m.id === optimisticId
            ? { ...m, id: String(result.id), createdAt: result.created_at }
            : m
        )
      );
      setTimeout(() => setSendState("idle"), 1500);
    } else {
      // Remove optimistic message on failure
      setMessages(messagesRef.current.filter((m: any) => m.id !== optimisticId));
      setSendState("failed");
      setToast("Failed to send — check your connection");
      setTimeout(() => setSendState("idle"), 3000);
    }

    setAttachments([]);
  }, [message, attachments, threadId, senderId, sendAs, to, cc, subject, sendMessage, sendInternalEmail, setMessages, activeThread]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;
    setAttachments((prev) => [...prev, ...Array.from(files)]);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }, []);

  // Drag-drop
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);
  const handleDragLeave = useCallback(() => setIsDragging(false), []);
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    setAttachments((prev) => [...prev, ...Array.from(e.dataTransfer.files)]);
  }, []);

  return (
    <div className="border-t border-border bg-surface/95 backdrop-blur-sm shrink-0">
      {/* Error toast banner */}
      {toast && (
        <div className="flex items-center gap-2 px-3 py-1.5 bg-danger/10 border-b border-danger/20">
          <AlertCircle className="w-3.5 h-3.5 text-danger shrink-0" />
          <span className="text-[11px] text-danger font-medium flex-1">{toast}</span>
          <button
            onClick={() => setToast(null)}
            className="p-0.5 rounded hover:bg-danger/10 text-danger/60 hover:text-danger transition-colors"
          >
            <X className="w-3 h-3" />
          </button>
        </div>
      )}

      {/* Email fields (collapsible) */}
      {(sendAs === "email" || showEmailFields) && (
        <div className="px-3 pt-2 pb-1 space-y-1.5 border-b border-border">
          <div className="flex items-center gap-2 text-[11px]">
            <span className="font-medium text-text-muted w-6">To:</span>
            <input
              ref={toInputRef}
              value={to}
              onChange={(e) => setTo(e.target.value)}
              placeholder={replyToEmail ? "Enter recipient email…" : "recipient@example.com"}
              className="flex-1 bg-transparent border-0 outline-none text-text placeholder:text-text-faint"
            />
          </div>
          <div className="flex items-center gap-2 text-[11px]">
            <span className="font-medium text-text-muted w-6">Cc:</span>
            <input
              value={cc}
              onChange={(e) => setCc(e.target.value)}
              placeholder="cc (optional)"
              className="flex-1 bg-transparent border-0 outline-none text-text placeholder:text-text-faint"
            />
          </div>
          <div className="flex items-center gap-2 text-[11px]">
            <span className="font-medium text-text-muted w-6">Sub:</span>
            <input
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Subject"
              className="flex-1 bg-transparent border-0 outline-none text-text placeholder:text-text-faint"
            />
          </div>
        </div>
      )}

      {/* Attachment chips */}
      {attachments.length > 0 && (
        <div className="flex flex-wrap gap-1.5 px-3 pt-2">
          {attachments.map((att, i) => (
            <div
              key={i}
              className="flex items-center gap-1.5 rounded-lg bg-surface-2 px-2.5 py-1 text-[10px] text-text-muted"
            >
              <ImageIcon className="w-3 h-3" />
              <span className="truncate max-w-[120px]">{att.name}</span>
              <button
                onClick={() => setAttachments((prev) => prev.filter((_, j) => j !== i))}
                className="ml-0.5 p-0.5 rounded hover:bg-surface-3 text-text-faint hover:text-text"
              >
                <X className="w-2.5 h-2.5" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Composer input row */}
      <div
        className={`composer-box flex items-end gap-2 px-3 py-2 ${isDragging ? "bg-primary/5" : ""}`}
        data-dragover={isDragging}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {/* Left: attach buttons */}
        <div className="flex items-center gap-0.5 pb-1.5">
          <button
            onClick={() => fileInputRef.current?.click()}
            className="p-1.5 rounded-lg hover:bg-surface-2 text-text-muted hover:text-text transition-colors"
            title="Attach file"
          >
            <Paperclip className="w-4 h-4" />
          </button>
          <button className="p-1.5 rounded-lg hover:bg-surface-2 text-text-muted hover:text-text transition-colors" title="Voice note">
            <Mic className="w-4 h-4" />
          </button>
          <button className="p-1.5 rounded-lg hover:bg-surface-2 text-text-muted hover:text-text transition-colors" title="Emoji">
            <Smile className="w-4 h-4" />
          </button>
          <button className="p-1.5 rounded-lg hover:bg-surface-2 text-text-muted hover:text-text transition-colors" title="Mention">
            <AtSign className="w-4 h-4" />
          </button>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={handleFileSelect}
          />
        </div>

        {/* Textarea */}          <textarea
          ref={inputRef}
          value={message}
          onChange={(e) => {
            setMessage(e.target.value);
            handleTypingChange(e.target.value);
          }}
          onKeyDown={handleKeyDown}
          placeholder={sendAs === "email" ? "Write an email…" : "Type a message…"}
          rows={1}
          className="composer-textarea flex-1 resize-none bg-transparent border-0 outline-none text-[13px] text-text placeholder:text-text-faint leading-relaxed py-1.5 max-h-[40vh]"
        />

        {/* Right: send-as toggle + send button */}
        <div className="flex items-center gap-1 pb-1.5">
          {/* Send-as mode */}
          <div className="flex items-center rounded-lg border border-border overflow-hidden text-[10px]">
            <button
              onClick={() => setSendAs("chat")}
              data-active={sendAs === "chat"}
              className={`px-2 py-1 font-semibold transition-colors ${
                sendAs === "chat"
                  ? "bg-primary text-white"
                  : "text-text-muted hover:text-text hover:bg-surface-2"
              }`}
            >
              Chat
            </button>
            <button
              onClick={() => { setSendAs("email"); setShowEmailFields(true); }}
              data-active={sendAs === "email"}
              className={`px-2 py-1 font-semibold transition-colors ${
                sendAs === "email"
                  ? "bg-primary text-white"
                  : "text-text-muted hover:text-text hover:bg-surface-2"
              }`}
            >
              Email
            </button>
          </div>

          {/* Send button with lifecycle */}
          <button
            onClick={handleSend}
            disabled={(!message.trim() && attachments.length === 0) || sendState === "sending" || (sendAs === "chat" && !threadId) || !senderId}
            className="p-1.5 rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed relative"
            title="Send (Enter)"
          >
            {sendState === "sending" ? (
              <Clock className="w-4 h-4 tick-clock" />
            ) : sendState === "sent" ? (
              <CheckCheck className="w-4 h-4 tick-read" />
            ) : sendState === "failed" ? (
              <X className="w-4 h-4" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
