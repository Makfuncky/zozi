import { API_URL, getAccessToken } from "@/lib/api";
import { openRealtimeSocket, type RealtimeStatus, type RealtimeSocketHandle } from "@shared/realtime";

export type { RealtimeStatus } from "@shared/realtime";

export function buildTrackingSocketUrl(orderId: string): string | null {
  const token = getAccessToken();
  if (!token) return null;
  return `${API_URL.replace(/^http/i, "ws").replace(/\/$/, "")}/ws/logistics?scope=order&order_id=${encodeURIComponent(orderId)}&token=${encodeURIComponent(token)}`;
}

export function connectTrackingSocket(
  orderId: string,
  onStatusChange: (status: RealtimeStatus) => void,
  onMessage: () => void,
): RealtimeSocketHandle {
  return openRealtimeSocket(buildTrackingSocketUrl(orderId), {
    onStatusChange,
    onMessage: () => onMessage(),
  });
}
