import { API_BASE, getCurrentAccessToken } from "@/lib/api";
import { openRealtimeSocket, type RealtimeStatus, type RealtimeSocketHandle } from "@shared/realtime";
import type { RealtimeUserMessage } from "@shared/notificationStore";

export function buildUserRealtimeSocketUrl(): string | null {
  const token = getCurrentAccessToken();
  if (!token) return null;
  return `${API_BASE.replace(/^http/i, "ws").replace(/\/$/, "")}/ws/user?token=${encodeURIComponent(token)}`;
}

export function connectUserRealtimeSocket(
  onStatusChange: (status: RealtimeStatus) => void,
  onMessage: (payload: RealtimeUserMessage | null) => void,
): RealtimeSocketHandle {
  return openRealtimeSocket<RealtimeUserMessage>(buildUserRealtimeSocketUrl(), {
    onStatusChange,
    onMessage,
  });
}

export function isNotificationRealtimeMessage(payload: RealtimeUserMessage | null): boolean {
  return !!payload?.type?.startsWith("notification.");
}

export function isTicketRealtimeMessage(payload: RealtimeUserMessage | null): boolean {
  return !!payload?.type?.startsWith("ticket.");
}

export function isAdminAlertRealtimeMessage(payload: RealtimeUserMessage | null): boolean {
  return !!payload?.type?.startsWith("admin.alert.");
}