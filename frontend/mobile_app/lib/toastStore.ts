import { create } from "zustand";

export interface Toast {
  id: string;
  type: "success" | "error" | "info" | "warning";
  message: string;
}

interface ToastState {
  toasts: Toast[];
  show: (type: Toast["type"], message: string, durationMs?: number) => void;
  dismiss: (id: string) => void;
}

let _uid = 0;

export const useToastStore = create<ToastState>((set, get) => ({
  toasts: [],
  show(type, message, durationMs = 3500) {
    const id = String(++_uid);
    set({ toasts: [...get().toasts, { id, type, message }] });
    setTimeout(() => get().dismiss(id), durationMs);
  },
  dismiss(id) {
    set({ toasts: get().toasts.filter((t) => t.id !== id) });
  },
}));

// Convenience helpers
export const toast = {
  success: (msg: string) => useToastStore.getState().show("success", msg),
  error: (msg: string) => useToastStore.getState().show("error", msg),
  info: (msg: string) => useToastStore.getState().show("info", msg),
  warning: (msg: string) => useToastStore.getState().show("warning", msg),
};
