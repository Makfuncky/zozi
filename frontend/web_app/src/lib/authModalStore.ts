"use client";

import { create } from "zustand";
import { useAuth } from "./useAuth";

export type AuthModalMode = "login" | "register";
type PendingAction = (() => void | Promise<void>) | null;

interface ResolvedOpenConfig {
  mode: AuthModalMode;
  pendingAction: PendingAction;
  initialError: string | null;
}

function resolveOpenConfig(
  modeOrAction?: AuthModalMode | PendingAction,
  actionOrError?: PendingAction | string | null,
  maybeError?: string | null,
): ResolvedOpenConfig {
  const base: ResolvedOpenConfig = {
    mode: "login",
    pendingAction: null,
    initialError: null,
  };

  if (modeOrAction === "login" || modeOrAction === "register") {
    base.mode = modeOrAction;
    if (typeof actionOrError === "function") {
      base.pendingAction = actionOrError;
      if (typeof maybeError === "string") {
        base.initialError = maybeError;
      }
      return base;
    }
    if (typeof actionOrError === "string") {
      base.initialError = actionOrError;
      return base;
    }
    return base;
  }

  if (typeof modeOrAction === "function") {
    base.pendingAction = modeOrAction;
    if (typeof actionOrError === "string") {
      base.initialError = actionOrError;
    }
    return base;
  }

  if (typeof actionOrError === "string") {
    base.initialError = actionOrError;
  }

  return base;
}

interface AuthModalState {
  isOpen: boolean;
  mode: AuthModalMode;
  initialError: string | null;
  pendingAction: PendingAction;
  open: (
    modeOrAction?: AuthModalMode | PendingAction,
    actionOrError?: PendingAction | string | null,
    maybeError?: string | null,
  ) => void;
  close: () => void;
  setMode: (mode: AuthModalMode) => void;
  setInitialError: (error: string | null) => void;
  consumePendingAction: () => PendingAction;
}

export const useAuthModalStore = create<AuthModalState>((set, get) => ({
  isOpen: false,
  mode: "login",
  initialError: null,
  pendingAction: null,
  open: (modeOrAction, actionOrError = null, maybeError = null) => {
    const next = resolveOpenConfig(modeOrAction, actionOrError, maybeError);
    set({
      isOpen: true,
      mode: next.mode,
      initialError: next.initialError,
      pendingAction: next.pendingAction,
    });
  },
  close: () => set({ isOpen: false, pendingAction: null, initialError: null }),
  setMode: (mode) => set({ mode }),
  setInitialError: (initialError) => set({ initialError }),
  consumePendingAction: () => {
    const action = get().pendingAction;
    set({ pendingAction: null });
    return action;
  },
}));

export function useRequireAuthAction() {
  const { isLoggedIn } = useAuth();
  const open = useAuthModalStore((state) => state.open);

  return (action: () => void | Promise<void>) => {
    if (isLoggedIn) {
      return action();
    }
    open(action);
  };
}
