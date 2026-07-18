"use client";

import { useAuth } from "./useAuth";
import { useAuthModalStore } from "./authModalStore";

export function useRequireAuthAction() {
  const { isLoggedIn } = useAuth();
  const open = useAuthModalStore((state) => state.open);

  return (action: () => void | Promise<void>) => {
    if (isLoggedIn) {
      return action();
    }
    open("login", action);
  };
}
