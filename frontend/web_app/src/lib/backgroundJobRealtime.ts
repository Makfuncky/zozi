import { API_URL } from "@/lib/api";
import { openRealtimeSocket, type RealtimeStatus, type RealtimeSocketHandle } from "@shared/realtime";

export type { RealtimeStatus } from "@shared/realtime";

export interface BackgroundJobWSMessage {
  event: "sweep_completed";
  sweep_name: "supplier" | "logistics";
  status: string;
  processed: number;
  batch_number: string | null;
  timestamp: string;
}

/**
 * Build the WebSocket URL for the admin background-jobs room.
 * No auth token is needed — the backend accepts any connection
 * (room is only accessible from the admin dashboard page).
 */
export function buildBackgroundJobSocketUrl(): string {
  return `${API_URL.replace(/^http/i, "ws").replace(/\/$/, "")}/ws/admin/background-jobs`;
}

/**
 * Connect to the admin background-jobs WebSocket.
 * Returns a handle with `.close()` to disconnect.
 */
export function connectBackgroundJobSocket(
  onStatusChange: (status: RealtimeStatus) => void,
  onMessage: (payload: BackgroundJobWSMessage | null) => void,
): RealtimeSocketHandle {
  return openRealtimeSocket<BackgroundJobWSMessage>(buildBackgroundJobSocketUrl(), {
    onStatusChange,
    onMessage,
    autoReconnect: true,
    maxReconnectAttempts: 20,
  });
}
