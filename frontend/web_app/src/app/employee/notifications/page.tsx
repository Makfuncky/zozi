"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Bell, CheckCircle, AlertTriangle, Info } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";

interface Notification {
  id: number;
  type: string;
  title: string;
  message: string | null;
  is_read: boolean;
  action_url: string | null;
  entity_type: string | null;
  entity_id: number | null;
  created_at: string;
}

const TYPE_ICONS: Record<string, typeof Bell> = {
  task: AlertTriangle,
  info: Info,
  success: CheckCircle,
  warning: AlertTriangle,
};

const TYPE_COLORS: Record<string, string> = {
  task: "bg-info/10 text-info",
  info: "bg-primary/10 text-primary",
  success: "bg-success/10 text-success",
  warning: "bg-warning/10 text-warning",
};

export default function EmployeeNotificationsPage() {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch("/api/v1/employee/hr/notifications");
      if (res.ok) setNotifications(await res.json());
    } catch {
      setNotifications([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const markAsRead = async (notificationId: number) => {
    try {
      await apiFetch(`/api/v1/employee/hr/notifications/${notificationId}/read`, {
        method: "POST",
      });
      setNotifications((prev) =>
        prev.map((n) => (n.id === notificationId ? { ...n, is_read: true } : n))
      );
    } catch {
      // ignore
    }
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <PanelContent className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-text">Notifications</h1>
          <p className="text-sm text-text-muted mt-1">
            {unreadCount > 0
              ? `${unreadCount} unread notification${unreadCount > 1 ? "s" : ""}`
              : "All caught up!"}
          </p>
        </div>
      </div>

      {loading ? (
        <PanelLoadingState
          count={5}
          className="!mt-0 space-y-3"
          blockClassName="h-16 rounded-xl bg-surface-2 animate-pulse"
        />
      ) : notifications.length === 0 ? (
        <div className="rounded-xl border border-border bg-surface p-8 text-center">
          <Bell className="h-12 w-12 mx-auto mb-3 text-text-muted" />
          <p className="text-sm font-medium text-text">No notifications</p>
          <p className="text-xs text-text-muted mt-1">
            You're all caught up! Check back later.
          </p>
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-2"
        >
          {notifications.map((notification) => {
            const Icon = TYPE_ICONS[notification.type] || Bell;
            const colorClass = TYPE_COLORS[notification.type] || "bg-gray-100 text-gray-500";
            return (
              <div
                key={notification.id}
                className={`rounded-xl border p-4 transition-colors ${
                  notification.is_read
                    ? "border-border bg-surface"
                    : "border-primary/30 bg-primary/5"
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`rounded-lg p-2 ${colorClass}`}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="text-sm font-semibold text-text truncate">
                        {notification.title}
                      </h3>
                      {!notification.is_read && (
                        <button
                          onClick={() => markAsRead(notification.id)}
                          className="text-xs text-primary hover:underline"
                        >
                          Mark read
                        </button>
                      )}
                    </div>
                    {notification.message && (
                      <p className="text-xs text-text-muted mt-1">
                        {notification.message}
                      </p>
                    )}
                    <p className="text-xs text-text-muted mt-2">
                      {new Date(notification.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </motion.div>
      )}
    </PanelContent>
  );
}
