/**
 * Recently Viewed Products — localStorage-based store.
 * Tracks the last N product snapshots visited. Used on product detail pages
 * and the browsing history widget.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";

const MAX_ITEMS = 16;

export interface ViewedProduct {
  id: number;
  name: string;
  price: number;
  image_url?: string;
  category?: string;
  rating?: number;
  viewedAt: number; // unix ms
}

interface RecentlyViewedState {
  products: ViewedProduct[];
  track: (product: ViewedProduct) => void;
  clear: () => void;
  ids: number[]; // convenience getter
}

export const useRecentlyViewedStore = create<RecentlyViewedState>()(
  persist(
    (set, get) => ({
      products: [],

      get ids() {
        return get().products.map((p) => p.id);
      },

      track: (product: ViewedProduct) => {
        const now = Date.now();
        const entry: ViewedProduct = { ...product, viewedAt: now };
        const filtered = get().products.filter((p) => p.id !== product.id);
        const updated = [entry, ...filtered].slice(0, MAX_ITEMS);
        set({ products: updated });
      },

      clear: () => set({ products: [] }),
    }),
    {
      name: "zozi_recently_viewed",
      // Only persist the products array
      partialize: (s) => ({ products: s.products }),
    }
  )
);
