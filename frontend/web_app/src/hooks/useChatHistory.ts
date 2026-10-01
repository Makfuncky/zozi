"use client";

import { useState, useCallback, useRef } from "react";
import { apiFetch, parseJsonResponse } from "@/lib/api";

// ── Types ────────────────────────────────────────────────────────────────

export interface ChatHistoryMessage {
  id: number;
  sender_id: number;
  sender_name: string;
  body: string;
  created_at: string;
}

interface ChatHistoryResponse {
  messages: ChatHistoryMessage[];
  has_more: boolean;
  next_cursor: number | null;
}

interface UseChatHistoryReturn {
  /** The accumulated list of older messages (most recent first). */
  olderMessages: ChatHistoryMessage[];
  /** True while a fetch is in-flight. */
  loading: boolean;
  /** True if there are more messages to load (cursor exists). */
  hasMore: boolean;
  /** Fetch the next page of older messages. */
  loadMore: () => Promise<void>;
  /** Reset pagination state (call when thread changes). */
  reset: () => void;
}

// ── Hook ─────────────────────────────────────────────────────────────────

/**
 * Cursor-based pagination hook for chat thread history.
 * Fetches older messages from GET /chat/threads/{id}/messages?cursor=...
 * and accumulates them so ChatStream can prepend them.
 */
export function useChatHistory(threadId: number | undefined): UseChatHistoryReturn {
  const [olderMessages, setOlderMessages] = useState<ChatHistoryMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(false);

  // The cursor for the next page: the oldest message ID we've loaded.
  const cursorRef = useRef<number | null>(null);
  // Track the current thread so we reset on change.
  const threadRef = useRef(threadId);
  const loadingRef = useRef(false);

  // Reset when thread changes
  if (threadRef.current !== threadId) {
    threadRef.current = threadId;
    setOlderMessages([]);
    setHasMore(false);
    cursorRef.current = null;
  }

  const loadMore = useCallback(async () => {
    if (threadId == null || loadingRef.current) return;
    loadingRef.current = true;
    setLoading(true);

    try {
      const params = new URLSearchParams({ limit: "50" });
      if (cursorRef.current != null) {
        params.set("cursor", String(cursorRef.current));
      }

      const res = await apiFetch(
        `/chat/threads/${threadId}/messages?${params.toString()}`,
      );

      if (!res.ok) {
        throw new Error(`Server error ${res.status}`);
      }

      const data: ChatHistoryResponse & { messages?: ChatHistoryMessage[] } =
        await parseJsonResponse(res);

      const fetched = data?.messages ?? [];
      const more = data?.has_more ?? false;
      const nextCursor = data?.next_cursor ?? null;

      if (fetched.length > 0) {
        cursorRef.current = fetched[0].id; // oldest in this batch
        setOlderMessages((prev) => [...prev, ...fetched]);
      } else {
        cursorRef.current = null;
      }
      setHasMore(more && fetched.length > 0);
    } catch {
      // Silently fail — the button will still be clickable to retry.
    } finally {
      loadingRef.current = false;
      setLoading(false);
    }
  }, [threadId]);

  const reset = useCallback(() => {
    setOlderMessages([]);
    setHasMore(false);
    cursorRef.current = null;
  }, []);

  return { olderMessages, loading, hasMore, loadMore, reset };
}
