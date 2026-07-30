"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { apiFetch, parseJsonResponse, getAccessToken } from "@/lib/api";
import type { ThreadSummary, Transport } from "@/components/comms/CommShell";

interface UnifiedInboxResult {
  items: ThreadSummary[];
  nextCursor: string | null;
  hasMore: boolean;
}

interface UseUnifiedInboxOptions {
  lens?: string;
  transport?: Transport | null;
  limit?: number;
}

export function useUnifiedInbox(opts: UseUnifiedInboxOptions = {}) {
  const { lens = "all", transport = null, limit = 50 } = opts;
  const [items, setItems] = useState<ThreadSummary[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const loadingRef = useRef(false);

  const fetchInbox = useCallback(async (cursorVal?: string | null) => {
    if (loadingRef.current) return;
    loadingRef.current = true;
    setLoading(true);

    try {
      const params = new URLSearchParams({ lens, limit: String(limit) });
      if (transport) params.set("transport", transport);
      if (cursorVal) params.set("cursor", cursorVal);

      const res = await apiFetch(`/comms/unified-inbox?${params}`);
      const data: UnifiedInboxResult = await parseJsonResponse(res);

      if (cursorVal) {
        setItems((prev) => [...prev, ...data.items]);
      } else {
        setItems(data.items);
      }
      setCursor(data.nextCursor);
      setHasMore(data.hasMore);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load inbox");
    } finally {
      setLoading(false);
      loadingRef.current = false;
    }
  }, [lens, transport, limit]);

  const loadMore = useCallback(() => {
    if (cursor && hasMore && !loadingRef.current) {
      fetchInbox(cursor);
    }
  }, [cursor, hasMore, fetchInbox]);

  // Initial fetch
  useEffect(() => {
    fetchInbox(null);
  }, [fetchInbox]);

  // WebSocket patch for real-time deltas — connect to both the
  // app-level communications channel AND the backend user notification
  // channel so email.received / new_message / message_read events all
  // trigger an inbox refresh.
  useEffect(() => {
    const sockets: WebSocket[] = [];

    // 1) Backend user notification channel (port 8000) — receives
    //    email.received events broadcast by realtime.py
    const token = getAccessToken();
    if (token) {
      const wsBase =
        window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
          ? "ws://127.0.0.1:8000"
          : `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.hostname}:8000`;

      try {
        const wsUser = new WebSocket(`${wsBase}/ws-chat/ws/user?token=${encodeURIComponent(token)}`);
        wsUser.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            // email.received — new internal email arrived
            // notification.created — a system notification
            // ticket.* — support ticket updates
            if (
              data.type === "email.received" ||
              data.type === "notification.created" ||
              data.type === "new_message"
            ) {
              fetchInbox(null);
            }
          } catch {}
        };
        sockets.push(wsUser);
      } catch {}
    }

    return () => {
      for (const ws of sockets) {
        ws.close();
      }
    };
  }, [fetchInbox]);

  const refetch = useCallback(() => fetchInbox(null), [fetchInbox]);

  return { items, loading, error, hasMore, loadMore, refetch, cursor };
}
