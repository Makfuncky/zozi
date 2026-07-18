"use client";

import { useCallback, useEffect } from "react";
import { apiFetch } from "@/lib/api";
import { notificationStore, useNotificationStore } from "@/lib/notificationStore";
import { useAuth } from "@/lib/useAuth";
import { useToastStore } from "@/lib/toastStore";
import { connectUserRealtimeSocket } from "@/lib/userRealtime";
import { buildRealtimeAlert } from "@shared/userRealtimeAlerts";

export default function UserRealtimeBridge() {
  const { isLoggedIn, isLoading } = useAuth();
  const addToast = useToastStore((state) => state.addToast);
  const recalcUnreadCount = useNotificationStore((state) => state.recalcUnreadCount);
  const reset = useNotificationStore((state) => state.reset);

  const loadUnreadCount = useCallback(async () => {
    const response = await apiFetch("/notifications");
    if (!response.ok) {
      reset();
      return;
    }

    const notifications = await response.json();
    recalcUnreadCount(Array.isArray(notifications) ? notifications : []);
  }, [recalcUnreadCount, reset]);

  useEffect(() => {
    if (isLoading) {
      return;
    }

    if (!isLoggedIn) {
      reset();
      return;
    }

    void loadUnreadCount().catch(() => reset());
  }, [isLoading, isLoggedIn, loadUnreadCount, reset]);

  useEffect(() => {
    if (isLoading || !isLoggedIn) {
      return;
    }

    const socket = connectUserRealtimeSocket(
      () => undefined,
      (payload) => {
        notificationStore.getState().applyRealtimeMessage(payload);

        const alert = buildRealtimeAlert(payload);
        if (alert) {
          addToast(alert.message, alert.tone);
        }
      },
    );

    return () => {
      socket?.close();
    };
  }, [addToast, isLoading, isLoggedIn]);

  return null;
}


