"use client";

import { useState, useCallback } from "react";
import { apiFetch, parseJsonResponse } from "@/lib/api";

/** Server response from POST /chat/threads/{id}/messages or /chat/message */
export interface ChatAttachmentData {
  id: number;
  type: string;
  file_name: string;
  file_size: number;
  file_url: string;
  mime_type: string;
}

export interface ChatMessageResponse {
  id: number;
  chat_id: string;
  sender_id: number;
  content: string;
  message_type: string;
  created_at: string;
  attachments?: ChatAttachmentData[];
}

/** Server response from POST /email-gateway/internal-by-email */
export interface InternalEmailResponse {
  email_id: number;
  thread_id: string;
  to: number[];
  subject: string;
  body: string;
  sender_id: number;
  sent_at: string;
  status: string;
  delivered_count: number;
  total_count: number;
}

interface UseSendMessageReturn {
  /** Send a message to a thread */
  sendMessage: (threadId: number, senderId: number, text: string, files?: File[]) => Promise<ChatMessageResponse | null>;
  /** Send a direct-message to a chat_id (e.g. "dm_abc123") */
  sendDirectMessage: (chatId: string, senderId: number, text: string, messageType?: string) => Promise<ChatMessageResponse | null>;
  /** Send an internal email to one or more recipients by email address */
  sendInternalEmail: (to: string[], subject: string, body: string, cc?: string[], in_reply_to?: number) => Promise<InternalEmailResponse | null>;
  /** True while a send is in-flight */
  sending: boolean;
  /** Last error message, or null */
  error: string | null;
  /** Clear error state */
  clearError: () => void;
}

/** Build a FormData payload for file + text uploads. */
async function _buildFormData(senderId: number, text: string, files: File[]): Promise<FormData> {
  const fd = new FormData();
  fd.append("sender_id", String(senderId));
  fd.append("message", text || `${files.length} file(s)`);
  for (const f of files) {
    fd.append("files", f);
  }
  return fd;
}

/**
 * Hook for sending chat messages to the backend.
 * Used by ComposerDock to persist messages to the database.
 */
export function useSendMessage(): UseSendMessageReturn {
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (threadId: number, senderId: number, text: string, files?: File[]): Promise<ChatMessageResponse | null> => {
      if (!text.trim() && (!files || files.length === 0)) return null;
      setSending(true);
      setError(null);

      try {
        const hasFiles = files && files.length > 0;
        const body = hasFiles
          ? await _buildFormData(senderId, text, files)
          : JSON.stringify({ sender_id: senderId, message: text });

        const headers: Record<string, string> = {};
        if (!hasFiles) {
          headers["Content-Type"] = "application/json";
        }
        // When files are present, Content-Type is set to multipart/form-data
        // automatically by the browser; we must NOT set it explicitly so
        // the boundary string is included.

        const endpoint = hasFiles
          ? `/chat/threads/${threadId}/messages/upload`
          : `/chat/threads/${threadId}/messages`;

        try {
          const res = await apiFetch(endpoint, {
            method: "POST",
            headers,
            body,
          });

          if (!res.ok) {
            let detail = `Server error ${res.status}`;
            try {
              const errData = await parseJsonResponse(res);
              detail = errData?.detail || errData?.message || detail;
            } catch { /* ignore parse failure */ }
            throw new Error(detail);
          }

          const data = await parseJsonResponse(res);
          setSending(false);
          return data as ChatMessageResponse;
        } catch (err) {
          // If files endpoint 404s (old server), fall back to JSON without files
          if (hasFiles && err instanceof Error && err.message.includes("404")) {
            // Fall through to JSON-only send
            const res = await apiFetch(`/chat/threads/${threadId}/messages`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ sender_id: senderId, message: text }),
            });

            if (!res.ok) {
              const errData = await parseJsonResponse(res);
              const detail = errData?.detail || errData?.message || `Server error ${res.status}`;
              setError(detail);
              setSending(false);
              return null;
            }

            const data = await parseJsonResponse(res);
            setSending(false);
            return data as ChatMessageResponse;
          }

          const msg = err instanceof Error ? err.message : "Failed to send media message";
          setError(msg);
          setSending(false);
          return null;
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Failed to send message";
        setError(msg);
        setSending(false);
        return null;
      }
    },
    []
  );

  const sendDirectMessage = useCallback(
    async (chatId: string, senderId: number, text: string, messageType = "text"): Promise<ChatMessageResponse | null> => {
      if (!text.trim()) return null;
      setSending(true);
      setError(null);

      try {
        const res = await apiFetch("/chat/message", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            chat_id: chatId,
            sender_id: senderId,
            content: text,
            message_type: messageType,
          }),
        });

        if (!res.ok) {
          const errData = await parseJsonResponse(res);
          const detail = errData?.detail || errData?.message || `Server error ${res.status}`;
          throw new Error(detail);
        }

        const data = await parseJsonResponse(res);
        setSending(false);
        return data as ChatMessageResponse;
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Failed to send message";
        setError(msg);
        setSending(false);
        return null;
      }
    },
    []
  );

  const sendInternalEmail = useCallback(
    async (to: string[], subject: string, body: string, cc?: string[], in_reply_to?: number): Promise<InternalEmailResponse | null> => {
      if (!to.length || !body.trim()) return null;
      setSending(true);
      setError(null);

      try {
        const res = await apiFetch("/email-gateway/internal-by-email", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            to,
            subject,
            body,
            cc: cc && cc.length > 0 ? cc : undefined,
            in_reply_to,
          }),
        });

        if (!res.ok) {
          const errData = await parseJsonResponse(res);
          const detail = errData?.detail || errData?.message || `Server error ${res.status}`;
          throw new Error(detail);
        }

        const data = await parseJsonResponse(res);
        setSending(false);
        return data as InternalEmailResponse;
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Failed to send internal email";
        setError(msg);
        setSending(false);
        return null;
      }
    },
    []
  );

  const clearError = useCallback(() => setError(null), []);

  return { sendMessage, sendDirectMessage, sendInternalEmail, sending, error, clearError };
}
