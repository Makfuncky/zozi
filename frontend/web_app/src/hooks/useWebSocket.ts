"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import { getAccessToken } from "@/lib/api";
import { useComm, type WsStatus } from "@/components/comms/CommShell";

// ── Config ──────────────────────────────────────────────────────────────

const WS_BASE =
  typeof window !== "undefined" &&
  (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
    ? "ws://127.0.0.1:8000"
    : `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.hostname}:8000`;

const PING_INTERVAL_MS = 25_000;
const RECONNECT_BASE_MS = 1_000;
const RECONNECT_MAX_MS = 30_000;
const MAX_RECONNECT_ATTEMPTS = 10;
const TYPING_HIDE_MS = 3_000;

// ── Hook ────────────────────────────────────────────────────────────────

/**
 * Subscribe to real-time messages for a chat room via WebSocket.
 * Automatically reconnects on drop and dispatches incoming `message`
 * events into the CommShell context so the ChatStream updates live.
 *
 * @param threadId - The room/thread ID to subscribe to (null to disconnect).
 * @param currentUserId - The current user's ID (used to suppress echo of own messages).
 */
export function useWebSocket(threadId: string | null, currentUserId?: number | string) {
  const { setMessages, setWsStatus } = useComm();

  // ── Typing state ──────────────────────────────────────────────
  const [typingUserNames, setTypingUserNames] = useState<string[]>([]);
  const typingTimersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  // ── Refs to avoid stale closures ───────────────────────────────
  const threadIdRef = useRef(threadId);
  threadIdRef.current = threadId;

  const currentUserIdRef = useRef(currentUserId);
  currentUserIdRef.current = currentUserId;

  const wsRef = useRef<WebSocket | null>(null);
  const pingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectAttempt = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const enabled = !!threadId;

  /** Build the WebSocket URL for a given room. */
  const buildUrl = useCallback((roomId: string): string | null => {
    const token = getAccessToken();
    if (!token) return null;
    return `${WS_BASE}/ws-chat/ws/chat/${roomId}?token=${encodeURIComponent(token)}`;
  }, []);

  /** Stop the ping keepalive interval. */
  const stopPing = useCallback(() => {
    if (pingRef.current) {
      clearInterval(pingRef.current);
      pingRef.current = null;
    }
  }, []);

  /** Clean up all resources. */
  const cleanup = useCallback(() => {
    stopPing();
    // Clear all typing timers
    for (const timer of typingTimersRef.current.values()) {
      clearTimeout(timer);
    }
    typingTimersRef.current.clear();
    setTypingUserNames([]);
    // Clear reconnect timer
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
    if (wsRef.current) {
      // Prevent reconnect handler from firing after intentional close
      wsRef.current.onclose = null;
      wsRef.current.onmessage = null;
      wsRef.current.onerror = null;
      wsRef.current.close();
      wsRef.current = null;
    }
    reconnectAttempt.current = 0;
    setWsStatus("disconnected");
  }, [stopPing, setWsStatus]);

  /**
   * Handle incoming typing events with debounced hide.
   * When a remote user types, show their name immediately.
   * If no new typing event arrives within TYPING_HIDE_MS, remove them.
   */
  const handleTypingEvent = useCallback((data: Record<string, unknown>) => {
    const names = data.typing_user_names as string[] | undefined;
    if (!names) return;

    // Use the full list from the server (it already excludes the sender)
    setTypingUserNames(names);

    // Set a backup timer for each name that clears after TYPING_HIDE_MS
    // — this guards against missed "is_typing: false" events
    for (const timer of typingTimersRef.current.values()) {
      clearTimeout(timer);
    }
    typingTimersRef.current.clear();

    if (names.length > 0) {
      const timer = setTimeout(() => {
        setTypingUserNames([]);
        typingTimersRef.current.clear();
      }, TYPING_HIDE_MS);
      typingTimersRef.current.set("_global_hide", timer);
    }
  }, []);

  /** Send a typing indicator over the WebSocket. */
  const sendTyping = useCallback((isTyping: boolean) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "typing", is_typing: isTyping }));
    }
  }, []);

  /** Send a read receipt to mark all unread messages as read. */
  const sendReadReceipt = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "read_receipt" }));
    }
  }, []);

  /** Open the WebSocket connection. */
  const connect = useCallback(() => {
    const roomId = threadIdRef.current;
    if (!roomId) return;

    const url = buildUrl(roomId);
    if (!url) return;

    // Close any existing socket
    wsRef.current?.close();
    wsRef.current = null;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        reconnectAttempt.current = 0;
        setTypingUserNames([]);
        setWsStatus("connected");
        // Start ping keepalive
        pingRef.current = setInterval(() => {
          try { ws.send(JSON.stringify({ type: "ping" })); } catch { /* ignore */ }
        }, PING_INTERVAL_MS);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          switch (data.type) {
            case "message": {
              const isOwn =
                currentUserIdRef.current != null &&
                data.sender_id != null &&
                String(data.sender_id) === String(currentUserIdRef.current);

              if (!isOwn) {
                const newMsg = {
                  id: String(data.message_id ?? `ws_${Date.now()}`),
                  threadId: String(data.room_id ?? roomId ?? ""),
                  senderId: String(data.sender_id ?? ""),
                  senderName: String(data.sender_name ?? "Unknown"),
                  body: String(data.content ?? ""),
                  createdAt: String(data.created_at ?? new Date().toISOString()),
                  transport: "chat" as const,
                };
                setMessages((prev) => [...prev, newMsg]);
              }
              break;
            }

            case "typing":
              handleTypingEvent(data);
              break;

            case "read_receipt":
              // Another user read messages in this room.
              // The count tells us how many messages were marked read.
              // This could be used to update the readBy field on sent messages
              // to show the blue double-check indicator.
              break;

            case "presence":
            case "user_joined":
            case "user_left":
              // Presence events — handled by the inbox polling
              break;
          }
        } catch {
          /* ignore malformed messages */
        }
      };

      ws.onclose = () => {
        stopPing();
        // Schedule reconnect if this wasn't an intentional close
        if (reconnectAttempt.current < MAX_RECONNECT_ATTEMPTS) {
          setWsStatus("reconnecting");
          const delay = Math.min(
            RECONNECT_BASE_MS * 2 ** reconnectAttempt.current,
            RECONNECT_MAX_MS,
          );
          reconnectAttempt.current += 1;
          reconnectTimer.current = setTimeout(connect, delay);
        } else {
          setWsStatus("disconnected");
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      // Connection failed — schedule reconnect
      setWsStatus("reconnecting");
      if (reconnectAttempt.current < MAX_RECONNECT_ATTEMPTS) {
        const delay = Math.min(
          RECONNECT_BASE_MS * 2 ** reconnectAttempt.current,
          RECONNECT_MAX_MS,
        );
        reconnectAttempt.current += 1;
        reconnectTimer.current = setTimeout(connect, delay);
      } else {
        setWsStatus("disconnected");
      }
    }
  }, [buildUrl, stopPing, handleTypingEvent]);

  // ── Effect ────────────────────────────────────────────────────
  useEffect(() => {
    if (!enabled) {
      cleanup();
      return;
    }

    connect();

    return () => {
      cleanup();
    };
  }, [enabled, connect, cleanup]);

  // ── Return ────────────────────────────────────────────────────
  return {
    reconnect: connect,
    typingUserNames,
    sendTyping,
    sendReadReceipt,
  };
}
