import { useStore } from "zustand";
import { notificationStore, type NotificationStoreState } from "@shared/notificationStore";

export { notificationStore };

export function useNotificationStore<T>(selector: (state: NotificationStoreState) => T): T {
  return useStore(notificationStore, selector);
}