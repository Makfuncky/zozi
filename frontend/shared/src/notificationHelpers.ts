/**
 * Shared helpers for notifications — used by both web_app and mobile_app.
 */

export type NotificationType =
  | "order_update"
  | "payment"
  | "promotion"
  | "review"
  | "system"
  | "supplier"
  | "return"
  | "wishlist"
  | "info";

export interface AppNotification {
  id: number;
  user_id?: number;
  type: NotificationType;
  title: string;
  message: string;
  read: boolean;
  link?: string;
  created_at: string;
}

export const NOTIFICATION_ICON: Record<NotificationType, string> = {
  order_update: "📦",
  payment: "💳",
  promotion: "🏷️",
  review: "⭐",
  system: "🔔",
  supplier: "🏪",
  return: "↩️",
  wishlist: "❤️",
  info: "ℹ️",
};

export const NOTIFICATION_COLOR: Record<NotificationType, string> = {
  order_update: "#3b82f6",
  payment: "#22c55e",
  promotion: "#f59e0b",
  review: "#a855f7",
  system: "#6b7280",
  supplier: "#14b8a6",
  return: "#ef4444",
  wishlist: "#ec4899",
  info: "#64748b",
};

export function normalizeNotificationType(type?: string): NotificationType {
  const valid: NotificationType[] = [
    "order_update", "payment", "promotion", "review",
    "system", "supplier", "return", "wishlist", "info",
  ];
  const key = (type ?? "info").toLowerCase() as NotificationType;
  return valid.includes(key) ? key : "info";
}

export function groupNotificationsByDate(
  notifications: AppNotification[]
): { date: string; items: AppNotification[] }[] {
  const groups: Record<string, AppNotification[]> = {};
  for (const n of notifications) {
    const date = new Date(n.created_at).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
    if (!groups[date]) groups[date] = [];
    groups[date].push(n);
  }
  return Object.entries(groups).map(([date, items]) => ({ date, items }));
}

export function countUnread(notifications: AppNotification[]): number {
  return notifications.filter((n) => !n.read).length;
}
