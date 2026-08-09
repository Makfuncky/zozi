"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import type { Message, Transport } from "@/components/comms/CommShell";

interface ThreadMessagesResult {
  messages: Message[];
  total?: number;
}

/**
 * Fetches messages for a given thread from the backend.
 * Handles different transport types with appropriate endpoints.
 */
async function fetchMessagesForThread(
  threadId: string,
  transport: Transport,
  limit: number,
  cursor?: string,
): Promise<ThreadMessagesResult> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (cursor) params.set("cursor", cursor);

  let endpoint = `/chat/threads/${threadId}/messages`;
  if (transport === "email") {
    endpoint = `/internal-emails?thread_id=${threadId}`;
  }

  const res = await apiFetch(`${endpoint}?${params}`);
  return parseJsonResponse(res);
}

interface UseThreadMessagesOptions {
  limit?: number;
}

export function useThreadMessages(opts: UseThreadMessagesOptions = {}) {
  const { limit = 50 } = opts;
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [activeTransport, setActiveTransport] = useState<Transport>("chat");
  const loadingRef = useRef(false);

  const loadMessages = useCallback(async (
    threadId: string,
    transport: Transport,
  ) => {
    if (loadingRef.current) return;
    loadingRef.current = true;
    setLoading(true);
    setError(null);
    setActiveThreadId(threadId);
    setActiveTransport(transport);

    try {
      const data = await fetchMessagesForThread(threadId, transport, limit);
      setMessages(data.messages ?? []);
    } catch (e) {
      const errMsg = e instanceof Error ? e.message : "Failed to load messages";
      setError(errMsg);
      setMessages([]);
    } finally {
      setLoading(false);
      loadingRef.current = false;
    }
  }, [limit]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setActiveThreadId(null);
    setError(null);
  }, []);

  return {
    messages,
    loading,
    error,
    activeThreadId,
    activeTransport,
    loadMessages,
    clearMessages,
  };
}
