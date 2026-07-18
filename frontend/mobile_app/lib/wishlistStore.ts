import { create } from "zustand";
import { WishlistEntry } from "@shared/types";
import { apiFetch } from "@/lib/api";

interface WishlistState {
  items: WishlistEntry[];
  isLoading: boolean;
  fetch: () => Promise<void>;
  add: (productId: number) => Promise<void>;
  remove: (productId: number) => Promise<void>;
  has: (productId: number) => boolean;
}

export const useWishlistStore = create<WishlistState>((set, get) => ({
  items: [],
  isLoading: false,

  async fetch() {
    set({ isLoading: true });
    try {
      const data = await apiFetch<WishlistEntry[]>("/wishlist");
      set({ items: Array.isArray(data) ? data : [] });
    } catch {
      // stay with local state
    } finally {
      set({ isLoading: false });
    }
  },

  async add(productId) {
    await apiFetch(`/wishlist/${productId}`, { method: "POST" });
    await get().fetch();
  },

  async remove(productId) {
    await apiFetch(`/wishlist/${productId}`, { method: "DELETE" });
    set({ items: get().items.filter((i) => i.product_id !== productId) });
  },

  has(productId) {
    return get().items.some((i) => i.product_id === productId);
  },
}));
