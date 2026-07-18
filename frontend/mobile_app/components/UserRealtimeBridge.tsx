import { useCallback, useEffect } from "react";
import { getNotifications } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";
import { notificationStore, useNotificationStore } from "@/lib/notificationStore";
import { toast } from "@/lib/toastStore";
import { connectUserRealtimeSocket } from "@/lib/userRealtime";
import { buildRealtimeAlert } from "@shared/userRealtimeAlerts";

export function UserRealtimeBridge() {
  const { isLoggedIn } = useAuthStore();
  const recalcUnreadCount = useNotificationStore((state) => state.recalcUnreadCount);
  const reset = useNotificationStore((state) => state.reset);

  const loadUnreadCount = useCallback(async () => {
    const notifications = await getNotifications();
    recalcUnreadCount(Array.isArray(notifications) ? notifications : []);
  }, [recalcUnreadCount]);

  useEffect(() => {
    if (!isLoggedIn) {
      reset();
      return;
    }

    void loadUnreadCount().catch(() => reset());
  }, [isLoggedIn, loadUnreadCount, reset]);

  useEffect(() => {
    if (!isLoggedIn) {
      return;
    }

    const socket = connectUserRealtimeSocket(
      () => undefined,
      (payload) => {
        notificationStore.getState().applyRealtimeMessage(payload);

        const alert = buildRealtimeAlert(payload);
        if (!alert) {
          return;
        }

        switch (alert.tone) {
          case "success":
            toast.success(alert.message);
            break;
          case "error":
            toast.error(alert.message);
            break;
          case "warning":
            toast.warning(alert.message);
            break;
          default:
            toast.info(alert.message);
        }
      },
    );

    return () => {
      socket?.close();
    };
  }, [isLoggedIn]);

  return null;
}