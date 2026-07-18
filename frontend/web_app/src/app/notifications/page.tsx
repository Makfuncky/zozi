"use client";

import { Button } from "@/components/ui/Button";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Bell, CheckCheck, Trash2, Package, AlertTriangle, Info } from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { connectUserRealtimeSocket, isNotificationRealtimeMessage } from "@/lib/userRealtime";
import { useNotificationStore } from "@/lib/notificationStore";
import { useAuth } from "@/lib/useAuth";
import { Notification } from "@/lib/types";
import { createRealtimeRefreshScheduler } from "@shared/realtime";

const TYPE_ICON: Record<string, React.ElementType> = {
  order_update: Package,
  low_stock: AlertTriangle,
  payout: CheckCheck,
  system: Info,
};

const TYPE_COLOR: Record<string, string> = {
  order_update: "theme-status-info",
  low_stock: "theme-status-warning",
  payout: "theme-status-success",
  system: "text-text-muted",
};

export default function NotificationsPage() {
  const { isLoggedIn, isLoading } = useAuth();
  const router = useRouter();
  const [notifs, setNotifs] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const recalcUnreadCount = useNotificationStore((state) => state.recalcUnreadCount);
  const resetUnreadCount = useNotificationStore((state) => state.reset);
  const loadNotifications = useCallback(async ({ silent = false }: { silent?: boolean } = {}) => {
    if (!silent) {
      setLoading(true);
    }
    try {
      const response = await apiFetch("/notifications");
      if (response.ok) {
        const data = await response.json();
        setNotifs(Array.isArray(data) ? data : []);
      } else {
        setNotifs([]);
      }
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
    // Intentionally excluding recalcUnreadCount and resetUnreadCount - they are stable store references
  }, []);

  useEffect(() => {
    if (isLoading) {
      return;
    }

    if (!isLoggedIn) {
      resetUnreadCount();
      return;
    }

    recalcUnreadCount(notifs);
  }, [isLoading, isLoggedIn, notifs, recalcUnreadCount, resetUnreadCount]);

  useEffect(() => {
    if (isLoading) {
      return;
    }
    if (!isLoggedIn) {
      setLoading(false);
      router.push("/login");
      return;
    }

    void loadNotifications();
  }, [isLoggedIn, isLoading, loadNotifications, router]);
  useEffect(() => {
    if (isLoading || !isLoggedIn) {
      return;
    }

    const scheduler = createRealtimeRefreshScheduler(() => loadNotifications({ silent: true }));

    const socket = connectUserRealtimeSocket(
      () => undefined,
      (payload) => {
        if (isNotificationRealtimeMessage(payload)) {
          scheduler.trigger();
        }
      },
    );

    return () => {
      scheduler.cancel();
      socket?.close();
    };
  }, [isLoading, isLoggedIn, loadNotifications]);

  const markAllRead = async () => {
    await apiFetch("/notifications/read-all", { method: "PUT" });
    setNotifs((ns) => ns.map((n) => ({ ...n, read: true })));
  };

  const markRead = async (id: number) => {
    await apiFetch(`/notifications/${id}/read`, { method: "PUT" });
    setNotifs((ns) => ns.map((n) => n.id === id ? { ...n, read: true } : n));
  };

  const deleteNotif = async (id: number) => {
    await apiFetch(`/notifications/${id}`, { method: "DELETE" });
    setNotifs((ns) => ns.filter((n) => n.id !== id));
  };

  const unreadCount = notifs.filter((n) => !n.read).length;

  return (
    <main className="min-h-screen">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-10">
        {/* Title row */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Bell className="theme-status-info h-5 w-5 text-primary" />
            <h1 className="text-xl font-bold text-text">Notifications</h1>
            {unreadCount > 0 && (
              <span className="theme-chip-warning rounded-full px-2 py-0.5 text-[11px] font-bold">
                {unreadCount} new
              </span>
            )}
          </div>
          {unreadCount > 0 && (
            <Button variant="primary" onClick={markAllRead}>
              <CheckCheck className="w-4 h-4" />
              Mark all as read
            </Button>
          )}
        </div>

        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-16 rounded-2xl bg-surface-2 animate-pulse" />
            ))}
          </div>
        ) : notifs.length === 0 ? (
          <div className="text-center py-20 text-text-faint">
            <Bell className="w-10 h-10 mx-auto mb-3 text-accent/30" />
            <p className="text-sm">No notifications yet</p>
          </div>
        ) : (
          <div className="space-y-2">
            {notifs.map((n) => {
              const Icon = TYPE_ICON[n.type] ?? Info;
              const color = TYPE_COLOR[n.type] ?? "text-text-muted";
              return (
                <motion.div
                  key={n.id}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  onClick={() => { if (!n.read) markRead(n.id); if (n.link) router.push(n.link); }}
                  className={`flex items-start gap-3 p-4 rounded-2xl border cursor-pointer transition-all ${
                    n.read
                      ? "theme-card border opacity-60"
                        : "theme-card border border-primary/20 shadow-card-sm"
                  }`}
                >
                  <div className={`mt-0.5 ${color}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-semibold ${n.read ? "text-text-muted" : "text-text"}`}>
                      {n.title}
                    </p>
                  <p className="text-xs text-text-faint mt-0.5">{n.message}</p>
                  <p className="text-[11px] text-text-faint mt-1">
                      {new Date(n.created_at).toLocaleString()}
                    </p>
                  </div>
                  {!n.read && (
                    <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary" />
                  )}
                  <button
                    onClick={(e) => { e.stopPropagation(); deleteNotif(n.id); }}
                    className="theme-action-danger rounded-lg p-1 text-text-faint"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>
    </main>
  );
}


