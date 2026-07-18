"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { API_URL } from "@/lib/api";

export interface WsChatMessage {
  type: "message";
  room_id: string;
  sender_id: number;
  sender_name: string;
  content: string;
  message_type: string;
  message_id: number;
  created_at: string;
}

export interface WsTypingEvent {
  type: "typing";
  room_id: string;
  user_id: number;
  user_name: string;
  is_typing: boolean;
  typing_user_ids: number[];
  typing_user_names: string[];
}

export interface WsPresenceEvent {
  type: "presence";
  room_id: string;
  user_id: number;
  user_name: string;
  status: "online" | "away" | "busy" | "offline";
  users: WsRoomUser[];
}

export interface WsReadReceiptEvent {
  type: "read_receipt";
  room_id: string;
  user_id: number;
  user_name: string;
  count: number;
}

export interface WsUserJoinedEvent {
  type: "user_joined";
  room_id: string;
  user_id: number;
  user_name: string;
  users: WsRoomUser[];
}

export interface WsUserLeftEvent {
  type: "user_left";
  room_id: string;
  user_id: number;
  user_name: string;
  users: WsRoomUser[];
}

export interface WsRoomUser {
  user_id: number;
  name: string;
  status: "online" | "away" | "busy" | "offline";
  last_seen?: string;
}

export type WsEvent =
  | WsChatMessage
  | WsTypingEvent
  | WsPresenceEvent
  | WsReadReceiptEvent
  | WsUserJoinedEvent
  | WsUserLeftEvent;

interface UseChatWebSocketOptions {
  roomId: string | null;
  token: string | null;
  userId: number | null;
  onMessage?: (msg: WsChatMessage) => void;
  onTyping?: (evt: WsTypingEvent) => void;
  onPresence?: (evt: WsPresenceEvent) => void;
  onReadReceipt?: (evt: WsReadReceiptEvent) => void;
  onUserJoined?: (evt: WsUserJoinedEvent) => void;
  onUserLeft?: (evt: WsUserLeftEvent) => void;
  onConnectionChange?: (connected: boolean) => void;
}

export function useChatWebSocket({
  roomId,
  token,
  userId,
  onMessage,
  onTyping,
  onPresence,
  onReadReceipt,
  onUserJoined,
  onUserLeft,
  onConnectionChange,
}: UseChatWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [roomUsers, setRoomUsers] = useState<WsRoomUser[]>([]);
  const [typingUserNames, setTypingUserNames] = useState<string[]>([]);

  const cleanup = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.onerror = null;
      wsRef.current.onmessage = null;
      if (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING) {
        wsRef.current.close();
      }
      wsRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (!roomId || !token) return;

    cleanup();

    const wsUrl = API_URL.replace(/^http/, "ws");
    const ws = new WebSocket(`${wsUrl}/ws/chat/${roomId}?token=${encodeURIComponent(token)}`);

    ws.onopen = () => {
      setIsConnected(true);
      setTypingUserNames([]);
      onConnectionChange?.(true);

      pingIntervalRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "ping" }));
        }
      }, 25000);
    };

    ws.onclose = () => {
      setIsConnected(false);
      setRoomUsers([]);
      onConnectionChange?.(false);

      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
      }

      reconnectTimerRef.current = setTimeout(() => {
        connect();
      }, 3000);
    };

    ws.onerror = () => {
      ws.close();
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WsEvent;

        switch (data.type) {
          case "message":
            onMessage?.(data);
            break;
          case "typing":
            setTypingUserNames(data.typing_user_names);
            onTyping?.(data);
            break;
          case "presence":
            setRoomUsers(data.users);
            onPresence?.(data);
            break;
          case "read_receipt":
            onReadReceipt?.(data);
            break;
          case "user_joined":
            setRoomUsers(data.users);
            onUserJoined?.(data);
            break;
          case "user_left":
            setRoomUsers(data.users);
            onUserLeft?.(data);
            break;
        }
      } catch {
        // ignore parse errors
      }
    };

    wsRef.current = ws;
  }, [roomId, token, cleanup, onConnectionChange, onMessage, onTyping, onPresence, onReadReceipt, onUserJoined, onUserLeft]);

  useEffect(() => {
    connect();
    return cleanup;
  }, [connect, cleanup]);

  const sendMessage = useCallback(
    (content: string, messageType = "text") => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "message", content, message_type: messageType }));
      }
    },
    []
  );

  const sendTyping = useCallback((isTyping: boolean) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "typing", is_typing: isTyping }));
    }
  }, []);

  const sendReadReceipt = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "read_receipt" }));
    }
  }, []);

  const sendPresence = useCallback((status: "online" | "away" | "busy") => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "presence", status }));
    }
  }, []);

  return {
    isConnected,
    roomUsers,
    typingUserNames,
    sendMessage,
    sendTyping,
    sendReadReceipt,
    sendPresence,
  };
}
