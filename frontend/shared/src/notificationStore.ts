import { createStore } from "zustand/vanilla";

export interface NotificationReadState {
  read: boolean;
}

export interface RealtimeUserMessage {
  type: string;
  action?: string | null;
  title?: string | null;
  message?: string | null;
  link?: string | null;
  level?: "success" | "error" | "info" | "warning" | null;
  audit_id?: number;
  product_id?: number;
  payout_id?: number;
  notification_id?: number;
  notification_type?: string | null;
  supplier_id?: number;
  ticket_id?: number;
  reply_id?: number;
  status?: string | null;
  read?: boolean;
  is_admin?: boolean;
  created_at?: string | null;
}

export interface NotificationStoreState {
  unreadCount: number;
  applyRealtimeMessage: (payload: RealtimeUserMessage | null) => void;
  recalcUnreadCount: (notifications: NotificationReadState[]) => void;
  reset: () => void;
  setUnreadCount: (count: number) => void;
}

function clampUnreadCount(value: number): number {
  return Math.max(0, value);
}

function nextUnreadCount(currentCount: number, payload: RealtimeUserMessage | null): number {
  if (!payload) {
    return currentCount;
  }

  if (payload.type === "notification.created") {
    return payload.read ? currentCount : currentCount + 1;
  }

  if (payload.type === "notification.updated" && payload.read === true) {
    return clampUnreadCount(currentCount - 1);
  }

  if (payload.type === "notification.deleted" && payload.read === false) {
    return clampUnreadCount(currentCount - 1);
  }

  return currentCount;
}

export const notificationStore = createStore<NotificationStoreState>((set) => ({
  unreadCount: 0,
  applyRealtimeMessage(payload) {
    set((state) => ({ unreadCount: nextUnreadCount(state.unreadCount, payload) }));
  },
  recalcUnreadCount(notifications) {
    set({ unreadCount: notifications.filter((notification) => !notification.read).length });
  },
  reset() {
    set({ unreadCount: 0 });
  },
  setUnreadCount(count) {
    set({ unreadCount: clampUnreadCount(count) });
  },
}));