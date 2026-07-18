"use client";

import { create } from "zustand";
import { apiFetch, getAccessToken } from "./api";

interface WishlistState {
  ids: number[];
  synced: boolean;
  add: (id: number) => void;
  remove: (id: number) => void;
  isInWishlist: (id: number) => boolean;
  initialize: () => void;
  syncFromBackend: () => Promise<void>;
}

const KEY = "wishlist";

function persistLocal(ids: number[]) {
  if (typeof window !== "undefined") {
    localStorage.setItem(KEY, JSON.stringify(ids));
  }
}

function hydrateLocal(): number[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function hasAuthToken(): boolean {
  if (typeof window === "undefined") return false;
  return getAccessToken() !== null;
}

export const useWishlistStore = create<WishlistState>((set, get) => ({
  ids: [],
  synced: false,

  add: (id) => {
    set((s) => {
      if (s.ids.includes(id)) return s;
      const next = [...s.ids, id];
      persistLocal(next);
      // Fire-and-forget backend sync when logged in
      if (hasAuthToken()) {
        apiFetch(`/wishlist/${id}`, { method: "POST" }).catch(() => null);
      }
      return { ids: next };
    });
  },

  remove: (id) => {
    set((s) => {
      const next = s.ids.filter((i) => i !== id);
      persistLocal(next);
      // Fire-and-forget backend sync when logged in
      if (hasAuthToken()) {
        apiFetch(`/wishlist/${id}`, { method: "DELETE" }).catch(() => null);
      }
      return { ids: next };
    });
  },

  isInWishlist: (id) => get().ids.includes(id),

  initialize: () => {
    const localIds = hydrateLocal();
    set({ ids: localIds });
    // Async backend sync — doesn't block UI, silently merges
    if (hasAuthToken()) {
      get().syncFromBackend();
    }
  },

  syncFromBackend: async () => {
    if (get().synced) return;
    try {
      const res = await apiFetch("/wishlist");
      if (!res.ok) return;
      const items: { product_id: number }[] = await res.json();
      const backendIds = items.map((i) => i.product_id);
      const localIds = hydrateLocal();
      // Union: both backend and any local-only items
      const merged = Array.from(new Set([...backendIds, ...localIds]));
      // Push local-only items to the backend so they're persisted
      for (const id of localIds) {
        if (!backendIds.includes(id)) {
          apiFetch(`/wishlist/${id}`, { method: "POST" }).catch(() => null);
        }
      }
      persistLocal(merged);
      set({ ids: merged, synced: true });
    } catch {
      // Silently fail — localStorage data stays intact
    }
  },
}));
